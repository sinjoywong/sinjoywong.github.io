ES社区的基本情况：官网和Github、代码规模、最新版本、最新稳定版、发布周期、基本功能特性，最新功能特性、比较优秀的文章和书籍

> 1. 单机ES测试集群的部署方法和硬件要求
> 2. 访问ES集群的方法：支持的SDK是哪些，C++、Golang和Python的SDK支持情况和使用，RGW使用了哪些ES接口
> 3. ==生产环境高可用ES集群的部署方法==
> 4. ==理论上或社区宣称的ES集群的局限性：故障切换原理，故障切换时对服务的影响，空集群性能，70%容量以上的性能（已用容量对哪些操作有影响），单集群的容量==
> 5. 调研或编写压测工具，基于之前几点的认识和目前能获得的物理硬件，置顶压测计划给出压测报告
>
> 背景是现在不少客户要要求全文检索，但目前我们存储产品中心没人对ES调研，所以需要有人探索一下
>
> 不知道你是打算了解es的什么。我之前做的主要是把对象元数据同步到es，es本身的架构原理推荐还是看es官网，和ceph同步这一块的原理可以看以下这些：
> https://docs.ceph.com/en/latest/radosgw/elastic-sync-module/
> https://zhuanlan.zhihu.com/p/338167396

# * 压测报告（待续）

> 待续

# 0. ES社区的基本情况

| 序号 | 项目         | 说明                                                         |
| ---- | ------------ | ------------------------------------------------------------ |
| 1    | 官网地址     | https://www.elastic.co/cn/                                   |
| 2    | github地址   | https://github.com/elastic/elasticsearch                     |
| 3    | 代码规模     | `git log  --pretty=tformat: --numstat \| awk '{ add += $1; subs += $2; loc += $1 - $2 } END { printf "added lines: %s, removed lines: %s, total lines: %s\n", add, subs, loc }'`<br />`added lines: 8348801, removed lines: 4955218, total lines: 3393583`<br />7.10版本代码总行数约为339万行。 |
| 4    | 最新版本     | 最新版本为7.10.1，2020年12月9日发布<br />参考https://github.com/elastic/elasticsearch/releases<br />7.10大版本功能特性：https://www.elastic.co/guide/en/elasticsearch/reference/7.10/breaking-changes-7.10.html<br />[可搜索快照公测](https://www.elastic.co/cn/blog/introducing-elasticsearch-searchable-snapshots) |
| 5    | 最新稳定版本 | 7.10.1 https://www.elastic.co/cn/downloads/elasticsearch<br /> |
| 6    | 发布周期     | 目前维护的大版本有6和7两个版本，近半年更新频率基本上一个月一个小版本，主要是一些bug fix。今年8月以来都只更新了7.x版本：<br />7.5.2 2020 Jan 22<br />7.6.0 2020 Feb 12<br />6.8.7 2020 Mar 5<br />7.6.1 2020 Mar 5<br />6.8.8 2020 Apr 1<br />7.6.2 2020 Apr 1<br />6.8.9 2020 May 13<br />7.7.0 2020 May 13<br />6.8.10 2020 Jun 3<br />7.7.1 2020 Jun 3<br />7.8.0 2020 Jun 18<br />6.8.11 2020 Jul 27<br />7.8.1 2020 Jul 27<br />6.8.12 2020 Aug 18<br />7.9.0 2020 Aug 18<br />7.9.1 2020 Sep 3<br />7.9.2 2020 Sep 24<br />7.9.3 2020 Oct 22<br />7.10.0 2020 Nov 11<br />7.10.1 2020 Dec 9<br />参考：https://github.com/elastic/elasticsearch/releases |
| 7    | 资料参考     | [《Elasticsearch源码解析与优化实战》--张超](https://weread.qq.com/web/reader/f9c32dc07184876ef9cdeb6)<br />[elasticsearch官方文档](https://www.elastic.co/guide/index.html)<br /> |

# 1. 单机部署Elasticsearch

> 参考《3. 部署Elasticsearch集群》章节，以单机模式部署即可。

# 2. 访问Elasticsearch

> 访问ES集群的方法：支持的SDK是哪些，C++、Golang和Python的SDK支持情况和使用，RGW使用了哪些ES接口

## 访问ES集群的方法

正如官网中所述的，“Elasticsearch 是一个分布式、RESTful 风格的搜索和数据分析引擎”，ES计划以RESTful风格的方式来操作集群。支持以下3种访问方式，且计划废弃Java API，只保留前两种REST ful API：

1. [HTTP REST接口](https://www.elastic.co/guide/en/elasticsearch/reference/current/rest-apis.html)
2. [Java REST API](https://www.elastic.co/guide/en/elasticsearch/client/java-rest/7.10/java-rest-overview.html)
3. [Java API](https://www.elastic.co/guide/en/elasticsearch/client/java-api/current/index.html)（保留至今是基于对早期版本的兼容性考虑，但官方从ES 7.0开始已废弃Java API，并计划在ES 8.0版本中完全移除Java API）

## RGW访问ES接口(待续)

[通过ES提供ceph rgw metadata搜索](https://ci-jie.github.io/2019/03/25/Ceph-Object-Storage-Elasticsearch-實作快速搜尋-metadata/)

[ceph rgw搭建ES同步模块](https://zhuanlan.zhihu.com/p/338167396)

[ceph ES sync module官方文档](https://docs.ceph.com/en/latest/radosgw/elastic-sync-module/)

# 3. 部署ElasticSearch集群

## 安装ElasticSearch

参考官网：https://www.elastic.co/guide/en/elastic-stack/current/installing-elastic-stack.html

https://www.elastic.co/guide/en/elasticsearch/reference/7.10/install-elasticsearch.html

使用rpm来安装应该是最方便的：

```shell
#1. 导入ElasticSearch PGP key
rpm --import https://artifacts.elastic.co/GPG-KEY-elasticsearch

#2.在/etc/yum.repos.d/下创建一个elasticsearch.repo，并添加如下配置：
[elasticsearch]
name=Elasticsearch repository for 7.x packages
baseurl=https://artifacts.elastic.co/packages/7.x/yum
gpgcheck=1
gpgkey=https://artifacts.elastic.co/GPG-KEY-elasticsearch
enabled=0
autorefresh=1
type=rpm-md

#3.yum安装
sudo yum install --enablerepo=elasticsearch elasticsearch 
```

对于内网环境，可以直接将下载好的rpm包拷入，直接安装即可。

## 部署参数设置

ES对环境的要求比较多且杂。

> 参考第4章和第21章

| 序号 | 类型                                                     | 说明                                                         |
| ---- | -------------------------------------------------------- | ------------------------------------------------------------ |
| 1    | 环境配置：JDK版本                                        | 不同ES版本对jdk版本有不同要求，目前最新版ES 7.10.1要求jdk 1.8以上。 |
| 2    | 环境配置：JVM内存配置                                    | 不建议为ES的JVM分配超过32GB的内存，否则可能出现Java内存指针压缩失效的情况。 |
| 3    | 环境配置：禁用交换分区                                   | ES只允许进程使用物理内存，不允许使用交换分区。应该直接禁用服务器的交换内存：<br />#禁用交换分区<br/>sudo swapoff -a<br/>#确认交换分区状态<br/>sudo free -m |
| 4    | 环境配置：最大进程数、文件描述符数、最大线程数、限制调整 | 将当前用户的软硬限制调大。<br />vim /etc/security/limits.conf<br/>* soft nproc 2048<br/>* hard nproc 4096<br/>* soft memlock unlimited<br/>* hard memlock unlimited<br/>* soft nofile 65535<br/>* hard nofile 65537 |
| 5    | 环境配置：防火墙                                         | 关闭防火墙，或添加对应规则：<br />service firewalld stop     |
| 6    | ES配置：不允许以root账户运行                             | 为了安全性，es不允许使用root权限运行，因此需要创建一个用户来运行。此时需要为该用户服务所有运行es时涉及到的文件夹权限：<br />groupadd es<br/>useradd es -g es -p passw0rd<br/>chown -R es:es /usr/share/elasticsearch/<br/>chown -R es:es /var/log/elasticsearch/<br/>chown -R es:es /var/lib/elasticsearch/<br/>chown -R es:es /etc/sysconfig/elasticsearch<br/>chown -R es:es /etc/elasticsearch<br/>chown -R es:es /var/log/elasticsearch/ |
| 7    | ES配置：副本数的选择                                     | 由于搜索使用较好的硬件配置，因此可以直接将副本数`number_of_replicas`设置为1即可，即每个分片由两个副本，一个为主副本，一个为从副本。若搜索请求的吞吐量较高，则可以适当增加该值，让搜索可以利用更多的节点。<br />该值可以后期动态调整，只会涉及到数据的复制和网络传输，而不会重建索引，因此对系统的影响较小。 |
| 8    | ES配置：path.data并path.logs默认路径调整                 | data和logs 默认路径：<br/>logs：/ var / log / elasticsearch<br/>data：/ var / data / elasticsearch<br />如果这些重要文件夹保留在其默认位置，则在将Elasticsearch升级到新版本时，存在删除它们的高风险，因此一般将其更改为自定义位置。 |
| 9    | ES配置：独立部署主节点，数据节点与主节点分离             | 将主节点和数据节点分离最大的好处就在于Master切换过程可以迅速完成，有机会跳过gateway和分片重新分配的过程。<br />例如有3台具备Master资格的节点独立部署，然后关闭当前活跃的主节点，新主当选后由于内存中持有最新的集群状态，因此可以跳过gateway的恢复过程，并且由于主节点没有存储数据，所以旧的Master离线不会产生未分配状态的分片。新主当选后集群可以迅速变为Green状态。 |

## 配置文件参考

测试环境为虚拟机virtual box 6.1，安装3台CentOS 7.6，各自安装好elastic search 7.10.1，并按照上一小节配置好必要的环境后，修改每个节点的配置文件 /etc/elasticsearch/elasticsearch.yml以实现特定的配置。

以下的配置文件构建了3台节点组成一个集群，集群名称为"my-application"，且3个节点都有资格当Master(即node.master: true)，同时都是数据节点。基于ES的原有设计，同时这3个节点都是协调节点。

> 受限于笔记本机能不易创建更多虚拟机，因此这三台节点同时为Master和DataNode，未做分离，但不影响功能测试。

```shell
#192.168.56.111:
cluster.name: my-application
node.name: node-1
node.attr.rack: r1
path.data: /var/lib/elasticsearch
path.logs: /var/log/elasticsearch
bootstrap.memory_lock: false
network.host: 192.168.56.111
network.bind_host: 192.168.56.111
network.publish_host: 192.168.56.111
transport.host: 192.168.56.111
transport.tcp.port: 9300
node.master: true
node.data: true
http.port: 9200
discovery.seed_hosts: ["192.168.56.111","192.168.56.112","192.168.56.113"]
cluster.initial_master_nodes: ["192.168.56.111","192.168.56.112","192.168.56.113"]
gateway.recover_after_nodes: 2
http.cors.enabled: true
http.cors.allow-origin: "*"

#192.168.56.112
cluster.name: my-application
node.name: node-2
node.attr.rack: r1
node.master: true
node.data: true
path.data: /var/lib/elasticsearch
path.logs: /var/log/elasticsearch
bootstrap.memory_lock: false
#network.bind_host: 0.0.0.0
network.host: 192.168.56.112
network.bind_host: 192.168.56.112
network.publish_host: 192.168.56.111
transport.host: 192.168.56.112
transport.tcp.port: 9300
#discovery.zen.ping.unicast.hosts
http.port: 9200
discovery.seed_hosts: ["192.168.56.111","192.168.56.112","192.168.56.113"]
cluster.initial_master_nodes: ["192.168.56.111","192.168.56.112","192.168.56.113"]
#gateway.recover_after_nodes: 3
#action.destructive_requires_name: true
http.cors.enabled: true
http.cors.allow-origin: "*"
action.destructive_requires_name: true

#192.168.56.113
cluster.name: my-application
node.name: node-3
node.attr.rack: r1
path.data: /var/lib/elasticsearch
path.logs: /var/log/elasticsearch
bootstrap.memory_lock: false
network.host: 192.168.56.113
network.bind_host: 192.168.56.113
network.publish_host: 192.168.56.113
transport.host: 192.168.56.113
transport.tcp.port: 9300
node.master: true
node.data: true
http.port: 9200
discovery.seed_hosts: ["192.168.56.111","192.168.56.112","192.168.56.113"]
cluster.initial_master_nodes: ["192.168.56.111","192.168.56.112","192.168.56.113"]
gateway.recover_after_nodes: 2
http.cors.enabled: true
http.cors.allow-origin: "*"
```

切换到用户es下，执行/usr/share/elasticsearch/bin/elasticsearch -d，使ES在后台运行，

查看集群信息，集群信息如下所示：

![image-20210104192027020](.1.CSP%E8%B0%83%E7%A0%94%EF%BC%9Aelasticsearch.assets/image-20210104192027020.png)

<img src=".1.CSP%E8%B0%83%E7%A0%94%EF%BC%9Aelasticsearch.assets/image-20210104192046295.png" alt="image-20210104192046295"  />

可用的命令为：

<img src=".1.CSP%E8%B0%83%E7%A0%94%EF%BC%9Aelasticsearch.assets/image-20210104192114723.png" alt="image-20210104192114723" style="zoom: 80%;" />

以上仅为虚拟机测试环境部署，受限于系统机能，主节点与数据节点未分离。而在实际的生产环境中，主节点与数据节点应分离，并可能分离协调节点。

整体架构可以参考：

https://developer.aliyun.com/article/777755

## IdealJ远程调试环境搭建

查看目前安装的ES的版本：

```shell
curl 192.168.56.111:9200 
{
  "name" : "node-1",
  "cluster_name" : "my-application",
  "cluster_uuid" : "88MvOzA1Q4-sJU_dysAtTw",
  "version" : {
    "number" : "7.10.1",
    "build_flavor" : "default",
    "build_type" : "rpm",
    "build_hash" : "1c34507e66d7db1211f66f3513706fdf548736aa",
    "build_date" : "2020-12-05T01:00:33.671820Z",
    "build_snapshot" : false,
    "lucene_version" : "8.7.0",
    "minimum_wire_compatibility_version" : "6.8.0",
    "minimum_index_compatibility_version" : "6.0.0-beta1"
  },
  "tagline" : "You Know, for Search"
}
```

可以看到为7.10.1。

在github上只有大版本号的分支，如7.10，而没有例如7.10.1的小版本，因此需要在这里下载已发布的对应版本源码： https://github.com/elastic/elasticsearch/releases

导入到IdealJ中，设置debug configurations:

![image-20210107181607052](.1.CSP%E8%B0%83%E7%A0%94%EF%BC%9Aelasticsearch.assets/image-20210107181607052.png)

将上图中Command line arguments for remote JVM中的配置拷贝到远端节点的jvm.options中：

![image-20210107181723069](.1.CSP%E8%B0%83%E7%A0%94%EF%BC%9Aelasticsearch.assets/image-20210107181723069.png)

![image-20210107181708285](.1.CSP%E8%B0%83%E7%A0%94%EF%BC%9Aelasticsearch.assets/image-20210107181708285.png)

重启elasticsearch进程，此时无论是前台执行还是后台执行，都会打印一行包含debug端口号的日志，此时即可在本地的idealJ中debug。

日志位置默认在`/var/log/elasticsearch/`下，也是使用log4j来实现，可以在`/etc/elasticsearch/log4j2.properties`中修改日志级别以查看。

# 4. ES局限性

> 理论上或社区宣称的ES集群的局限性：故障切换原理，故障切换时对服务的影响，空集群性能，70%容量以上的性能（已用容量对哪些操作有影响），单集群的容量

## 索引建立的时候需确定主分片数

主分片数决定了索引可以被分为多少片，分片数越多，

> 通过分片路由算法计算shardId：`shard_num = hash（_routing） % num_primary_shards`，此处_routing表示文档id，num_primay_shards为主分片数目，shard_num为该文档id对应的分片号。
>
> 若中途更改主分片数目，则会引起路由信息的变化，若要使其还能找到原有文档，则可能需要对文档进行迁移，重新建立关系。目前ES不支持这么做。

不能灵活动态地调整索引的主分片数目，副分片数目则可以灵活修改。6.x后有所改进，实现了索引的主分片的拆分和缩小。

分片是将一个Elasticsearch索引分割成一些更小的索引的过程，这样才能在同一集群的不同节点上将它们分散开。在查询的时候，总结果集汇总了所有分片的数据。

默认为每个索引创建5个分片，即使是单节点环境也是如此。这种冗余被称为“预分配”（over allocation）。

早期版本（5.x之前）不支持修改主分片数目，在5.x之后可以在一定条件下支持对某个索引的主分片进行**拆分(split)和缩小(shrink)**（==尚未测试具体条件==）。主分片不够时可以考虑新建索引，使用索引别名，类似于软链接来实现相同URL访问的目的，或者使用_split API来拆分索引（6.x之后）。分片数量过多后增加集群处理压力，可以shrink减少主分片数目。

**目前版本仍不支持索引分片的动态调整。**若应用程序的增长超过了单台服务器的容量时，只能重新创建一个具有更多分片的新索引，并重新索引数据。这样的行为需要大量的时间和服务器资源，在生产环境中是很危险的。因此只能按照预计情况来确定索引的分片数目。

理想的情况是通过计划使用的节点数来确定分片数量。同时考虑到高可用和查询的吞吐量，需要配置副本。如果计划将来使用10个节点，就给索引配置10个分片，考虑到副本，若每个副本有一份额外的拷贝(number_of_replicas=1)，最终将有20个分片，其中10个为主分片，10个为从分片。公式如下：

所需最大节点数 = 分片数 * （副本数 + 1）

> 参考《深入理解ElasticSearch（原书第三版）》，6.2.2

## 【新增】 shardId计算方法：

```java
TransportBulkAction.doRun()
  -> ShardIterator indexShards(ClusterState clusterState, String index, String id, @Nullable String routing) 
  -> IndexShardRoutingTable shards(ClusterState clusterState, String index, String id, String routing)
  -> int generateShardId(IndexMetadata indexMetadata, @Nullable String id, @Nullable String routing) 
  -> int calculateScaledShardId(IndexMetadata indexMetadata, String effectiveRouting, int partitionOffset)
```

此处的index为索引名称，id为文档id，routing从`DocWriteRequest`中得到，表示自定义的路由规则，默认为null。effectiveRouting作为一个中间变量，若有自定义的路由规则，则直接赋值为routing，否则赋值为文档id。

然后传到`Murmur3HashFunction.hash()`中计算：

```java
final int hash = Murmur3HashFunction.hash(effectiveRouting) + partitionOffset;
```

为什么搞个“自定义设置路由”呢？

在自定义路由PUT文档的时候，这样哈希的时候就直接以自定义路由的名称哈希，也就是可以人为地把几个文档可以放到同一个索引里，同时在一次正常的查询情况下，请求会被发给所有的shard（不考虑副本），然后等所有shard返回，再将结果聚合，返回给调用方。若一开始就知道数据在哪个shard上，则可以提高性能。

http://vearne.cc/archives/3219

处于保护性的考虑，ES还提供了一个参数`index.routing_partition_size`用于避免自定义id和routing值不够随机造成的数据倾斜的问题。在计算的时候实际上就是给了一个随机值的偏移：

```java
//OperationRouting.java
if (indexMetadata.isRoutingPartitionedIndex()) {
  partitionOffset = Math.floorMod(Murmur3HashFunction.hash(id), indexMetadata.getRoutingPartitionSize());
} else {
  // we would have still got 0 above but this check just saves us an unnecessary hash calculation
  partitionOffset = 0;
}

private static int calculateScaledShardId(IndexMetadata indexMetadata, String effectiveRouting, int partitionOffset) {
  final int hash = Murmur3HashFunction.hash(effectiveRouting) + partitionOffset;

  // we don't use IMD#getNumberOfShards since the index might have been shrunk such that we need to use the size
  // of original index to hash documents
  return Math.floorMod(hash, indexMetadata.getRoutingNumShards()) / indexMetadata.getRoutingFactor();
}
```







## 掉电保护由写日志translog实现

在写操作时，是write-back模式：先在内存中缓冲一段数据，再将其落盘。其落盘时机可以是手动调用flush，也可以是操作系统的一些缓存落盘策略（如达到某阈值、经过多长时间）。而ES在内存数据结构建立之后，就返回成功，而不等到数据落盘才返回，这样保证了“近实时搜索”这一特性。

对于掉电保护，则是通过写日志来实现的。每次对ES进行操作时均记录事务日志。当ES启动的时候则会重放translog中所有在最后一次提交后发生的变更操作。

trans_log的下刷策略可以由参数控制。从ES 2.x开始，默认情况下translog的持久化策略为：每个请求都flush。这将极大地影响ES写入速度，但也是最可靠的，在数据写入主分片成功后，但尚未写到副分片时，若主机发生掉电，由于先写了translog，对其进行replay仍旧可以使得数据一致性得到保障。配置如下：

```shell
index.translog.durability: request
```

而若允许可能的数据丢失的话，可以调整translog持久化策略为**周期性下刷**或**到达一定阈值后下刷**。配置如下所示：

```shell
#刷盘策略按照sync_interval配置指定的周期进行：
index.translog.durability: async
#每120s下刷一次（默认为5s,且不可低于100ms）
index.translog.sync_interval: 120s
#当内存中的translog大小超过1GB时下刷。默认为512MB。
index.translog.flush_threshould_size: 1024mb 
```

> 若有非易失性内存，或BBU保护则无需每次请求都下刷也能保证内存数据不丢失。但此时还需要一些额外的软硬件来保证内存数据的下刷与恢复。 一些统一存储控制器会做这个功能，但是这种通用的服务器可能要兼容性一般无法这样设计。

## Lazy Delete：单个索引不能太大

ES的更新、删除操作实际上是标记操作。以_id为单位的删除文档不会立刻释放空间，只有在Lucene分段合并的时候才检测delete标记，进行实际的删除工作（类似于LevelDB）。

> Lucene的数据结构为LSM树，将随机写在内存中生成局部有序的小树，在下穿

即使手工触发分段合并（从而使其提前实质上的清除），仍会引起较高的I/O压力，并且可能因为分段巨大导致在合并过程中磁盘空间不足（分段合并过程中，新段的产生需要一定的磁盘空间，我们要保证系统有足够的剩余可用空间。当分段大小大于磁盘可用空间的一半即会导致无法真正地物理删除）。因此在实际应用中，不应该向单个索引持续写数据，直到其分片巨大无比。

可能的解决方法是：每天创建一个索引，起一个新的名字，然后用原有的名字以别名的方式软链接过来。也可以在数据量小的时候用_shrink API来缩小主分片的数量，从而降低集群负载。

> 感觉维护起来很麻烦，不知道有实际业务的运维人员一般怎么处理的。可以询问es相关运维人员。

## 弱一致性

只要主分片写入完成后就允许读，以达到”近实时搜索“，这样若查询请求刚好由副分片来承担，而此时副分片还未同步主分片的数据，则可能造成两次搜索结果不同。

> 可能对于搜索业务来说，结果不需要太精确，能搜到差不多的东西就行，一次不行搜两次？社区是否有人注意到这个问题？是否有提出解决方案？

## 副分片写入也需索引

写流程过程中，主副本写入时也需要索引，而不能直接将主分片的数据拷贝，这样浪费了计算能力。

# 5. 故障切换原理

要了解故障切换，首先需要了解ES集群的架构、配置管理、数据组织、读写流程。具体内容可以翻阅《Elasticsearch源码解析与优化实践》，此处列出基本介绍：

## 基本概念

**索引：**Elasticsearch存储数据的逻辑名字空间，在有分片和副本的情况下可能由一个或多个Lucene索引构成。

**分片：**分片就是可以存储在一个或多个节点之上的容器，由Lucene段组成。索引由一到多个分片组成，让数据可以分布开。

分片是单个Lucene实例，这是Elasticsearch管理的比较底层的功能。索引是指向主分片和副本分片的逻辑空间。

> Elasticsearch会自动管理集群中所有的分片，当发生故障的时候，Elasticsearch会把分片移动到不同的节点或者添加新的节点。Elasticsearch将索引分解成多个分片。当你创建一个索引，你可以简单地定义你想要的分片数量。每个分片本身是一个全功能的、独立的单元，可以托管在集群中的任何节点上。

分片也有主从之分。所有改动索引的操作都发生在主分片上。从分片的数据由主分片复制而来，支持数据快速检索和高可用。如果主分片所在的服务器宕机了，从分片会自动升级为主分片。

**副本：**副本是为支持高可用而保存在分片中的另一份数据。副本也有助于提供快速检索体验。

**文档**：文档就是JSON对象，包含的实际数据由键值对构成。有一点非常重要：一旦某个字段上生成了索引，Elasticsearch就会为那个字段创建一个数据类型。从2.x版开始，都会进行严格的类型检查。

**映射：**如1.1节所述，文档在生成索引之前都要经历分析阶段。配置如何将输入文本拆分成词条、哪些词条要被过滤出来、还要经过哪些额外处理（比如去除HTML标签）等，这就是映射要扮演的角色——存储分析链所需的信息。虽然Elasticsearch能根据字段的值自动检测字段的类型，有时候（事实上几乎是所有时候）用户还是想自己来配置映射，以避免出现一些令人不愉快的意外。

**节点：**运行在服务器上的单个Elasticsearch服务实例被称为节点。一般来说按照功能划分分为**主节点**、**数据节点**、**协调节点**。这几个角色也可以由同一个物理节点扮演，但基于ES的代码处理流程，考虑到高可用的设计，可能需要恰当地分离角色，让某些物理节点只承担单一的功能，以加速故障时的恢复速度，减少严重故障的可能。

**集群：**多个协同工作的Elasticsearch节点的集合被称为集群。

## 整体架构

ES其实就是在Lucene上面加的一层包装，考虑了分布式系统下的数据分片、选主、故障检测、故障切换、负载均衡等功能。索引实际的加入和查询工作由Lucene来实现。

整体分为数据管理和配置管理两部分。

* 存储管理：负责管理数据的读取和更新，使用多副本方式保证数据的可靠性和可用性。

* 配置管理：使用Master节点对配置信息进行管理，并在有更新的时候广播到所有节点上，维护所有配置信息的一致性。

数据副本模型基于主从模式，在实现过程中参考了微软的PacificA算法。配置管理与数据副本分离。

ES与Lucene的关系如下所示：一个ES的索引可以被拆分为多个分片shard；一个分片就是一个Lucene索引，这个Lucene索引内部又被分为若干段（segment），每一段都是一个倒排索引。一个倒排索引又由多个文档的数据组成。在每个分段内部，文档的不同字段被单独建立索引。每个字段的值由若干词（Term）组成，Term是原文本内容经过分词器处理和语言处理后的最终结果。

> Lucene和倒排索引相关可参考：https://zhuanlan.zhihu.com/p/33671444

![image-20210107165621099](.1.CSP%E8%B0%83%E7%A0%94%EF%BC%9Aelasticsearch.assets/image-20210107165621099.png)

而在集群层面，举例说明分片的数据分布与节点的关系：

假设有1个节点，有一个索引，主分片数为3，即由P0，P1和P2组成。由于只有一个节点，因此副本数为0。其中P0，P1，P2表示主副本（P与R表示Primary与Replica）：

![image-20210111152321773](.1.CSP%E8%B0%83%E7%A0%94%EF%BC%9Aelasticsearch.assets/image-20210111152321773.png)

若再添加一个节点，副本数为1，则副分片被某种规则分配到node2，主分片和副分片的分布呈现高可用状态，即使两个节点挂掉任意一个，都不影响数据的可用性（R0，R1，R2表示从副本）：

![image-20210111152331197](.1.CSP%E8%B0%83%E7%A0%94%EF%BC%9Aelasticsearch.assets/image-20210111152331197.png)

再添加一个节点，则又会按照如下分布，此时可以支持挂掉两个节点而不影响数据的可用性：

![image-20210111151935056](.1.CSP%E8%B0%83%E7%A0%94%EF%BC%9Aelasticsearch.assets/image-20210111151935056.png)

### 索引分片的分布规则

如何决定某个索引的主分片和若干个副分片保存在哪个DataNode上呢？即数据分布的拓扑模型是如何决定的？

这样的分片的数据分布是通过**MasterNode**的**allocator**和**decider**来两个阶段共同决定的：

allocators决定了某个索引的某个shard可以分布到哪些节点上（==这里是简单暴力地找出拥有分片数最少的节点列表，并按分片数量升序排序，分片较少的节点会被优先选择==），deciders则是==通过一些规则来确认这些节点是否确实可以被分配给某个shard来用==。

默认有16个AllocationDeciders，用于在Allocator划分出来某个shardId可用的节点后，然后根据不同的规则决定这些某个节点是否真的可被shardId的分片使用：

<img src=".1.CSP%E8%B0%83%E7%A0%94%EF%BC%9Aelasticsearch.assets/image-20210110161956995.png" alt="image-20210110161956995" style="zoom:50%;" />

例如，SameShardAllocationDecider则保证了不会出现某个shard的主副本和从副本都在一个节点上分配；AwarenessAllocationDecider起到了可用区划分的作用，感知了服务器、机架等，尽量分散存储shard等。

> 感觉分配起来还是很麻烦，没有找到类似于crushmap那样的通过配置文件直接更改数据分布方式的方法。可能ES作为搜索引擎而非存储引擎，省去了这些复杂性。

此处又分为两个需求，一个是客户端请求过来后，如何知道这个索引的某个分片在什么位置，即分配已存在的分片，从磁盘中找到它们。

一个是平衡分片在节点间的分布，常用于在节点增删、创建新集群的时候。

这就引出了元数据管理的内容定义、元数据同步（主节点的收集、向集群所有节点的广播）、元数据的增删改查。

### 元数据正常操作

ES中的元数据主要包含三个层面：

* 集群状态元数据：主要包含主要包含uuid等配置信息、路由信息等，其中最重要的是**内容路由信息**，代码中描述为RoutingTable，它描述了“哪个分片位于哪个节点”这种信息。 

  ![image-20210110154421576](.1.CSP%E8%B0%83%E7%A0%94%EF%BC%9Aelasticsearch.assets/image-20210110154421576.png)

  ```text
  ClusterState内容包括：
      long version: 当前版本号，每次更新加1
      String stateUUID：该state对应的唯一id
      RoutingTable routingTable：所有index的路由表
      DiscoveryNodes nodes：当前集群节点
      MetaData metaData：集群的meta数据
      ClusterBlocks blocks：用于屏蔽某些操作
      ImmutableOpenMap<String, Custom> customs: 自定义配置
      ClusterName clusterName：集群名
  MetaData中需要持久化的包括：
      String clusterUUID：集群的唯一id。
      long version：当前版本号，每次更新加1
      Settings persistentSettings：持久化的集群设置
      ImmutableOpenMap<String, IndexMetaData> indices: 所有Index的Meta
      ImmutableOpenMap<String, IndexTemplateMetaData> templates：所有模版的Meta
      ImmutableOpenMap<String, Custom> customs: 自定义配置
  
  ```

  集群状态由Master节点管理，

  **集群元数据的持久化：**在这里需要注意的是routingTable不会持久化到磁盘中==（为什么不持久化？集群所有节点都掉线怎么办？这样还如何找到原来的对应关系？看起来需要扫盘重建routingTable）==。除此之外的其他元数据都会持久化到磁盘中。只有具备Master资格的节点和数据节点可以持久化集群状态（==这意味着独立出来的预处理节点和协调节点中不维护元数据==）。 

  （见《Elasticsearch源码解析与优化实践》 第11章）

  **重建RoutingTable时机**：==集群完全重启时，依靠gateway的recovery过程重建RoutingTable==。这个Recovery过程实际上是在Master选举成功后，Master从所有节点中拉取集群级和索引级元数据信息，然后选择版本号最大的作为权威元数据。而”主分片位于那个节点“是allocation模块动态计算的，先前的主分片不一定还被选为新的主分片。

  > 此处的allocation听起来可能有歧义，此处并非是说例如”内存分配“的分配，而只是说根据一些规则建立shardId和nodeId的对应关系。

  **读取RoutingTable时机：**当读取某个文档时，根据路由算法确定目的分片后，从RoutingTable中查找分片位于那个节点，然后将请求转发到目的节点。

  **修改RoutingTable时机：**理论上，集群中节点数目发生变化的时候，RoutingTable就会发生变化。==是否会有数据迁移？==

  集群状态由**主节点**负责维护，如果主节点从数据节点接收更新，则将这些更新广播到集群的其他节点，让每个节点上的集群状态保持最新。ES 2.0版本之后，更新的集群状态信息只发增量内容，并且是被压缩的。

  > 自定义路由优化：https://blog.csdn.net/cnweike/article/details/38531997
  >
  > https://blog.csdn.net/ZYC88888/article/details/100727714

* 其次是index级别的元数据：

  ```
  IndexMetaData中需要持久化的包括：
      long version：当前版本号，每次更新加1。
      int routingNumShards: 用于routing的shard数, 只能是该Index的numberOfShards的倍数，用于split。
      State state: Index的状态, 是个enum，值是OPEN或CLOSE。
      Settings settings：numbersOfShards，numbersOfRepilicas等配置。
      ImmutableOpenMap<String, MappingMetaData> mappings：Index的mapping
      ImmutableOpenMap<String, Custom> customs：自定义配置。
      ImmutableOpenMap<String, AliasMetaData> aliases： 别名
      long[] primaryTerms：primaryTerm在每次Shard切换Primary时加1，用于保序。
      ImmutableOpenIntMap<Set<String>> inSyncAllocationIds：处于InSync状态的AllocationId，用于保证数据一致性，下一篇文章会介绍。
  ```

  c

* 再次是事务日志translog。描述了ES对Lucene的操作。在每次操作之前，先写translog日志，日志遵循一定的规则落盘，从而起到掉电保护的作用。

---

参考代码中数据结构的定义可以更加明确地理解元数据包含了什么：

```java
//.../cluster/ClusterState.java
public class ClusterState implements ToXContentFragment, Diffable<ClusterState> {
  ...
  private final long version;
  private final String stateUUID;
  private final RoutingTable routingTable;
  private final DiscoveryNodes nodes;
  private final Metadata metadata;
  private final ClusterBlocks blocks;
  private final ImmutableOpenMap<String, Custom> customs;
  private final ClusterName clusterName;
  private final boolean wasReadFromDiff;
  private final int minimumMasterNodesOnPublishingMaster;
  private volatile RoutingNodes routingNodes;
	...
}

//.../cluster/metadata/Metadata.java
public class Metadata implements Iterable<IndexMetadata>, Diffable<Metadata>, ToXContentFragment {
  ...
  private final String clusterUUID;
  private final boolean clusterUUIDCommitted;
  private final long version;
  private final CoordinationMetadata coordinationMetadata;
  private final Settings transientSettings;
  private final Settings persistentSettings;
  private final Settings settings;
  private final DiffableStringMap hashesOfConsistentSettings;
  private final ImmutableOpenMap<String, IndexMetadata> indices;
  private final ImmutableOpenMap<String, IndexTemplateMetadata> templates;
  private final ImmutableOpenMap<String, Custom> customs;
  private final transient int totalNumberOfShards; // Transient ? not serializable anyway?
  private final int totalOpenIndexShards;
  private final String[] allIndices;
  private final String[] visibleIndices;
  private final String[] allOpenIndices;
  private final String[] visibleOpenIndices;
  private final String[] allClosedIndices;
  private final String[] visibleClosedIndices;
	...
}
```

clusterState元数据包含了如下数据结构：

其中，DicoveryNodes中主要包含了集群中的节点分类信息：一共有哪些节点，dataNodes、masterNodes、IngestNodes分别有哪些。

allocators与deciders的工作原理参考：

> ```java
> //AsyncShardFetch.java
> //【添加位置】：对于某个shardId即分片，将“不应该将该分片分配到某个节点”的节点号添加到ignore列表中，将在后面allocate的时候使用
> public void processAllocation(RoutingAllocation allocation) {
> for (String ignoreNode : ignoreNodes) {
> allocation.addIgnoreShardForNode(shardId, ignoreNode);
> }
> }
> //RoutingAllocation.java，将某个shardId不允许使用的nodeId添加到ignoredShardToNodes中：
> public void addIgnoreShardForNode(ShardId shardId, String nodeId) {
> if (ignoredShardToNodes == null) {
> ignoredShardToNodes = new HashMap<>();
> }
> ignoredShardToNodes.computeIfAbsent(shardId, k -> new HashSet<>()).add(nodeId);
> }
> 
> //AllocationDeciders.java
> //【使用位置】：针对当前处理的shardId和nodeId,若在ignoredShardToNodes中找到对应的nodeId，则意味着decider不允许使用这个nodeId：
> public Decision canAllocate(ShardRouting shardRouting, RoutingNode node, RoutingAllocation allocation) {
> if (allocation.shouldIgnoreShardForNode(shardRouting.shardId(), node.nodeId())) {
> return Decision.NO;//Decider不允许这个nodeId为这个shardId服务
> }
> ...
> }
> 
> //RoutingAllocation.java
> public boolean shouldIgnoreShardForNode(ShardId shardId, String nodeId) {
> if (ignoredShardToNodes == null) {
> return false;
> }
> Set<String> nodes = ignoredShardToNodes.get(shardId);
> return nodes != null && nodes.contains(nodeId);
> }
> ```

对于已有索引，需分为两个部分：

* 主分片：allocators只允许把主分片指定在已经拥有该分片完整数据的节点上。
* 副分片：allocators先判断其他节点是否已有该分片的数据的副本（即使不是最新的），若有，则优先把分片分配到其中一个节点。因为副分片一旦分配，就需要从主分片中进行数据同步。

### 元数据的恢复

> 参考11.3 元数据的恢复

对于分布式系统，在节点完全重启时，各节点保存的元数据可能不同，因此需要找到正确的”权威元数据“。由gateway的recovery负责。仅由Master节点负责，基本思路是获取所有从节点的元数据信息，然后根据版本号最大的作为最新元数据，然后将其更新。

### 索引分片时机

有以下几种场景下会触发索引分片： index增删、node增删、 手工reroute、replica数量改变、集群重启。

### 索引健康状态表示

每个索引也有上述三种状态，假设丢失了一个副分片，该分片所属的索引和整个集群变为Yellow状态，其他索引仍为Green。

## 集群节点角色

### 主节点（master node)

> 看起来与ceph中的active mgr功能类似。

主节点负责集群层面的相关操作，管理集群变更。在代码层面，负责了分片的allocate、decide，但不包括路由信息（即某个分片需要放到哪个节点上）。

通过配置 `node.master: true`（默认）使节点具有被选举为 Master 的**资格**。主节点是全局唯一的，将从**有资格**成为Master的节点中进行选举。

主节点也可以作为数据节点，但应该尽可能做少量的工作，因此**生产环境**应尽量分离主节点和数据节点，创建独立主节点的配置：

```shell
node.master: true
node.data: false
```

为了防止数据丢失，每个主节点应该知道有资格成为主节点的数量，默认为1，为避免网络分区时出现多主的情况，配置 `discovery.zen.minimum_master_nodes`原则上最小值应该是：（master_eligible_nodes / 2）+ 1

### 数据节点(data node)

负责保存数据、执行数据相关操作：CRUD、搜索、聚合等。数据节点对CPU、内存、I/O要求较高。

通过配置`node.data: true`（默认）来使一个节点成为数据节点，也可以通过下面的配置创建一个数据节点：

```shell
node.master: false
node.data: true
node.ingest: false
```

### 预处理节点(Ingest node)

这是从5.0版本开始引入的概念。预处理操作允许在索引文档之前，即写入数据之前，通过事先定义好的一系列的processors（处理器）和pipeline（管道），对数据进行某种转换、富化。

processors和pipeline拦截bulk请求（bulk请求可以在单个请求中一次执行多个操作）和index请求，在应用相关操作后将文档传回给index或bulk API。

**默认情况下，所有的节点上都启用ingest功能**。如果想在某个节点上禁用ingest，则可以添加配置`node.ingest: false`，也可以通过下面的配置创建一个仅用于预处理的节点：

```shell
node.master: false
node.data: false
node.ingest: true
```

### 协调节点(Coordinating node)

客户端请求可以发送到集群的任何节点，每个节点都知道任意文档所处的位置，然后转发这些请求，收集数据并返回给客户端，处理客户端请求的节点称为协调节点。

> 猜想：协调节点的引入是基于ES的主从模式的充分利用--若有大量并发读请求，则无需只在主分片上序列化进行，而是可以直接从副分片中读取。
>
> 类似于ceph里的所有monitor都维护了相同的crush map，知道数据应该下发到哪个pg -> osd中。

**协调节点将请求转发给保存数据的数据节点。每个数据节点在本地执行请求，并将结果返回协调节点。**

协调节点收集完数据后，将每个数据节点的结果合并为单个全局结果。对结果收集和排序的过程可能需要很多CPU和内存资源。

**默认情况下，所有节点都具有协调节点的角色对应的功能。**当然也可以通过下面的配置创建一个仅用于协调的节点（单独分离是否有用？有人认为用处不大：[es单独分离协调节点意义在哪](https://elasticsearch.cn/question/8789)，也可能在特定的场景下有用：[阿里云es优化案例](https://developer.aliyun.com/article/777755)）：

```shell
node.master: false
node.data: false
node.ingest: false
```

## 配置管理

全局的配置管理器负责管理所有副本组的配置，节点可以向管理器提出添加、一处副本的请求，每次请求都要附带当前配置版本号，只有这个版本号与配置管理器记录的一致才会被执行。若请求成功，这个新配置将被分配新的版本号。


## 写流程

ES中的每个索引都被拆分为多个分片，并且每个分片都有多个副本。这些副本被称为副本组（replication group）。在添加、删除文档的时候，各个副本必须同步，否则从各个副本读取数据时会有不一致问题。

数据副本模型是主备模式，主分片是所有索引操作的入口，它负责验证索引操作是否有效，一旦主分片接收一个索引操作，主分片的副分片也会接收该操作。

写操作分为三种类型： 索引新文档、更新、删除。需要注意这一点，并考虑写流程中出现异常场景的处理的一致性。（详见10.6 如何保证副分片与主分片一致）

以不同角色节点执行的任务整理流程如下图所示。

![image-20210112100835064](.1.CSP%E8%B0%83%E7%A0%94%EF%BC%9Aelasticsearch.assets/image-20210112100835064.png)

此时这三个节点都是数据节点，同时具有协调节点的功能，node1也是master节点。简要步骤如下：

1. 客户端向node1发送写请求；
2. node1使用文档ID来确定文档处于分片0，通过集群状态元数据中的内容路由表知道分片0位于node3。因此请求被转发到Node3。
3. node3主分片执行写操作，若写成功，则将请求并发转发到node1,node2的副分片上，等待返回结果。当所有副分片都报告成功，node3将向node1（协调节点）返回成功，协调节点再向客户端报告成功。

>  需要注意的是，写入主分片便可以对该分片的数据进行搜索。这也是“近实时搜索”的来源。这样可能造成从主分片和副分片中读取的结果不一致的问题。

>  **协调节点**负责创建索引、转发请求到主分片节点、等待响应、回复客户端。

**写流程中遇到故障**

如果请求在协调节点的路由阶段失败，则会等待集群状态更新，拿到更新后，进行重试，如果再次失败，则仍旧等集群状态更新，直到超时1分钟为止。超时后仍失败则进行整体请求失败处理。

在主分片写入过程中，写入是阻塞的。只有写入成功，才会发起写副本请求。如果主shard写失败，则整个请求被认为处理失败。如果有部分副本写失败，则整个请求被认为处理成功。

参考：

[in-sync set，写故障处理](https://blog.csdn.net/qq_21383435/article/details/109684151)

## 读流程

简单流程如下所示：

1. 客户端向node1下发请求（node1此时不仅是master，也是默认的协调节点，也是数据节点）。
2. node1作为协调节点，使用文档ID来确定文档归属于哪个分片，此处假设为分片0。通过集群状态中的路由表信息可以获取到分片0有三个副本数据，分别保存在这三个节点上，可以将请求发送到任意节点。此处假设发送到node2。
3. node2读取数据，将结果返回给作为协调节点角色的node1，然后由node1返回给客户端。

![image-20210112100244898](.1.CSP%E8%B0%83%E7%A0%94%EF%BC%9Aelasticsearch.assets/image-20210112100244898.png)

### 读失败的处理

尝试从别的分片副本读取。

## 主分片节点流程与故障处理

当主节点异常时，集群会重新选举主节点。当某个主分片异常时，会将副分片提升为主分片。

## 从分片节点流程与故障处理

### 错误检测

分布式系统常见的问题有：网络分区、节点离线等异常。此处同样使用了租约（Lease）机制来保证多个节点之间配置信息的强一致性。（就的主副本和新的主副本同时存在的情况下，旧的主副本可能没有意识到重新分配了一个新的主副本，从而导致一致性问题）

处理方法：主副本定期向其他从副本获取租约。

可能情况：

1. 若主副本节点未在租约期内收到从副本节点的回复，则主副本节点认为从副本节点异常，向配置管理器汇报，将该异常从副本从副本组中移除，同时也将自己降级，不再作为主副本节点。

   >  ==为什么这么做？什么时候选出新的主？==

2. 若从副本节点未在租约期内收到主副本节点的租约请求，则认为主副本异常，将向配置管理器汇报，将主副本从副本组中移除，同时将自己升为新的主。若存在多个从副本，则那个从副本先执行成功，那个从副本就是新的主。

### 节点失效检测

根据节点身份的不同，有两种失效探测器：

* Master节点中，有NodesFaultDetection，简称NodesFD，定期探测加入集群的节点是否活跃；
* 非Master节点中，有MasterFaultDetection，简称MasterFD，定期探测Master节点是否活跃。

默认探测周期：1s，发送ping请求来探测节点是否正常，若失败超过一定次数（默认3次），或收到底层连接模块的节点离线通知时，将处理节点离开事件。

### 主副分片错误检测

主副本定期向其他副本获取租约，采用了两个不同的period来保证了分布式系统中的网络分区、节点离线等异常可能导致的配置不一致问题：

* 若主副本在lease period未收到从副本节点的租约回复，则主副本节点认为从副本节点异常，向配置管理器汇报，将该异常从副本从副本组中移除，同时，它自己也降级，不再作为主副本节点。
* 若从副本在grace period内未收到主副本节点的租约回复，则从副本节点认为主副本异常，向配置管理器汇报，将主副本从副本组中移除，同时将自己提升为新的主。若有多个从副本，则谁先执行成功谁就是新的主。

这样在没有时钟漂移的情况下，只要grace period >= lease period，该租约机制就能保证主副本比任何从副本先感知到租约失效。同时任何一个从副本只有在它租约失效后才会争取做主副本，再选出新的主副本之前，旧的主副本已经降级，不会产生两个主副本。

硬盘损坏、节点离线、配置错误等，都会导致无法在副分片上执行某个操作。此时主分片需汇报这些错误信息。

# 6. 故障切换时对服务的影响

从数据完整性的角度划分，集群健康状态分为三种：

* Green，所有的主分片和副分片都正常运行。
* Yellow，所有的主分片都正常运行，但不是所有的副分片都正常运行。这意味着存在单点故障风险。
* Red，有主分片没能正常运行。

## 索引恢复流程

索引恢复（indices.recovery）是ES数据恢复过程。待恢复的数据是客户端写入成功，但未执行刷盘（flush）的Lucene分段。例如，一方面节点可能因软件故障或掉电等硬件故障异常重启时，写入磁盘的数据先到文件系统的缓冲，未来得及刷盘；另一方面，写入操作在多个分片副本上没有来得及全部执行，副分片需要同步成和主分片完全一致此时需要使用translog进行replay。

### 主分片恢复

从translog中自我恢复，尚未执行flush到磁盘的Lucene分段可以从translog中重建。

主分片恢复过程中允许有新的写请求，这一部分请求也可以通过translog来恢复。

### 副分片恢复

需要从主分片中拉取Lucene分段和translog进行恢复（但是有机会跳过拉取Lucene分段的过程）

副分片恢复的时候允许有新的写请求。也是基于这个需求，从复制Lucene分段的那一刻开始，所恢复的副分片数据不包括新增的内容，而这些内容存在于主分片的translog中，因此副分片需要从主分片节点拉取translog进行重放，以获取新增内容。这就需要主分片节点的translog不被清理。为了防止主分片节点的translog被清理，ES多个版本进行了优化（详见《elsaticsearch源码解析与实践》10.4）。

## 索引恢复触发条件

索引恢复的触发条件包括从快照备份恢复、节点加入和离开、索引的_open操作等。

在索引恢复过程中可以对主副节点占用带宽进行限制，也可以对超时时间、重试时间进行限制。详见第10章。

## 关闭一个节点对集群的影响

举例说明，若有3个主分片，副本数为2，有三个节点，示意图如下所示：

![image-20210112142108943](.1.CSP%E8%B0%83%E7%A0%94%EF%BC%9Aelasticsearch.assets/image-20210112142108943.png)

关闭节点1后，集群中缺失了P1和P2两个主分片，也缺失了MasterNode角色的节点，此时集群的状态为red。集群即将开始故障转移工作，此时将重新选主（此时假设选择Node2为新的MasterNode），然后新的主将立即提升从副本为主副本。此时集群的状态将是yellow。

![image-20210112141918252](.1.CSP%E8%B0%83%E7%A0%94%EF%BC%9Aelasticsearch.assets/image-20210112141918252.png)

Node1重新加入后，如果 `Node 1` 依然拥有着之前的分片，它将尝试去重用它们，同时仅从主分片复制发生了修改的数据文件，就和集群原本的那样。

> 如何实现的？

## kill一个节点对集群的影响

ES进程会捕获SIGTERM信号（kill命令默认信号）进行处理，调用各模块的stop方法，让它们有机会停止服务，安全退出。进程重启期间，如果主节点被关闭，则集群会重新选主，在这期间，集群有一个短暂的无主状态。如果集群中的主节点是单独部署的，则新主当选后，可以跳过gateway和recovery流程，否则新主需要重新分配旧主所持有的分片：提升其他副本为主分片，以及分配新的副分片。

如果数据节点被关闭，则读写请求的TCP连接也会因此关闭，对客户端来说写操作执行失败。但写流程已经到达Engine环节的会正常写完，只是客户端无法感知结果。此时客户端重试，如果使用自动生成ID，则数据内容会重复。

综合来说，滚动升级产生的影响是中断当前写请求，以及主节点重启可能引起的分片分配过程。提升新的主分片一般都比较快，因此对集群的写入可用性影响不大。当索引部分主分片未分配时，使用自动生成ID的情况下，如果持续写入，则客户端对失败重试可能会成功（请求到达已分配成功的主分片），但是会在不同的分片之间产生数据倾斜，倾斜程度视期间数量而定。

## 节点数小于quorum数时集群无法读写

**quorum计算**：`quorum = int（ （primary + number_of_replicas） / 2 ） + 1`

 若集群中的节点数小于quorum，则集群会有一个超时等待时间，默认1分钟超时。

 es提供了一种特殊的处理场景，就是说当number_of_replicas>1时才生效。如果只有1个primary shard，replica=1，此时就2个shard， (1 + 1 / 2) + 1 = 2，要求必须有2个shard是活跃的，但是可能就1个node，此时就1个shard是活跃的，在这种场景下也应该允许集群工作。

# 7. 集群性能（待续）

## 空集群性能

## 70%容量占用时集群性能

## 已用容量对哪些操作有影响

删除操作是进行标记删除，只有在Lucene合并的时候才会触发实际的删除，且删除时需要额外的空间进行合并。若剩余容量小于合并所需空间，则会导致删除失败。

[腾讯云ES集群规划及性能优化实践](https://cloud.tencent.com/developer/article/1696747)

# 8. 故障切换状态

可以分为集群中某个节点自动故障挂掉，和当由于坏盘、维护等故障需主动下线一个节点两部分。

对于主动下线，需要考虑节点的数据迁移。见21.1.3 移除节点。

模拟下线节点：

```shell
#节点上线：
PUT _cluster/settings{＂transient＂ : {＂cluster.routing.allocation.exclude._name＂ : ＂node-1＂}}
#节点上线
PUT _cluster/settings{＂transient＂ : {＂cluster.routing.allocation.exclude._name＂ : ＂＂}}
```

## 查看集群整体恢复状态

```shell
curl -XGET $HOST/_cat/recovery?v
```

详细参数见官网描述：https://www.elastic.co/guide/en/elasticsearch/reference/current/cat-recovery.html

![image-20210107145428481](.1.CSP%E8%B0%83%E7%A0%94%EF%BC%9Aelasticsearch.assets/image-20210107145428481.png)

## 查看某个索引的恢复状态

```shell
curl -XGET $HOST/{index}/_recovery?pretty
```

此处示例：`curl -XGET $HOST/twitter/_recovery?pretty`（仅截取1个shard部分内容：

![image-20210107145943924](.1.CSP%E8%B0%83%E7%A0%94%EF%BC%9Aelasticsearch.assets/image-20210107145943924.png)

# 测试脚本

```shell
#!/bin/bash
HOST="http://192.168.56.111:9200"

function get_nodes(){
    curl -XGET $HOST/_cat/nodes?v
}
#get_nodes
function search(){
    curl -XGET  $HOST/_search
}
#search


function put_documents(){
    curl -XPUT $HOST/customer?pretty
}
#put_documents

function get_indices(){
    curl -XGET $HOST/_cat/indices?v
}
#get_indices

function index_document(){
    echo "-----$FUNCNAME-------"
    curl -XPUT $HOST/$1/_doc/$2?pretty \
        -H "Content-Type:application/json" \
        -d '
        {
            "name": "sherlock holmes"
        }
        '
}
index_document customer 10

function get_document_from_indice_with_id(){
    echo "\n-----$FUNCNAME-------\n"
    curl -XGET $HOST/$1/_doc/$2?pretty
}

function update_document(){
    curl -XPOST $HOST/$1/$2/_update \
        -H "Content-Type:application/json" \
        -d '
        {
            "age": 11
        }
        '
}
#index_document twitter 1
#get_document_from_indice_with_id twitter 1
#update_document twitter 1
#get_document_from_indice_with_id twitter 1

function search_all_documents(){
    echo "\n-----$FUNCNAME-------\n"
    curl -XGET $HOST/$1/_search?q=*&sort=name:asc&pretty
}

#--indice management
function create_indice(){
    echo ""
    echo "\n-----$FUNCNAME-------\n"
    echo ""

    curl -XPUT $HOST/$1 \
    -H "Content-Type:application/json" \
    -d '
    {
        "settings":{
            "index":{
                "number_of_shards": 3,
                "number_of_replicas": 2
            }
        }
    }
    '
}

function get_indice_settings(){
    echo "\n-----$FUNCNAME-------\n"
    curl -XGET $HOST/$1/_settings?pretty
    curl -XGET $HOST/$1/_mappings?pretty
}

function get_indice_stats(){
    curl -XGET $HOST/$1/_stats?pretty
}

function get_indice_segments(){
    curl -XGET $HOST/$1/_segments?pretty
}

function delete_indice(){
    echo "\n-----$FUNCNAME-------\n"
    curl -XDELETE $HOST/$1
}

function head_indice(){
    echo "\n-----$FUNCNAME-------\n"
    curl -XHEAD $HOST/$1
}


function modify_settings(){
    curl -XPUT $HOST/$1/_settings \
    -H "Content-Type: application/json" \
    -d '
    {
        "index":{
            "number_of_replicas":2
        }
    }
    '
}

function get_indice_storagement(){
     curl -XGET $HOST/$1/_shard_stores
}
#get_indice_storagement twitter


#--------------HA-------------------
function get_cluster_recovery(){
    curl -XGET $HOST/_cat/recovery?v
}
#get_cluster_recovery

function get_indice_recovery(){
    curl -XGET $HOST/$1/_recovery?pretty
}
#get_indice_recovery twitter

#curl -s ＂192.168.56.111:9200/_all/_stats?level=shards&pretty＂ |grep sync_id|wc–l
function get_shard_stat(){
    curl -XGET $HOST/_all/_stats?pretty&level=shards

}
#get_shard_stat

function set_log_level(){
    curl -XPUT $HOST/_cluster/settings \
        -H "Content-Type:application/json" \
        -d '
        {
            "transient" : {
                "logger.discovery" : "DEBUG",
                "logger.index.search.slowlog" : "DEBUG"
            }
        }
        '
}
#set_log_level

function get_metadata_state(){
    curl -XGET $HOST/nodes/0/_state/*.st
}
get_metadata_state
function main(){
    #index_document customer 1
    #get_document_from_indice_with_id customer 1
    #search_all_documents customer
    #delete_indice twitter
    #create_indice twitter
    #get_indice_settings twitter
    #get_indice_stats twitter
    get_indice_segments twitter
}
#main
```



# 参考

[Elasticsearch: 权威指南

[官方主页](https://www.elastic.co/guide/cn/elasticsearch/guide/current/index.html)

[官方部署文档](https://www.elastic.co/guide/en/elasticsearch/reference/current/rpm.html)

[es 6.x与7.x配置文件发生变化](https://blog.csdn.net/qq_40384985/article/details/89814501)

[Elasticsearch源码解析与优化实战](https://weread.qq.com/web/reader/f9c32dc07184876ef9cdeb6k8f132430178f14e45fce0f7)

[阿里云：es分布式一致性原理剖析，元数据管理](https://zhuanlan.zhihu.com/p/35294658)

