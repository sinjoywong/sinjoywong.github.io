```javascript
ceph-authtool /etc/ceph/ceph.client.radosgw.keyring -n client.rgw.node03 --gen-key

ceph-authtool -n client.rgw.node03 --cap osd 'allow rwx' --cap mon 'allow rwx' /etc/ceph/ceph.client.radosgw.keyring

ceph -k /etc/ceph/ceph.client.admin.keyring auth add client.rgw.node03 -i /etc/ceph/ceph.client.radosgw.keyring

cat >> /etc/ceph/ceph.conf << EOF
[client.rgw.node03]
host=node03
keyring=/etc/ceph/ceph.client.radosgw.keyring
log file=/var/log/radosgw/client.radosgw.gateway.log
rgw_frontends = civetweb port=8080
EOF


mkdir /var/log/radosgw
chown ceph:ceph /var/log/radosgw

```

添加OSD时：ceph-volume lvm batch: error: GPT headers found, they must be removed on: /dev/sdb

```shell
DISK=/dev/sdb
sgdisk --zap-all $DISK
重启
```



删除集群：

cephadm rm-cluster --fsid=xxx --force

部署：

https://www.cnblogs.com/zjz20/p/14136349.html



ssh-copy-id -f -i /etc/ceph/ceph.pub node02

ssh-copy-id -f -i /etc/ceph/ceph.pub node03



ceph orch host add node02

ceph orch host add node03

ceph orch device ls

ceph orch apply osd --all-available-devices



可能只有在HEALTH的情况下才能安装成功：

```
ceph orch apply rgw myorg chongqing --placement="1 node01"

```

ceph orch ls

无法按照apply rgw的方法：https://bugzilla.redhat.com/show_bug.cgi?id=1858884





开启日志：

ceph config set global log_to_file true

cd /run/ceph/6206b502-bd26-11eb-9a8d-080027ae43bf/

ceph --admin-daemon ceph-client.rgw.myorg.chongqing.node01.yuhlpu.1.94894851806392.asok config set debug_rgw 20