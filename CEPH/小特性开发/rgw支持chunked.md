1. 由于CSP不支持chunked编码
2. 需要在Node JS SDK调用cos.putObject 接口时，传入文件大小到 ContentLength 字段，才能保证cos.putObject 不使用chunked，否则cos.putObject 有可能在某些情况下使用chunked
3. 在proxy_request_bufferring on时，stgw会把chunked转成content length（这个说法是我用社区版nginx测试的，最好等stgw的同学确认一下），所以无论cos.putObject是否指定ContentLength 字段，都能正常操作，而规避CSP不支持chunked的问题（这个说法是我用社区版nginx测试的，最要等stgw的同学确认一下）
4. 在proxy_request_bufferring off时，对应几百KB以上的文件，stgw会把chunked透传（没有转成content length，这个说法是我用社区版nginx测试的，最好等stgw的同学确认一下），所以就会看到CSP不支持chunked所引起的size 0的问题
5. 上述3和4是为了解释为啥stgw变更前会不一样，但无论在proxy_request_bufferring off或on时，都建议在cos.putObject的调用指定ContentLength以确保适应两种场景"

```shell
# 2011年的一个commit，支持Swift的chunked PUT Object，但故意封掉S3
https://github.com/ceph/ceph/commit/7726e78d44f25205accb85ed16dd861048d2eace

# 2012年的一个commit，有意封掉chunked POST Object，无论Swift还是S3
# 由于需要从表单中读入信息到内存中，用于鉴权，估计加入这个是为了防止DoS攻击打爆内存
https://github.com/ceph/ceph/commit/391775b78e5c5e6ab6262a0ac0765160189c246b

# 思路
# 1. 添加配置项rgw_s3_allow_chunked_put_obj=false/true，默认值为false
# 2. 参考Swift的代码，在 rgw_s3_allow_chunked_put_obj=true时，支持S3和COSv5的chunked put object
# 3. 用shell对Atomic和分片上传都验证chunked put object
# 4. 由于POST是用于表单上传，SDK中并不使用，Swift和S3也都不支持，暂不考虑调整
```

这里简单地测过普通上传和分片上传的，md5比对过是一致的。没有想明白为什么社区版的S3不放开，明明不需要做什么改动。。

有content length，一下子就可以判断大小是否超过5GB了，如果chunked要写了很多数据之后才知道，这时已经白收了好多数据，还得清理，多麻烦。
作为厂商，明显content length的限制更省成本。

## rgw中令S3支持chunked上传

### 原理

content-length的获得：

```c++
const char* content_length = info.env->get("CONTENT_LENGTH");
const char* http_content_length = info.env->get("HTTP_CONTENT_LENGTH");
if (!http_content_length != !content_length) {
  /* Easy case: one or the other is missing */
  s->length = (content_length ? content_length : http_content_length);
  ...
    s->length = content_length;
  // End of: else if (s->cct->_conf->rgw_content_length_compat &&
  //   content_length &&
  // http_content_length)
} else {
  /* no content length was defined */
  s->length = NULL;
}

if (s->length) {
  if (*s->length == '\0') {
    s->content_length = 0;
  } else {
    string err;
    s->content_length = strict_strtoll(s->length, 10, &err);
    if (!err.empty()) {
      ldout(s->cct, 10) << "bad content length, aborting" << dendl;
      return -EINVAL;
    }
  }
}

if (s->content_length < 0) {
  ldout(s->cct, 10) << "negative content length, aborting" << dendl;
  return -EINVAL;
}
```



```c++
//从req_state中拿出一块长为cl的数据到bp
//意味着此时req_state中已经有客户端的所有数据了？
int RGWPutObj_ObjStore::get_data(bufferlist& bl) {
  size_t cl;
  uint64_t chunk_size = s->cct->_conf->rgw_max_chunk_size;//默认为4MB
  if (s->length) {//若为包含content-length，则cl为length减去ofs
    cl = atoll(s->length) - ofs;//ofs表示当前处理到的数据的位置起始点，cl表示本次要处理的数据长度。这个长度若大于rgw_max_chunk_size，就切割出一个rgw_max_chunk_size大小的块，否则直接用自身的长度
    if (cl > chunk_size)
      cl = chunk_size;
  } else {//若为chunked，则直接使本次处理的cl=4MB
    cl = chunk_size;
  }

  int len = 0;
  {
    ACCOUNTING_IO(s)->set_account(true);
    bufferptr bp(cl);//开辟一块cl大小的buffer。cl表示当前要处理的数据长度
		//从req_state中接收到buffer，函数详见下文。
    //问题：此处是如何记住之前recv到哪里的？
    //此时即使每次都指定了cl为4MB，剩余的不足4MB，也会自动切割保留有效数据。
    //若是这样，那前面s->length中的判断作用是什么？仅仅是减少bufferptr的空间浪费？
    const auto read_len  = recv_body(s, bp.c_str(), cl);
    if (read_len < 0) {
      return read_len;
    }
    len = read_len;
    bl.append(bp, 0, len);
    ACCOUNTING_IO(s)->set_account(false);
  }
  if ((uint64_t)ofs + len > s->cct->_conf->rgw_max_put_size) {
    return -ERR_TOO_LARGE;
  }
  return len;
}

//
int recv_body(struct req_state* const s,
              char* const buf,
              const size_t max)
{
  try {
    return RESTFUL_IO(s)->recv_body(buf, max);
  } catch (rgw::io::Exception& e) {
    return -e.code().value();
  }
}
//src/rgw/rgw_asio_frontend.cc
size_t recv_body(char* buf, size_t max) override {
    auto& message = parser.get();
    auto& body_remaining = message.body();
    body_remaining.data = buf;
    body_remaining.size = max;

    while (body_remaining.size && !parser.is_done()) {
      boost::system::error_code ec;
      http::read_some(stream, buffer, parser, ec);
      if (ec == http::error::need_buffer) {
        break;
      }
      if (ec) {
        ldout(cct, 4) << "failed to read body: " << ec.message() << dendl;
        throw rgw::io::Exception(ec.value(), std::system_category());
      }
    }
    return max - body_remaining.size;//body_remaining.size记录当前剩余的数据的size
  }
};
```



```c++
std::tuple<int, bufferlist > rgw_rest_read_all_input(struct req_state *s,
                                        const uint64_t max_len,
                                        const bool allow_chunked)
{
  size_t cl = 0;
  int len = 0;
  bufferlist bl;

  if (s->length)
    cl = atoll(s->length);
  else if (!allow_chunked)
    return std::make_tuple(-ERR_LENGTH_REQUIRED, std::move(bl));

  if (cl) {
    if (cl > (size_t)max_len) {
      return std::make_tuple(-ERANGE, std::move(bl));
    }

    bufferptr bp(cl + 1);
  
    len = recv_body(s, bp.c_str(), cl);
    if (len < 0) {
      return std::make_tuple(len, std::move(bl));
    }

    bp.c_str()[len] = '\0';
    bp.set_length(len);
    bl.append(bp);

  } else if (allow_chunked && !s->length) {
    const char *encoding = s->info.env->get("HTTP_TRANSFER_ENCODING");
    if (!encoding || strcmp(encoding, "chunked") != 0)
      return std::make_tuple(-ERR_LENGTH_REQUIRED, std::move(bl));

    int ret = 0;
    std::tie(ret, bl) = read_all_chunked_input(s, max_len);
    if (ret < 0)
      return std::make_tuple(ret, std::move(bl));
  }

  return std::make_tuple(0, std::move(bl));
}
```



### 代码修改



### 测试结果

#### 测试方法

```shell
#!/bin/bash
touch object0_chunked
echo "object0_chunked test" > object0_chunked
OBJECT="TESTFILE_10MB"

s3Key=""
s3Secret=""
BUCKET=bucket0
KEY=$OBJECT
host=127.0.0.1:8000

function put_with_chunked(){
  resource="/$BUCKET/$KEY"
  contentType="text/plain"
  dateValue=$(date -R -u)
  stringToSign="PUT

${contentType}
${dateValue}
${resource}"
  signature=$(/bin/echo -n "$stringToSign" | openssl sha1 -hmac ${s3Secret} -binary | base64)
  curl -X PUT \
    --verbose \
    -H "Date: ${dateValue}" \
    -H "Content-Type: ${contentType}" \
    -H "Authorization: AWS ${s3Key}:${signature}" \
    -H "Transfer-Encoding: chunked" \
    -T "$OBJECT" \
    "http://${host}${resource}"
}

function put_obj_init_multipart(){
  resource="/$BUCKET/$KEY?uploads"
  contentType="text/plain"
  dateValue=$(date -R -u)
  stringToSign="POST

${contentType}
${dateValue}
${resource}"
  signature=$(/bin/echo -n "$stringToSign" | openssl sha1 -hmac ${s3Secret} -binary | base64)
  curl -X POST \
    --verbose \
    -H "Date: ${dateValue}" \
    -H "Content-Type: ${contentType}" \
    -H "Authorization: AWS ${s3Key}:${signature}" \
    -H "Transfer-Encoding: chunked" \
    "http://${host}${resource}"
}

UPLOADID="2~PxW4nFlOgkuVVxV1NS1VpVtqpIeqDSo"
function put_obj_multipart(){
  PARTNUMBER=1
  resource="/$BUCKET/$KEY?partNumber=$PARTNUMBER&uploadId=$UPLOADID"
  contentType="text/plain"
  dateValue=$(date -R -u)
  stringToSign="PUT

${contentType}
${dateValue}
${resource}"
  signature=$(/bin/echo -n "$stringToSign" | openssl sha1 -hmac ${s3Secret} -binary | base64)
  curl -X PUT \
    --verbose \
    -H "Date: ${dateValue}" \
    -H "Content-Type: ${contentType}" \
    -H "Authorization: AWS ${s3Key}:${signature}" \
    -H "Transfer-Encoding: chunked" \
    -T "$OBJECT" \
    "http://${host}${resource}"
}

function put_obj_complete_multipart(){
  resource="/$BUCKET/$KEY?uploadId=$UPLOADID"
  contentType="text/plain"
  dateValue=$(date -R -u)
  stringToSign="POST

${contentType}
${dateValue}
${resource}"
  signature=$(/bin/echo -n "$stringToSign" | openssl sha1 -hmac ${s3Secret} -binary | base64)
  curl -X POST \
    --verbose \
    -H "Date: ${dateValue}" \
    -H "Content-Type: ${contentType}" \
    -H "Authorization: AWS ${s3Key}:${signature}" \
    -H "Transfer-Encoding: chunked" \
    -d '
<CompleteMultipartUpload xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
    <Part>
        <ETag>"52715e3e5a02a64c46d67dd768673211"</ETag>
        <PartNumber>1</PartNumber>
    </Part>
</CompleteMultipartUpload>
' \
    "http://${host}${resource}"
}


function main(){
#put_with_chunked
#put_obj_init_multipart
#put_obj_multipart
put_obj_complete_multipart
}
main
```

## 测试结果

### 普通上传

```shell
[root@vm_3_72_centos ~]# ./chunked_put_obj.sh 
* About to connect() to 127.0.0.1 port 8000 (#0)
*   Trying 127.0.0.1...
* Connected to 127.0.0.1 (127.0.0.1) port 8000 (#0)
> PUT /bucket0/object0_chunked HTTP/1.1
> User-Agent: curl/7.29.0
> Host: 127.0.0.1:8000
> Accept: */*
> Date: Wed, 02 Jun 2021 08:45:15 +0000
> Content-Type: text/plain
> Authorization: AWS 0555b35654ad1656d804:Gv2SUB62srzRf5gN9JQQoVlbJ1I=
> Transfer-Encoding: chunked
> Expect: 100-continue
> 
< HTTP/1.1 100 CONTINUE
< HTTP/1.1 200 OK
< Content-Length: 0
< ETag: "22e314c0dba706c0fbcef3be6d64d34f"
< Accept-Ranges: bytes
< x-amz-request-id: tx00000000000000000002d-0060b7451b-1043-default
< Date: Wed, 02 Jun 2021 08:45:15 GMT
< Connection: Keep-Alive
< 
* Connection #0 to host 127.0.0.1 left intact

get object: bucket0/object0_chunked
{
    "AcceptRanges": "bytes", 
    "ContentType": "text/plain", 
    "LastModified": "Wed, 02 Jun 2021 08:45:15 GMT", 
    "ContentLength": 21, 
    "ETag": "\"22e314c0dba706c0fbcef3be6d64d34f\"", 
    "Metadata": {}
}

[root@vm_3_72_centos ~]# md5sum object0_chunked*
22e314c0dba706c0fbcef3be6d64d34f  object0_chunked
22e314c0dba706c0fbcef3be6d64d34f  object0_chunked.down
```

### 分片上传

```shell
[root@vm_3_72_centos /data ]# ./chunked_put_obj.sh 
* About to connect() to 127.0.0.1 port 8000 (#0)
*   Trying 127.0.0.1...
* Connected to 127.0.0.1 (127.0.0.1) port 8000 (#0)
> POST /bucket0/TESTFILE_10MB?uploads HTTP/1.1
> User-Agent: curl/7.29.0
> Host: 127.0.0.1:8000
> Accept: */*
> Date: Tue, 01 Jun 2021 12:30:57 +0000
> Content-Type: text/plain
> Authorization: AWS 0555b35654ad1656d804:870NLtRQkRUT1+LsG+RGTnoB0vA=
> Transfer-Encoding: chunked
> 
< HTTP/1.1 200 OK
< x-amz-request-id: tx000000000000000000004-0060b62881-1043-default
< Content-Type: application/xml
< Content-Length: 251
< Date: Tue, 01 Jun 2021 12:30:59 GMT
< Connection: Keep-Alive
< 
* Connection #0 to host 127.0.0.1 left intact
<?xml version="1.0" encoding="UTF-8"?><InitiateMultipartUploadResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/"><Bucket>bucket0</Bucket><Key>TESTFILE_10MB</Key><UploadId>2~PxW4nFlOgkuVVxV1NS1VpVtqpIeqDSo</UploadId></InitiateMultipartUploadResult>

[root@vm_3_72_centos /data ]# vim chunked_put_obj.sh 
[root@vm_3_72_centos /data ]# ./chunked_put_obj.sh 
* About to connect() to 127.0.0.1 port 8000 (#0)
*   Trying 127.0.0.1...
* Connected to 127.0.0.1 (127.0.0.1) port 8000 (#0)
> PUT /bucket0/TESTFILE_10MB?partNumber=1&uploadId=2~PxW4nFlOgkuVVxV1NS1VpVtqpIeqDSo HTTP/1.1
> User-Agent: curl/7.29.0
> Host: 127.0.0.1:8000
> Accept: */*
> Date: Tue, 01 Jun 2021 12:31:42 +0000
> Content-Type: text/plain
> Authorization: AWS 0555b35654ad1656d804:WWtnHIcylt6LK0GznsdkyUllntA=
> Transfer-Encoding: chunked
> Expect: 100-continue
> 
< HTTP/1.1 100 CONTINUE
< HTTP/1.1 200 OK
< Content-Length: 0
< ETag: "52715e3e5a02a64c46d67dd768673211"
< Accept-Ranges: bytes
< x-amz-request-id: tx000000000000000000005-0060b628ae-1043-default
< Date: Tue, 01 Jun 2021 12:31:42 GMT
< Connection: Keep-Alive
< 
* Connection #0 to host 127.0.0.1 left intact
[root@vm_3_72_centos /data ]# vim chunked_put_obj.sh 
[root@vm_3_72_centos /data ]# ./chunked_put_obj.sh 
* About to connect() to 127.0.0.1 port 8000 (#0)
*   Trying 127.0.0.1...
* Connected to 127.0.0.1 (127.0.0.1) port 8000 (#0)
> POST /bucket0/TESTFILE_10MB?uploadId=2~PxW4nFlOgkuVVxV1NS1VpVtqpIeqDSo HTTP/1.1
> User-Agent: curl/7.29.0
> Host: 127.0.0.1:8000
> Accept: */*
> Date: Tue, 01 Jun 2021 12:32:02 +0000
> Content-Type: text/plain
> Authorization: AWS 0555b35654ad1656d804:MKik7OTvm8zBgVD9F/olTGjjHlw=
> Transfer-Encoding: chunked
> 
> d8
* upload completely sent off: 223 out of 216 bytes
< HTTP/1.1 200 OK
< x-amz-request-id: tx000000000000000000006-0060b628c2-1043-default
< Content-Type: application/xml
< Content-Length: 320
< Date: Tue, 01 Jun 2021 12:32:03 GMT
< Connection: Keep-Alive
< 
* Connection #0 to host 127.0.0.1 left intact
<?xml version="1.0" encoding="UTF-8"?><CompleteMultipartUploadResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/"><Location>http://127.0.0.1:8000/bucket0/TESTFILE_10MB</Location><Bucket>bucket0</Bucket><Key>TESTFILE_10MB</Key><ETag>&quot;b5ed02a870d5d9

[root@vm_3_72_centos /data ]# aws s3api get-object --bucket bucket0 --key TESTFILE_10MB TESTFILE_multi_down --endpoint-url=http://127.0.0.1:8000
{
    "AcceptRanges": "bytes",
    "LastModified": "2021-06-01T12:32:03+00:00",
    "ContentLength": 9637830,
    "ETag": "\"b5ed02a870d5d9c75a8544b012fbe6f6-1\"",
    "ContentType": "text/plain",
    "Metadata": {}
}
[root@vm_3_72_centos /data ]# md5sum TESTFILE_*    
52715e3e5a02a64c46d67dd768673211  TESTFILE_10MB
52715e3e5a02a64c46d67dd768673211  TESTFILE_multi_down
```





### 优化：最大对象限制

```shell
> PUT /bucket0/TESTFILE_6GB HTTP/1.1
> User-Agent: curl/7.29.0
> Host: 127.0.0.1:8000
> Accept: */*
> Date: Thu, 01 Jul 2021 12:20:11 +0000
> Content-Type: text/plain
> Authorization: AWS 0555b35654ad1656d804:SLH+dfeq/0/Zo5c3TOwqsYsut8g=
> Transfer-Encoding: chunked
> Expect: 100-continue
> 
< HTTP/1.1 100 CONTINUE
< HTTP/1.1 400 Bad Request
< Content-Length: 219
< x-amz-request-id: tx000000000000000000007-0060ddb2fb-1043-default
< Accept-Ranges: bytes
< Content-Type: application/xml
< Date: Thu, 01 Jul 2021 12:22:07 GMT
< Connection: Keep-Alive
* HTTP error before end of send, stop sending
< 
* Closing connection 0
<?xml version="1.0" encoding="UTF-8"?><Error><Code>EntityTooLarge</Code><BucketName>bucket0</BucketName><RequestId>tx000000000000000000007-0060ddb2fb-1043-default</RequestId><HostId>1043-default-default</HostId></Error>
```

chunked方式上传6GB对象代码分析：

```shell
rgw_process_authenticated
RGWPutObj::execute
RGWPutObj_ObjStore_S3::get_data
RGWPutObj_ObjStore::get_data
```

### 代码分析

此时所有数据都已经读取在缓冲区中（保存在哪里？）

在缓冲区中默认每次取4MB（即rgw_max_chunk_size规定的大小），并append到bl中。

```c++
int RGWPutObj_ObjStore::get_data(bufferlist& bl)
{
  size_t cl;
  uint64_t chunk_size = s->cct->_conf->rgw_max_chunk_size;
  if (s->length) {
    cl = atoll(s->length) - ofs;
    if (cl > chunk_size)
      cl = chunk_size;
  } else {
    cl = chunk_size;
  }

  int len = 0;
  {
    ACCOUNTING_IO(s)->set_account(true);
    bufferptr bp(cl);

    const auto read_len  = recv_body(s, bp.c_str(), cl);
    if (read_len < 0) {
      return read_len;
    }

    len = read_len;
    bl.append(bp, 0, len);

    ACCOUNTING_IO(s)->set_account(false);
  }

  if ((uint64_t)ofs + len > s->cct->_conf->rgw_max_put_size) {
    return -ERR_TOO_LARGE;
  }

  return len;
}
```



## 参考

1.[Content-Length与trunked](https://juejin.cn/post/6844903937825488909)

使用python-swiftclient:

https://github.com/openstack/python-swiftclient

https://docs.openstack.org/python-swiftclient/newton/swiftclient.html#module-swiftclient.client

使用curl构建swift token:https://gist.github.com/drewkerrigan/2876196

Transfer-Encoding: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Headers/Transfer-Encoding

## 总结

1. `Content-Length`如果存在且生效, 必须是正确的, 否则会发生异常.(大于实际值会超时, 小于实际值会截断并可能导致后续的数据解析混乱)

   如果报文中包含`Transfer-Encoding: chunked`首部, 那么`Content-Length`将被忽略.