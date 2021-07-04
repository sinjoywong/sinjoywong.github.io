# Ceph如何估算一个Pool的可用容量

[TOC]

## 故事

在处理TCE工单时，遇到一个案例：在新建的集群中，概览页显示的总裸容量远小于存储节点磁盘容量的加和。对比ceph df的输出，前端与Ceph是一致的。查看节点的磁盘列表时，意外发现有一个磁盘的已用容量非常大远远超过其他磁盘的平均水平。询问后知道，一线为了测试磁盘容量告警，往里面dd了数据但是忘了删除。清理了这个磁盘后，集群总容量恢复正常。这才想起了以前了解过Ceph计算Pool容量的原理，并给一线提供了解释。本文对代码原理做一下记录，备查。

```shell
[root@100 ~]# ceph -c /data/cos/ceph.DATASTOR_L.conf df       
GLOBAL:
    SIZE       AVAIL      RAW USED     %RAW USED 
    130TiB     130TiB      5.78GiB             0 
POOLS:
    NAME                           ID     USED        %USED     MAX AVAIL     OBJECTS 
    default.rgw.buckets.non-ec     1           0B         0       37.0TiB           0 
    default.rgw.meta               2      2.69KiB         0       37.0TiB          20 
    default.rgw.buckets.index      3           0B         0       37.0TiB          32 
    default.rgw.control            4           0B         0       37.0TiB           8 
    .rgw.root                      5      1.10KiB         0       37.0TiB           4 
    default.rgw.log                6           0B         0       37.0TiB        1183 
    default.rgw.buckets.data       7       186MiB         0       37.0TiB          53 
```

这里default.rgw.buckets.data的USED+MAX AVAIL就是csp-console显示的存储池的总容量。USED的容量比较直观，就是已经存放的对象的尺寸之和，MAX AVAIL的计算比较绕，下面是对MAX AVAIL计算方法的分析。


## MAX AVAIL代码简析

ceph df中的关于Pool的大多数数据（比如对象数OBJECTS和已用空间USED）都是在对象写入时都记录到PG中的，而一个Pool的可用空间MAX AVAIL则是计算出来的。PGMap::get_rule_avail()负责计算裸容量的MAX AVAIL。以下是对该函数的注释。

```c++
int64_t PGMap::get_rule_avail(const OSDMap& osdmap, int ruleno) const
{
  // 这是一个map，key是OSD ID，value则是OSD的CRUSH weight占整个wm所有OSD的CRUSH Weight总和的比例。
  map<int,float> wm;
  // 这里根据ruleno找到Pool所用的CRUSH Rule
  // 然后根据CRUSH Rule中的TAKE操作，找到该Pool对应的所有root（一般情况下只有一个root）
  // 接着对这些root进行广度优先遍历，完成对wm的计算
  int r = osdmap.crush->get_rule_weight_osd_map(ruleno, &wm);
  // 如果返回值为负数，则表明出错了
  if (r < 0) {
    return r;
  }
  // 如果wm为空，则该Pool不对应任何OSD，可用容量显然是0
  if (wm.empty()) {
    return 0;
  }

  // 根据配置确定每个OSD的最高使用比例，默认full ratio是0.95（见mon_osd_full_ratio配置项）
  float fratio;
  if (osdmap.require_osd_release >= CEPH_RELEASE_LUMINOUS &&
      osdmap.get_full_ratio() > 0) {
    fratio = osdmap.get_full_ratio();
  } else {
    fratio = get_fallback_full_ratio();
  }

  // 遍历wm，用每个OSD到达fratio之前的剩余容量除以wm[OSD]的值，来估算总的裸容量，然后选择其中的最小值
  // 上文故事中，偏小的容量就来源于此逻辑——有一个盘剩余容量很小了，但权值的比重却和其他盘一样
  int64_t min = -1;
  for (auto p = wm.begin(); p != wm.end(); ++p) {
    auto osd_info = osd_stat.find(p->first);
    if (osd_info != osd_stat.end()) {
      if (osd_info->second.kb == 0 || p->second == 0) {
	// osd must be out, hence its stats have been zeroed
	// (unless we somehow managed to have a disk with size 0...)
	//
	// (p->second == 0), if osd weight is 0, no need to
	// calculate proj below.
	continue;
      }
      double unusable = (double)osd_info->second.kb *
	(1.0 - fratio);
      double avail = MAX(0.0, (double)osd_info->second.kb_avail - unusable);
      avail *= 1024.0;
      int64_t proj = (int64_t)(avail / (double)p->second);
      if (min < 0 || proj < min) {
	min = proj;
      }
    } else {
      dout(0) << "Cannot get stat of OSD " << p->first << dendl;
    }
  }
  return min;
}
```

有一个历史顺便提一下，本来PGMap::get_rule_avail()是被ceph-mon直接调用并生成结果的，但引入了ceph-mgr之后，是由ceph-mgr的DaemonServer::send_report()调用PGMap::get_rule_avail()，生成结果后，发给ceph-mon，然后ceph-mon将结果存入PGMapDigest中，ceph df则是从PGMapDigest中直接查询出来的。

在有了裸容量的MAX AVAIL之后，PGMapDigest::dump_object_stat_sum()又进行了一些简单的计算才能得到用于显示的%USED和MAX AVAIL。

```c++
void PGMapDigest::dump_object_stat_sum(
  TextTable &tbl, Formatter *f,
  const object_stat_sum_t &sum, uint64_t avail,
  float raw_used_rate, bool verbose,
  const pg_pool_t *pool)
{
  float curr_object_copies_rate = 0.0;
  if (sum.num_object_copies > 0)
    curr_object_copies_rate = (float)(sum.num_object_copies - sum.num_objects_degraded) / sum.num_object_copies;

  float used = 0.0;
  // note avail passed in is raw_avail, calc raw_used here.
  if (avail) {
    // 对象的逻辑尺寸乘以副本数，然后再根据副本缺失的情况进行一下校正，得到已使用的裸容量
    used = sum.num_bytes * raw_used_rate * curr_object_copies_rate;
    // 将已使用的裸容量加上MAX AVAIL就是总容量，进而可以计算已经使用的比例
    used /= used + avail;
  } else if (sum.num_bytes) {
    used = 1.0;
  }

  if (f) {
    f->dump_int("kb_used", SHIFT_ROUND_UP(sum.num_bytes, 10));
    f->dump_int("bytes_used", sum.num_bytes);
    f->dump_format_unquoted("percent_used", "%.2f", (used*100));
    f->dump_unsigned("max_avail", avail / raw_used_rate);
    f->dump_int("objects", sum.num_objects);
    if (verbose) {
      f->dump_int("quota_objects", pool->quota_max_objects);
      f->dump_int("quota_bytes", pool->quota_max_bytes);
      f->dump_int("dirty", sum.num_objects_dirty);
      f->dump_int("rd", sum.num_rd);
      f->dump_int("rd_bytes", sum.num_rd_kb * 1024ull);
      f->dump_int("wr", sum.num_wr);
      f->dump_int("wr_bytes", sum.num_wr_kb * 1024ull);
      f->dump_int("raw_bytes_used", sum.num_bytes * raw_used_rate * curr_object_copies_rate);
    }
  } else {
    tbl << stringify(si_t(sum.num_bytes));
    tbl << percentify(used*100);
    // 将裸的MAX AVAIL除以副本数得到逻辑可见的MAX AVAIL
    tbl << si_t(avail / raw_used_rate);
    tbl << sum.num_objects;
    if (verbose) {
      tbl << stringify(si_t(sum.num_objects_dirty))
          << stringify(si_t(sum.num_rd))
          << stringify(si_t(sum.num_wr))
          << stringify(si_t(sum.num_bytes * raw_used_rate * curr_object_copies_rate));
    }
  }
}
```

## MAX AVAIL脚本模拟

考虑到非研发恐怕看不懂以上描述，以下是上述算法的简化版脚本：

```shell
# Assuming all HDD OSDs belong to a 3-replica data pool
CEPH_CONF=$(ls /data/cos/ceph.*.conf | head -1)
ceph -c $CEPH_CONF osd df | tee osd_df.txt

cat osd_df.txt |
  grep hdd |
  awk '{print $1 " " $3 " " $5 " " $8}' |
  sed 's/[a-zA-Z]*//g' |
  tee id_weight_cap_usep.txt

SUM_WEIGHT=$(cat id_weight_cap_usep.txt |
             awk 'BEGIN{sum_weight=0}
                  {sum_weight+=$2}
                  END{print sum_weight}')
MON_OSD_FULL_RATIO=0.95
# 3副本的话就是REPLICAS=3，如果是4+2的EC的话，REPLICAS=3/2
REPLICAS=3

# Yes, MAX_AVAIL is the minimum available one according to Cannikin Law
# MIN_AVAIL=10000000 is just to take a large enough value instead of a specific value
MAX_AVAIL=$(cat id_weight_cap_usep.txt |
            awk "BEGIN {MIN_AVAIL=10000000}
                 {
                   EVAL_SIZE = \$3 * ($MON_OSD_FULL_RATIO - \$4/100) * $SUM_WEIGHT / \$2;
                   if (MIN_AVAIL > EVAL_SIZE) MIN_AVAIL=EVAL_SIZE;
                 }
                 END{print MIN_AVAIL / ($REPLICAS)}")
echo "MAX AVAIL: $MAX_AVAIL"
```