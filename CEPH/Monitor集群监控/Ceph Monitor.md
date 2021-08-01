## 涉及知识

1. Monitor管理了什么？
2. Monitor之间如何通信？
3. Monitor要正常运行需要满足哪些条件？
4. OSDMap机制：与Monitor的关系https://www.xsky.com/tec/186/

## Monitor基本概念

Mon的作用：负责监控整个集群，维护集群的健康状态，维护展示集群状态的各种图表，如OSD Map、Monitor Map、PG Map和CRUSH Map、采集系统的日志。

Paxos：分布式一致性算法，算出一个主节点。通过mon节点的端口号和ip来计算主节点一般选取端口号小的为主如果端口号一样的情况那就选择ip地址小的为主节点。主要负责维护和传播集群表的权威副本，paxos要求集群中超过半数monitor处于活跃状态才能正常工作，以解决分布式系统常见的脑裂问题。

为了防止一些临时性故障造成短时间内出现大量的集群表更新和传播，对集群的稳定性和性能造成影响，ceph将集群表的更新操作进行了串行化处理，即任何时刻只允许某个特定的monitor统一发起集群表更新，一段时间内的更新会被合并为一个请求提交，这个特殊的monitor称为leader，其他的monitor称为peon.

leader通过选票产生，一旦某个monitor赢得超过半数的选票成为leader，leader通过续租的方式延长作为leader的租期(3秒更新租约，6秒超时)，一旦集群中有任何的成员发生变化，整个集群就会重新触发leader选举。

Monitor 为ceph集群启动的第一个服务组件，如果第一个节点创建时monitor服务没有正常运行，后续的osd和其他和ceph集群相关的服务将不能正常创建，Monitor使用public网络进行对外提供服务，如果public网络异常将导致无法访问集群

注意：集群中monitor的数量部署为奇数个一般部署三个，如果要增加就一次性增加俩个，mon必须存活一般以上比如三个mon只允许down一个5个只允许down2个这样以此类推不然会出问题。

## 正常运行的条件

一般来说，在实际运行中，ceph monitor的个数是2n+1(n>=0)个，在线上至少3个，只要正常的节点数>=n+1，ceph的paxos算法能保证系统的正常运行。所以，对于3个节点，同时只能挂掉一个。一般来说，同时挂掉2个节点的概率比较小，但是万一挂掉2个呢？

如果ceph的monitor节点超过半数挂掉，paxos算法就无法正常进行仲裁(quorum)，此时，ceph集群会阻塞对集群的操作，直到超过半数的monitor节点恢复。

所以，

（1）如果挂掉的2个节点至少有一个可以恢复，也就是monitor的元数据还是OK的，那么只需要重启ceph-mon进程即可。所以，对于monitor，最好运行在RAID的机器上。这样，即使机器出现故障，恢复也比较容易。

（2）如果挂掉的2个节点的元数据都损坏了呢？出现这种情况，说明人品不行，2台机器的RAID磁盘同时损坏，这得多背？肯定是管理员嫌工资太低，把机器砸了。如何恢复呢？

其实，也没有其它办法，只能想办法将故障的节点恢复，但元数据已经损坏。幸好还有一个元数据正常的节点，通过它可以恢复。

## 常用命令

```shell
#Mon进程:
root@192 sherloc]# ps aux | grep ceph-mon
root        3616  0.2  7.9 494248 80808 ?        Ssl  02:44   0:48 ceph-mon -i 192.168.56.101-CLUSTERMON_A -c /data/cos/ceph.CLUSTERMON_A.conf --mon_data /data/cos/mon/mon.CLUSTERMON_A

# 查看quorum状态:
[root:192]# ceph -c /data/cos/ceph.DATAACCESS.conf quorum_status

{"election_epoch":140,"quorum":[0,1,2],"quorum_names":["192.168.56.101-CLUSTERMON_A","192.168.56.102-CLUSTERMON_B","192.168.56.103-CLUSTERMON_C"],"quorum_leader_name":"192.168.56.101-CLUSTERMON_A","monmap":{"epoch":3,"fsid":"30e60b11-162d-4b7f-b310-6b0e8bd4b8e9","modified":"2020-09-27 23:15:39.712847","created":"2020-09-27 23:11:00.503800","features":{"persistent":["kraken","luminous"],"optional":[]},"mons":[{"rank":0,"name":"192.168.56.101-CLUSTERMON_A","addr":"192.168.56.101:6789/0","public_addr":"192.168.56.101:6789/0"},{"rank":1,"name":"192.168.56.102-CLUSTERMON_B","addr":"192.168.56.102:6790/0","public_addr":"192.168.56.102:6790/0"},{"rank":2,"name":"192.168.56.103-CLUSTERMON_C","addr":"192.168.56.103:6791/0","public_addr":"192.168.56.103:6791/0"}]}}

#过滤出leader mon:
[root:192]# ceph -c $CEPH_CONF quorum_status -f json-pretty | grep "leader"

"quorum_leader_name": "192.168.56.101-CLUSTERMON_A",

# 查看mon的map 
[root:192]# ceph mon -c /data/cos/ceph.DATAACCESS.conf dump

dumped monmap epoch 3
epoch 3
fsid 30e60b11-162d-4b7f-b310-6b0e8bd4b8e9
last_changed 2020-09-27 23:15:39.712847
created 2020-09-27 23:11:00.503800
0: 192.168.56.101:6789/0 mon.192.168.56.101-CLUSTERMON_A
1: 192.168.56.102:6790/0 mon.192.168.56.102-CLUSTERMON_B
2: 192.168.56.103:6791/0 mon.192.168.56.103-CLUSTERMON_C

# 查看mon的状态 
[root:192]# ceph mon -c /data/cos/ceph.DATAACCESS.conf stat

e3: 3 mons at {192.168.56.101-CLUSTERMON_A=192.168.56.101:6789/0,192.168.56.102-CLUSTERMON_B=192.168.56.102:6790/0,192.168.56.103-CLUSTERMON_C=192.168.56.103:6791/0}, election epoch 140, leader 0 192.168.56.101-CLUSTERMON_A, quorum 0,1,2 192.168.56.101-CLUSTERMON_A,192.168.56.102-CLUSTERMON_B,192.168.56.103-CLUSTERMON_C
```

---

## Mon因盘满自杀

mon_data_avail_crit
mon_data_avail_warn

### 启动时判断

在monitor的main函数，启动时判断磁盘使用状态，若已经超过mon_data_avail_crit，则不启动。

```c++
//ceph_mon.cc, main
  {
    // check fs stats. don't start if it's critically close to full.
    ceph_data_stats_t stats;
    int err = get_fs_stats(stats, g_conf->mon_data.c_str());
    if (err < 0) {
      derr << "error checking monitor data's fs stats: " << cpp_strerror(err)
           << dendl;
      exit(-err);
    }
    if (stats.avail_percent <= g_conf->mon_data_avail_crit) {
      derr << "error: monitor data filesystem reached concerning levels of"
           << " available storage space (available: "
           << stats.avail_percent << "% " << byte_u_t(stats.byte_avail)
           << ")\nyou may adjust 'mon data avail crit' to a lower value"
           << " to make this go away (default: " << g_conf->mon_data_avail_crit
           << "%)\n" << dendl;
      exit(ENOSPC);
    }
  }
```

### 定期向monitor汇报状态时判断

```c++
void DataHealthService::get_health(
    list<pair<health_status_t,string> >& summary,
    list<pair<health_status_t,string> > *detail){
  	...
    health_status_t health_status = HEALTH_OK;
    string health_detail;
    if (stats.fs_stats.avail_percent <= g_conf->mon_data_avail_crit) {
      health_status = HEALTH_ERR;
      health_detail = "low disk space, shutdown imminent";
    } else if (stats.fs_stats.avail_percent <= g_conf->mon_data_avail_warn) {
      health_status = HEALTH_WARN;
      health_detail = "low disk space";
    }
  
}
```





```c++
//DatahealthService.cc
void DataHealthService::service_tick(){
  ...
  DataStats &ours = stats[mon->messenger->get_myinst()];

  if (ours.fs_stats.avail_percent <= g_conf->mon_data_avail_crit) {
    derr << "reached critical levels of available space on local monitor storage"
         << " -- shutdown!" << dendl;
    force_shutdown();
    return;
  }
}

void force_shutdown() {
    generic_dout(0) << "** Shutdown via Data Health Service **" << dendl;
    queue_async_signal(SIGINT);
}
```



### 配置设置

该值可以再ceph.conf中设置：

```c++
    Option("mon_data_avail_crit", Option::TYPE_INT, Option::LEVEL_ADVANCED)
    .set_default(5)
    .set_description(""),

    Option("mon_data_avail_warn", Option::TYPE_INT, Option::LEVEL_ADVANCED)
    .set_default(30)
    .set_description(""),
```



## 参考

1. ceph heartbeat分析，osd心跳分析： https://zhuanlan.zhihu.com/p/128631881
2. ceph osdmap 机制浅析：https://cloud.tencent.com/developer/article/1664568
3. Monitor, cluster maps, 一致性，bootstrapping monitors，配置，paxos：https://access.redhat.com/documentation/en-us/red_hat_ceph_storage/1.3/html/configuration_guide/monitor_configuration_reference



