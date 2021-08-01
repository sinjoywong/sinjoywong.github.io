/var/run/ceph/

https://zhuanlan.zhihu.com/p/110079635

admin_socket的创建：https://blog.csdn.net/littleflower_song/article/details/50477115

## 问题收集

1. ceph daemon 是如何工作的？
2. admin_socket的创建时机
3. admin_socket的创建方法



```c++
//src/common/options.cc
Option("run_dir", Option::TYPE_STR, Option::LEVEL_ADVANCED)
    .set_default("/var/run/ceph")
    .set_description("path for the 'run' directory for storing pid and socket files")
    .add_service("common")
    .add_see_also("admin_socket"),

Option("admin_socket", Option::TYPE_STR, Option::LEVEL_ADVANCED)
  .set_default("")
  .set_daemon_default("$run_dir/$cluster-$name.asok")
  .set_description("path for the runtime control socket file, used by the 'ceph daemon' command")
  .add_service("common"),

Option("admin_socket_mode", Option::TYPE_STR, Option::LEVEL_ADVANCED)
  .set_description("file mode to set for the admin socket file, e.g, '0755'")
  .add_service("common")
  .add_see_also("admin_socket"),


/src/common/common_init.cc
CephContext *common_preinit(const CephInitParameters &iparams,
			    enum code_environment_t code_env, int flags)
{
  ...
  if ((flags & CINIT_FLAG_UNPRIVILEGED_DAEMON_DEFAULTS)) {
   // make this unique despite multiple instances by the same name.
   conf.set_val_default("admin_socket",
			  "$run_dir/$cluster-$name.$pid.$cctid.asok");
  }
  ...
}
```



Ambari:

```shell
#ceph.conf.j2
[client]
{% if 'CIFS' in cos_component or 'NFS' in cos_component %}
# only CIFS and NFS
admin_socket = /var/run/ceph/$cluster-$name.$pid.asok
{% endif %}
```



删除时机：

在setup_osd.sh.j2中，可以看到在部署osd的时候会尝试删除，以清理环境：

```shell
# cleanup some files in case of garbage from previous installation
rm -rf /var/run/ceph/ceph.{{cos_component}}-osd.*.asok || true
rm -rf /var/run/ceph/ceph.{{cos_component}}-osd.*.pid || true
```

