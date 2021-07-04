# ceph数据分布与PG均衡

[TOC]

>  还有另一个问题哈，这个地方，是在调 OSD reweight 吗？刚建好集群都没数据，为啥要调呢，应该是写入一段时间数据，发现各 OSD 的 PG 不均衡，才需要调吧？

## 涉及知识

1. Ceph [CRUSH算法](http://www.ssrc.ucsc.edu/Papers/weil-sc06.pdf)与配置工具crushtool

2. weight是什么？reweight是什么？与osd的pg_num有什么关系？与osd所在磁盘的容量有什么关系？如何决定PG和OSD之间的映射关系？

3. crush计算规则是什么？入参应该不只是pg_id，还有weight、reweight等，否则无法数据均衡

4. 如何定义PG分布是否均衡？

5. 如何通过ambari来触发相应脚本，来执行offline_rebalance? [DONE]

6. offline_rebalance干了些啥？调整的是weight还是reweight? 为什么要这么干？

7. 知道一个bucket_name和object_key，是如何知道在哪个pg_id，osd，osd中的哪个offset的，长度是多少的？

8. pg与pgp的联系与区别？为什么还要设计一个pgp?

   

《ceph源码分析》 p9, p10, 

[ceph osd weight与ceph osd crush reweight的区别](https://ceph.io/geen-categorie/difference-between-ceph-osd-reweight-and-ceph-osd-crush-reweight/)

[建议pg_num的计算](https://ceph.com/pgcalc/)

```shell
$ ceph osd tree

ID  CLASS WEIGHT    TYPE  NAME                        STATUS REWEIGHT PRI-AFF 
-6        125.51343 root  00000000-fast                                                           
-5        125.51343       datacenter 00000000-fast-datacenter.yfm4-v6-iaas                         
-12       41.84602         rack 00000000-fast-rack.M201-F01                                     
-11       41.84602            host 00000000-fast-10.19.0.15 
0    ssd  3.52898               osd.0                   up  1.00000 1.00000 
5    ssd  3.37804               osd.5                   up  1.00000 1.00000 
7    ssd  3.45203               osd.7                   up  1.00000 1.00000 
...
```

以上述为例， WEIGHT表示权重，只有磁盘的容量有关。一般1TB为1.000， 500GB就是0.5，不因磁盘的可用空间减少而变化。该值可以通过以下命令设置：

```shell
ceph osd crush reweight osd.0 5
```

而REWEIGHT是一个0到1的值，可以用以下命令设置：

```shell
ceph osd reweight 0 0.8
```

当REWEIGHT改变时，WEIGHT的值不发生变化。

REWEIGHT的值影响PG到OSD的映射关系。由于CRUSH算法随机分配是概率统计意义上的数据均衡，当小规模集群PG数目相对较少时，会产生一些不均匀的情况。通过调整reweight参数，用于达到数据均衡。

这个参数不会持久化。当osd out时，REWEIGHT的值变为0，当该osd重新up时，该值就会恢复到1，而不会保留之前修改过的值。

```shell
[root@10 /data/sher]# /usr/bin/crushtool --test --show-utilization \
   -i crushmap_in \
   --num-rep 3 \
   --rule 7 \
   --x 512 \
   --pool-id 0
   
rule 7 (cos_rep_00000000-fast_host), x = 0..511, numrep = 3..3
rule 7 (cos_rep_00000000-fast_host) num_rep 3 result size == 3: 512/512
  device 0:   stored : 41     expected : 42.6667      affected_expected : 42.6667
  device 1:   stored : 59     expected : 42.6667      affected_expected : 42.6667
  device 2:   stored : 43     expected : 42.6667      affected_expected : 42.6667
  device 3:   stored : 32     expected : 42.6667      affected_expected : 42.6667
  device 4:   stored : 34     expected : 42.6667      affected_expected : 42.6667
  device 5:   stored : 44     expected : 42.6667      affected_expected : 42.6667
  device 6:   stored : 48     expected : 42.6667      affected_expected : 42.6667
  device 7:   stored : 36     expected : 42.6667      affected_expected : 42.6667
  device 8:   stored : 42     expected : 42.6667      affected_expected : 42.6667
  device 9:   stored : 41     expected : 42.6667      affected_expected : 42.6667
  device 10:  stored : 32     expected : 42.6667      affected_expected : 42.6667
  device 11:  stored : 41     expected : 42.6667      affected_expected : 42.6667
...
```

~~--这里的stored表示该device保存PG的数量，expected表示预期的pg数目。

这里的stored, expected, affected_expected表示的是对象，而不是PG。

> 错误：pg_num应该是2的n次方吧，

> https://docs.ceph.com/en/mimic/man/8/crushtool/
>
> `--show-utilization```
>
> Displays the expected and actual utilisation for each device, for each number of replicas. For instance:
>
> ```
> device 0: stored : 951      expected : 853.333
> device 1: stored : 963      expected : 853.333
> ...
> ```
>
> shows that device **0** stored **951** values and was expected to store **853**. Implies **–show-statistics**.

```shell
crushtool -i mapfn --reweight-item name weight
                         reweight a given item (and adjust ancestor
                         weights as needed)
```

## 代码实现

Erwa中：ambari-server/src/main/resources/common-services/COS/1.0.0/package/scripts/mon.py

```python
def offline_rebalance(self, env):
        import params
        env.set_params(params)
        if params.cos_dss_type in ('bs',):
            raise Fail('Not Implemented')
        elif params.cos_dss_type == 'os':
            cos_op_pool = params.cos_op_dss_prefix + "default.rgw.buckets.data"
        elif params.cos_dss_type == 'fs':
            cos_op_pool = params.cos_op_dss_prefix + "fs.data"
        cos_input_crush_map = os.path.join(params.tmp_dir,
            'input_crush_map.{0}'.format(params.cos_component))
        cos_output_crush_map = os.path.join(params.tmp_dir,
            'output_crush_map.{0}'.format(params.cos_component))
        rebalance_functions.check_pg_health(params.cos_mon_conf)
        rebalance_functions.offline_rebalance(params.cos_mon_conf,
                                              cos_input_crush_map,
                                              cos_output_crush_map,
                                              cos_op_pool,
                                              1.001)
```



```python
def offline_rebalance(conf_path, input_path, output_path,
                      pool_name, expected_overload=1.01):
    download_crush_map(conf_path, input_path)
    pool_id, rep_num, crush_rule, pg_num = get_pool_info(conf_path,
                                                         pool_name)
    pgs_per_osd, expected_pgs = simulate_pg_distribution([pool_id],
                                                         [pg_num],
                                                         rep_num,
                                                         crush_rule,
                                                         input_path)
    asc_pgs_per_osd = sorted(pgs_per_osd.iteritems(), key=lambda t: t[1])
    cur_max_diff = max(abs(asc_pgs_per_osd[0][1]- expected_pgs),
                       abs(asc_pgs_per_osd[-1][1] - expected_pgs))
    last_max_diff = sys.maxint
    while cur_max_diff * 1.0 / expected_pgs > expected_overload - 1:
        weights_per_osd = get_osd_weight_stats(input_path)
        new_weights_per_osd = cal_new_weight(pgs_per_osd, weights_per_osd,
                                             expected_pgs, expected_overload)
        apply_new_weight(new_weights_per_osd, input_path, output_path)
        last_max_diff = cur_max_diff
        pgs_per_osd, expected_pgs = simulate_pg_distribution([pool_id],
                                                             [pg_num],
                                                             rep_num,
                                                             crush_rule,
                                                             output_path)
        asc_pgs_per_osd = sorted(pgs_per_osd.iteritems(), key=lambda t: t[1])
        cur_max_diff = max(abs(asc_pgs_per_osd[0][1] - expected_pgs),
                           abs(asc_pgs_per_osd[-1][1] - expected_pgs))
        print("cur_max_diff={0}, last_max_diff={1}, expected_pgs={2}".format(
            cur_max_diff, last_max_diff, expected_pgs))
        if cur_max_diff > last_max_diff:
            print("Unable to reduce cur_max_diff further")
            os.remove(output_path)
            shutil.copyfile(input_path, output_path)
            break
        else:
            os.remove(input_path)
            shutil.copyfile(output_path, input_path)
    upload_crush_map(conf_path, output_path)
```

---

虚拟机测试：

```shell
[root@localhost ~]# ceph -c /data/cos/ceph.DATAACCESS.conf -s
  cluster:
    id:     e56749d2-1952-43df-b4cd-ce10dded1ea2
    health: HEALTH_WARN
            clock skew detected on mon.192.168.56.201-CLUSTERMON_B, mon.192.168.56.202-CLUSTERMON_C

  services:
    mon: 3 daemons, quorum 192.168.56.200-CLUSTERMON_A,192.168.56.201-CLUSTERMON_B,192.168.56.202-CLUSTERMON_C
    mgr: CLUSTERMGR-192.168.56.200(active)
    osd: 6 osds: 6 up, 6 in
    rgw: 1 daemon active

  data:
    pools:   7 pools, 596 pgs
    objects: 1.46k objects, 2.93KiB
    usage:   669MiB used, 23.3GiB / 23.9GiB avail
    pgs:     596 active+clean

[root@localhost ~]# ceph osd tree
ID  CLASS WEIGHT  TYPE NAME                               STATUS REWEIGHT PRI-AFF
 -6       0.02930 root 00000000-default
 -5       0.02930  datacenter 00000000-default-datacenter.dc1
-16       0.00977   rack 00000000-default-rack.r1
-15       0.00977    host 00000000-default-192.168.56.200
  2   hdd 0.00488       osd.2                                up  1.00000 1.00000
  5   hdd 0.00488       osd.5                                up  1.00000 1.00000
-12       0.00977   rack 00000000-default-rack.r2
-11       0.00977    host 00000000-default-192.168.56.201
  1   hdd 0.00488       osd.1                                up  1.00000 1.00000
  4   hdd 0.00488       osd.4                                up  1.00000 1.00000
 -4       0.00977   rack 00000000-default-rack.r3
 -3       0.00977    host 00000000-default-192.168.56.202
  0   hdd 0.00488       osd.0                                up  1.00000 1.00000
  3   hdd 0.00488       osd.3                                up  1.00000 1.00000
 -1             0 root default
 
[root@localhost ~]# ceph osd pool ls detail
pool 1 '00000000-default.rgw.buckets.index' replicated size 3 min_size 2 crush_rule 5 object_hash rjenkins pg_num 64 pgp_num 64 last_change 46 flags hashpspool stripe_width 0 application rgw
pool 2 'default.rgw.meta' replicated size 3 min_size 2 crush_rule 5 object_hash rjenkins pg_num 4 pgp_num 4 last_change 51 flags hashpspool stripe_width 0 application rgw
pool 3 'default.rgw.control' replicated size 3 min_size 2 crush_rule 5 object_hash rjenkins pg_num 4 pgp_num 4 last_change 54 flags hashpspool stripe_width 0 application rgw
pool 4 '00000000-default.rgw.buckets.non-ec' replicated size 3 min_size 2 crush_rule 5 object_hash rjenkins pg_num 4 pgp_num 4 last_change 58 flags hashpspool stripe_width 0 application rgw
pool 5 '.rgw.root' replicated size 3 min_size 2 crush_rule 5 object_hash rjenkins pg_num 4 pgp_num 4 last_change 61 flags hashpspool stripe_width 0 application rgw
pool 6 'default.rgw.log' replicated size 3 min_size 2 crush_rule 5 object_hash rjenkins pg_num 4 pgp_num 4 last_change 64 flags hashpspool stripe_width 0 application rgw
pool 7 '00000000-default.rgw.buckets.data' replicated size 3 min_size 2 crush_rule 5 object_hash rjenkins pg_num 512 pgp_num 512 last_change 67 flags hashpspool stripe_width 0 expected_num_objects 1024 application rgw

[root@localhost localhost]# crushtool --test --show-utilization \
> -i compiled_crushmap \
> --num-rep 3 \
> --rule 5 \
> --x 512 \
> --pool-id 7
rule 5 (cos_rep_00000000-default_rack), x = 0..511, numrep = 3..3
rule 5 (cos_rep_00000000-default_rack) num_rep 3 result size == 3:	512/512
  device 0:		 stored : 247	 expected : 256	 affected_expected : 256
  device 1:		 stored : 266	 expected : 256	 affected_expected : 256
  device 2:		 stored : 274	 expected : 256	 affected_expected : 256
  device 3:		 stored : 265	 expected : 256	 affected_expected : 256
  device 4:		 stored : 246	 expected : 256	 affected_expected : 256
  device 5:		 stored : 238	 expected : 256	 affected_expected : 256
  
-------------------
#---------------
# 处理完成后：   |
#---------------
[root@localhost localhost]# ceph -s
  cluster:
    id:     e56749d2-1952-43df-b4cd-ce10dded1ea2
    health: HEALTH_WARN
            clock skew detected on mon.192.168.56.201-CLUSTERMON_B, mon.192.168.56.202-CLUSTERMON_C

  services:
    mon: 3 daemons, quorum 192.168.56.200-CLUSTERMON_A,192.168.56.201-CLUSTERMON_B,192.168.56.202-CLUSTERMON_C
    mgr: CLUSTERMGR-192.168.56.200(active)
    osd: 6 osds: 6 up, 6 in
    rgw: 1 daemon active

  data:
    pools:   7 pools, 596 pgs
    objects: 1.46k objects, 2.93KiB
    usage:   670MiB used, 23.3GiB / 23.9GiB avail
    pgs:     596 active+clean
    
 [root@localhost localhost]# crushtool --test --show-utilization -i compiled_crushmap2 --num-rep 3 --rule 5 --x 512 --pool-id 7
rule 5 (cos_rep_00000000-default_rack), x = 0..511, numrep = 3..3
rule 5 (cos_rep_00000000-default_rack) num_rep 3 result size == 3:	512/512
  device 0:		 stored : 256	 expected : 256	 affected_expected : 256
  device 1:		 stored : 256	 expected : 256	 affected_expected : 256
  device 2:		 stored : 256	 expected : 256	 affected_expected : 256
  device 3:		 stored : 256	 expected : 256	 affected_expected : 256
  device 4:		 stored : 256	 expected : 256	 affected_expected : 256
  device 5:		 stored : 256	 expected : 256	 affected_expected : 256
  
[root@localhost ~]# ceph osd tree
ID  CLASS WEIGHT  TYPE NAME                                STATUS REWEIGHT PRI-AFF
 -6       0.02911 root 00000000-default
 -5       0.02911  datacenter 00000000-default-datacenter.dc1
-16       0.00975   rack 00000000-default-rack.r1
-15       0.00975    host 00000000-default-192.168.56.200
  2   hdd 0.00452       osd.2                                up  1.00000 1.00000
  5   hdd 0.00523       osd.5                                up  1.00000 1.00000
-12       0.00967   rack 00000000-default-rack.r2
-11       0.00967    host 00000000-default-192.168.56.201
  1   hdd 0.00465       osd.1                                up  1.00000 1.00000
  4   hdd 0.00502       osd.4                                up  1.00000 1.00000
 -4       0.00969   rack 00000000-default-rack.r3
 -3       0.0096     host 00000000-default-192.168.56.202
  0   hdd 0.00507       osd.0                                up  1.00000 1.00000
  3   hdd 0.00462       osd.3                                up  1.00000 1.00000

```

---

本质原因是CRUSH算法是一个伪随机算法，即使从大体上讲，根据osd对应磁盘的大小不同，会分配不同数目的PG，但实际上从精确角度讲还是不能完全均衡。这样在刚创建集群的时候，手动进行调权，使得集群中osd按照容量来调整WEIGHT，使得容纳相应的合理的PG数目就很有必要了。

在虚拟机中，新建一个集群，然后手动offline reweight，可以直观地看到效果：

```shell
[root@localhost ~]# ceph -c /data/cos/ceph.DATAACCESS.conf -s
  cluster:
    id:     e56749d2-1952-43df-b4cd-ce10dded1ea2
    health: HEALTH_WARN
            clock skew detected on mon.192.168.56.201-CLUSTERMON_B, mon.192.168.56.202-CLUSTERMON_C

  services:
    mon: 3 daemons, quorum 192.168.56.200-CLUSTERMON_A,192.168.56.201-CLUSTERMON_B,192.168.56.202-CLUSTERMON_C
    mgr: CLUSTERMGR-192.168.56.200(active)
    osd: 6 osds: 6 up, 6 in
    rgw: 1 daemon active

  data:
    pools:   7 pools, 596 pgs
    objects: 1.46k objects, 2.93KiB
    usage:   669MiB used, 23.3GiB / 23.9GiB avail
    pgs:     596 active+clean

[root@localhost ~]# ceph osd tree
ID  CLASS WEIGHT  TYPE NAME                               STATUS REWEIGHT PRI-AFF
 -6       0.02930 root 00000000-default
 -5       0.02930  datacenter 00000000-default-datacenter.dc1
-16       0.00977   rack 00000000-default-rack.r1
-15       0.00977    host 00000000-default-192.168.56.200
  2   hdd 0.00488       osd.2                                up  1.00000 1.00000
  5   hdd 0.00488       osd.5                                up  1.00000 1.00000
-12       0.00977   rack 00000000-default-rack.r2
-11       0.00977    host 00000000-default-192.168.56.201
  1   hdd 0.00488       osd.1                                up  1.00000 1.00000
  4   hdd 0.00488       osd.4                                up  1.00000 1.00000
 -4       0.00977   rack 00000000-default-rack.r3
 -3       0.00977    host 00000000-default-192.168.56.202
  0   hdd 0.00488       osd.0                                up  1.00000 1.00000
  3   hdd 0.00488       osd.3                                up  1.00000 1.00000
 -1             0 root default
 
[root@localhost ~]# ceph osd pool ls detail
pool 1 '00000000-default.rgw.buckets.index' replicated size 3 min_size 2 crush_rule 5 object_hash rjenkins pg_num 64 pgp_num 64 last_change 46 flags hashpspool stripe_width 0 application rgw
pool 2 'default.rgw.meta' replicated size 3 min_size 2 crush_rule 5 object_hash rjenkins pg_num 4 pgp_num 4 last_change 51 flags hashpspool stripe_width 0 application rgw
pool 3 'default.rgw.control' replicated size 3 min_size 2 crush_rule 5 object_hash rjenkins pg_num 4 pgp_num 4 last_change 54 flags hashpspool stripe_width 0 application rgw
pool 4 '00000000-default.rgw.buckets.non-ec' replicated size 3 min_size 2 crush_rule 5 object_hash rjenkins pg_num 4 pgp_num 4 last_change 58 flags hashpspool stripe_width 0 application rgw
pool 5 '.rgw.root' replicated size 3 min_size 2 crush_rule 5 object_hash rjenkins pg_num 4 pgp_num 4 last_change 61 flags hashpspool stripe_width 0 application rgw
pool 6 'default.rgw.log' replicated size 3 min_size 2 crush_rule 5 object_hash rjenkins pg_num 4 pgp_num 4 last_change 64 flags hashpspool stripe_width 0 application rgw
pool 7 '00000000-default.rgw.buckets.data' replicated size 3 min_size 2 crush_rule 5 object_hash rjenkins pg_num 512 pgp_num 512 last_change 67 flags hashpspool stripe_width 0 expected_num_objects 1024 application rgw

[root@localhost localhost]#  ceph osd getcrushmap -o compiled_crushmap

#以 pool 7为例：
[root@localhost localhost]# crushtool --test --show-utilization \
> -i compiled_crushmap \
> --num-rep 3 \
> --rule 5 \
> --x 512 \
> --pool-id 7
rule 5 (cos_rep_00000000-default_rack), x = 0..511, numrep = 3..3
rule 5 (cos_rep_00000000-default_rack) num_rep 3 result size == 3:	512/512
  device 0:		 stored : 247	 expected : 256	 affected_expected : 256
  device 1:		 stored : 266	 expected : 256	 affected_expected : 256
  device 2:		 stored : 274	 expected : 256	 affected_expected : 256
  device 3:		 stored : 265	 expected : 256	 affected_expected : 256
  device 4:		 stored : 246	 expected : 256	 affected_expected : 256
  device 5:		 stored : 238	 expected : 256	 affected_expected : 256
  
#-----------
#开始reweight:

#---------------
# offline reweight处理完成后
#---------------
[root@localhost localhost]# ceph -s
  cluster:
    id:     e56749d2-1952-43df-b4cd-ce10dded1ea2
    health: HEALTH_WARN
            clock skew detected on mon.192.168.56.201-CLUSTERMON_B, mon.192.168.56.202-CLUSTERMON_C

  services:
    mon: 3 daemons, quorum 192.168.56.200-CLUSTERMON_A,192.168.56.201-CLUSTERMON_B,192.168.56.202-CLUSTERMON_C
    mgr: CLUSTERMGR-192.168.56.200(active)
    osd: 6 osds: 6 up, 6 in
    rgw: 1 daemon active

  data:
    pools:   7 pools, 596 pgs
    objects: 1.46k objects, 2.93KiB
    usage:   670MiB used, 23.3GiB / 23.9GiB avail
    pgs:     596 active+clean
    
 [root@localhost localhost]#  ceph osd getcrushmap -o compiled_crushmap2
  
 #可以看到在新的crushmap中，stored严格地域expected相等了：
 [root@localhost localhost]# crushtool --test --show-utilization -i compiled_crushmap2 --num-rep 3 --rule 5 --x 512 --pool-id 7
rule 5 (cos_rep_00000000-default_rack), x = 0..511, numrep = 3..3
rule 5 (cos_rep_00000000-default_rack) num_rep 3 result size == 3:	512/512
  device 0:		 stored : 256	 expected : 256	 affected_expected : 256
  device 1:		 stored : 256	 expected : 256	 affected_expected : 256
  device 2:		 stored : 256	 expected : 256	 affected_expected : 256
  device 3:		 stored : 256	 expected : 256	 affected_expected : 256
  device 4:		 stored : 256	 expected : 256	 affected_expected : 256
  device 5:		 stored : 256	 expected : 256	 affected_expected : 256

#可以看到在osd tree中，每个OSD的WEIGHT发生了轻微的变化：
[root@localhost ~]# ceph osd tree
ID  CLASS WEIGHT  TYPE NAME                                STATUS REWEIGHT PRI-AFF
 -6       0.02911 root 00000000-default
 -5       0.02911  datacenter 00000000-default-datacenter.dc1
-16       0.00975   rack 00000000-default-rack.r1
-15       0.00975    host 00000000-default-192.168.56.200
  2   hdd 0.00452       osd.2                                up  1.00000 1.00000
  5   hdd 0.00523       osd.5                                up  1.00000 1.00000
-12       0.00967   rack 00000000-default-rack.r2
-11       0.00967    host 00000000-default-192.168.56.201
  1   hdd 0.00465       osd.1                                up  1.00000 1.00000
  4   hdd 0.00502       osd.4                                up  1.00000 1.00000
 -4       0.00969   rack 00000000-default-rack.r3
 -3       0.0096     host 00000000-default-192.168.56.202
  0   hdd 0.00507       osd.0                                up  1.00000 1.00000
  3   hdd 0.00462       osd.3                                up  1.00000 1.00000

```

