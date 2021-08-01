# radosgw-admin bucket list与list-bucket

在处理问题《租户端无法获取bucket列表》时，使用radosgw-admin bucket list测试是否可以获取到bukcet列表来测试是否可用，但是实际上这和从前端使用list-buckets的原理不同。

前者是直接在pool中查找，

而后者是通过ak/sk来获得username，然后在omap中查找的。

因此需要梳理一下相关代码流程，以加深对ceph的理解。



## radosgw-admin bucket list代码流程

```c++
//ceph, rgw_admin.cc
int main(int argc, const char ** argv) {
 ...
 
   if (opt_cmd == OPT_BUCKETS_LIST) {
     if (bucket_name.empty()) {
       RGWBucketAdminOp::info(store, bucket_op, f);
     } else {
       RGWBucketInfo bucket_info;
       int ret = init_bucket(tenant, bucket_name, bucket_id, bucket_info, bucket);
       if (ret < 0) {
         cerr << "ERROR: could not init bucket: " << cpp_strerror(-ret) << std::endl;
         return -ret;
       }
       formatter->open_array_section("entries");
       bool truncated;
       int count = 0;
       if (max_entries < 0)
         max_entries = 1000;

       string prefix;
       string delim;
       vector<rgw_bucket_dir_entry> result;
       map<string, bool> common_prefixes;
       string ns;

       RGWRados::Bucket target(store, bucket_info);
       RGWRados::Bucket::List list_op(&target);

       list_op.params.prefix = prefix;
       list_op.params.delim = delim;
       list_op.params.marker = rgw_obj_key(marker);
       list_op.params.ns = ns;
       list_op.params.enforce_ns = false;
       list_op.params.list_versions = true;

       do {
         ret = list_op.list_objects(max_entries - count, &result, &common_prefixes, &truncated);
         if (ret < 0) {
           cerr << "ERROR: store->list_objects(): " << cpp_strerror(-ret) << std::endl;
           return -ret;
         }

         count += result.size();

         for (vector<rgw_bucket_dir_entry>::iterator iter = result.begin(); iter != result.end(); ++iter) {
           rgw_bucket_dir_entry& entry = *iter;
           encode_json("entry", entry, formatter);
         }
         formatter->flush(cout);
       } while (truncated && count < max_entries);

       formatter->close_section();
       formatter->flush(cout);
     } /* have bucket_name */
   } /* OPT_BUCKETS_LIST */
 ...
}
```



```c++
int RGWRados::cls_bucket_list_ordered(RGWBucketInfo& bucket_info,
				      int shard_id,
				      rgw_obj_index_key& start,
				      const string& prefix,
				      uint32_t num_entries,
				      bool list_versions,
				      map<string, rgw_bucket_dir_entry>& m,
				      bool *is_truncated,
				      rgw_obj_index_key *last_entry,
				      bool (*force_check_filter)(const string& name))
```



## list-bucket代码流程

```c++
//ceph, cls_user.cc
//这里的cls是一个通用的模块，可以自主注册函数使用，此处注册了list_buckets：
cls_register_cxx_method(h_class, "list_buckets", CLS_METHOD_RD, cls_user_list_buckets, &h_user_list_buckets);

//ceph, cls_user.cc
static int cls_user_list_buckets(cls_method_context_t hctx, bufferlist *in, bufferlist *out)
{
  bufferlist::iterator in_iter = in->begin();

  cls_user_list_buckets_op op;
  try {
    ::decode(op, in_iter);
  } catch (buffer::error& err) {
    CLS_LOG(1, "ERROR: cls_user_list_op(): failed to decode op");
    return -EINVAL;
  }

  map<string, bufferlist> keys;

  const string& from_index = op.marker;
  const string& to_index = op.end_marker;
  const bool to_index_valid = !to_index.empty();

#define MAX_ENTRIES 1000
  size_t max_entries = op.max_entries;
  if (max_entries > MAX_ENTRIES)
    max_entries = MAX_ENTRIES;

  string match_prefix;
  cls_user_list_buckets_ret ret;

  int rc = cls_cxx_map_get_vals(hctx, from_index, match_prefix, max_entries, &keys, &ret.truncated);
  if (rc < 0)
    return rc;

  CLS_LOG(20, "from_index=%s to_index=%s match_prefix=%s",
          from_index.c_str(),
          to_index.c_str(),
          match_prefix.c_str());

  list<cls_user_bucket_entry>& entries = ret.entries;
  map<string, bufferlist>::iterator iter = keys.begin();

  string marker;

  for (; iter != keys.end(); ++iter) {
    const string& index = iter->first;
    marker = index;

    if (to_index_valid && to_index.compare(index) <= 0) {
      ret.truncated = false;
      break;
    }

    bufferlist& bl = iter->second;
    bufferlist::iterator biter = bl.begin();
    try {
      cls_user_bucket_entry e;
      ::decode(e, biter);
      entries.push_back(e);
    } catch (buffer::error& err) {
      CLS_LOG(0, "ERROR: cls_user_list: could not decode entry, index=%s", index.c_str());
    }
  }

  if (ret.truncated) {
    ret.marker = marker;
  }

  ::encode(ret, *out);

  return 0;
}


//ceph, rgw_op.h
class RGWListBuckets : public RGWOp {
  ...
  const string name() override { return "list_buckets"; }
  RGWOpType get_type() override { return RGW_OP_LIST_BUCKETS; 
  ...
}
```

