# S3 WORM标准简述

write once, read many (WORM) 。也被aws称为Object Lock。主要功能是灵活地实现了不同级别的对文件的保护功能：

1. **保护期有固定时限**：在一定时间内（最少1天，最大无限制 ^[5]^ 如何表示？CSP中以0来表示），对一个新对象或已有对象版本进行保护，使其不被修改或删除，时间到后允许修改删除。这种模式被称为*rentention模式*。

   1.1） rentention模式1，受控后门：*Governance mode*，在保护期内，普通用户无法修改删除对象或更改rentention设置，而具有特权*s3:BypassGovernanceRetention*的用户可以删除或更改（覆盖或删除）*Governance mode rentention*设置和对象本身。

   > 需要在头部中携带`x-amz-bypass-governance-retention:true`。（这个头部是否需要显式地加上？如果不用curl自行构建，是否有什么工具自带？）另：S3标准中显示s3控制台默认携带。
   >
   > 需要权限 `s3:BypassGovernanceRetention` or`s3:GetBucketObjectLockConfiguration`

   1.2） rentention模式2，绝对保护：*Compliance mode*，谁都无法修改删除对象或rentention设置（即无法修改到期时间），只能等待retention时间到期。

2. **保护期没有时限**：不限时地对一个新对象或已有对象版本进行保护，使其文件不被修改或删除，除非移除这个标记：legal hold。

> 1. 实际上第2种主要适用于不知道应该保留多长时间，但确实应该进行保护的场景。
> 2. legal hold的修改需要有`s3:PutObjectLegalHold`权限。

其他：

1. 可以自由地组合retention和legal hold两种形式。即允许两种属性同时施加于一个对象而互不影响，各自独立地作用。这样就有了两个层面的保护。

2. 对象锁仅作用于versioned bucket。retention和legal hold作用于单个的object version中。当lock一个object时，元数据中会保存该version的相关信息。对于一个版本的对象加对象锁时，仅仅是对这个版本的对象进行了保护，而不会阻止创建该对象的新的版本。我们也可以对同一个key的对象的不同版本施加不同的WORM策略。
3. 对于Rentention模式，使用bucket的默认设置时，设置的不是到期日时间戳（Retain Until Date），而是一个时间期限，例如几天，几年。当存放对象到bucket中时，将根据该bucket的默认设置期限计算一个Retain Until Date，然后将其添加到对象版本的创建时间戳中，该对象的元数据中将保存Retain Until Date。而若显式地给一个对象版本设置retention mode和期限时，这些设置将覆盖从bucket中计算出来的值。

> 存储桶的默认设置只有在新对象加入之后生效，而不会更改桶中已有的对象。即：一旦新对象创建后，其retention属性由桶的默认属性获得，而此后如果修改存储桶的默认retention不会修改已有的对象的属性。^[5]^
>
> 若对一个桶设置默认的retention period，在上传对象到这个桶时必须携带`Content-MD5`头。^[5]^

S3 Object Lock官方文档：https://docs.aws.amazon.com/AmazonS3/latest/dev/object-lock-overview.html

## 与versioning的组合

version实现的功能是，通过一个状态标记，来实现以下几个功能：

1. unable： 单一版本，若有相同名称，将覆盖源文件。通过null标记来表示。

2. enable：多版本，通过VersionId来表示不同版本，使用一个IsLatest属性来标记当前最新对象。

   > 这样的话如何获得最新对象？是否需要遍历？通过什么遍历？

3. suspend：挂起，从当前开始不再生成新版本。通过让新版本的状态设为null来实现，每次上传同名文件时，将按照原有的null来覆盖。

# 3. S3 ObjectLock标准/社区N版WORM/CSP版WORM实现功能对比

| 序号 | S3标准                                                       | 社区N版WORM                                                  |
| ---- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| 1    | **Retention mode: <br />Governance mode**<br /><br />1. 固定期限内保护对象版本，期限外则不保护；<br />2. 普通用户无法覆盖、删除对象版本或修改对象版本的retention设置，而具有权限`s3:BypassGovernanceRetention`或<br />`s3:GetBucketObjectLockConfiguration`的用户，并且头部显式地包含`x-amz-bypass-governance-retention:true`则可以。 | 1.与S3标准一致<br />2.1通过object versioning来保护某个对象版本不被覆盖，将生成新的version-id<br />2.2 删除时复用了versioning的效果，创建一个delete-marker，并生成一个新的Id，并阻止指定version-id真正删除对象。<br />2.3 权限控制与S3一致。 |
| 2    | **Retention mode:<br />Compliance mode**<br />1. 固定期限内保护对象版本<br />2. 保护期内任何用户都无法覆盖、删除对象版本或修改对象版本的retention设置 | 1.实现固定保护期功能<br />2.1 通过object versioning来保护某个对象版本不被覆盖，将生成新的对象版本<br />2.2 删除时只针对GOVERNANCE进行了判断，非GOVERNANCE将报错，以实现COMPLIANCE模式禁止删除的效果 |
|      | **Retention periods**:<br /><br />1. 可以针对某个对象设置retention period，也可以直接使用桶的默认设置；<br />2. 当使用桶的默认设置时，设置的不是到期日，而是保护时长（几天或几年）。此时将根据保护时长和该对象版本的创建时间戳计算，得到到期日Retain Until Date，保存到对象的元数据中； | 1. 通过put object retention API实现针对某个对象单独设置retention period。<br />2.与S3标准一致<br /> |
| 3    | **Legal Holds mode**：<br />1.只要该属性被设置，就能实现对象版本的不限期保护覆盖、删除的功能<br />2.实现拥有`s3:PutObjectLegalHold`特权的用户修改该属性功能 | 1.1通过versioning来保证不被覆盖，而是生成新的version-id的对象<br />1.2 通过`RGW_ATTR_OBJECT_LEGAL_HOLD`的属性来避免 |
|      | Retention mode与Legal Holds mode可叠加使用，以实现限时与不限时的双重保护功能 | 与S3标准一致。                                               |
| 4    | 开启桶的对象锁时，只能对于一个新的桶开启。<br />（标准中指出可以找aws管理员来实现对已有的桶开启对象锁） | 与s3标准一致。                                               |
| 5    | **开启桶的对象锁时的默认设置**：<br />1.如果给桶设置一个默认的配置，之后加入的对象都将使用这个配置。加入之后的对象也可以独立地使用retention period或legal holds，或都使用；<br />2.创建开启对象锁的桶时，将自动开启桶的versioning功能；<br />3.一旦创建开启对象锁的桶后，将无法关闭对象锁功能，也无法suspend桶的versioning功能。<br />4. 若上传时对象使用桶的默认设置，一旦该对象上传后，其retention设置将与桶无关，更改桶的属性将不会影响对象的属性。 | 1. put-object-lock-configuration：通过新增一个DefaultRetention类来保存该桶的默认设置，新加入该桶的对象将复制该设置到对象版本的元数据中；<br />2.直接同时在bucket_info中设置objectLock和versioning标记<br />3.获取bucket_info中的状态阻拦<br />4.将属性写入到对象的attr: `RGW_ATTR_OBJECT_RETENTION`中 |
| 6    | **Default retention settings:**<br />1.当创建一个开启对象锁的桶时，直接放入的对象还不具备被保护的效果。只有设置了default retention mode(governance/compliance)和 period(此时指定的不是到期日，而是有效时长），之后放入该桶的对象才能被保护；<br />2.Default retention将会在新对象上传到该桶的时候被自动应用，除非在上传对象的时候显式地指定了不同的retention mode。<br />3. 如果想要强制地针对所有新的对象使用桶的默认retention mode设置，那么只需设置了桶的默认设置，并且取消用户设置对象retention的权限即可。 | 1.创建开启对象锁的桶只是设置了对象锁和versioning的标记，并无其他的流程，只有设置了DefaultRetention才构造了相应的数据结构，将相关属性放到bucket_info中，用于对象上传时拷贝设置项。<br />2. 如1所示。<br />3.权限限制。 |

# 社区N版中WORM的使用及对应实现

社区N版的WORM实现紧跟了aws的标准，包括了开启、关闭、查询桶的WORM状态，独立设置对象的ObjectLock，设置对象的legal hold属性。

在实现上，实际上是通过bucket versioning来实现

## 5.1 社区N版WORM上传对象时的实现

### 5.1.1 简单上传对象

在一个已默认开启GOVERNANCE模式的对象锁的桶中上传对象，将会在写入rgw_rados时将bucket_info中的默认retention信息加入到`RGW_ATTR_OBJECT_RETENTION`中：

```c++
int RGWRados::Object::Write::_do_write_meta(uint64_t size, uint64_t accounted_size, map<string, bufferlist>& attrs, bool assume_noent, bool modify_tail,void *_index_op) {
  ...
  if (target->bucket_info.obj_lock_enabled() && target->bucket_info.obj_lock.has_rule() && meta.flags == PUT_OBJ_CREATE) {
    auto iter = attrs.find(RGW_ATTR_OBJECT_RETENTION);
    if (iter == attrs.end()) {
      real_time lock_until_date = target->bucket_info.obj_lock.get_lock_until_date(meta.set_mtime);
      string mode = target->bucket_info.obj_lock.get_mode();//GOVERNANCE/COMPLIANCE  
      RGWObjectRetention obj_retention(mode, lock_until_date);
      bufferlist bl;
      obj_retention.encode(bl);
      op.setxattr(RGW_ATTR_OBJECT_RETENTION, bl);
    }
  }
  ...
}
```

### 5.1.2 上传对象时携带自定义配置

在代码实现中，在get_params过程中获得了从HTTP头中得到的请求，判断是否为Retention，LegalHold（代码中也可以看到二者之间不是二选一的关系，可以两者兼得），并设置标记，供后续使用：

```c++
RGWPutObj_ObjStore_S3::get_params() {
  //handle object lock
  //1. 从头中获得Retention以及LegalHold相关参数
  auto obj_lock_mode_str = s->info.env->get("HTTP_X_AMZ_OBJECT_LOCK_MODE");
  auto obj_lock_date_str = s->info.env->get("HTTP_X_AMZ_OBJECT_LOCK_RETAIN_UNTIL_DATE");
  auto obj_legal_hold_str = s->info.env->get("HTTP_X_AMZ_OBJECT_LOCK_LEGAL_HOLD");
  //2. 处理Retention相关
  if (obj_lock_mode_str && obj_lock_date_str) {
    boost::optional<ceph::real_time> date = ceph::from_iso_8601(obj_lock_date_str);
    if (boost::none == date || ceph::real_clock::to_time_t(*date) <= ceph_clock_now()) {
        ret = -EINVAL;
        ldpp_dout(this,0) << "invalid x-amz-object-lock-retain-until-date value" << dendl;
        return ret;
    }
    if (strcmp(obj_lock_mode_str, "GOVERNANCE") != 0 && strcmp(obj_lock_mode_str, "COMPLIANCE") != 0) {
        ret = -EINVAL;
        ldpp_dout(this,0) << "invalid x-amz-object-lock-mode value" << dendl;
        return ret;
    }
    obj_retention = new RGWObjectRetention(obj_lock_mode_str, *date);
  } else if ((obj_lock_mode_str && !obj_lock_date_str) || (!obj_lock_mode_str && obj_lock_date_str)) {
    ret = -EINVAL;
    ldpp_dout(this,0) << "need both x-amz-object-lock-mode and x-amz-object-lock-retain-until-date " << dendl;
    return ret;
  }
  //3.处理LegalHold相关
  if (obj_legal_hold_str) {
    if (strcmp(obj_legal_hold_str, "ON") != 0 && strcmp(obj_legal_hold_str, "OFF") != 0) {
        ret = -EINVAL;
        ldpp_dout(this,0) << "invalid x-amz-object-lock-legal-hold value" << dendl;
        return ret;
    }
    obj_legal_hold = new RGWObjectLegalHold(obj_legal_hold_str);
  }
  //4.容错
  if (!s->bucket_info.obj_lock_enabled() && (obj_retention || obj_legal_hold)) {
    ldpp_dout(this, 0) << "ERROR: object retention or legal hold can't be set if bucket object lock not configured" << dendl;
    ret = -ERR_INVALID_REQUEST;
    return ret;
  }
```

之后

```c++
void RGWPutObj::execute() {
  ...
  op_ret = get_system_versioning_params(s, &olh_epoch, &version_id);
  ...
  if (s->bucket_info.versioning_enabled()) {
      if (!version_id.empty()) {
        obj.key.set_instance(version_id);
      } else {
        store->gen_rand_obj_instance_name(&obj);
        version_id = obj.key.instance;
      }
  }
  ...
  //写入attr
  if (obj_legal_hold) {
    bufferlist obj_legal_hold_bl;
    obj_legal_hold->encode(obj_legal_hold_bl);
    emplace_attr(RGW_ATTR_OBJECT_LEGAL_HOLD, std::move(obj_legal_hold_bl));
  }
  if (obj_retention) {
    bufferlist obj_retention_bl;
    obj_retention->encode(obj_retention_bl);
    emplace_attr(RGW_ATTR_OBJECT_RETENTION, std::move(obj_retention_bl));
  }
}
```

## 5.2 社区N版WORM删除对象的实现

代码中，需先在get_params中获取头中是否有`HTTP_X_AMZ_BYPASS_GOVERNANCE_RETENTION`。这是先决条件，若没有该头，将无法删除对象：

```c++
RGWDeleteObj_ObjStore_S3::get_params(){
  ...
  const char *bypass_gov_header = s->info.env->get("HTTP_X_AMZ_BYPASS_GOVERNANCE_RETENTION");
  if (bypass_gov_header) {
     std::string bypass_gov_decoded = url_decode(bypass_gov_header);
     bypass_governance_mode = boost::algorithm::iequals(bypass_gov_decoded, "true");//该值默认为false
  }
  ...
}
```

然后在verify_permission中，需要进一步确认用户具有`s3BypassGovernanceRetention`权限。最终起到作用的是`RGWDeleteObj.bypass_perm`，该值在构造函数中被设置为true，在下面`verify_permission`中若鉴权不通过，才被设置为false：

```c++
int RGWDeleteObj::verify_permission() {
  int op_ret = get_params();
  if (op_ret) {
    return op_ret;
  }
  if (s->iam_policy || ! s->iam_user_policies.empty()) {
    if (s->bucket_info.obj_lock_enabled() && bypass_governance_mode) {//要有对应头部
      //然后需要具有s3BypassGovernanceRetention权限
      auto r = eval_user_policies(s->iam_user_policies, s->env, boost::none, 
                                  rgw::IAM::s3BypassGovernanceRetention,
                                  ARN(s->bucket, s->object.name));
       if (r == Effect::Deny) {
          bypass_perm = false;
       } else if (r == Effect::Pass && s->iam_policy) {
          r = s->iam_policy->eval(s->env, *s->auth.identity, 
                                rgw::IAM::s3BypassGovernanceRetention,
                                ARN(s->bucket, s->object.name));
        if (r == Effect::Deny) {
           bypass_perm = false;
        }
      }
   }
   ...
  }
```

然后在`execute()`中进行最后的处理：

```c++
void RGWDeleteObj::execute(){
  ...
  if (check_obj_lock) {
      auto aiter = attrs.find(RGW_ATTR_OBJECT_RETENTION);
      if (aiter != attrs.end()) {
        RGWObjectRetention obj_retention;
        try {
          decode(obj_retention, aiter->second);//从attr RGW_ATTR_OBJECT_RETENTION中获取RGWObjectRetention
        } catch (buffer::error& err) {
          ldpp_dout(this, 0) << "ERROR: failed to decode RGWObjectRetention" << dendl;
          op_ret = -EIO;
          return;
        }
        if (ceph::real_clock::to_time_t(obj_retention.get_retain_until_date()) > ceph_clock_now()) {
          if (obj_retention.get_mode().compare("GOVERNANCE") != 0 //1.该对象的attr中WORM模式限制为GOVERNANCE（从这里也可以看出来若是COMPLIANCE直接报错了，即rgw代码中没有针对COMPLIANCE做其他逻辑，只要是retention模式，但不是“GOVERNANCE”，都不允许删除
              || !bypass_perm                                     //2.s3BypassGovernanceRetention权限限制
              || !bypass_governance_mode) {               //3.HTTP_X_AMZ_BYPASS_GOVERNANCE_RETENTION头部限制
            //只有以上三个条件都满足，才能允许删除，否则报错 
                op_ret = -EACCES;
             return;
          }
        }
      }
    //第二步,判断另一种对象锁：legal hold（这样也说明两种对象锁可以同时使用）
      aiter = attrs.find(RGW_ATTR_OBJECT_LEGAL_HOLD);
      if (aiter != attrs.end()) {
        RGWObjectLegalHold obj_legal_hold;
        try {
          decode(obj_legal_hold, aiter->second);
        } catch (buffer::error& err) {
          ldpp_dout(this, 0) << "ERROR: failed to decode RGWObjectLegalHold" << dendl;
          op_ret = -EIO;
          return;
        }
        if (obj_legal_hold.is_enabled()) {//若legal hold标记还存在，则阻止删除对象。
          op_ret = -EACCES;
          return;
        }
      }
    }  
  ...
}
```

**rgw::IAM:: bucked的权限管理**

> 注：s3BypassGovernanceRetention等没有更新到authentication.rst中，可以加上。

```c++
void rgw_add_to_iam_environment(rgw::IAM::Environment& e, std::string_view key, std::string_view val){
  
}
```

遗留问题： 未看到s3BypassGovernanceRetention在什么时候加上权限的。

## 5.3 社区N版WORM功能测试

### 5.3.1 桶的WORM设置

#### 设置对象的WORM时，需使用开启对象锁的桶

```shell
aws s3api put-object-retention --bucket bucket0 --key object0_worm 
Mode="GOVERNANCE"|"COMPLIANCE",,RetainUntilDate=timestamp

# 附录：获得某个时刻的Unix时间戳：
date -d "2020-12-12 00:00:00" +%s
```

在get/put-object-retention操作前，需要先设置object lock，即WORM。因为retention是基于bucket的对象锁来考虑的，单独讲object retention没有意义。此处的处理方式是报错invalid request：

```c++
void RGWPutObjRetention::execute() {
  if (!s->bucket_info.obj_lock_enabled()) {
    ldpp_dout(this, 0) << "ERROR: object retention can't be set if bucket object lock not configured" << dendl;
    op_ret = -ERR_INVALID_REQUEST;
    return;
  }
  ...
}
```

![image-20201208193112981](.1.CSP%E8%B0%83%E7%A0%94%EF%BC%9AL2N%20WORM.assets/image-20201208193112981.png)

代码中的`bucket_info.obj_lock_enabled()`的实现：

`bool obj_lock_enabled() const { return (flags & BUCKET_OBJ_LOCK_ENABLED) != 0; }`

该flag是在创建桶的时候，通过一个位来`BUCKET_OBJ_LOCK_ENABLED`表示的：

```c++
//rgw_op.cc,
void RGWCreateBucket::execute(
  ...
	if (obj_lock_enabled) {
    info.flags = BUCKET_VERSIONED | BUCKET_OBJ_LOCK_ENABLED;//唯一设置该值到bucket_info中的位置
  }
...
}
```

而对于上文中obj_lock_enabled设置的位置有3处：

1. 定义了obj_lock_enabled属性在RGWCreateBucket结构体中，默认值为false：

```c++
//rgw_op.h中
class RGWCreateBucket : public RGWOp {
  ...
  bool obj_lock_enabled;
  ...
  public:
  RGWCreateBucket() : has_cors(false), relaxed_region_enforcement(false), obj_lock_enabled(false) {}//构造函数中默认设置obj_lock_enabled为false
  ...
}
```

2. 创建bucket时，get_params时根据header `x-amz-bucket-object-lock-enabled`来设置：

```c++
//rgw_rest_s3.cc
int RGWCreateBucket_ObjStore_S3::get_params(){
  ...
  auto iter = s->info.x_meta_map.find("x-amz-bucket-object-lock-enabled");
  if (iter != s->info.x_meta_map.end()) {
    if (!boost::algorithm::iequals(iter->second, "true") && !boost::algorithm::iequals(iter->second, "false")) {
      return -EINVAL;
    }
    obj_lock_enabled = boost::algorithm::iequals(iter->second, "true");
  }
}
```

3. 对于当前zone不是master_zone时，从master zone中获得。

> 需详细梳理多zone。

```c++
void RGWCreateBucket::execute() {
  if (!store->svc.zone->is_meta_master()) {
    JSONParser jp;
    op_ret = forward_request_to_master(s, NULL, store, in_data, &jp);
    ...
    obj_lock_enabled = master_info.obj_lock_enabled();
    ...
  }else{
    ...
  }
}
```

#### 不能对已有的bucket设置object lock

> 虽然aws开发文档中提出了联系管理员可以对已有的bucket设置objectLock，但是未设置成S3标准：
>
> You can only enable Object Lock for new buckets. If you want to turn on Object Lock for an existing bucket, contact AWS Support。^[5]^
>
> 而目前N版ceph中的实现是不允许的。

```shell
aws s3api put-object-lock-configuration \
              --bucket my-bucket-with-object-lock \
              --object-lock-configuration '{ "ObjectLockEnabled": "Enabled", "Rule": { "DefaultRetention": { "Mode": "COMPLIANCE", "Days": 50 }}}'
```

对某个桶设置object lock，不能在已有的桶上设置，否则报错：

```c++
void RGWPutBucketObjectLock::execute() {
  if (!s->bucket_info.obj_lock_enabled()) {
    ldpp_dout(this, 0) << "ERROR: object Lock configuration cannot be enabled on existing buckets" << dendl;
    op_ret = -ERR_INVALID_BUCKET_STATE;
    return;
  }
  ...
}
```

![image-20201208194602709](.1.CSP%E8%B0%83%E7%A0%94%EF%BC%9AL2N%20WORM.assets/image-20201208194602709.png)

#### 新建一个开启object lock功能的桶

> 将同时启动该桶的versioning功能。

aws s3api create-bucket提供了如下一个参数：

```shell
--object-lock-enabled-for-bucket |  --no-object-lock-enabled-for-bucket (boolean)
   Specifies  whether you want S3 Object Lock to be enabled for the new  bucket.
```

创建一个桶，开启object-lock功能：

```shell
aws s3api --endpoint-url $S3_HOST --profile Nautilus create-bucket --bucket bucket_object_lock --object-lock-enabled-for-bucket
```

该属性通过http头部传递：

```c++
//rgw_rest_s3.cc
int RGWCreateBucket_ObjStore_S3::get_params(){
  ...
	auto iter = s->info.x_meta_map.find("x-amz-bucket-object-lock-enabled");
  if (iter != s->info.x_meta_map.end()) {
   	if (!boost::algorithm::iequals(iter->second, "true") && 					
       	!boost::algorithm::iequals(iter->second, "false")) {
     		return -EINVAL;
   	}
  	obj_lock_enabled = boost::algorithm::iequals(iter->second, "true");//将obj_lock_enabled设置为true
  }
  ...
}
```

抓包检查HTTP头，确认头部：

![image-20201212193920573](.1.CSP%E8%B0%83%E7%A0%94%EF%BC%9AL2N%20WORM.assets/image-20201212193920573.png)

```shell
PUT /bucket_worm HTTP/1.1
Host: 192.168.56.101:7480
Accept-Encoding: identity
x-amz-bucket-object-lock-enabled: True #注意此处
User-Agent: aws-cli/2.1.7 Python/3.7.4 Darwin/19.6.0 exe/x86_64 prompt/off command/s3api.create-bucket
X-Amz-Date: 20201212T113802Z
X-Amz-Content-SHA256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
Authorization: AWS4-HMAC-SHA256 Credential=8JTMWE51W8RBTCCE9RVP/20201212/us-east-1/s3/aws4_request, SignedHeaders=host;x-amz-bucket-object-lock-enabled;x-amz-content-sha256;x-amz-date, Signature=3d7fdd9aa87ec7daf805f228d552bae754bf48328312936e5646a7f2afdb79a6
Content-Length: 0

HTTP/1.1 200 OK
x-amz-request-id: tx000000000000000000035-005fd4ab9a-156cdb-default
Content-Length: 877
Date: Sat, 12 Dec 2020 11:38:02 GMT
Connection: Keep-Alive

{
    "bucket_info": {
        "bi_shard_hash_type": 0,
        "bucket": {
            "bucket_id": "a30132e6-53ae-4721-9511-ba773697d0f0.1404176.4",
            "explicit_placement": {
                "data_extra_pool": "",
                "data_pool": "",
                "index_pool": ""
            },
            "marker": "a30132e6-53ae-4721-9511-ba773697d0f0.1404176.4",
            "name": "bucket_worm",
            "tenant": ""
        },
        "creation_time": "2020-12-12 11:38:02.685928Z",
        "flags": 34,   #注意此处
        "has_instance_obj": "true",
        "has_website": "false",
        "index_type": 0,
        "mdsearch_config": [],
        "new_bucket_instance_id": "",
        "num_shards": 0,
        "owner": "rgw",
        "placement_rule": "default-placement",
        "quota": {
            "check_on_raw": false,
            "enabled": false,
            "max_objects": -1,
            "max_size": -1,
            "max_size_kb": 0
        },
        "requester_pays": "false",
        "reshard_status": 0,
        "swift_ver_location": "",
        "swift_versioning": "false",
        "zonegroup": "21413621-3e2e-4755-95e8-3e8134162fe5"
    },
    "entry_point_object_ver": {
        "tag": "_PZ-_aFVEDdr5LqqkCiQJwAa",
        "ver": 1
    },
    "object_ver": {
        "tag": "_FXVr8JvFnfaSdm-3H7aYfPR",
        "ver": 1
    }
}
```

注意上边的flag=34，查看代码可以发现flag的定义：

```c++
//rgw_common.h
enum RGWBucketFlags {
  BUCKET_SUSPENDED = 0x1,
  BUCKET_VERSIONED = 0x2,
  BUCKET_VERSIONS_SUSPENDED = 0x4,
  BUCKET_DATASYNC_DISABLED = 0X8,
  BUCKET_MFA_ENABLED = 0X10,
  BUCKET_OBJ_LOCK_ENABLED = 0X20,
};
```

可以确认该bucket具有`BUCKET_VERSIONED`与`BUCKET_OBJ_LOCK_ENABLED`两个属性。这也是S3文档中指出的，开启object-lock的桶都默认开启了versioning，同样检查桶的versioning状态可以看到这一点：

```shell
aws s3api --endpoint-url "$S3_HOST" --profile $PROFILE get-bucket-versioning --bucket "$1" 
```

返回结果：

![image-20201212195257309](.1.CSP%E8%B0%83%E7%A0%94%EF%BC%9AL2N%20WORM.assets/image-20201212195257309.png)

```shell
{
    "Status": "Enabled",
    "MFADelete": "Disabled"
}
```

在开启桶的object-lock时，是什么时候设置的该flag呢？是在execute的时候：

```c++
void RGWCreateBucket::execute(){
	...
  if (obj_lock_enabled) {
    info.flags = BUCKET_VERSIONED | BUCKET_OBJ_LOCK_ENABLED;
  }
  ...
}
```

#### 桶的对象锁设置put-object-lock-configuration

在开启桶的对象锁后，上传对象时仍不会有WORM功能，除非后期显式地对独立的对象设置。

检查当前的桶的属性：

```shell
GET /bucket_worm?object-lock HTTP/1.1
Host: 192.168.56.101:7480
Accept-Encoding: identity
User-Agent: aws-cli/2.1.7 Python/3.7.4 Darwin/19.6.0 exe/x86_64 prompt/off command/s3api.get-object-lock-configuration
X-Amz-Date: 20201212T123421Z
X-Amz-Content-SHA256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
Authorization: AWS4-HMAC-SHA256 Credential=8JTMWE51W8RBTCCE9RVP/20201212/us-east-1/s3/aws4_request, SignedHeaders=host;x-amz-content-sha256;x-amz-date, Signature=d47f8a6b82cf29a9d0ef85bcf768b94ec54d281fab4a374d069db347fb4a70f4

HTTP/1.1 200 OK
x-amz-request-id: tx000000000000000000038-005fd4b8cd-156cdb-default
Content-Type: application/xml
Content-Length: 135
Date: Sat, 12 Dec 2020 12:34:21 GMT
Connection: Keep-Alive

<?xml version="1.0" encoding="UTF-8"?><ObjectLockConfiguration><ObjectLockEnabled>Enabled</ObjectLockEnabled></ObjectLockConfiguration>
```

可以看到只有ObjectLockEnabled的属性为Enabled。表明该桶已开启对象锁功能，但没有默认WORM设置。

可以桶过如下命令设置DefaultRetention。

> 目前ceph只实现了DefaultRetention。

设置桶的默认WORM设置：

```shell
aws s3api --endpoint-url $S3_HOST --profile Nautilus \
    put-object-lock-configuration \
              --bucket bucket_object_lock \
              --object-lock-configuration '{ "ObjectLockEnabled": "Enabled", "Rule": { "DefaultRetention": { "Mode": "GOVERNANCE", "Days": 1 }}}'
```

目前`--object-lock-configuration`可以使用的属性如下所示，其中Days和Years在同一时刻只能使用一个。

```json
{
  "ObjectLockEnabled": "Enabled",
  "Rule": {
     "DefaultRetention": {
     "Mode": "GOVERNANCE"|"COMPLIANCE",
     "Days": integer,
     "Years": integer
     }
  }
}
```

抓包查看请求：

> RGWPutBucketObjectLock类没有实现了respond方法，但为什么都没有返回？不好。后续应该可以改进。\
>
> 【新增】：S3定义就是[这样](https://docs.aws.amazon.com/AmazonS3/latest/API/API_PutObjectLockConfiguration.html)

```shell
PUT /bucket_worm?object-lock HTTP/1.1
Host: 192.168.56.101:7480
Accept-Encoding: identity
Content-MD5: KX8zVPpu4gleE1JHJvOt6w==
User-Agent: aws-cli/2.1.7 Python/3.7.4 Darwin/19.6.0 exe/x86_64 prompt/off command/s3api.put-object-lock-configuration
X-Amz-Date: 20201212T124406Z
X-Amz-Content-SHA256: 5704e39d448968ac0cde311795eb61dc2a9e93627823324764a73e9d36521887
Authorization: AWS4-HMAC-SHA256 Credential=8JTMWE51W8RBTCCE9RVP/20201212/us-east-1/s3/aws4_request, SignedHeaders=content-md5;host;x-amz-content-sha256;x-amz-date, Signature=253406d302d4cbe664f9934c1a8b3502d6d636917cd29d92056080260dd9acae
Content-Length: 232

<ObjectLockConfiguration xmlns="http://s3.amazonaws.com/doc/2006-03-01/"><ObjectLockEnabled>Enabled</ObjectLockEnabled><Rule><DefaultRetention><Mode>GOVERNANCE</Mode><Days>1</Days></DefaultRetention></Rule></ObjectLockConfiguration>

#response:
HTTP/1.1 200 OK
x-amz-request-id: tx000000000000000000039-005fd4bb16-156cdb-default
Content-Length: 0
Date: Sat, 12 Dec 2020 12:44:06 GMT
Connection: Keep-Alive
```

put bucket object lock主要代码实现如下：

> 在代码中，该操作put-object-lock-configuration需要`rgw::IAM::s3PutBucketObjectLockConfiguration`权限。

```c++
void RGWPutBucketObjectLock::execute() {
  ...
  RGWXMLDecoder::decode_xml("ObjectLockConfiguration", obj_lock, &parser, true);//将头部过来的配置解析到obj_lock
  ...
  s->bucket_info.obj_lock = obj_lock;//将obj_lock挂到bucket_info中
}
```



#### 查看桶get-object-lock-configuration

> 遗留问题：是否可以新增Rule? 答：看代码只有DefaultRetention类，应该不可以。
>
> 看起来只有retention类型的默认设置，而没有governance的默认设置。

```shell
aws s3api --endpoint-url $S3_HOST --profile Nautilus get-object-lock-configuration --bucket bucket_worm

# Result:
{
    "ObjectLockConfiguration": {
        "ObjectLockEnabled": "Enabled",
        "Rule": {
            "DefaultRetention": {
                "Mode": "GOVERNANCE",
                "Days": 1
            }
        }
    }
}
```

抓包：

```shell
GET /bucket_worm?object-lock HTTP/1.1
Host: 192.168.56.101:7480
Accept-Encoding: identity
User-Agent: aws-cli/2.1.7 Python/3.7.4 Darwin/19.6.0 exe/x86_64 prompt/off command/s3api.get-object-lock-configuration
X-Amz-Date: 20201212T131401Z
X-Amz-Content-SHA256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
Authorization: AWS4-HMAC-SHA256 Credential=8JTMWE51W8RBTCCE9RVP/20201212/us-east-1/s3/aws4_request, SignedHeaders=host;x-amz-content-sha256;x-amz-date, Signature=24edb352e0afef39443789d5287eabc57a6d5ad0a2aaaf9146963563e23109f4

HTTP/1.1 200 OK
x-amz-request-id: tx00000000000000000003a-005fd4c219-156cdb-default
Content-Type: application/xml
Content-Length: 222
Date: Sat, 12 Dec 2020 13:14:01 GMT
Connection: Keep-Alive

<?xml version="1.0" encoding="UTF-8"?><ObjectLockConfiguration><ObjectLockEnabled>Enabled</ObjectLockEnabled><Rule><DefaultRetention><Mode>GOVERNANCE</Mode><Days>1</Days></DefaultRetention></Rule></ObjectLockConfiguration>
```

> 在代码中可以看到，该操作需要具有`rgw::IAM::s3GetBucketObjectLockConfiguration`权限。

在`RGWGetBucketObjectLock::execute()`只是进行容错，什么都没有做，主要逻辑在：

```c++
void RGWGetBucketObjectLock_ObjStore_S3::send_response(){
  ...
  encode_xml("ObjectLockConfiguration", s->bucket_info.obj_lock, s->formatter);
  ...
}
```

#### 对于一个已开启对象锁属性的桶，禁止关闭该桶的objectLock或挂起versioning状态

> Once you create a bucket with Object Lock enabled, you can't disable Object Lock or suspend versioning for the bucket.[参考](https://docs.aws.amazon.com/AmazonS3/latest/dev/object-lock-overview.html)

这是因为对象锁是基于versioning来实现的。

在代码中，对put-object-lock-configuration时，只实现了`ObjectLockEnabled=Enabled`的可选项，若非`Enabled`则在decode_xml时直接报错，并没有设置改值为false的选项：

```c++
void RGWObjectLock::decode_xml(XMLObj *obj) {
  string enabled_str;
  RGWXMLDecoder::decode_xml("ObjectLockEnabled", enabled_str, obj, true);
  if (enabled_str.compare("Enabled") != 0) {
    throw RGWXMLDecoder::err("invalid ObjectLockEnabled value");
  } else {
    enabled = true;
  }
  rule_exist = RGWXMLDecoder::decode_xml("Rule", rule, obj);
}
```

![image-20201212212928598](.1.CSP%E8%B0%83%E7%A0%94%EF%BC%9AL2N%20WORM.assets/image-20201212212928598.png)

`#define ERR_MALFORMED_XML        2029`

2） 若设置桶的状态为`Suspended`时，将会报错：

`An error occurred (InvalidBucketState) when calling the PutBucketVersioning operation: Unknown`

![image-20201212213623482](.1.CSP%E8%B0%83%E7%A0%94%EF%BC%9AL2N%20WORM.assets/image-20201212213623482.png)

`#define ERR_INVALID_BUCKET_STATE       2221`

代码是在这里限制的：

```c++
void RGWSetBucketVersioning::execute() {
  ...
    if (s->bucket_info.obj_lock_enabled() && versioning_status != VersioningEnabled) {
      op_ret = -ERR_INVALID_BUCKET_STATE;
      return;
    }
  ...
}
```

### 5.3.2 设置对象put-object-retention: GOVERNANCE

#### 简单上传一个对象，不带任何参数

```shell
aws s3api --endpoint-url "$S3_HOST" --profile $PROFILE put-object --bucket "$1" --key "$2" --body "$2"
{
    "ETag": "\"8e12c8bb45f220907e32fd42545c2220\"",
    "VersionId": "oAJQQFl2m.JBma0N2kw6CxEhW3L.vie"
}
```

抓包，可以看到返回了一个x-amz-version-id。

```shell
HTTP/1.1 100 CONTINUE

PUT /bucket_worm/object_worm HTTP/1.1
Host: 192.168.56.101:7480
Accept-Encoding: identity
User-Agent: aws-cli/2.1.7 Python/3.7.4 Darwin/19.6.0 exe/x86_64 prompt/off command/s3api.put-object
Content-MD5: jhLIu0XyIJB+Mv1CVFwiIA==
Expect: 100-continue
X-Amz-Date: 20201212T140130Z
X-Amz-Content-SHA256: 8dc0a5533f495505b83e04c4787bc3004b403e287048d5a6f6bfc11117a80498
Authorization: AWS4-HMAC-SHA256 Credential=8JTMWE51W8RBTCCE9RVP/20201212/us-east-1/s3/aws4_request, SignedHeaders=content-md5;host;x-amz-content-sha256;x-amz-date, Signature=e3f1d0f134c0cf85f719742a838cee12789aa601ad140ed5b73793bc526bd357
Content-Length: 12

object_worm
HTTP/1.1 200 OK
Content-Length: 0
ETag: "8e12c8bb45f220907e32fd42545c2220"
Accept-Ranges: bytes
x-amz-version-id: oAJQQFl2m.JBma0N2kw6CxEhW3L.vie
Rgwx-Mtime: 1607781690.678246843
x-amz-request-id: tx00000000000000000003e-005fd4cd3a-156cdb-default
Date: Sat, 12 Dec 2020 14:01:30 GMT
Connection: Keep-Alive
```

2）若在上传对象时指定对象锁相关属性，则略有不同

此时将在头中携带object-lock相关信息，将覆盖桶的默认设置，携带到对象的xattr中。

```shell
aws s3api --endpoint-url "$S3_HOST" --profile $PROFILE put-object --bucket "$1" --key "$2" --body "$2" \
					--object-lock-mode GOVERNANCE \
					--object-lock-retain-until-date 1607788800 \
					--object-lock-legal-hold-status OFF
```

返回结果：

```shell
{
    "ETag": "\"f9a8dafd776749dbef7c0bcf9fa083d4\"",
    "VersionId": "Uw9oEQzzcEqWRm9DTXHumbh0lrF2I7q"
}
```

抓包：

```shell
HTTP/1.1 100 CONTINUE

PUT /bucket_worm/object_worm_2 HTTP/1.1
Host: 192.168.56.101:7480
Accept-Encoding: identity
x-amz-object-lock-mode: GOVERNANCE 													#注意此处
x-amz-object-lock-retain-until-date: 2020-12-12T16:00:00Z   #注意此处
x-amz-object-lock-legal-hold: OFF														#注意此处
User-Agent: aws-cli/2.1.7 Python/3.7.4 Darwin/19.6.0 exe/x86_64 prompt/off command/s3api.put-object
Content-MD5: +aja/XdnSdvvfAvPn6CD1A==
Expect: 100-continue
X-Amz-Date: 20201212T142214Z
X-Amz-Content-SHA256: aeb4884a3888ae6a9b81dc4abeeda52cf9446a8a9698f3c34b196e242b26d7d0
Authorization: AWS4-HMAC-SHA256 Credential=8JTMWE51W8RBTCCE9RVP/20201212/us-east-1/s3/aws4_request, SignedHeaders=content-md5;host;x-amz-content-sha256;x-amz-date;x-amz-object-lock-legal-hold;x-amz-object-lock-mode;x-amz-object-lock-retain-until-date, Signature=cd9faec5ac9885c2d527a00ccb0b5b59a415527ae8aa20e74e32a51122a3c7d0
Content-Length: 120

this is object_worm_2 with user's worm settings when upload
this is object_worm_2 with user's worm settings when upload
HTTP/1.1 200 OK
Content-Length: 0
ETag: "f9a8dafd776749dbef7c0bcf9fa083d4"
Accept-Ranges: bytes
x-amz-version-id: Uw9oEQzzcEqWRm9DTXHumbh0lrF2I7q
Rgwx-Mtime: 1607782934.074731834
x-amz-request-id: tx000000000000000000040-005fd4d216-156cdb-default
Date: Sat, 12 Dec 2020 14:22:14 GMT
Connection: Keep-Alive
```

#### 确认属性设置get-object-retention

```shell
 aws s3api --endpoint-url "$S3_HOST" --profile $PROFILE get-object-retention --bucket "$1"  --key "$2"
```

得到结果：

```shell
{
    "Retention": {
        "Mode": "GOVERNANCE",
        "RetainUntilDate": "2020-12-13T14:01:30.678246+00:00"
    }
}
```

抓包：

```shell
GET /bucket_worm/object_worm?retention HTTP/1.1
Host: 192.168.56.101:7480
Accept-Encoding: identity
User-Agent: aws-cli/2.1.7 Python/3.7.4 Darwin/19.6.0 exe/x86_64 prompt/off command/s3api.get-object-retention
X-Amz-Date: 20201212T140912Z
X-Amz-Content-SHA256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
Authorization: AWS4-HMAC-SHA256 Credential=8JTMWE51W8RBTCCE9RVP/20201212/us-east-1/s3/aws4_request, SignedHeaders=host;x-amz-content-sha256;x-amz-date, Signature=52b3c5a7d5c0729d18e665285a6b1f31c959f056aad721e198798a386a8dc2e2

HTTP/1.1 200 OK
x-amz-request-id: tx00000000000000000003f-005fd4cf08-156cdb-default
Content-Type: application/xml
Content-Length: 149
Date: Sat, 12 Dec 2020 14:09:12 GMT
Connection: Keep-Alive

<?xml version="1.0" encoding="UTF-8"?><Retention><Mode>GOVERNANCE</Mode><RetainUntilDate>2020-12-13T14:01:30.678246843Z</RetainUntilDate></Retention>
```

日志中可以看到读取了object-retention：

![image-20201212221140023](.1.CSP%E8%B0%83%E7%A0%94%EF%BC%9AL2N%20WORM.assets/image-20201212221140023.png)

代码实现中，此时需要`rgw::IAM::s3GetObjectRetention`权限。

```c++
void RGWGetObjRetention::execute() {
  ...
  auto aiter = attrs.find(RGW_ATTR_OBJECT_RETENTION);
  ...
  obj_retention.decode(iter);
}
```

#### 在retention period中，普通用户无法删除对象

#### 在retention period结束后，普通用户可以删除对象

#### 在retention period中，普通用户无法修改对象retention属性

#### 在retention period中，普通用户或特权用户上传相同key的对象会生成一个新的对象version，而不会覆盖原有的对象

#### 在retention period中，有bypass-governance-retention权限可以删除对象

#### 在retention period中，有bypass-governance-retention权限可以修改retention属性

#### 在retention period中，有bypass-governance-retention权限修改了桶的DefaultRetention属性后不影响已有的对象的retention属性

### 5.3.3 设置对象put-object-retention: COMPLIANCE

#### 获得对象属性get-object-retention

#### 在retention period中，普通用户无法删除该对象

#### 在retention period结束后，普通用户无法删除该对象

#### 在retention period中，普通用户上传相同key的对象时生成一个新的对象version，而不会覆盖原有对象

#### 在retention period中，普通用户无法修改retention属性

#### 在retention period中，root用户也无法删除对象和修改retention属性

### 5.3.4 设置对象put-object-legal-hold

上传一个对象，并开启其legal hold功能：

```shell
aws s3api --endpoint-url "$S3_HOST" --profile $PROFILE put-object --bucket "$1" --key "$2" --body "$2" --object-lock-legal-hold-status ON

{
    "ETag": "\"6b4ec1c155b186348727f05e5d977bde\"",
    "VersionId": "EwbdDMGK4bfJckxZ8YlY9CGvAqhWOaS"
}
```

抓包：

```shell
HTTP/1.1 100 CONTINUE

PUT /bucket_worm/object_worm_3 HTTP/1.1
Host: 192.168.56.101:7480
Accept-Encoding: identity
x-amz-object-lock-legal-hold: ON  #注意此处
User-Agent: aws-cli/2.1.7 Python/3.7.4 Darwin/19.6.0 exe/x86_64 prompt/off command/s3api.put-object
Content-MD5: a07BwVWxhjSHJ/BeXZd73g==
Expect: 100-continue
X-Amz-Date: 20201213T033215Z
X-Amz-Content-SHA256: 0ec7007a0f14f6b4f7a5866833170467987b6f1a253e63531b4e02534b90cfe0
Authorization: AWS4-HMAC-SHA256 Credential=8JTMWE51W8RBTCCE9RVP/20201213/us-east-1/s3/aws4_request, SignedHeaders=content-md5;host;x-amz-content-sha256;x-amz-date;x-amz-object-lock-legal-hold, Signature=dc19418422d845dd92ea0da80d191ad95fa11c363a12724ae90d0492c260b1c9
Content-Length: 38

this is object_worm_3 with legal hold
HTTP/1.1 200 OK
Content-Length: 0
ETag: "6b4ec1c155b186348727f05e5d977bde"
Accept-Ranges: bytes
x-amz-version-id: EwbdDMGK4bfJckxZ8YlY9CGvAqhWOaS
Rgwx-Mtime: 1607830336.096497434
x-amz-request-id: tx000000000000000000041-005fd58b40-156cdb-default
Date: Sun, 13 Dec 2020 03:32:16 GMT
Connection: Keep-Alive
```

#### 确认对象属性get-object-legal-hold

```shell
{
    "LegalHold": {
        "Status": "ON"
    }
}
```

抓包：

```shell
GET /bucket_worm/object_worm_3?legal-hold HTTP/1.1
Host: 192.168.56.101:7480
Accept-Encoding: identity
User-Agent: aws-cli/2.1.7 Python/3.7.4 Darwin/19.6.0 exe/x86_64 prompt/off command/s3api.get-object-legal-hold
X-Amz-Date: 20201213T043938Z
X-Amz-Content-SHA256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
Authorization: AWS4-HMAC-SHA256 Credential=8JTMWE51W8RBTCCE9RVP/20201213/us-east-1/s3/aws4_request, SignedHeaders=host;x-amz-content-sha256;x-amz-date, Signature=60abed12fbb913656d4c3929032f864386126512c19893c3d04b38647a189bbf

HTTP/1.1 200 OK
x-amz-request-id: tx000000000000000000042-005fd59b0a-156cdb-default
Content-Type: application/xml
Content-Length: 80
Date: Sun, 13 Dec 2020 04:39:38 GMT
Connection: Keep-Alive

<?xml version="1.0" encoding="UTF-8"?><LegalHold><Status>ON</Status></LegalHold>
```

#### 在有legal-hold属性的情况下，用户无法删除该对象

```shell
#上传object_worm_4到一个开启object lock的桶(但未设置默认retention)，并开启legalHold
{
    "ETag": "\"1462e86edabc4fb624789f57abacaa04\"",
    "VersionId": "edtPWzun8hNEPeErz7eeQpqhibkhvRG"
}
```

此时若指定已经增加了LegalHold的对象版本来删除，则会报403错误：

```shell
#那么此时是否可以通过指定对象版本号来删除该对象版本呢？答案自然是不行的：
#delete_object_version_id bucket_worm_no_default object_worm_4 IjECcFOReGiwGSkJy5b8OdumdB1kdJE
An error occurred (AccessDenied) when calling the DeleteObject operation: Unknown
```

抓包：

```shell
DELETE /bucket_worm_no_default/object_worm_4?versionId=IjECcFOReGiwGSkJy5b8OdumdB1kdJE HTTP/1.1
Host: 192.168.56.101:7480
Accept-Encoding: identity
User-Agent: aws-cli/2.1.7 Python/3.7.4 Darwin/19.6.0 exe/x86_64 prompt/off command/s3api.delete-object
X-Amz-Date: 20201213T124835Z
X-Amz-Content-SHA256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
Authorization: AWS4-HMAC-SHA256 Credential=8JTMWE51W8RBTCCE9RVP/20201213/us-east-1/s3/aws4_request, SignedHeaders=host;x-amz-content-sha256;x-amz-date, Signature=b17d81fb6832d6a5247fb43d206709f7125f0419fb9611556bb0d746de982491
Content-Length: 0

HTTP/1.1 403 Forbidden
Content-Length: 236
x-amz-request-id: tx000000000000000000019-005fd60da3-171a8c-default
Accept-Ranges: bytes
Content-Type: application/xml
Date: Sun, 13 Dec 2020 12:48:35 GMT
Connection: Keep-Alive

<?xml version="1.0" encoding="UTF-8"?><Error><Code>AccessDenied</Code><BucketName>bucket_worm_no_default</BucketName><RequestId>tx000000000000000000019-005fd60da3-171a8c-default</RequestId><HostId>171a8c-default-default</HostId></Error>
```

![image-20201213205146836](.1.CSP%E8%B0%83%E7%A0%94%EF%BC%9AL2N%20WORM.assets/image-20201213205146836.png)

#### 在关闭legal hold属性后，用户可以删除该对象版本

```shell
#关闭该对象的legal-hold属性后，测试能否删除(注意此时需要指定version-id，否则报NoSuchKey)
aws s3api --endpoint-url "$S3_HOST" --profile $PROFILE put-object-legal-hold --bucket "$1" --key "$2"  --legal-hold Status=OFF --version-id IjECcFOReGiwGSkJy5b8OdumdB1kdJE
{
    "LegalHold": {
        "Status": "OFF"
    }
}
```

此时可以删除：

```shell
aws s3api --endpoint-url "$S3_HOST" --profile $PROFILE delete-object --bucket "$1" --key "$2"  --version-id $3
{
    "VersionId": "IjECcFOReGiwGSkJy5b8OdumdB1kdJE"
}
```

代码实现：

```c++
void RGWDeleteObj::execute() {
  ...
    aiter = attrs.find(RGW_ATTR_OBJECT_LEGAL_HOLD);
  if (aiter != attrs.end()) {
    RGWObjectLegalHold obj_legal_hold;
    try {
      decode(obj_legal_hold, aiter->second);
    } catch (buffer::error& err) {
      ldpp_dout(this, 0) << "ERROR: failed to decode RGWObjectLegalHold" << dendl;
      op_ret = -EIO;  
      return;
    }
    if (obj_legal_hold.is_enabled()) {
      op_ret = -EACCES;
      return;
    }
  }
  ...
}
```

#### 在有legal-hold属性的情况下，普通用户上传相同key的对象会生成新的version，而不会覆盖原有对象

```shell
#再次上传object_worm_4到一个该桶，并附带legalHold开启
{
    "ETag": "\"1462e86edabc4fb624789f57abacaa04\"",
    "VersionId": "IjECcFOReGiwGSkJy5b8OdumdB1kdJE"
}
```

#### 不指定版本号删除对象，将生成一个delete marker而不是真正地删除对象

此时仍旧可以通过version-id来获得该对象，但不能只通过key来获得：

```shell
#不指定版本号删除object_worm_4，将在原有的version序列上生成一个delete marker，并生成一个新的versionID。
{
    "DeleteMarker": true,
    "VersionId": "hKPOBqVGkk-GuFwmQSmtRdW9SruNGSO"
}
#指定版本号 IjECcFOReGiwGSkJy5b8OdumdB1kdJE 来get object_worm_4，可以获取到，表明未被删除。

#list-object-versions可以看到当前的version状态，之前上传的两个version的对象object_worm_4，此时的IsLatest都为false，意味着只能通过指定key和version-id的方式获得，若只是指定key则无法获得：
{
    "Versions": [
        {
            "ETag": "\"1462e86edabc4fb624789f57abacaa04\"",
            "Size": 76,
            "StorageClass": "STANDARD",
            "Key": "object_worm_4",
            "VersionId": "IjECcFOReGiwGSkJy5b8OdumdB1kdJE",
            "IsLatest": false,
            "LastModified": "2020-12-13T12:38:44.620000+00:00",
            "Owner": {
                "DisplayName": "rgw",
                "ID": "rgw"
            }
        },
        {
            "ETag": "\"1462e86edabc4fb624789f57abacaa04\"",
            "Size": 76,
            "StorageClass": "STANDARD",
            "Key": "object_worm_4",
            "VersionId": "edtPWzun8hNEPeErz7eeQpqhibkhvRG",
            "IsLatest": false,
            "LastModified": "2020-12-13T12:33:18.533000+00:00",
            "Owner": {
                "DisplayName": "rgw",
                "ID": "rgw"
            }
        }
    ],
    "DeleteMarkers": [
        {
            "Owner": {
                "DisplayName": "rgw",
                "ID": "rgw"
            },
            "Key": "object_worm_4",
            "VersionId": "hKPOBqVGkk-GuFwmQSmtRdW9SruNGSO",
            "IsLatest": true,
            "LastModified": "2020-12-13T12:41:37.639000+00:00"
        }
    ]
}

#此时不指定版本号get object_worm_4，将返回NoSuchKey错误:
An error occurred (NoSuchKey) when calling the GetObject operation: Unknown

#同时可以注意到此处的该对象版本的ObjectLockLegalHoldStatus为ON，表明该对象的LegalHold属性为开启的状态：
{
    "AcceptRanges": "bytes",
    "LastModified": "2020-12-13T12:38:44+00:00",
    "ContentLength": 76,
    "ETag": "\"1462e86edabc4fb624789f57abacaa04\"",
    "VersionId": "IjECcFOReGiwGSkJy5b8OdumdB1kdJE",
    "ContentType": "binary/octet-stream",
    "Metadata": {},
    "ObjectLockLegalHoldStatus": "ON"
}
```

#### 在有legal-hold属性的情况下，普通用户无法修改该对象版本的legal hold属性

#### 在有legal-hold属性的情况下，有s3:PutObjectLegalHold权限的用户可以修改该对象版本的legal hold属性

## 5.4 社区N版worm相关代码提交：

rgw: add S3 object lock feature to support object worm #26538 [https://github.com/ceph/ceph/pull/26538](https://link.zhihu.com/?target=https%3A//github.com/ceph/ceph/pull/26538)

- PUT/GET bucket object lock
- PUT/GET object retention
- PUT/GET object legal hold

## 5.5 社区N版对象锁数据结构

而ObjectLock和BucketWORM的数据结构如下所示：

```c++
//默认Retention设置，包括mode:COMPLIANCE/GOVERNANCE，保留时长（以天数为单位或以年数为单位）。
class DefaultRetention {
protected:
  string mode;
  int days;
  int years;

public:
  DefaultRetention(): days(0), years(0) {};//默认保留天数为0
  ...
}

//rgw对象锁数据结构
class RGWObjectLock {
protected:
  bool enabled; //是否开启
  bool rule_exist; //rule是否存在。当设置ObjectLockRule后设置为true，默认为false
  ObjectLockRule rule;

public:
  RGWObjectLock():enabled(true), rule_exist(false) {}//默认对象锁开启，默认未设置rule
  ...
}

class ObjectLockRule {
protected:
  DefaultRetention defaultRetention;//此处的rule只有这一个
public:
  int get_days() const {
    return defaultRetention.get_days();
  }

  int get_years() const {
    return defaultRetention.get_years();
  }

  string get_mode() const {
    return defaultRetention.get_mode();
  }
  ...
}

class RGWObjectRetention {
protected:
  string mode;
  ceph::real_time retain_until_date;
public:
  RGWObjectRetention() {}
  RGWObjectRetention(string _mode, ceph::real_time _date): mode(_mode), retain_until_date(_date) {}
  ...
}

class RGWObjectLegalHold {
protected:
  string status;
public:
  RGWObjectLegalHold() {}
  RGWObjectLegalHold(string _status): status(_status) {}
  ...
}
```

# 附录

1. git log --oneline | grep WORM 看对应哪些改动
2. AWS S3 WORM特性： http://tapd.oa.com/SealStorage/markdown_wikis/show/#1220360132000448625
3. https://github.com/ceph/ceph/pull/26538
4. aws 官方文档：https://amazonaws-china.com/cn/blogs/storage/protecting-data-with-amazon-s3-object-lock/
5. aws官方文档：S3 Object Lock overview: https://docs.aws.amazon.com/AmazonS3/latest/dev/object-lock-overview.html
6. 社区N版第一次提交：https://github.com/ceph/ceph/pull/26538/commits
7. ceph代码中encode以及decode: https://docs.ceph.com/en/latest//dev/encoding/
8. ceph shard，背景、动态bucket分片、: https://www.jianshu.com/p/583d880b8a15?open_source=weibo_search
9. ceph multisite data sync: datalog: https://www.jianshu.com/p/6290e9102960
10. rgw::IAM::s3GetObject等，bucket policy的实现：https://blog.csdn.net/yujia_666/article/details/108331761

# 脚本参考

```shell
#!/bin/bash

function create_bucket(){
    aws s3api --endpoint-url "$S3_HOST" --profile $PROFILE create-bucket --bucket "$1"
}

function create_bucket_with_object_lock(){
    aws s3api --endpoint-url "$S3_HOST" --profile $PROFILE create-bucket --bucket "$1" --object-lock-enabled-for-bucket
}
function list_objects(){
    aws s3api --endpoint-url "$S3_HOST" --profile $PROFILE list-objects --bucket "$1"
}

function delete_bucket(){
    aws s3api --endpoint-url "$S3_HOST" --profile $PROFILE delete-bucket --bucket "$1"
}

function delete_object(){
    aws s3api --endpoint-url "$S3_HOST" --profile $PROFILE delete-object --bucket "$1" --key "$2"
}

function delete_object_version_id(){
    aws s3api --endpoint-url "$S3_HOST" --profile $PROFILE delete-object --bucket "$1" --key "$2"  --version-id $3
}

function put_object(){
    aws s3api --endpoint-url "$S3_HOST" --profile $PROFILE put-object --bucket "$1" --key "$2" --body "$2"
}

function put_object_object_lock_legal_hold(){
    #aws s3api --endpoint-url "$S3_HOST" --profile $PROFILE put-object --bucket "$1" --key "$2" --body "$2" --object-lock-mode GOVERNANCE --object-lock-retain-until-date 1607788800 --object-lock-legal-hold-status OFF
    aws s3api --endpoint-url "$S3_HOST" --profile $PROFILE put-object --bucket "$1" --key "$2" --body "$2" --object-lock-legal-hold-status $3
}

function get_object(){
    aws s3api --endpoint-url "$S3_HOST" --profile $PROFILE get-object --bucket "$1" --key "$2" "download_$2" 
}

function get_object_version_id(){
    aws s3api --endpoint-url "$S3_HOST" --profile $PROFILE get-object --bucket "$1" --key "$2" "download_$2" --version-id $3
}

function head_object(){
    aws s3api --endpoint-url "$S3_HOST" --profile $PROFILE head-object --bucket "$1" --key "$2"
}

function list_object_versions(){
    aws s3api --endpoint-url "$S3_HOST" --profile $PROFILE list-object-versions --bucket "$1" 
}

function get_bucket_versioning(){
    aws s3api --endpoint-url "$S3_HOST" --profile $PROFILE get-bucket-versioning --bucket "$1" 
}

function put_bucket_versioning(){
    aws s3api --endpoint-url "$S3_HOST" --profile $PROFILE put-bucket-versioning --bucket "$1" --versioning-configuration Status=Suspended
}

function get_object_lock_configuration(){
    aws s3api --endpoint-url "$S3_HOST" --profile $PROFILE get-object-lock-configuration --bucket "$1"
}

function put_object_lock_configuration(){
    aws s3api --endpoint-url "$S3_HOST" --profile $PROFILE put-object-lock-configuration --bucket "$1" \
    --object-lock-configuration '{ "ObjectLockEnabled": "", "Rule": { "DefaultRetention": { "Mode": "GOVERNANCE", "Days": 1 }}}'
    #--object-lock-configuration '{ "ObjectLockEnabled": "Enabled", "Rule": { "DefaultRetention": { "Mode": "GOVERNANCE", "Days": 1 }}}'
}

function get_object_retention(){
    aws s3api --endpoint-url "$S3_HOST" --profile $PROFILE get-object-retention --bucket "$1"  --key "$2"
}

function put_object_retention(){
    aws s3api --endpoint-url "$S3_HOST" --profile $PROFILE  put-object-retention --bucket "$1" --key "$2"
}

function get_object_legal_hold(){
    aws s3api --endpoint-url "$S3_HOST" --profile $PROFILE get-object-legal-hold --bucket "$1"  --key "$2"
}
function get_object_legal_hold_version_id(){
    aws s3api --endpoint-url "$S3_HOST" --profile $PROFILE get-object-legal-hold --bucket "$1"  --key "$2" --version-id $3
}

function put_object_legal_hold_status_version_id(){
    aws s3api --endpoint-url "$S3_HOST" --profile $PROFILE put-object-legal-hold --bucket "$1" --key "$2"  --legal-hold Status=$3 --version-id $4
}

#put_object bucket0 object0
#copy_object bucket0 object0 bucket1

#create_bucket_with_object_lock bucket_worm
#get_bucket_versioning bucket_worm
#delete_bucket bucket_worm
#list_objects bucket_worm
#get_object_lock_configuration bucket_worm
#put_object_lock_configuration bucket_worm
#put_bucket_versioning bucket_worm
#touch object_worm 
#echo "object_worm" >> object_worm
#put_object bucket_worm object_worm
#get_object_retention bucket_worm object_worm
#touch object_worm_2
#echo "this is object_worm_2 with user's worm settings when upload" >> object_worm_2
#put_object_object_lock bucket_worm object_worm_2
#touch object_worm_3
#echo "this is object_worm_3 with legal hold" >> object_worm_3
#put_object_object_lock bucket_worm object_worm_3
#get_object_legal_hold bucket_worm object_worm_3

#touch object_worm_4
#echo "this is object_worm_4 with legal hold" >> object_worm_4
#put_object_object_lock bucket_worm object_worm_4
#delete_object bucket_worm object_worm_4
#get_object bucket_worm object_worm_4

#put_object_legal_hold bucket_worm object_worm_4
#get_object_legal_hold bucket_worm object_worm_4

#create_bucket_with_object_lock bucket_worm_no_default
#get_object_lock_configuration bucket_worm_no_default

#put_object_object_lock_legal_hold bucket_worm_no_default object_worm_4 ON
#delete_object_version_id bucket_worm_no_default object_worm_4 XfCHXWHsjaAW9TkGoSgSxqMmiok9arf
#delete_object_version_id bucket_worm_no_default object_worm_4 IjECcFOReGiwGSkJy5b8OdumdB1kdJE
#delete_object bucket_worm_no_default object_worm_4
#list_objects bucket_worm_no_default
#list_object_versions bucket_worm_no_default

#get_object_version_id bucket_worm_no_default object_worm_4 IjECcFOReGiwGSkJy5b8OdumdB1kdJE
#delete_object_version_id bucket_worm_no_default object_worm_4 IjECcFOReGiwGSkJy5b8OdumdB1kdJE

#put_object_legal_hold_status_version_id bucket_worm_no_default object_worm_4 OFF IjECcFOReGiwGSkJy5b8OdumdB1kdJE 
#get_object_legal_hold_version_id bucket_worm_no_default object_worm_4 IjECcFOReGiwGSkJy5b8OdumdB1kdJE
#delete_object_version_id bucket_worm_no_default object_worm_4 IjECcFOReGiwGSkJy5b8OdumdB1kdJE
#get_object bucket_worm_no_default object_worm_4 37PExmQIs64aCmkkqu0ds49Y1c81fwK
#delete_object  bucket_object_lock object0_worm_overwrite_bucket_conf
#head_object bucket_object_lock object0_worm_overwrite_bucket_conf --version-id  WI3q0Adue5SkHU1FU0E1K03rI60aOhY
#delete_bucket bucket_object_lock 
#get_object_lock_configuration bucket_object_lock 
```

