## ListBucket源码分析

包含unordered和ordered的两种方式。

[rgw: ability to list bucket contents in unsorted order for efficiency](https://github.com/sinjoywong/ceph/commit/6da5a5888c8605497cddc83b73cee1528d1b4b44)





rgw_list_bucket_min_readahead=1000,默认list的数目。



list_objects

```c++
process_request
RGWREST::get_handler
  |--> RGWHandler_REST_S3::init
RGWHandler_REST_S3::authorize
  |--> rgw::auth::Strategy::apply
  |--> rgw::auth::Strategy::authenticate
    |--> //walk auth_stack to get engine
    |--> engine.authenticate(dpp,s);
		//rgw::auth::AnonymousEngine
		//rgw::auth::s3::LocalEngine
    	|--> rgw::auth::s3::AWSEngine::authenticate
        	|--> rgw::auth::s3::LocalEngine::authenticate
  |--> case result_t::Status::GRANTED:
	|--> strategy_handle_granted
  |--> rgw::auth::Strategy::apply //applier = rgw::auth::IdentityApplier
  |--> s->perm_mask = applier->get_perm_mask();
  |--> applier->modify_request_state(dpp, s);
            
rgw_process_authenticated
  |--> RGWHandler_REST::init_permissions
    |--> RGWHandler::do_init_permissions
    |--> rgw_build_bucket_policies
  ...
  |--> RGWListBucket::verify_permission
    |--> RGWListBucket_ObjStore_S3::get_params
    |--> RGWListBucket_ObjStore_S3::get_common_params
    |--> verify_bucket_permission
    |--> verify_bucket_permission
      |--> eval_user_policies(user_policies, s->env, boost::none, op, ARN(bucket));
      |--> eval_or_pass(bucket_policy, s->env, *s->auth.identity, op, ARN(bucket));
      //此处可以看出来，bucket_acl通过后便不再验证user_acl。
      |--> verify_bucket_permission_no_policy(dpp, s, user_acl, bucket_acl, perm);
        |-->if(!bucket_acl) return false;
        |--> if((perm & (int)s->perm_mask) != perm) return false;
        |--> if (bucket_acl->verify_permission(dpp, *s->auth.identity, perm, perm,
                                    s->info.env->get("HTTP_REFERER"))) return true;
        |--> return user_acl->verify_permission(dpp, *s->auth.identity, perm, perm);
  ...
  |-->RGWListBucket::execute    
    |--> RGWRados::Bucket::List::list_objects
    |--> RGWRados::Bucket::List::list_objects_ordered 
    |--> RGWRados::cls_bucket_list_ordered
      |--> RGWRados::open_bucket_index //获得oids
      |--> RGWRados::open_bucket_index_base //get bucket_oid_base
      
    |--> CLSRGWConcurrentIO::operator
    |--> CLSRGWIssueBucketList::issue_op
    |--> issue_bucket_list_op
    |--> librados::ObjectOperation::exec
    |--> call
    |--> add_call
    |--> ObjectOperation::add_op
	|--> 
```



看下 radosgw-admin -c  $(ls /data/cos/ceph.*.conf | head -1)  bucket stats --bucket cosbench1

