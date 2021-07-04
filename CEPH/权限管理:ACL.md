# Ceph整理：认证与ACL

## 参考文档

[aws标准定义：ACL](https://docs.aws.amazon.com/AmazonS3/latest/dev-retired/acl-overview.html)

[ceph官方文档：Authentication and ACLs](https://docs.ceph.com/en/latest/radosgw/s3/authentication/)



## 认证





## Access Control Lists(ACLs)

每个Bucket或是Object都有一个ACL属性，用于规定AWS账户或分组进行对资源访问的权限控制。当收到一个请求的时候，将会对相应的ACL进行检查，并验证请求者是否有访问权限。

当创建一个bucket或object时，aws s3将会创建一个默认的ACL，并且赋予资源所有者对该资源的full control权限：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<AccessControlPolicy xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
  <Owner>
    <ID>*** Owner-Canonical-User-ID ***</ID>
    <DisplayName>owner-display-name</DisplayName>
  </Owner>
  <AccessControlList>
    <Grant>
      <Grantee xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
               xsi:type="Canonical User">
        <ID>*** Owner-Canonical-User-ID ***</ID>
        <DisplayName>display-name</DisplayName>
      </Grantee>
      <Permission>FULL_CONTROL</Permission>
    </Grant>
  </AccessControlList>
</AccessControlPolicy> 
```

> 其中，Owner通过[AWS cononical user ID](https://docs.aws.amazon.com/AmazonS3/latest/dev-retired/acl-overview.html#finding-canonical-id)的形式指明了该资源的owner。
>
> Grant表明了Grantee(受让人)以及Permission(权限)。
>
> 其中，Grantee(受让人)可以是一个AWS账户，也可以是一个**预定义**的Amazon S3分组。可以使用一个邮箱地址或canonical user ID。当使用邮箱地址的时候，本质上也是通过邮箱地址获得canonical user ID，然后将其添加到ACL中，而不直接使用邮箱地址。
>
> * 预定义分组（Amazon S3 Predefined Groups）
>
>   可以是
>
>   * Authenticated User group：
>   * All Users group
>   * Log Delivery group

## 可以赋予的权限分类

| Permission     | When granted on a bucket                                     | When granted on an object                                    |
| :------------- | :----------------------------------------------------------- | :----------------------------------------------------------- |
| `READ`         | Allows grantee to list the objects in the bucket             | Allows grantee to read the object data and its metadata      |
| `WRITE`        | Allows grantee to create, overwrite, and delete any object in the bucket | Not applicable                                               |
| `READ_ACP`     | Allows grantee to read the bucket ACL                        | Allows grantee to read the object ACL                        |
| `WRITE_ACP`    | Allows grantee to write the ACL for the applicable bucket    | Allows grantee to write the ACL for the applicable object    |
| `FULL_CONTROL` | Allows grantee the READ, WRITE, READ_ACP, and WRITE_ACP permissions on the bucket | Allows grantee the READ, READ_ACP, and WRITE_ACP permissions on the object |

## ACL Permission与Access Policy Permissions的映射关系

| ACL permission | Corresponding access policy permissions when the ACL permission is granted on a bucket | Corresponding access policy permissions when the ACL permission is granted on an object |
| :------------- | :----------------------------------------------------------- | :----------------------------------------------------------- |
| `READ`         | `s3:ListBucket`, `s3:ListBucketVersions`, and `s3:ListBucketMultipartUploads` | `s3:GetObject`, `s3:GetObjectVersion`, and `s3:GetObjectTorrent` |
| `WRITE`        | `s3:PutObject` and `s3:DeleteObject`.In addition, when the grantee is the bucket owner, granting `WRITE` permission in a bucket ACL allows the `s3:DeleteObjectVersion` action to be performed on any version in that bucket. | Not applicable                                               |
| `READ_ACP`     | `s3:GetBucketAcl`                                            | `s3:GetObjectAcl` and`s3:GetObjectVersionAcl`                |
| `WRITE_ACP`    | `s3:PutBucketAcl`                                            | `s3:PutObjectAcl` and`s3:PutObjectVersionAcl`                |
| `FULL_CONTROL` | Equivalent to granting `READ`, `WRITE`, `READ_ACP`, and `WRITE_ACP` ACL permissions. Accordingly, this ACL permission maps to a combination of corresponding access policy permissions. | Equivalent to granting `READ`, `READ_ACP`, and`WRITE_ACP` ACL permissions. Accordingly, this ACL permission maps to a combination of corresponding access policy permissions. |



## [条件关键字/Condition Keys](https://docs.aws.amazon.com/AmazonS3/latest/dev-retired/amazon-s3-policy-keys.html#grant-putobject-conditionally-1)

在授予访问策略权限时，可以使用条件键来约束使用桶策略的对象上的ACL值。可以使用如下所示的context key来强制在请求中使用特定的ACL:

- `s3:x-amz-grant-read` ‐ Require read access.
- `s3:x-amz-grant-write` ‐ Require write access.
- `s3:x-amz-grant-read-acp` ‐ Require read access to the bucket ACL.
- `s3:x-amz-grant-write-acp` ‐ Require write access to the bucket ACL.
- `s3:x-amz-grant-full-control` ‐ Require full control.
- `s3:x-amz-acl` ‐ Require a [Canned ACL](https://docs.aws.amazon.com/AmazonS3/latest/dev-retired/acl-overview.html#canned-acl).



## ACL 底层保存

[Actions, resources, and condition keys for Amazon S3](https://docs.aws.amazon.com/AmazonS3/latest/dev-retired/list_amazons3.html)

```shell
NAME
       put-bucket-acl -

DESCRIPTION
       Sets  the  permissions on an existing bucket using access control lists
       (ACL). For more information, see Using ACLs .  To  set  the  ACL  of  a
       bucket, you must have WRITE_ACP permission.
       
       You  can  use  one  of the following two ways to set a bucket's permis-
       sions:
       o Specify the ACL in the request body
       o Specify permissions using request headers

			 NOTE:
          You cannot specify access permission using both  the  body  and  the
          request headers
```





https://www.cnblogs.com/dengchj/p/11908514.html

https://www.kanzhun.com/jiaocheng/172426.html

https://blog.csdn.net/litianze99/article/details/77983723

```shell
[root@192 ~]# radosgw-admin bucket stats --bucket bucket0
2021-05-19 02:25:11.817 7fa48a1fb840  2 []all 8 watchers are set, enabling cache
2021-05-19 02:25:11.826 7fa44f7fe700  2 []RGWDataChangesLog::ChangesRenewThread: start
{
    "bucket": "bucket0",
    "num_shards": 128,
    "tenant": "",
    "zonegroup": "9da63615-9342-4328-b573-bf506520407d",
    "placement_rule": "poolQQ",
    "explicit_placement": {
        "data_pool": "",
        "data_tail_pool": "",
        "data_extra_pool": "",
        "index_pool": ""
    },
    "index_type": "Normal",
    "id": "d67748bd-b048-4922-aa7c-397fc59aa34e.45400.1",
    "marker": "d67748bd-b048-4922-aa7c-397fc59aa34e.45400.1",
    "index_type": "Normal",
    "owner": "admin",
    "ver": .....
    "usage": {
        "rgw.main": {
            "size": 26619856,
            "size_actual": 26619904,
            "size_utilized": 26619856,
            "size_kb": 25996,
            "size_kb_actual": 25996,
            "size_kb_utilized": 25996,
            "num_objects": 1
        },
        "rgw.multimeta": {
            "size": 0,
            "size_actual": 0,
            "size_utilized": 0,
            "size_kb": 0,
            "size_kb_actual": 0,
            "size_kb_utilized": 0,
            "num_objects": 0
        }
    },
    "bucket_quota": {
        "enabled": true,
        "check_on_raw": false,
        "max_size": -1,
        "max_size_kb": 0,
        "max_objects": 20000000
    }
}
2021-05-19 02:25:11.844 7fa48a1fb840  2 []removed watcher, disabling cache


#----------------
[root@192 ~]# ceph osd pool ls
.rgw.root
default.rgw.meta
default.rgw.log
default.rgw.control
00000000-default.rgw.buckets.index
00000000-default.rgw.buckets.non-ec
00000000-default.rgw.buckets.data

#===-------
```

## 测试脚本

#### 测试脚本

```shell
S3_HOST=http://localhost:8000

PROFILE="default"
OBJECT_BIG=TESTFILE_10MB
OBJECT_BIG_SSE=TESTFILE_10MB_SSE
BUCKET="bucket0"
OBJECT="object0"

function create_bucket(){
   echo "create $1"
   aws s3api --endpoint-url $S3_HOST --profile $PROFILE \
        create-bucket --bucket $1
   aws s3api --endpoint-url $S3_HOST --profile $PROFILE \
        put-object --bucket $1 --key $OBJECT
}


function get_bucket_acl(){
   echo "get_bucket_acl"
   aws s3api --endpoint-url $S3_HOST --profile $PROFILE \
       get-bucket-acl --bucket $BUCKET
}


function put_bucket_acl_private(){
echo "put_bucket_acl_private"
   aws s3api --endpoint-url $S3_HOST --profile $PROFILE \
        put-bucket-acl --bucket $BUCKET \
        --acl private
}

function put_bucket_acl_public_read(){
echo "put_bucket_acl_public_read"
   aws s3api --endpoint-url $S3_HOST --profile $PROFILE \
        put-bucket-acl --bucket $BUCKET \
        --acl public-read
}

function put_bucket_acl_public_read_write(){
echo "put_bucket_acl_public_read_write"
   aws s3api --endpoint-url $S3_HOST --profile $PROFILE \
        put-bucket-acl --bucket $BUCKET \
        --acl public-read-write
}

function get_object_acl(){
   echo "get_object_acl"
   aws s3api --endpoint-url $S3_HOST --profile $PROFILE \
       get-object-acl --bucket $BUCKET --key $OBJECT
}


function put_object_acl_private(){
echo "put_object_acl_private"
   aws s3api --endpoint-url $S3_HOST --profile $PROFILE \
        put-object-acl --bucket $BUCKET  --key $OBJECT \
        --acl private
}

function put_object_acl_public_read(){
echo "put_object_acl_public_read"
   aws s3api --endpoint-url $S3_HOST --profile $PROFILE \
        put-object-acl --bucket $BUCKET --key $OBJECT \
        --acl public-read
}

function put_object_acl_public_read_write(){
echo "put_object_acl_public_read_write"
   aws s3api --endpoint-url $S3_HOST --profile $PROFILE \
        put-object-acl --bucket $BUCKET --key $OBJECT \
        --acl public-read-write
}




function canned_acl_test(){
    create_bucket $BUCKET
put_bucket_acl_private
get_bucket_acl
put_bucket_acl_public_read
get_bucket_acl
put_bucket_acl_public_read_write
get_bucket_acl

put_object_acl_private
get_object_acl
put_object_acl_public_read
get_object_acl
put_object_acl_public_read_write
get_object_acl

}
```

#### 测试结果



需要整理一下ACL PERM的位设置：

```c++
#define RGW_PERM_NONE            0x00
#define RGW_PERM_READ            0x01
#define RGW_PERM_WRITE           0x02
#define RGW_PERM_READ_ACP        0x04
#define RGW_PERM_WRITE_ACP       0x08
#define RGW_PERM_READ_OBJS       0x10
#define RGW_PERM_WRITE_OBJS      0x20
#define RGW_PERM_FULL_CONTROL    ( RGW_PERM_READ | RGW_PERM_WRITE | \
                                  RGW_PERM_READ_ACP | RGW_PERM_WRITE_ACP )
#define RGW_PERM_ALL_S3          RGW_PERM_FULL_CONTROL
#define RGW_PERM_INVALID         0xFF00

enum ACLGranteeTypeEnum {
/* numbers are encoded, should not change */
  ACL_TYPE_CANON_USER = 0,
  ACL_TYPE_EMAIL_USER = 1,
  ACL_TYPE_GROUP      = 2,
  ACL_TYPE_UNKNOWN    = 3,
  ACL_TYPE_REFERER    = 4,
};

enum ACLGroupTypeEnum {
/* numbers are encoded should not change */
  ACL_GROUP_NONE                = 0,
  ACL_GROUP_ALL_USERS           = 1,
  ACL_GROUP_AUTHENTICATED_USERS = 2,
};
```

添加权限的时候实际上是这样：

```c++
void RGWAccessControlList::_add_grant(ACLGrant *grant)
{
  ACLPermission& perm = grant->get_permission();
  ACLGranteeType& type = grant->get_type();
  switch (type.get_type()) {
  case ACL_TYPE_REFERER:
    referer_list.emplace_back(grant->get_referer(), perm.get_permissions());

    /* We're specially handling the Swift's .r:* as the S3 API has a similar
     * concept and thus we can have a small portion of compatibility here. */
     if (grant->get_referer() == RGW_REFERER_WILDCARD) {
       acl_group_map[ACL_GROUP_ALL_USERS] |= perm.get_permissions();
     }
    break;
  case ACL_TYPE_GROUP:
    acl_group_map[grant->get_group()] |= perm.get_permissions();
    break;
  default:
    {
      rgw_user id;
      if (!grant->get_id(id)) {
        ldout(cct, 0) << "ERROR: grant->get_id() failed" << dendl;
      }
      acl_user_map[id.to_str()] |= perm.get_permissions();
    }
  }
}
```



### put_bucket_acl bt:

```shell
0  RGWAccessControlPolicy_S3::rebuild (this=this@entry=0x7fc3e7ee18c0, store=0x7fc3e6fd4000, owner=owner@entry=0x7fc3e71662a8, dest=...)
    at /data/ceph/src/rgw/rgw_acl_s3.cc:701
#1  0x00007fc3e5784819 in RGWPutACLs::execute (this=0x7fc3e7166210) at /data/ceph/src/rgw/rgw_op.cc:5489
#2  0x00007fc3e57bbde2 in rgw_process_authenticated (handler=handler@entry=0x7fc3e7cd04a0, op=@0x7fc3b2a863d8: 0x7fc3e7166210, req=req@entry=0x7fc3b2a86f90, 
    s=s@entry=0x7fc3b2a867c0, skip_retarget=skip_retarget@entry=false) at /data/ceph/src/rgw/rgw_process.cc:104
#3  0x00007fc3e57bd08e in process_request (store=0x7fc3e6fd4000, rest=0x7fff0dc45e40, req=req@entry=0x7fc3b2a86f90, frontend_prefix="", auth_registry=..., 
    client_io=client_io@entry=0x7fc3b2a86fc0, olog=0x0, http_ret=http_ret@entry=0x7fc3b2a86f8c) at /data/ceph/src/rgw/rgw_process.cc:265
#4  0x00007fc3e5619e45 in RGWCivetWebFrontend::process (this=0x7fc3e7164320, conn=<optimized out>)
    at /data/ceph/src/rgw/rgw_civetweb_frontend.cc:38
#5  0x00007fc3e568c55f in handle_request (conn=conn@entry=0x7fc3e7251000) at /data/ceph/src/civetweb/src/civetweb.c:9890

```

### put object时添加acl设置测试：原有实现

```c++
#0  RGWAccessControlList_S3::create_canned (this=this@entry=0x7fa8b8486a40, owner=..., bucket_owner=..., canned_acl="public-read", support_cos_default=support_cos_default@entry=fals
e)
    at /data/ceph/src/rgw/rgw_acl_s3.cc:471
#1  0x00007fa8e9a9a2df in create_canned (support_cos_default=<optimized out>, canned_acl="", bucket_owner=..., _owner=..., this=0x7fa8b8486a30) at /data/ceph/src/
rgw/rgw_acl_s3.h:93
#2  create_s3_policy (s=0x7fa8b84877c0, store=<optimized out>, s3policy=..., owner=..., is_obj_acl=is_obj_acl@entry=true) at /data/ceph/src/rgw/rgw_rest_s3.cc:127
3
#3  0x00007fa8e9ab7a3b in RGWPutObj_ObjStore_S3::get_params (this=0x7fa8ec8f6000) at /data/ceph/src/rgw/rgw_rest_s3.cc:1466
#4  0x00007fa8e999463c in RGWPutObj::execute (this=0x7fa8ec8f6000) at /data/ceph/src/rgw/rgw_op.cc:3850
```





## get object acl



get object acl:

```shell
#1  0x00007fa8e9b3efb5 in ACLGrant_S3::to_xml (this=this@entry=0x7fa8eca09ca8, cct=0x7fa8eb9941c0, out=...) at /data/ceph/src/rgw/rgw_acl_s3.cc:268
#2  0x00007fa8e9b3f301 in RGWAccessControlList_S3::to_xml (this=0x7fa8eca02d30, out=...) at /data/ceph/src/rgw/rgw_acl_s3.cc:315
#3  0x00007fa8e9b3f394 in RGWAccessControlPolicy_S3::to_xml (this=0x7fa8eca02d20, out=...) at /data/ceph/src/rgw/rgw_acl_s3.cc:538
#4  0x00007fa8e99887ae in decode_policy (cct=cct@entry=0x7fa8eb9941c0, bl=..., policy=policy@entry=0x7fa8eca02d20) at /data/ceph/src/rgw/rgw_op.cc:167
#5  0x00007fa8e9990257 in get_obj_policy_from_attr (bucket_attrs=std::map with 2 elements = {...}, obj=..., policy=0x7fa8eca02d20, bucket_info=..., obj_ctx=..., 
    store=0x7fa8ebb0c000, cct=<optimized out>) at /data/ceph/src/rgw/rgw_op.cc:234
#6  read_obj_policy (store=store@entry=0x7fa8ebb0c000, s=s@entry=0x7fa8b74857c0, bucket_info=..., bucket_attrs=std::map with 2 elements = {...}, acl=0x7fa8eca02d20, 
    policy=..., bucket=..., object=...) at /data/ceph/src/rgw/rgw_op.cc:377
#7  0x00007fa8e9990bbc in rgw_build_object_policies (store=0x7fa8ebb0c000, s=0x7fa8b74857c0, prefetch_data=<optimized out>)
    at /data/ceph/src/rgw/rgw_op.cc:600
#8  0x00007fa8e9990cd4 in RGWHandler::do_read_permissions (this=0x7fa8eccd1e40, op=<optimized out>, only_bucket=<optimized out>)
    at /data/ceph/src/rgw/rgw_op.cc:7695
#9  0x00007fa8e99b9d04 in rgw_process_authenticated (handler=handler@entry=0x7fa8eccd1e40, op=@0x7fa8b74853d8: 0x7fa8ebc9dcc0, req=req@entry=0x7fa8b7485f90, 
    s=s@entry=0x7fa8b74857c0, skip_retarget=skip_retarget@entry=false) at /data/ceph/src/rgw/rgw_process.cc:65
---Type <return> to continue, or q <return> to quit---n
#10 0x00007fa8e99bb07e in process_request (store=0x7fa8ebb0c000, rest=0x7ffc4908bd10, req=req@entry=0x7fa8b7485f90, frontend_prefix="", auth_registry=..., 
    client_io=client_io@entry=0x7fa8b7485fc0, olog=0x0, http_ret=http_ret@entry=0x7fa8b7485f8c) at /data/ceph/src/rgw/rgw_process.cc:265
#11 0x00007fa8e9817e35 in RGWCivetWebFrontend::process (this=0x7fa8ebc9c320, conn=<optimized out>) at /data/ceph/src/rgw/rgw_civetweb_frontend.cc:38
#12 0x00007fa8e988a54f in handle_request (conn=conn@entry=0x7fa8ebd8e000) at /data/ceph/src/civetweb/src/civetweb.c:9890
#13 0x00007fa8e988bedb in process_new_connection (conn=<optimized out>) at /data/ceph/src/civetweb/src/civetweb.c:12328
#14 worker_thread_run (thread_func_param=0x7fa8ebb7c800) at /data/ceph/src/civetweb/src/civetweb.c:12505
#15 worker_thread (thread_func_param=0x7fa8ebb7c800) at /data/ceph/src/civetweb/src/civetweb.c:12542
```

