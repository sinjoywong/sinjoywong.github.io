# 用户管理：UserSuspended

## 问题

```shell
GET /?marker=&prefix=&max-keys=1000&delimiter=%2F&encoding-type=url HTTP/1.1
Host: xxx
Connection: keep-alive
Accept-Encoding: gzip, deflate
Accept: */*
User-Agent: coscmd-v1.8.6.21
Authorization: q-sign-algorithm=sha1&q-ak=AKIDxxx&q-sign-time=1627982615;1627992675&q-key-time=1627982615;1627992675&q-header-list=&q-url-param-list=delimiter;encoding-type;marker;max-keys;prefix&q-signature=xx

HTTP/1.1 403 Forbidden
Date: Tue, 03 Aug 2021 09:22:25 GMT
Content-Type: application/xml
Content-Length: 248
Connection: keep-alive
Server: openresty/1.19.3.1
x-cos-request-id: tx0000000000000003e1778-0061090b7b-2ffa8f-default
Accept-Ranges: bytes

<?xml version="1.0" encoding="UTF-8"?><Error><Code>UserSuspended</Code><BucketName>chongqing-tbase-backup-1255000001</BucketName><RequestId>tx0000000000000003e1778-0061090b7b-2ffa8f-default</RequestId><HostId>2ffa8f-default-default</HostId></Error>G
```

## 考虑

1. 如何定义用户状态？
2. 管理用户状态有哪几种？
3. 如何开通用户？
4. 



ERR_USER_SUSPENDED

```mermaid

```

```c++
#define RGW_USER_ENABLED                0
#define RGW_USER_SUSPEND_NORMAL         0x01
#define RGW_USER_SUSPEND_NONACTIVATED   0x02
#define RGW_USER_SUSPEND_ISOLATED       0x04
```







```c++
int process_request(...){
  ...
  if (s->user->suspended) {
    if (s->user->suspended & RGW_USER_SUSPEND_NONACTIVATED) {
      dout(10) << "user is suspended, because user is not activated, uid=" << s->user->user_id << dendl;
    } else if (s->user->suspended & RGW_USER_SUSPEND_ISOLATED) {
      dout(10) << "user is suspended, because user is isolated, uid=" << s->user->user_id << dendl;
    } else {
      dout(10) << "user is suspended, uid=" << s->user->user_id << dendl;
    }
    
    abort_early(s, op, -ERR_USER_SUSPENDED, handler);
    goto done;
  }
  ...
}
```



```c++
static int read_bucket_policy(RGWRados *store,
                              struct req_state *s,
                              RGWBucketInfo& bucket_info,
                              map<string, bufferlist>& bucket_attrs,
                              RGWAccessControlPolicy *policy,
                              rgw_bucket& bucket)
{
  if (!s->system_request && bucket_info.flags & BUCKET_SUSPENDED) {
    ldpp_dout(s, 0) << "NOTICE: bucket " << bucket_info.bucket.name
        << " is suspended" << dendl;
    return -ERR_USER_SUSPENDED;
  }
...
}
```







## 设置User状态

```c++
//rgw_admin.cc

// set suspension operation parameters
  if (opt_cmd == OPT_USER_ENABLE)
    user_op.set_suspension(RGW_USER_ENABLED);
  else if (opt_cmd == OPT_USER_SUSPEND)
    user_op.set_suspension(suspend_type);
```



````c++
void RGWOp_User_Modify::execute(){
     RESTArgs::get_bool(s, "suspended", false, &suspended);
    
    if (s->info.args.exists("suspended"))
        op_state.set_suspension(suspended)
}
````

```c++
int RGWUser::execute_add(RGWUserAdminOpState& op_state, std::string *err_msg)
{
      user_info.suspended = op_state.get_suspension_status();
    ...
}

int RGWUser::execute_modify(RGWUserAdminOpState& op_state, std::string *err_msg)
{
    if (op_state.has_suspension_op()) {
        __u8 suspended = op_state.get_suspension_status();
        user_info.suspended = suspended;
        ...
    }
    ret = store->set_buckets_enabled(bucket_names, !suspended);
}
```



## bucket suspended

bucket的flag

```c++
enum RGWBucketFlags {
  BUCKET_SUSPENDED = 0x1, //看这个
  BUCKET_VERSIONED = 0x2,
  BUCKET_VERSIONS_SUSPENDED = 0x4,
  BUCKET_DATASYNC_DISABLED = 0X8,
  BUCKET_MFA_ENABLED = 0X10,
  BUCKET_OBJ_LOCK_ENABLED = 0X20,
};
```

### Set方法



```c++
//rgw_user.cc
int RGWUser::execute_modify(RGWUserAdminOpState& op_state, std::string *err_msg)
{
    
	ret = store->set_buckets_enabled(bucket_names, !suspended);

```



```c++
int RGWRados::set_buckets_enabled(vector<rgw_bucket>& buckets, bool enabled)
{
    if (enabled) {
      info.flags &= ~BUCKET_SUSPENDED;
    } else {
      info.flags |= BUCKET_SUSPENDED;
    }
}
```



```c++

int RGWRados::bucket_suspended(rgw_bucket& bucket, bool *suspended)
{
  RGWBucketInfo bucket_info;
  auto obj_ctx = svc.sysobj->init_obj_ctx();
  int ret = get_bucket_info(obj_ctx, bucket.tenant, bucket.name, bucket_info, NULL);
  if (ret < 0) {
    return ret;
  }

  *suspended = ((bucket_info.flags & BUCKET_SUSPENDED) != 0);
  return 0;
}
```



### Get方法

```c++
static int read_bucket_policy(RGWRados *store,
                              struct req_state *s,
                              RGWBucketInfo& bucket_info,
                              map<string, bufferlist>& bucket_attrs,
                              RGWAccessControlPolicy *policy,
                              rgw_bucket& bucket)
{
  if (!s->system_request && bucket_info.flags & BUCKET_SUSPENDED) {
    ldpp_dout(s, 0) << "NOTICE: bucket " << bucket_info.bucket.name
        << " is suspended" << dendl;
    return -ERR_USER_SUSPENDED;
  }
    ...
}

static int read_obj_policy(RGWRados *store,
                           struct req_state *s,
                           RGWBucketInfo& bucket_info,
                           map<string, bufferlist>& bucket_attrs,
                           RGWAccessControlPolicy* acl,
                           string *storage_class,
			   boost::optional<Policy>& policy,
                           rgw_bucket& bucket,
                           rgw_obj_key& object)
{
  string upload_id;
  upload_id = s->info.args.get("uploadId");
  rgw_obj obj;

  if (!s->system_request && bucket_info.flags & BUCKET_SUSPENDED) {
    ldpp_dout(s, 0) << "NOTICE: bucket " << bucket_info.bucket.name
        << " is suspended" << dendl;
    return -ERR_USER_SUSPENDED;
  }
  ...
}
```

