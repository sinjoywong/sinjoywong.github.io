最近在适配S3 BucketEncryption接口，一开始基于N版rgw开发，后来发现需要在L版上开发，因此需要代码回迁。在回迁过程中，发现L版和N版有十分大的不同。

| 编号 | 项目          | L版实现                                                      | N版实现                                                      | 备注                |
| ---- | ------------- | ------------------------------------------------------------ | ------------------------------------------------------------ | ------------------- |
| 1    | string与char* | const string name() override { return "init_multipart"; }    | const char* name() const override { return "init_multipart"; } | 用char*有什么好处？ |
| 2    | 内存管理      | char *data;<br/>  int len;<br />因此在构造函数和析构函数中需要初始化和free指针 | bufferlist data;                                             |                     |
| 3    |               | const auto max_size = s->cct->_conf->rgw_max_put_param_size;<br/>  op_ret = rgw_rest_read_all_input(s,&data, &len, max_size, false);<br/>  return op_ret; | const auto max_size = s->cct->_conf->rgw_max_put_param_size;<br/>  std::tie(op_ret, data) = rgw_rest_read_all_input(s, max_size, false);<br/>  return op_ret; | 这是根据第2条的结果 |
|      |               | ::decode()                                                   | decode()                                                     |                     |
|      |               |                                                              | ldpp_dout(this, 0) << "ERROR: store->list_objects():" <<dendl; |                     |





### rgw_rest_read_all_input的作用：

将s中的数据都读取到data中，长度为len（len也是从s中获得的）。

```c++
const auto max_size = s->cct->_conf->rgw_max_put_param_size;
  r = rgw_rest_read_all_input(s, &data, &len, max_size, false);
  if (r < 0) {
    return r;
  }  

```

此处 `rgw_max_put_param_size`是个配置文件中定义的数字，表示PUT请求中可以允许的最大的json/xml参数的大小。





### rgw req_state的作用域与生命周期？

每个请求到达rgw(`process_request`)，都被封装成为一个RGWOp，这个结构是这个请求自始至终都存在的数据`结构。

它定义了所有操作的接口范式，所有的具体操作都要继承自这个类，并实现对应的接口：

```c++
//rgw_op.h

class RGWOp {
protected:
  struct req_state *s; //保存一个HTTP请求需要的所有状态，例如ceph 上下文指针cct、RGWOpType、length、bucket_attrs、
  RGWHandler *dialect_handler;
  RGWRados *store;
  RGWCORSConfiguration bucket_cors;
  bool cors_exist;
  RGWQuotaInfo bucket_quota;
  RGWQuotaInfo user_quota;
  int op_ret;

  int do_aws4_auth_completion();

  virtual int init_quota();

public:
  RGWOp()
    : s(nullptr),
      dialect_handler(nullptr),
      store(nullptr),
      cors_exist(false),
      op_ret(0) {
  }

  virtual ~RGWOp() = default;

  int get_ret() const { return op_ret; }

  virtual int init_processing() {
    op_ret = init_quota();
    if (op_ret < 0)
      return op_ret;

    return 0;
  }

  virtual void init(RGWRados *store, struct req_state *s, RGWHandler *dialect_handler) {
    this->store = store;
    this->s = s;
    this->dialect_handler = dialect_handler;
  }
  int read_bucket_cors();
  bool generate_cors_headers(string& origin, string& method, string& headers, string& exp_headers, unsigned *max_age);

  virtual int verify_params() { return 0; }
  virtual bool prefetch_data() { return false; }

  /* Authenticate requester -- verify its identity.
   *
   * NOTE: typically the procedure is common across all operations of the same
   * dialect (S3, Swift API). However, there are significant exceptions in
   * both APIs: browser uploads, /info and OPTIONS handlers. All of them use
   * different, specific authentication schema driving the need for per-op
   * authentication. The alternative is to duplicate parts of the method-
   * dispatch logic in RGWHandler::authorize() and pollute it with a lot
   * of special cases. */
  virtual int verify_requester(const rgw::auth::StrategyRegistry& auth_registry) {
    /* TODO(rzarzynski): rename RGWHandler::authorize to generic_authenticate. */
    return dialect_handler->authorize();
  }
  virtual int verify_permission() = 0;
  virtual int verify_op_mask();
  virtual void pre_exec() {}
  virtual void execute() = 0;
  virtual void send_response() {}
  virtual void complete() {
    send_response();
  }
  virtual const string name() = 0;
  virtual RGWOpType get_type() { return RGW_OP_UNKNOWN; }

  virtual uint32_t op_mask() { return 0; }

  virtual int error_handler(int err_no, string *error_content);
};
```

### s->info.env的生命周期

创建：rgw_process.cc, process_request()中，使用client_io->get_env()获得RGWEnv& env，然后在req_state的初始化中赋值到req_state中：

```c++
//rgw_process.cc
int process_request(rgw::sal::RGWRadosStore* const store,
                    RGWREST* const rest,
                    RGWRequest* const req,
                    const std::string& frontend_prefix,
                    const rgw_auth_registry_t& auth_registry,
                    RGWRestfulIO* const client_io,
                    OpsLogSocket* const olog,
                    optional_yield yield,
		    rgw::dmclock::Scheduler *scheduler,
                    int* http_ret)
{
  ...
	RGWEnv& rgw_env = client_io->get_env();
  struct req_state rstate(g_ceph_context, &rgw_env, &user, req->id);
  ...
```

这即说明了，这个env是从client请求中获得的。这就影响后面的一个操作：

commit: db2a69f84

在complete multipart时，

### s->info.args中保存的是什么？

查看req_state的结构体定义，可以看到：

```c++
//rgw_common.h
struct req_state {
  ...
  req_info info;
  ...
}

struct req_info {
  const RGWEnv *env;
  RGWHTTPArgs args; //此处： s->info.args，保存HTTP请求头中携带的数据，是个map
  map<string, string> x_meta_map;

  string host;
  const char *method;
  string script_uri;
  string request_uri;
  string request_uri_aws4;
  string effective_uri;
  string request_params;
  string domain;

  req_info(CephContext *cct, const RGWEnv *env);
  void rebuild_from(req_info& src);
  void init_meta_info(bool *found_bad_meta);
};

//获取方式：
max_keys = s->info.args.get("max-keys");
delimiter = s->info.args.get("delimiter");


//获取的实现：
//rgw_common.h
const string& RGWHTTPArgs::get(const string& name, bool *exists) const
{
  auto iter = val_map.find(name);
  bool e = (iter != std::end(val_map));
  if (exists)
    *exists = e;
  if (e)
    return iter->second;
  return empty_str;
}
```



### 从HTTP头中获取参数

```c++
if_nomatch = s->info.env->get("HTTP_IF_NONE_MATCH");
copy_source = url_decode(s->info.env->get("HTTP_X_AMZ_COPY_SOURCE", ""));
```



### encode/decode是在做什么？bufferlist是什么？

类似于将一个结构体打包成一个buffer，便于下发到RADOS或网络传输。详见ceph官网bufferlist。

```c++
//rgw_rest_s3.h
bufferlist tags_bl;
obj_tags.encode(tags_bl);
ldout(s->cct, 20) << "Read " << obj_tags.count() << "tags" << dendl;
attrs[RGW_ATTR_TAGS] = tags_bl;
```





L版：

```c++
void encode(bufferlist& bl) const {
  ENCODE_START(1, 1, bl);
  ::encode(referer_patterns, bl);
  ::encode(protection_type, bl);
  ::encode(empty_referer_denied, bl);
  ::encode(protection_enabled, bl);
  ENCODE_FINISH(bl);
}
void decode(bufferlist::iterator& bl) {
  DECODE_START(1, bl);
  ::decode(referer_patterns, bl);
  ::decode(protection_type, bl);
  ::decode(empty_referer_denied, bl);
  ::decode(protection_enabled, bl);
  DECODE_FINISH(bl);
}
```

N版：

```c++
void encode(bufferlist& bl) const {
  ENCODE_START(2, 1, bl);
  encode(name, bl);
  encode(instance, bl);
  encode(ns, bl);
  ENCODE_FINISH(bl);
}
void decode(bufferlist::const_iterator& bl) {
  DECODE_START(2, bl);
  decode(name, bl);
  decode(instance, bl);
  if (struct_v >= 2) {
    decode(ns, bl);
  }
  DECODE_FINISH(bl);
}
```

### 如何response?

参考  xxx::send_response

### 如何获得xattrs?

```c++
rgw_obj obj;
obj.init_ns(s->bucket, meta_oid, RGW_OBJ_NS_MULTIPART);
obj.set_in_extra_data(true);
res = get_obj_attrs(store, s, obj, xattrs)//store为父类RGWOp中保存的RGWRados *store.
   
   
   
```



### L版XML解析的实现

针对每个标记，都实现一个继承自XMLObj的类，参考rgw_cors_s3.cc。int RGWPutCORS_ObjStore_S3::get_params()、

xml格式：https://docs.aws.amazon.com/cli/latest/reference/s3api/put-bucket-cors.html

https://docs.aws.amazon.com/AmazonS3/latest/dev/cors.html

```xml
<CORSConfiguration>
 <CORSRule>
   <AllowedOrigin>http://www.example1.com</AllowedOrigin>

   <AllowedMethod>PUT</AllowedMethod>
   <AllowedMethod>POST</AllowedMethod>
   <AllowedMethod>DELETE</AllowedMethod>

   <AllowedHeader>*</AllowedHeader>
 </CORSRule>
 <CORSRule>
   <AllowedOrigin>http://www.example2.com</AllowedOrigin>

   <AllowedMethod>PUT</AllowedMethod>
   <AllowedMethod>POST</AllowedMethod>
   <AllowedMethod>DELETE</AllowedMethod>

   <AllowedHeader>*</AllowedHeader>
 </CORSRule>
 <CORSRule>
   <AllowedOrigin>*</AllowedOrigin>
   <AllowedMethod>GET</AllowedMethod>
 </CORSRule>
</CORSConfiguration>
```



### 针对CAM的判断

这里实现了什么？

```c++
void RGWOptionsCORS_ObjStore_S3::send_response()
{
  string hdrs, exp_hdrs;
  uint32_t max_age = CORS_MAX_AGE_INVALID;
  /*EACCES means, there is no CORS registered yet for the bucket
   *ENOENT means, there is no match of the Origin in the list of CORSRule
   */
  if (op_ret == -ENOENT)
    op_ret = -EACCES;
  if (op_ret < 0) {
    set_req_state_err(s, op_ret);
    dump_errno(s);
    if (store->s3_auth_use_cam()) {
      end_header(s, this);
    } else {
      end_header(s, NULL);
    }
    ...
  }
}
```

