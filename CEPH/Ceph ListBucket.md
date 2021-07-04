## ListBucket源码分析





```shell

list_objects
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

