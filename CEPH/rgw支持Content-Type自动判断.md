## 需求分析

目测这个功能在RGW的Swift里有，可以看看如何移植到S3上来

```shell
搜索 mime.types, rgw_mime_types_file, ext_mime_map, rgw_find_mime_by_ext 得到更多信息。
RGW_ATTR_CONTENT_TYPE
```

## MIME是什么

**参考**：https://blog.csdn.net/jmjhx/article/details/99728680

MIME-type和Content-Type的关系：
当web服务器收到静态的资源文件请求时，依据请求文件的后缀名在服务器的MIME配置文件中找到对应的MIME Type，再根据MIME Type设置HTTP Response的Content-Type，然后浏览器根据Content-Type的值处理文件。

**什么是MIME-TYPE：**
为什么这么说呢？首先，我们要了解浏览器是如何处理内容的。在浏览器中显示的内容有 HTML、有 XML、有 GIF、还有 Flash ...
那么，浏览器是如何区分它们，绝对什么内容用什么形式来显示呢？答案是 MIME Type，也就是该资源的媒体类型。
媒体类型通常是通过 HTTP 协议，由 Web 服务器告知浏览器的，更准确地说，是通过 Content-Type 来表示的，例如:

`Content-Type: text/HTML`
表示内容是 text/HTML 类型，也就是超文本文件。为什么是“text/HTML”而不是“HTML/text”或者别的什么？MIME Type 不是个人指定的，是经过 ietf 组织协商，以 RFC 的形式作为建议的标准发布在网上的，大多数的 Web 服务器和用户代理都会支持这个规范 (顺便说一句，Email 附件的类型也是通过 MIME Type 指定的)。
通常只有一些在互联网上获得广泛应用的格式才会获得一个 MIME Type，如果是某个客户端自己定义的格式，一般只能以 application/x- 开头。

## swift中通过后缀自动获取Content-Type

### mime配置

```shell
Option("rgw_mime_types_file", Option::TYPE_STR, Option::LEVEL_BASIC)
    .set_default("/etc/mime.types")
    .set_description("Path to local mime types file")
    .set_long_description("The mime types file is needed in Swift when uploading an object. If object's content type is not specified, RGW will use data from this file to assign a content type to the object."),
```

该文件定义了众多Content-Type的map。在rgw启动时，`rgw_main.cc, main()`下，通过`rgw_tools_init`从文件读取到`ext_mime_map`中，以供rgw使用。

### 流程分析

#### PutObj:

对于PutObj请求，若header中没有携带Content-Type信息，将尝试根据对象名称后缀来判断，

若有后缀，则拆分出来，调用`rgw_find_mime_by_ext`来获得Content-Type，获得后写入RGW_ATTR_CONTENT_TYPE中。

若没有后缀，则考虑根据s->format强制设置一个type。

> 此处的s->format一般是特定的Handler来显式指定的，例如：
>
> `RGWHandler_REST_S3::init_from_header(s,RGW_FORMAT_XML, true);`
>
> 默认为`RGW_FORMAT_PLAIN`。

其中`force_content_type`是为了Swift协议中规定即使不包含body也要返回Content-Type header,例如[openstack:put object in swift](https://docs.openstack.org/api-ref/object-store/index.html?expanded=create-or-replace-object-detail#create-or-replace-object)（对比Request和Respond，可以发现Request中Content-Type是optional，而Respond中确要求必须包含，这一点也可以在附录Swift和S3下PutObject抓包看到）。S3应该不需要[S3:put object](https://docs.aws.amazon.com/AmazonS3/latest/API/API_PutObject.html)：

> ```
> Swift sends Content-Type HTTP header even if the response
> doesn't contain body. We have this behaviour implemented
> until applying some changes in end_header() function.
> ```

[rgw: enforce Content-Type in Swift responses.](https://github.com/ceph/ceph/commit/106aeba206736d4080326f9bc191876bed63370b)

[rgw: we should not overide Swift sent content type](https://github.com/ceph/ceph/commit/423cf136f15df3099c9266f55932542d303c2713)

```c++
#PutObj
process_request
rgw_process_authenticated
RGWPutObj_ObjStore_SWIFT::verify_permission
RGWPutObj::verify_permission
RGWPutObj_ObjStore_SWIFT::get_params
 |--> rgw_find_mime_by_ext(suffix_str)
 |--> s->generic_attrs[RGW_ATTR_CONTENT_TYPE] = mime
RGWPutObj::execute
 |--> rgw::putobj::AtomicObjectProcessor::complete
 |--> RGWRados::Object::Write::write_meta
 |--> RGWRados::Object::Write::_do_write_meta
    |--> content_type = rgw_bl_str(bl);
 |--> RGWRados::Bucket::UpdateIndex::complete(...,content_type,...)
    |--> get_bucket_shard(&bs);
    |--> ent.meta.content_type = content_type;
    |--> store->cls_obj_complete_add(*bs, obj, optag, poolid, epoch, ent, category, remove_objs, bilog_flags, zones_trace);
    |--> RGWRados::cls_obj_complete_op
    |--> cls_rgw_bucket_complete_op
    |--> librados::v14_2_0::ObjectOperation::exec
    |--> ObjectOperation::call
    |--> ObjectOperation::add_call
      |--> OSDOp& osd_op = add_op(op);
    |--> librados::AioCompletion *completion = arg->rados_completion;
    |-->  bs.index_ctx.aio_operate(bs.bucket_obj, arg->rados_completion, &o);
    |--> librados::v14_2_0::IoCtx::aio_operate
    	|--> librados::IoCtxImpl::queue_aio_write(AioCompletionImpl *c)
    	|--> objecter->prepare_mutate_op
    	|--> objecter->op_submit(op, &c->tid);
    	
RGWOp::complete
RGWPutObj_ObjStore_SWIFT::send_response
  |--> end_header
	   |--> force_content_type
```

#### GetObj:

```c++
#GetObj
process_request
rgw_process_authenticated
RGWGetObj::execute
RGWGetObj_ObjStore_SWIFT::send_response_data
  --> get_contype_from_attrs(attrs, content_type) //从 RGW_ATTR_CONTENT_TYPE 获取
  --> end_header(s, this, !content_type.empty() ? content_type.c_str()
	     : "binary/octet-stream"); //若获取到的content_type为空，则设定为binary/octet-stream
```

#### CopyObj:

```c++
process_request
rgw_process_authenticated
RGWOp::complete
RGWCopyObj_ObjStore_SWIFT::send_response
  |--> get_contype_from_attrs(attrs, content_type);
  |--> end_header(s, this, !content_type.empty() ? content_type.c_str()
	       : "binary/octet-stream");
```

## S3中通过header设置Content-Type

### PutObj

> 以`aws s3api put-object --bucket $BUCKET --key $OBJECT --content-type text/plain`为例：

```c++
process_request
RGWREST::get_handler
RGWREST::preprocess
  |--> s->generic_attrs[giter->second] = env;//将s->info->env中的header存入
  //eg: ["user.rgw.content_type"] = "text/plain" //CONTENT_TYPE

rgw_process_authenticated
RGWPutObj::execute
populate_with_generic_attrs(s, attrs)//将generic_attrs中的content_type写出到attrs
rgw::putobj::AtomicObjectProcessor::complete
RGWRados::Object::Write::write_meta
RGWRados::Object::Write::_do_write_meta
	|--> if(name.compare(RGW_ATTR_CONTENT_TYPE) == 0)
    |--> content_type = rgw_bl_str(bl);
```

### GetObj

```c++
process_request
rgw_process_authenticated
RGWGetObj::execute
RGWGetObj_ObjStore_S3::send_response_data
  |--> if (iter->first.compare(RGW_ATTR_CONTENT_TYPE) == 0)
  |--> if (!content_type) {                                                                                                             
  |-->  content_type_str = rgw_bl_str(iter->second);  
  |-->  content_type = content_type_str.c_str(); 
```

## 修改点

在RGWPutObj_ObjStore_S3::get_params()中，添加：

```c++
if (!s->generic_attrs.count(RGW_ATTR_CONTENT_TYPE)) {
    ldout(s->cct, 5) << "content type wasn't provided, trying to guess" << dendl;
    const char *suffix = strrchr(s->object.name.c_str(), '.');
    if (suffix) {
        suffix++;
        if (*suffix) {
            string suffix_str(suffix);
            const char *mime = rgw_find_mime_by_ext(suffix_str);
            if (mime) {
                s->generic_attrs[RGW_ATTR_CONTENT_TYPE] = mime;
            }
        }
    }
}
```

## 自测

### 自测场景

1. put-object时，若header中指定content-type，则不去guess type，以header中指定的为准(即使该值不属于MIME标准)。
2. put-object时，若header中未指定content-type，则从object名称后缀中解析，在mime.types中做匹配。若能匹配，则加入attrs中；若不能匹配，则不加入attrs中，并在send_response时保持为默认值`binary/octet-stream`。

### 测试脚本

```shell
#!/bin/bash

PROFILE="Vstart_testid"
S3_HOST="http://x.x.x.x:8000"

function list_buckets(){
    aws s3api --endpoint-url "$S3_HOST" --profile $PROFILE list-buckets
}

function create_bucket(){
    aws s3api --endpoint-url "$S3_HOST" --profile $PROFILE create-bucket --bucket "$1"
}

function put_object(){
    aws s3api --endpoint-url "$S3_HOST" --profile $PROFILE put-object --bucket "$1" --key "$2" --body "$2"
}

function put_object_with_content_type_header(){
    aws s3api --endpoint-url "$S3_HOST" --profile $PROFILE put-object --bucket "$1" --key "$2" --body "$2" --content-type "$3"
}

function get_object(){
    aws s3api --endpoint-url $S3_HOST --profile $PROFILE \
        get-object --bucket "$1" \
                   --key "$2" \
                   "$2".down 
}

function test_put_object_no_suffix_no_header(){
    echo "#1.test_put_object_no_suffix_no_header"
    put_object bucket0 object0
    get_object bucket0 object0
}

function test_put_object_with_suffix_no_header(){
    echo "#2.test_put_object_with_suffix_no_header"
    touch object0.bmp
    echo "object0.bmp~~" > object0.bmp
    put_object bucket0 object0.bmp
    get_object bucket0 object0.bmp
}

function test_put_object_no_suffix_with_header(){
    echo "#3.test_put_object_no_suffix_with_header"
    touch "object0"
    echo "object0" > object0
    put_object_with_content_type_header bucket0 object0 "image/bmp"
    get_object bucket0 object0
}

function test_put_object_no_suffix_with_wrong_header(){
    echo "#4.test_put_object_no_suffix_with_wrong_header"
    touch "object0"
    echo "object0" > object0
    put_object_with_content_type_header bucket0 object0 "wrong/mime"
    get_object bucket0 object0
}

function test_put_object_with_suffix_with_wrong_header(){
    echo "#5.test_put_object_with_suffix_with_wrong_header"
    touch object0.bmp
    echo "object0.bmp~~" > object0.bmp
    put_object_with_content_type_header bucket0 object0.bmp "wrong/mime"
    get_object bucket0 object0.bmp
}

function test_put_object_with_suffix_with_diff_header(){
    echo "#6.test_put_object_with_suffix_with_diff_header"
    touch object0.txt 
    echo "object0.txt~~~" > object0.txt
    put_object_with_content_type_header bucket0 object0.txt "image/bmp"
    get_object bucket0 object0.txt
}

function test_put_object_with_wrong_suffix_no_header(){
    echo "#7.test_put_object_with_wrong_suffix_no_header"
    touch object0.wrong_suffix 
    echo "object0.wrong_suffix~~~" > object0.wrong_suffix
    put_object bucket0 object0.wrong_suffix
    get_object bucket0 object0.wrong_suffix
}

function main(){
    create_bucket bucket0
    test_put_object_no_suffix_no_header
    test_put_object_with_suffix_no_header
    test_put_object_no_suffix_with_header
    test_put_object_no_suffix_with_wrong_header
    test_put_object_with_suffix_with_wrong_header
    test_put_object_with_suffix_with_diff_header
    test_put_object_with_wrong_suffix_no_header
}
main
```

### 测试结果

```shell
#1.test_put_object_no_suffix_no_header
{
    "ETag": "\"197d6057db574d459936284126bca77a\""
}
{
    "AcceptRanges": "bytes",
    "LastModified": "2021-07-08T03:48:36+00:00",
    "ContentLength": 8,
    "ETag": "\"197d6057db574d459936284126bca77a\"",
    "ContentType": "binary/octet-stream",
    "Metadata": {}
}
#2.test_put_object_with_suffix_no_header
{
    "ETag": "\"a32784e9abb495e3febace244fa824f1\""
}
{
    "AcceptRanges": "bytes",
    "LastModified": "2021-07-08T03:48:42+00:00",
    "ContentLength": 14,
    "ETag": "\"a32784e9abb495e3febace244fa824f1\"",
    "ContentType": "image/bmp",
    "Metadata": {}
}
#3.test_put_object_no_suffix_with_header
{
    "ETag": "\"197d6057db574d459936284126bca77a\""
}
{
    "AcceptRanges": "bytes",
    "LastModified": "2021-07-08T03:48:48+00:00",
    "ContentLength": 8,
    "ETag": "\"197d6057db574d459936284126bca77a\"",
    "ContentType": "image/bmp",
    "Metadata": {}
}
#4.test_put_object_no_suffix_with_wrong_header
{
    "ETag": "\"197d6057db574d459936284126bca77a\""
}
{
    "AcceptRanges": "bytes",
    "LastModified": "2021-07-08T03:48:53+00:00",
    "ContentLength": 8,
    "ETag": "\"197d6057db574d459936284126bca77a\"",
    "ContentType": "wrong/mime",
    "Metadata": {}
}
#5.test_put_object_with_suffix_with_wrong_header
{
    "ETag": "\"a32784e9abb495e3febace244fa824f1\""
}
{
    "AcceptRanges": "bytes",
    "LastModified": "2021-07-08T03:48:59+00:00",
    "ContentLength": 14,
    "ETag": "\"a32784e9abb495e3febace244fa824f1\"",
    "ContentType": "wrong/mime",
    "Metadata": {}
}
#6.test_put_object_with_suffix_with_diff_header
{
    "ETag": "\"410291211bd15062b265ae9b17cac13f\""
}
{
    "AcceptRanges": "bytes",
    "LastModified": "2021-07-08T03:49:05+00:00",
    "ContentLength": 15,
    "ETag": "\"410291211bd15062b265ae9b17cac13f\"",
    "ContentType": "image/bmp",
    "Metadata": {}
}
#7.test_put_object_with_wrong_suffix_no_header
{
    "ETag": "\"53016300384f9edfbf8c6f4e21d8faf3\""
}
{
    "AcceptRanges": "bytes",
    "LastModified": "2021-07-08T03:49:11+00:00",
    "ContentLength": 24,
    "ETag": "\"53016300384f9edfbf8c6f4e21d8faf3\"",
    "ContentType": "binary/octet-stream",
    "Metadata": {}
}
```

## 附录

### swift在没有body时也强制返回content-type

> S3无此要求。

#### swift put obj抓包

```shell
#不指定后缀
HEAD /swift/v1/bucket0/object0 HTTP/1.1
Host: 127.0.0.1:8000
Accept-Encoding: identity
x-auth-token: AUTH_rgwtk0b000000746573743a746573746572d5b4ea27f83a71af8543e66077840539118dc95dcd6ddf13a54ef59e241a3de47e59af2a
user-agent: python-swiftclient-3.12.0

HTTP/1.1 404 Not Found
Content-Length: 9
X-Trans-Id: tx000000000000000000031-0060e4f205-1041-default
X-Openstack-Request-Id: tx000000000000000000031-0060e4f205-1041-default
Accept-Ranges: bytes
Content-Type: text/plain; charset=utf-8
Date: Wed, 07 Jul 2021 00:15:01 GMT
Connection: Keep-Alive

PUT /swift/v1/bucket0/object0 HTTP/1.1
Host: 127.0.0.1:8000
Accept-Encoding: identity
x-object-meta-mtime: 1625588824.761210
x-auth-token: AUTH_rgwtk0b000000746573743a746573746572d5b4ea27f83a71af8543e66077840539118dc95dcd6ddf13a54ef59e241a3de47e59af2a
Content-Length: 11
user-agent: python-swiftclient-3.12.0

object0~~~
HTTP/1.1 201 Created
etag: a86616bd389f15308f8fe9b26545abbd
Last-Modified: Wed, 07 Jul 2021 00:15:02 GMT
X-Trans-Id: tx000000000000000000032-0060e4f205-1041-default
X-Openstack-Request-Id: tx000000000000000000032-0060e4f205-1041-default
Content-Type: text/plain; charset=utf-8 #注意此处
Content-Length: 0
Date: Wed, 07 Jul 2021 00:15:02 GMT
Connection: Keep-Alive

#----指定txt后缀
HEAD /swift/v1/bucket0/object0.txt HTTP/1.1
Host: 127.0.0.1:8000
Accept-Encoding: identity
x-auth-token: AUTH_rgwtk0b000000746573743a74657374657201a7b6170fb68f8a7e42e660a80a2827aa761013c6a51053cbd60de789b3338529d91527
user-agent: python-swiftclient-3.12.0

HTTP/1.1 200 OK
Content-Length: 0
Accept-Ranges: bytes
Last-Modified: Wed, 07 Jul 2021 00:09:58 GMT
X-Timestamp: 1625616598.48832
etag: d41d8cd98f00b204e9800998ecf8427e
X-Object-Meta-Mtime: 1625588780.825202
X-Trans-Id: tx000000000000000000029-0060e4f0fe-1041-default
X-Openstack-Request-Id: tx000000000000000000029-0060e4f0fe-1041-default
Content-Type: text/plain #注意此处
Date: Wed, 07 Jul 2021 00:10:38 GMT
Connection: Keep-Alive

PUT /swift/v1/bucket0/object0.txt HTTP/1.1
Host: 127.0.0.1:8000
Accept-Encoding: identity
x-object-meta-mtime: 1625588780.825202
x-auth-token: AUTH_rgwtk0b000000746573743a74657374657201a7b6170fb68f8a7e42e660a80a2827aa761013c6a51053cbd60de789b3338529d91527
content-length: 0
user-agent: python-swiftclient-3.12.0

HTTP/1.1 201 Created
etag: d41d8cd98f00b204e9800998ecf8427e
Last-Modified: Wed, 07 Jul 2021 00:10:38 GMT
X-Trans-Id: tx00000000000000000002a-0060e4f0fe-1041-default
X-Openstack-Request-Id: tx00000000000000000002a-0060e4f0fe-1041-default
Content-Type: text/plain; charset=utf-8
Content-Length: 0
Date: Wed, 07 Jul 2021 00:10:38 GMT
Connection: Keep-Alive
```

#### s3 put obj 抓包

```shell
PUT /bucket0/object0 HTTP/1.1
Host: 127.0.0.1:8000
Accept-Encoding: identity
User-Agent: aws-cli/1.18.156 Python/3.6.8 Linux/4.18.0-193.28.1.el8_2.x86_64 botocore/1.18.15
X-Amz-Date: 20210706T161910Z
X-Amz-Content-SHA256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
Authorization: AWS4-HMAC-SHA256 Credential=0555b35654ad1656d804/20210706/chongqing/s3/aws4_request, SignedHeaders=host;x-amz-content-sha256;x-amz-date, Signature=40ea66ce7c4c084d13fc68b775e1c7a53aa61b1fd1176a9c61c91221569f641e
Content-Length: 0

HTTP/1.1 200 OK
Content-Length: 0
ETag: "d41d8cd98f00b204e9800998ecf8427e"
Accept-Ranges: bytes
x-amz-request-id: tx000000000000000000004-0060e4827e-1041-default
Date: Tue, 06 Jul 2021 16:19:10 GMT
Connection: Keep-Alive

#------
PUT /bucket0/object0.txt HTTP/1.1
Host: 127.0.0.1:8000
Accept-Encoding: identity
User-Agent: aws-cli/1.18.156 Python/3.6.8 Linux/4.18.0-193.28.1.el8_2.x86_64 botocore/1.18.15
X-Amz-Date: 20210706T162708Z
X-Amz-Content-SHA256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
Authorization: AWS4-HMAC-SHA256 Credential=0555b35654ad1656d804/20210706/chongqing/s3/aws4_request, SignedHeaders=host;x-amz-content-sha256;x-amz-date, Signature=1b41d03eb1c62bb720e33570f4dd93b7dd90cd3a82125473f3dc5b80b7e2b93c
Content-Length: 0

HTTP/1.1 200 OK
Content-Length: 0
ETag: "d41d8cd98f00b204e9800998ecf8427e"
Accept-Ranges: bytes
x-amz-request-id: tx000000000000000000005-0060e4845c-1041-default
Date: Tue, 06 Jul 2021 16:27:08 GMT
Connection: Keep-Alive
#注意此处，没有Content-Type
```

### CONTENT_TYPE与user.rgw.content_type

`RGW_ATTR_CONTENT_TYPE`如何和`user.rgw.content_type`建立联系？

generic_attrs_map中定义了header和attrs名称的映射：

```c++
(gdb) p	generic_attrs_map
$12 = std::map with 7 elements = {
  ["CONTENT_TYPE"] = "user.rgw.content_type",
  ["HTTP_CACHE_CONTROL"] = "user.rgw.cache_control",
  ["HTTP_CONTENT_DISPOSITION"] = "user.rgw.content_disposition",
  ["HTTP_CONTENT_ENCODING"] = "user.rgw.content_encoding",
  ["HTTP_CONTENT_LANGUAGE"] = "user.rgw.content_language",
  ["HTTP_EXPIRES"] = "user.rgw.expires",
  ["HTTP_X_ROBOTS_TAG"] = "user.rgw.x-robots-tag"
}
```

实现方式：

```c++
/*
 * mapping between rgw object attrs and output http fields
 */
static const struct rgw_http_attr base_rgw_to_http_attrs[] = {
  { RGW_ATTR_CONTENT_LANG,      "Content-Language" },
  { RGW_ATTR_EXPIRES,           "Expires" },
  { RGW_ATTR_CACHE_CONTROL,     "Cache-Control" },
  { RGW_ATTR_CONTENT_DISP,      "Content-Disposition" },
  { RGW_ATTR_CONTENT_ENC,       "Content-Encoding" },
  { RGW_ATTR_USER_MANIFEST,     "X-Object-Manifest" },
  { RGW_ATTR_X_ROBOTS_TAG ,     "X-Robots-Tag" },
  { RGW_ATTR_STORAGE_CLASS ,    "X-Amz-Storage-Class" },
  /* RGW_ATTR_AMZ_WEBSITE_REDIRECT_LOCATION header depends on access mode:
   * S3 endpoint: x-amz-website-redirect-location
   * S3Website endpoint: Location
   */
  { RGW_ATTR_AMZ_WEBSITE_REDIRECT_LOCATION, "x-amz-website-redirect-location" },
};

static const struct generic_attr generic_attrs[] = {
  { "CONTENT_TYPE",             RGW_ATTR_CONTENT_TYPE },
  { "HTTP_CONTENT_LANGUAGE",    RGW_ATTR_CONTENT_LANG },
  { "HTTP_EXPIRES",             RGW_ATTR_EXPIRES },
  { "HTTP_CACHE_CONTROL",       RGW_ATTR_CACHE_CONTROL },
  { "HTTP_CONTENT_DISPOSITION", RGW_ATTR_CONTENT_DISP },
  { "HTTP_CONTENT_ENCODING",    RGW_ATTR_CONTENT_ENC },
  { "HTTP_X_ROBOTS_TAG",        RGW_ATTR_X_ROBOTS_TAG },
};

struct generic_attr {
  const char *http_header;
  const char *rgw_attr;
};

map<string, string> rgw_to_http_attrs;
static map<string, string> generic_attrs_map;
map<int, const char *> http_status_names;
```

generic_attrs中的key则是user.rgw.xxx形式的：

```shell
p s->generic_attrs
$9 = {
  first = "user.rgw.content_type",
  second = "video/webm"
}
```

在attrs中，一般使用attrs[RGW_ATTR_xxx]这种形式来使用，查看代码发现RGW_ATTR_CONTENT_TYPE和generic_attrs_map中的user.rgw.content_type实际上是一致的，只是不同的表现形式：

```c++
#define RGW_ATTR_PREFIX  "user.rgw."
#define RGW_ATTR_CONTENT_TYPE	RGW_ATTR_PREFIX "content_type"
```

## 路线

```shell
commit eccf36980511de7ed122a38d426170496ffdea64
Author: Ken Dreyer <kdreyer@redhat.com>
Date:   Tue Jun 23 13:41:53 2015 -0600

    packaging: RGW depends on /etc/mime.types
    
    If the mimecap RPM or mime-support DEB is not installed, then the
    /etc/mime.types file is not present on the system. RGW attempts to read
    this file during startup, and if the file is not present, RGW logs an
    error:
    
      ext_mime_map_init(): failed to open file=/etc/mime.types ret=-2
    
    Make the radosgw package depend on the mailcap/mime-support packages so
    that /etc/mime.types is always available on RGW systems.
    
    http://tracker.ceph.com/issues/11864 Fixes: #11864
```

