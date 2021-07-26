





```shell
rgw_process_authenticated
RGWGetObj::execute
RGWRados::Object::Read::prepare
	|--> int r = source->get_state(&astate, true); #获取attr
	|--> RGWRados::get_obj_stat
	|--> RGWRados::get_obj_state_impl
	|--> RGWObjectCtx::get_state
```

