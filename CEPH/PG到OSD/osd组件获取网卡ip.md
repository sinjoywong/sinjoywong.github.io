

1. Messanger是什么？
2. osd 的ip和端口是如何指定的？

```shell
"back_addr": "10.19.0.167:6813/260058",
"back_addr": "10.19.0.167:6809/251359",
```





\1. 打开debug_ms=2，发现创建存储桶时超时的osd_op与osd_op_reply时间超过10s的请求现象如下（举例说明）：

```shell
2021-07-02 16:31:43.803002 7f8320041700 1 [tx000000000000000000085-0060deceef-c13d2-default] -- 172.17.65.89:0/3367017120 --> 10.87.65.100:6815/27957 -- osd_op(unknown.0.0:14100 5.2b3 5:cd54e34a:::.dir.6eddafad-0b63-42a8-90d9-93c17425ffbb.791506.4.7:head [create,call rgw.bucket_init_index] snapc 0=[] ondisk+write+known_if_redirected e46566) v8 -- 0x55ef6f478b00 con 0

2021-07-02 16:31:57.243643 7f836b0d7700 1 [] -- 172.17.65.89:0/3367017120 <== osd.72 10.87.65.100:6815/27957 23 ==== osd_op_reply(14100 .dir.6eddafad-0b63-42a8-90d9-93c17425ffbb.791506.4.7 [create,call] v46566'155 uv155 ondisk = 0) v8 ==== 238+0+0 (2825413023 0 0) 0x55ef71f9b080 con 0x55ef6f906000
```

可以看到172.17.65.89发起，接收端却是10.87.65.100。

在部署该套集群的时候网络环境比较复杂，每台机器对外使用EIP暴露（例如10.87.x.x），内部集群访问使用网卡IP（例如172.17.x.x）

通过osd dump可以看到部分osd使用的是EIP，而非网卡IP：

```shell
osd.9 up in weight 1 up_from 45812 up_thru 46565 down_at 45796 last_clean_interval [45794,45799) 10.87.193.72:6821/465070 10.87.193.72:6830/465070 10.87.193.72:6832/465070 10.87.193.72:6833/465070 exists,up ecc0ad38-5af7-4ff0-9ef6-4f05360821f1
```

从172.17.65.89指定length去ping 10.87.65.100,发现length大于128就会丢包。

可以看出原因是部分OSD获取ip时错误地获取了EIP，而非网卡IP。



处理方法：

1. 登录Ambari后端
2. 在datastor中配置

```shell
public_network=172.17.0.0/16
cluster_network=172.17.0.0/16
```

3. 在Ambari中逐个重启节点组件
4. ceph osd dump中确认该节点中osd的ip都为172.17.x.x，而非10.87.x.x。

该操作会在ceph.conf中添加上述两行网络配置，osd进程启动时将会直接使用该ip，从而不会错误地获取EIP。



## osd ip设置

### osd启动

ceph_osd.cc

```shell
pick_addresses
	
```









```c++
int main(int argc, const char **argv) {
  ...
    r = pick_addresses(g_ceph_context, CEPH_PICK_ADDRESS_CLUSTER, &cluster_addrs,
                       iface_preferred_numa_node)

    if (ms_cluster->bindv(cluster_addrs) < 0)
    forker.exit(1);
  
  entity_addrvec_t hb_back_addrs = cluster_addrs;
  for (auto& a : hb_back_addrs.v) {
    a.set_port(0);
  }
  if (ms_hb_back_server->bindv(hb_back_addrs) < 0)
    forker.exit(1);
  if (ms_hb_back_client->client_bind(hb_back_addrs.front()) < 0)
    forker.exit(1);
    ...
  
   osd = new OSD(g_ceph_context,
                store,
                whoami,
                ms_cluster,
                ms_public,
                ms_hb_front_client,
                ms_hb_back_client,
                ms_hb_front_server,
                ms_hb_back_server,
                ms_objecter,
                &mc,
                data_path,
                journal_path);
  
  
```



## osd metadata示例

`ceph osd metadata osd.1`:

```shell
[root@10 ~]# ceph osd metadata osd.1
{
    "id": 1,
    "arch": "x86_64",
    "back_addr": "10.19.0.44:6849/3538928",
    "back_iface": "bond1",
    "backend_filestore_dev_node": "nvme0n1",
    "backend_filestore_partition_path": "/dev/nvme0n1p2",
    "ceph_version": "ceph version 12.2.12-700.2.6.2.1615723753 (df767d4013ccf042afc37e750c8298cc3f4a53a5) luminous (stable)",
    "cpu": "Intel(R) Xeon(R) Platinum 8255C CPU @ 2.50GHz",
    "default_device_class": "ssd",
    "distro": "tlinux",
    "distro_description": "Tencent tlinux 2.2 (Final)",
    "distro_version": "2.2",
    "filestore_backend": "xfs",
    "filestore_f_type": "0x58465342",
    "front_addr": "10.19.0.44:6800/2538928",
    "front_iface": "bond1",
    "hb_back_addr": "10.19.0.44:6850/3538928",
    "hb_front_addr": "10.19.0.44:6851/3538928",
    "hostname": "10.19.0.44",
    "journal_rotational": "0",
    "kernel_description": "#1 SMP Wed Jan 15 20:02:40 CST 2020",
    "kernel_version": "3.10.107-1-tlinux2-0052",
    "mem_swap_kb": "2104508",
    "mem_total_kb": "790383472",
    "os": "Linux",
    "osd_data": "/data/cos/osd/osd.DATASTOR_SSD_A",
    "osd_journal": "/data/cos/osd/osd.DATASTOR_SSD_A/journal",
    "osd_objectstore": "filestore",
    "rotational": "0"
}
```

