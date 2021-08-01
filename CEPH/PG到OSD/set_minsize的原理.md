## 问题提出

1. min_size影响哪些操作？
2. min_size是如何影响操作的？
3. list bucket是否不需要判断min_size？
4. osd_pool_default_min_size的作用是什么e？https://blog.csdn.net/a1454927420/article/details/98080139
5. 

代码相关：

```c++
pool->min_size
pool.info.min_size

```





## ListBuckets是如何工作的

```shell
BUCKET AND OBJECT LISTING
Buckets that belong to a given user are listed in an omap of an object named “<user_id>.buckets” (for example, “foo.buckets”) in pool “default.rgw.meta” with namespace “users.uid”. These objects are accessed when listing buckets, when updating bucket contents, and updating and retrieving bucket statistics (e.g. for quota).

See the user-visible, encoded class ‘cls_user_bucket_entry’ and its nested class ‘cls_user_bucket’ for the values of these omap entires.

These listings are kept consistent with buckets in pool “.rgw”.

Objects that belong to a given bucket are listed in a bucket index, as discussed in sub-section ‘Bucket Index’ above. The default naming for index objects is “.dir.<marker>” in pool “default.rgw.buckets.index”.

https://docs.ceph.com/en/latest/radosgw/layout/
```



bt:

```shell
#0  librados::ObjectOperation::exec (this=this@entry=0x7ff5829a5b10, cls=cls@entry=0x7ff5b5b0fe69 "user", 
    method=method@entry=0x7ff5b5aeda80 "list_buckets", inbl=..., completion=<optimized out>)
    at /data/sherlocwang/L_Dawa/Dawa/src/librados/librados.cc:223
#1  0x00007ff5b598099c in cls_user_bucket_list (op=..., in_marker="", end_marker="", max_entries=max_entries@entry=1000, 
    entries=empty std::list, out_marker=out_marker@entry=0x7ff5829a5cc0, truncated=truncated@entry=0x7ff5829a5ca5, 
    pret=pret@entry=0x7ff5829a5b0c) at /data/sherlocwang/L_Dawa/Dawa/src/cls/user/cls_user_client.cc:89

out_marker=out_marker@entry=0x7ff57f19ecc0, truncated=truncated@entry=0x7ff57f19eca5, pret=pret@entry=0x7ff57f19eb0c)
    at /data/sherlocwang/L_Dawa/Dawa/src/cls/user/cls_user_client.cc:87
#1  0x00007ff5b5709526 in RGWRados::cls_user_list_buckets (this=this@entry=0x7ff5b879a000, obj=..., in_marker="", end_marker="", 
    max_entries=max_entries@entry=1000, entries=empty std::list, out_marker=out_marker@entry=0x7ff57f19ecc0, 
    truncated=truncated@entry=0x7ff57f19eca5) at /data/sherlocwang/L_Dawa/Dawa/src/rgw/rgw_rados.cc:14088
#2  0x00007ff5b55cff1a in rgw_read_user_buckets (store=0x7ff5b879a000, user_id=..., buckets=..., marker="", end_marker="", 
    max=max@entry=1000, need_stats=false, is_truncated=is_truncated@entry=0x7ff5b8637ee0, default_amount=default_amount@entry=1000)
    at /data/sherlocwang/L_Dawa/Dawa/src/rgw/rgw_bucket.cc:126
#3  0x00007ff5b569b784 in RGWListBuckets::execute (this=0x7ff5b8637e00) at /data/sherlocwang/L_Dawa/Dawa/src/rgw/rgw_op.cc:2267
#4  0x00007ff5b56dbdd2 in rgw_process_authenticated (handler=handler@entry=0x7ff5b8b705e0, op=@0x7ff57f19f3d8: 0x7ff5b8637e00, 
    req=req@entry=0x7ff57f19ff90, s=s@entry=0x7ff57f19f7c0, skip_retarget=skip_retarget@entry=false)
    at /data/sherlocwang/L_Dawa/Dawa/src/rgw/rgw_process.cc:104
#5  0x00007ff5b56dd07e in process_request (store=0x7ff5b879a000, rest=0x7ffd2bfdb720, req=req@entry=0x7ff57f19ff90, frontend_prefix="",
    auth_registry=..., client_io=client_io@entry=0x7ff57f19ffc0, olog=0x0, http_ret=http_ret@entry=0x7ff57f19ff8c)
    at /data/sherlocwang/L_Dawa/Dawa/src/rgw/rgw_process.cc:265
#6  0x00007ff5b5539e35 in RGWCivetWebFrontend::process (this=0x7ff5b892a320, conn=<optimized out>)
    at /data/sherlocwang/L_Dawa/Dawa/src/rgw/rgw_civetweb_frontend.cc:38
#7  0x00007ff5b55ac54f in handle_request (conn=conn@entry=0x7ff5b8a44000) at /data/sherlocwang/L_Dawa/Dawa/src/civetweb/src/civetweb.c:9890
#8  0x00007ff5b55adedb in process_new_connection (conn=<optimized out>) at /data/sherlocwang/L_Dawa/Dawa/src/civetweb/src/civetweb.c:12328
#9  worker_thread_run (thread_func_param=0x7ff5b880a800) at /data/sherlocwang/L_Dawa/Dawa/src/civetweb/src/civetweb.c:12505
#10 worker_thread (thread_func_param=0x7ff5b880a800) at /data/sherlocwang/L_Dawa/Dawa/src/civetweb/src/civetweb.c:12542
```

## rgw到osd/PG

从上面的stack中可以看到，list bucket最终到达了对应最终代码：

```c++
//src/cls/cls_user_client.cc
void cls_user_bucket_list(librados::ObjectReadOperation& op,
                          const string& in_marker,
                          const string& end_marker,
                          int max_entries,
                          list<cls_user_bucket_entry>& entries,
                          string *out_marker,
                          bool *truncated,
                          int *pret)
{
  bufferlist inbl;
  cls_user_list_buckets_op call;
  call.marker = in_marker;
  call.end_marker = end_marker;
  call.max_entries = max_entries;

  encode(call, inbl);

  op.exec("user", "list_buckets", inbl, new ClsUserListCtx(&entries, out_marker, truncated, pret));
}
```

此处很奇怪，不太好看到是走到哪里。实际上是类似于cls模块注册了一些回调函数：

```c++
//src/cls/user/cls_user.cc

CLS_INIT(user)
{
  CLS_LOG(1, "Loaded user class!");
   cls_register_cxx_method(h_class, "list_buckets", CLS_METHOD_RD, cls_user_list_buckets, &h_user_list_buckets);
}
```

其中`cls_user_list_buckets`为方法名称，`h_user_list_buckets`为一个void型指针，作为返回值传递。

即上述方法实际调用了：

```c++
//src/cls/user/cls_user.cc
//in为输入值，out为&truncated
static int cls_user_list_buckets(cls_method_context_t hctx, bufferlist *in, bufferlist *out){
  auto in_iter = in->cbegin();
  cls_user_list_buckets_op op;
  try {
    decode(op, in_iter); //从输入中decode得到op
  } catch (buffer::error& err) {
    CLS_LOG(1, "ERROR: cls_user_list_op(): failed to decode op");
    return -EINVAL;
  }

  map<string, bufferlist> keys;

  const string& from_index = op.marker;
  const string& to_index = op.end_marker;
  const bool to_index_valid = !to_index.empty();
  ...
  string match_prefix;
  cls_user_list_buckets_ret ret;
  //结果输出为keys，即为所得结果。详见下文：
  int rc = cls_cxx_map_get_vals(hctx, from_index, match_prefix, max_entries, &keys, &ret.truncated);
  CLS_LOG(20, "from_index=%s to_index=%s match_prefix=%s",
          from_index.c_str(),
          to_index.c_str(),
          match_prefix.c_str());

  list<cls_user_bucket_entry>& entries = ret.entries;
  map<string, bufferlist>::iterator iter = keys.begin();

  string marker;
	//遍历keys，逐个decode，放到entries中
  /*
  返回值的数据结构如下：
  struct cls_user_list_buckets_ret {
  	list<cls_user_bucket_entry> entries;
  	string marker;
  	bool truncated
  */
  for (; iter != keys.end(); ++iter) {
    const string& index = iter->first;
    marker = index;

    if (to_index_valid && to_index.compare(index) <= 0) {
      ret.truncated = false;
      break;
    }

    bufferlist& bl = iter->second;
    auto biter = bl.cbegin();
    try {
      cls_user_bucket_entry e;
      decode(e, biter);
      entries.push_back(e);
    } catch (buffer::error& err) {
      CLS_LOG(0, "ERROR: cls_user_list: could not decode entry, index=%s", index.c_str());
    }
  }

  if (ret.truncated) {
    ret.marker = marker;
  }

  encode(ret, *out);

  return 0;
}
```

其中`cls_cxx_map_get_vals`：

```c++
//src/objclass/class_api.cc
int cls_cxx_map_get_vals(cls_method_context_t hctx, const string &start_obj,
			 const string &filter_prefix, uint64_t max_to_get,
			 map<string, bufferlist> *vals, bool *more)
{
  PrimaryLogPG::OpContext **pctx = (PrimaryLogPG::OpContext **)hctx;
  vector<OSDOp> ops(1);
  OSDOp& op = ops[0];
  int ret;

  encode(start_obj, op.indata);
  encode(max_to_get, op.indata);
  encode(filter_prefix, op.indata);
	//设置osd op为“获取omap”：
  op.op.op = CEPH_OSD_OP_OMAPGETVALS;
  
  //进入osd的处理流程,详见下文：
  ret = (*pctx)->pg->do_osd_ops(*pctx, ops);
  if (ret < 0)
    return ret;

  auto iter = op.outdata.cbegin();
  try {
    decode(*vals, iter);
    decode(*more, iter);
  } catch (buffer::error& err) {
    return -EIO;
  }
  return vals->size();
}
```

`do_osd_ops`则进入了osd的处理流程：

> 疑问：此处如何到达判断PG active状态的？

```c++
//src/osd/PrimaryLogPG.cc
int PrimaryLogPG::do_osd_ops(OpContext *ctx, vector<OSDOp>& ops)
{
  int result = 0;
  SnapSetContext *ssc = ctx->obc->ssc;
  ObjectState& obs = ctx->new_obs;
  object_info_t& oi = obs.oi;
  const hobject_t& soid = oi.soid;
  ...

  PGTransaction* t = ctx->op_t.get();
  dout(10) << "do_osd_op " << soid << " " << ops << dendl;
  ctx->current_osd_subop_num = 0;
  for (auto p = ops.begin(); p != ops.end(); ++p, ctx->current_osd_subop_num++, ctx->processed_subop_count++) {
    OSDOp& osd_op = *p;
    ceph_osd_op& op = osd_op.op;

    ...
    switch (op.op) {
    ...
      case CEPH_OSD_OP_OMAPGETVALS:
        ++ctx->num_read;
        {
          string start_after;
          uint64_t max_return;
          string filter_prefix;
          try {
            decode(start_after, bp);
            decode(max_return, bp);
            decode(filter_prefix, bp);
          }
          catch (buffer::error& e) {
            result = -EINVAL;
            tracepoint(osd, do_osd_op_pre_omapgetvals, soid.oid.name.c_str(), soid.snap.val, "???", 0, "???");
            goto fail;
          }
          if (max_return > cct->_conf->osd_max_omap_entries_per_request) {
            max_return = cct->_conf->osd_max_omap_entries_per_request;
          }
          tracepoint(osd, do_osd_op_pre_omapgetvals, soid.oid.name.c_str(), soid.snap.val, start_after.c_str(), max_return, filter_prefix.c_str());

          uint32_t num = 0;
          bool truncated = false;
          bufferlist bl;
         //此处的 object_info_t& oi = obs.oi;
         //ObjectState& obs = ctx->new_obs
         // ObjectState new_obs;  // resulting ObjectState
         // ctx为OpContext指针  
          if (oi.is_omap()) {
            ObjectMap::ObjectMapIterator iter = osd->store->get_omap_iterator(
              ch, ghobject_t(soid)
            );
            if (!iter) {
              result = -ENOENT;
              goto fail;
            }
            iter->upper_bound(start_after);
            if (filter_prefix > start_after) iter->lower_bound(filter_prefix);
            for (num = 0;
                 iter->valid() &&
                 iter->key().substr(0, filter_prefix.size()) == filter_prefix;
                 ++num, iter->next()) {
              dout(20) << "Found key " << iter->key() << dendl;
              if (num >= max_return ||
                  bl.length() >= cct->_conf->osd_max_omap_bytes_per_request) {
                truncated = true;
                break;
              }
              encode(iter->key(), bl);
              encode(iter->value(), bl);
            }
          } // else return empty out_set
          encode(num, osd_op.outdata);
          osd_op.outdata.claim_append(bl);
          encode(truncated, osd_op.outdata);
          ctx->delta_stats.num_rd_kb += shift_round_up(osd_op.outdata.length(), 10);
          ctx->delta_stats.num_rd++;
        }
        break;
        ...
    }
  }
```

## 页面显示

运营端存储桶管理中，决定存储桶是否可用：

```shell
#General
Request URL: http://192.168.56.200:8089/api/bucket/
Request Method: GET
Status Code: 502 Bad Gateway
Remote Address: 192.168.56.200:8089
Referrer Policy: strict-origin-when-cross-origin

#Response Headers
Connection: keep-alive
Content-Length: 289
Content-Type: application/json; charset=utf-8
Date: Wed, 12 May 2021 08:41:51 GMT
ETag: W/"121-gCJO0r3NshAfQp3pGUGvL53VY/0"
Server: nginx/1.16.1
set-cookie: csp-session-id=s%3AmQrFxDdjbXJXtDaNHaiVljTbGeSmnh3w.Kj8K8BJ9uusP%2BfDM4d%2BAm4E7mUsA25dxfVuoWNZRyCE; Path=/; Expires=Wed, 12 May 2021 10:41:51 GMT; HttpOnly
Vary: Origin, Accept-Encoding
X-Powered-By: Express

#Request Headers
Accept: application/json, text/plain, */*
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9,en;q=0.8
Connection: keep-alive
Cookie: csp-session-id=s%3AmQrFxDdjbXJXtDaNHaiVljTbGeSmnh3w.Kj8K8BJ9uusP%2BfDM4d%2BAm4E7mUsA25dxfVuoWNZRyCE
Host: 192.168.56.200:8089
Referer: http://192.168.56.200:8089/object-storage/bucket
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36
```

response具体解析：

```shell
message: "Data Access unavailable at 80"
stack: "Error: \n    at new c (/data/csp-ins/2.8.1.780/csp-console/server/app.js:1:65553)\n    at V.get (/data/csp-ins/2.8.1.780/csp-console/server/app.js:1:61648)\n    at process._tickCallback (internal/process/next_tick.js:68:7)"
status: 502
```

## ceph的min_size如何决定是否可用：

Ceph中，每个pool可以设置size以及min_size，他们默认分别是3和2（当然可以在配置文件里配置这两个属性的默认值，也可以在pool创建后通过ceph的命令更改pool的size以及min_size属性）。

size是该pool的副本数，也即数据有size个副本；min_size是指当集群出现故障时，PG至少还有min_size副本正常时，可以服务io。

那么min_size是怎么控制io是否能服务的呢? min_size控制io是否能服务主要是如下两步:

## 1. 根据min_size设置PG的状态

PG在peering状态结束后，也即在PG::RecoveryState::Active::react(const AllReplicasActivated &evt)函数中，会进行判断，如果该PG对应的正常状态的OSD数量大于等于min_size,设置该PG为PG_STATE_ACTIVE状态，否则设置为PG_STATE_PEERED状态。设置代码如下:

```text
if (pg->acting.size() >= pg->pool.info.min_size) {
    pg->state_set(PG_STATE_ACTIVE);
} else {
    pg->state_set(PG_STATE_PEERED);
}
```

## 2. 根据PG状态判断是否能服务io

当有io服务落到这个PG时，这个时候ReplicatedPG::do_request函数会进行响应，然后在该函数里会判断PG的状态:若该PG的状态是active，则能服务io;否则若该PG的状态是PEERED,而不是active，则不会继续服务io，而是把该io丢到waiting_for_active队列后就返回了，等之后PG状态变成active了，再从该队列中拿出该io，进行重发。具体代码如下:

```c++
void PrimaryLogPG::do_request(
  OpRequestRef& op,
  ThreadPool::TPHandle &handle)
{
...
switch (msg_type) {
  case CEPH_MSG_OSD_OP:
  case CEPH_MSG_OSD_BACKOFF:
    if (!is_active()) {
      dout(20) << " peered, not active, waiting for active on " << op << dendl;
      waiting_for_active.push_back(op);
      op->mark_delayed("waiting for active");
      return;
    }
```

---

## PG的Op以及状态判断

```c++
void PGOpItem::run(
  OSD *osd,
  OSDShard *sdata,
  PGRef& pg,
  ThreadPool::TPHandle &handle)
{
  osd->dequeue_op(pg, op, handle);
  pg->unlock();
}

--> pg->do_request(op, handle);
--> void PrimaryLogPG::do_request(
  OpRequestRef& op,
  ThreadPool::TPHandle &handle)
{
  ...
  switch (msg_type) {
  case CEPH_MSG_OSD_OP:
  case CEPH_MSG_OSD_BACKOFF:
    if (!is_active()) {
      dout(20) << " peered, not active, waiting for active on " << op << dendl;
      waiting_for_active.push_back(op);
      op->mark_delayed("waiting for active");
      return;
    }
  ...
  }
}
-->   bool is_active() const { return state_test(PG_STATE_ACTIVE); }

```

## 重试机制

1. 保存位置
2. 保存时机
3. 取出时机
4. 重试时机

```c++

waiting_for_active中
```

