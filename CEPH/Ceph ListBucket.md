## ListBucket源码分析

list_objects

```c++
process_request
RGWOp::verify_requester
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


RGWRados::Bucket::List::list_objects_ordered 
RGWRados::cls_bucket_list_ordered
CLSRGWConcurrentIO::operator
CLSRGWIssueBucketList::issue_op
issue_bucket_list_op
librados::ObjectOperation::exec
call
add_call
ObjectOperation::add_op
	--> 
```



看下 radosgw-admin -c  $(ls /data/cos/ceph.*.conf | head -1)  bucket stats --bucket cosbench1

