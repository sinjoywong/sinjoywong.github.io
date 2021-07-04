# 问题收集

1. 谁定义权重?如何定义权重? 如何决定写到哪个osd上? 

   > rule决定一个数据对象有多少个副本, 这些副本存储的限制条件(如3个副本放在不同的机架中)
   >
   > 例如: `step chooseleaf firstn 0 type host ` 隔离域为host级,即不同副本在不同的主机上. 

2. 单AZ->多AZ通过CRUSH MAP进行调整的原理是什么? crushmap从本质上如何影响数据的分布?如何影响故障时的数据迁移? 

   > 本质上就是placement rule的自定义下, 使得数据按照预想中的进行分布.
   >
   > AZ即Available Zone, 高可用区域, 此处可以有不同的定义, 如region, datacenter, host等. 
   >
   > 在当前操作中定义为datacenter, 意味着在数据下发到osd的选择时, 将会分离到多个不同的datacenter中. 至于复制多少分, 则是由副本数决定的(此处使用了2个物理AZ, 通过创建4个datacenter来实现4个虚拟AZ, 设置副本数为4, 可以实现挂掉一个物理AZ,还有双副本的效果)

3. 更改crushmap的名称的作用是什么? 谁在读取crushmap? 什么时候在读取crushmap? 

   > 

4. crushmap中包含什么信息? 对于多个rule, 如何选择? 谁来读取rule? 怎么起到相应的作用?

5. clustermap/ monitor map/ crushmap 对IO流程的影响?

6. 故障域与CRUSH的关系? CRUSH map中如何定义故障域? 发生故障时如何读取? 如何作用? OSD中的数据如何迁移? 谁来负责发起迁移请求? 如何知道已经迁移结束? 

### 服务管理

服的名格式为： ceph-radosgw@rgw. ，如。

```
~]$ systemctl restart ceph-radosgw@rgw.ceph-storage-1
```

# ceph.conf的推送

注意：ceph.conf配置文件一般应该修改管理节点的配置文件，然后由管理节点统一推送到指定的节点。也可以直接修改对应的节点的文件，无论以何种方式修改完成后都需要重启对应的RadosGW服务。通过管理节推送配置文件的命令如下。

```
~]$ ceph-deploy --overwrite-conf config  push ceph-storage-1
```

- –overwrite-conf：表示强制覆盖，如果修改了管理节点的ceph.conf配置文件后，这样管理节点与被推送的节点的配置文件不一致，这时候如果确认没有问题就需要强制覆盖。



# ceph集群报 Monitor clock skew detected 错误问题排查

```shell
# 产生问题的原因，monitor的时钟同步出现时间偏差，ceph默认偏差大于0.05s就会出现这个报警。
$ ceph health detail
HEALTH_WARN clock skew detected on mon.1, mon.2
mon.1 addr 192.168.0.6:6789/0 clock skew 8.37274s > max 0.05s (latency 0.004945s)
mon.2 addr 192.168.0.7:6789/0 clock skew 8.52479s > max 0.05s (latency 0.005965s)

#解决方法：

1:添加配置参数：              
vim /etc/ceph/ceph.conf
[mon.ceph-100-80]
host = ceph-100-80
mon_data = /var/lib/ceph/mon/ceph-ceph-100-80/
mon_addr = 172.16.100.80:6789
# 添加内容如下：
mon clock drift allowed = 2   增加时间误差（不推荐）
mon clock drift warn backoff = 30    
#同步配置文件
ceph-deploy --overwrite-conf admin ceph-100-{80..82}
#重启mon 服务
/etc/init.d/ceph restart mon

2.一般情况下可以直接重启monitor
systemctl restart ceph-mon@bj-tdxy-ccs-128-65（centos 7）
```

## 集群下线机器节点

```shell
# 针对这台机器的所有osd进行以下操作：
ceph osd out {osd.num}   # 标记为out状态，不让该osd继续承载pg
systemctl stop ceph-osd@{osd.num}  # 停止osd相关进程 状态变为down
ceph osd crush remove osd.{osd.num}  # crush map 中删除osd条目
ceph auth del osd.{osd.num}  # 删除 OSD 认证密钥 
ceph osd rm osd.{osd.num}  # 删除osd
# 所有的osd节点下线删除之后：
ceph osd crush remove `hostname -s`  # 将主机条目从crush map中删除
ceph -s # 等待集群变为active+clean状态
```

## osd的Flags

```shell
# osd的Flags
noin   #通常和noout一起用防止OSD up/down跳来跳去    
noout  #MON在过了300秒(mon_osd_down_out_interval)后自动将down掉的OSD标记为out，一旦out数据就会开始迁移，建议在处理故障期间设置该标记，避免数据迁移。
       #(故障处理的第一要则设置osd noout 防止数据迁移。ceph osd set noout ,ceph osd unset noout)
noup   #通常和nodwon一起用解决OSD up/down跳来跳去
nodown #网络问题可能会影响到Ceph进程之间的心跳，有时候OSD进程还在,却被其他OSD一起举报标记为down,导致不必要的损耗，如果确定OSD进程始终正常  
      # 可以设置nodown标记防止OSD被误标记为down.
full  # 如果集群快要满了，你可以预先将其设置为FULL，注意这个设置会停止写操作。
      # (有没有效需要实际测试)
pause  # 这个标记会停止一切客户端的读写，但是集群依旧保持正常运行。
nobackfill
norebalance  # 这个标记通常和上面的nobackfill和下面的norecover一起设置，在操作集群(挂掉OSD或者整个节点)时，如果不希望操作过程中数据发生恢复迁移等，可以设置这个标志，记得操作完后unset掉。
norecover  #也是在操作磁盘时防止数据发生恢复。
noscrub  # ceph集群不做osd清理
nodeep-scrub #有时候在集群恢复时，scrub操作会影响到恢复的性能，和上面的noscrub一起设置来停止scrub。一般不建议打开。
notieragent  # 停止tier引擎查找冷数据并下刷到后端存储。

cpeh osd set {option} # 设置所有osd标志
ceph osd unset {option} # 解除所有osd标志

# 使用下面的命令去修复pg和osd
ceph osd repair ：# 修复一个特定的osd
ceph pg repair # 修复一个特定的pg，可能会影响用户的数据，请谨慎使用。
ceph pg scrub：# 在指定的pg上做处理
ceph deep-scrub # 在指定的pg上做深度清理。
ceph osd set pause #  搬移机房时可以暂时停止读写，等待客户端读写完毕了，就可以关闭集群
```

## Auth的CAPs

```shell
  allow,r,w,x,class-read,class-write,*,profile osd,profile bootstrap-osd
```

## Auth的CAPs

```shell
Creating    #当创建一个池的时候，Ceph会创建一些PG(通俗点说就是在OSD上建目录)，处于创建中的PG就被标记为creating，当创建完之后，那些处于Acting集合
            (ceph pg map 1.0 osdmap e9395 pg 1.0 (1.0) -> up [27,4,10] acting [27,4,10]，对于pg它的三副本会分布在osd.27,osd.4,osd.10上，那么这三
            个OSD上的pg1.0就会发生沟通，确保状态一致)的PG就会进行peer(osd互联)，当peering完成后，也就是这个PG的三副本状态一致后，这个PG就会变成active+clean状态，
            也就意味着客户端可以进行写入操作了。
Peering     peer过程实际上就是让三个保存同一个PG副本的OSD对保存在各自OSD上的对象状态和元数据进行协商的过程，但是呢peer完成并不意味着每个副本都保存着最新的数据。
            直到OSD的副本都完成写操作，Ceph才会通知客户端写操作完成。这确保了Acting集合中至少有一个副本，自最后一次成功的peer后。剩下的不好翻译因为没怎么理解。（对象和元数据的状态达成一致的过程。）
Active      当PG完成了Peer之后，就会成为active状态，这个状态意味着主从OSD的该PG都可以提供读写了。
Clean       这个状态的意思就是主从OSD已经成功peer并且没有滞后的副本。PG的正常副本数满足集群副本数。
Degraded    当客户端向一个主OSD写入一个对象时，主OSD负责向从OSD写剩下的副本， 在主OSD写完后,
            在从OSD向主OSD发送ack之前，这个PG均会处于降级状态。
            而PG处于active+degraded状态是因为一个OSD处于active状态但是这个OSD上的PG并没有保存所有的对象。
            当一个OSDdown了，Ceph会将这个OSD上的PG都标记为降级。当这个挂掉的OSD重新上线之后，OSD们必须重新peer。
            然后，客户端还是可以向一个active+degraded的PG写入的。当OSDdown掉五分钟后，集群会自动将这个OSD标为out,
            然后将缺少的PGremap到其他OSD上进行恢复以保证副本充足，这个五分钟的配置项是mon osd down out interval，默认值为300s。
            PG如果丢了对象，Ceph也会将其标记为降级。
            你可以继续访问没丢的对象，但是不能读写已经丢失的对象了。
            假设有9个OSD，三副本，然后osd.8挂了，在osd.8上的PG都会被标记为降级，
            如果osd.8不再加回到集群那么集群就会自动恢复出那个OSD上的数据，在这个场景中，PG是降级的然后恢复完后就会变成active状态。
Recovering  Ceph设计之初就考虑到了容错性，比如软硬件的错误。当一个OSD挂了，
            它所包含的副本内容将会落后于其他副本，当这个OSD起来之后，
            这个OSD的数据将会更新到当前最新的状态。这段时间，这个OSD上的PG就会被标记为recover。
            而recover是不容忽视的，因为有时候一个小的硬件故障可能会导致多个OSD发生一连串的问题。
            比如，如果一个机架或者机柜的路由挂了，会导致一大批OSD数据滞后，
            每个OSD在故障解决重新上线后都需要进行recover。
            Ceph提供了一些配置项，用来解决客户端请求和数据恢复的请求优先级问题，这些配置参考上面加粗的字体吧。
Backfilling   当一个新的OSD加入到集群后，CRUSH会重新规划PG将其他OSD上的部分PG迁移到这个新增的PG上。
            如果强制要求新OSD接受所有的PG迁入要求会极大的增加该OSD的负载。
            回填这个OSD允许进程在后端执行。一旦回填完成后，新的OSD将会承接IO请求。在回填过程中，你可能会看到如下状态：
            backfill_wait: 表明回填动作被挂起，并没有执行。
            backfill：表明回填动作正在执行。
            backfill_too_full：表明当OSD收到回填请求时，由于OSD已经满了不能再回填PG了。 
imcomplete: 当一个PG不能被回填时，这个PG会被认为是不完整的。
            同样，Ceph提供了一系列的参数来限制回填动作，包括osd_max_backfills：OSD最大回填PG数。
            osd_backfill_full_ratio：当OSD容量达到默认的85%是拒绝回填请求。osd_backfill_retry_interval:字面意思。
Remmapped   当Acting集合里面的PG组合发生变化时，数据从旧的集合迁移到新的集合中。
            这段时间可能比较久，新集合的主OSD在迁移完之前不能响应请求。
            所以新主OSD会要求旧主OSD继续服务指导PG迁移完成。
            一旦数据迁移完成，新主OSD就会生效接受请求。
Stale      Ceph使用心跳来确保主机和进程都在运行，OSD进程如果不能周期性的发送心跳包，
            那么PG就会变成stuck状态。默认情况下，OSD每半秒钟汇报一次PG，up thru,boot, failure statistics等信息，要比心跳包更会频繁一点。
            如果主OSD不能汇报给MON或者其他OSD汇报主OSD挂了，Monitor会将主OSD上的PG标记为stale。当启动集群后，
            直到peer过程完成，PG都会处于stale状态。而当集群运行了一段时间后，如果PG卡在stale状态，
            说明主OSD上的PG挂了或者不能给MON发送信息。
Misplaced   有一些回填的场景：PG被临时映射到一个OSD上。而这种情况实际上不应太久，
            PG可能仍然处于临时位置而不是正确的位置。这种情况下个PG就是misplaced。
            这是因为正确的副本数存在但是有个别副本保存在错误的位置上。

Incomplete  当一个PG被标记为incomplete,说明这个PG内容不完整或者peer失败，
            比如没有一个完整的OSD用来恢复数据了。
scrubbing   清理中，pg正在做不一致性校验。
inconsistent   不一致的，pg的副本出现不一致。比如说对象的大小不一样了。

卡住的pg状态：  
Unclean: 归置组里有些对象的副本数未达到期望次数，它们应该在恢复中；  
Inactive: 归置组不能处理读写请求，因为它们在等着一个持有最新数据的OSD 回到up 状态；  
Stale: 归置组们处于一种未知状态，因为存储它们的OSD 有一阵子没向监视器报告了
（由mon osd report timeout 配置） 
为找出卡住的归置组，执行：
ceph pg dump_stuck [unclean|inactive|stale|undersized|degraded]
```



## crushmap的获取和编译

```shell
1.从任何一个monitor中获取crushmap：
ceph osd getcrushmap -o crushmap.bin
2.反编译使之能够阅读
crushtool -d crushmap.bin -o crushmap.txt
3.修改文件
4.编译文件
crushtool -c crushmap.txt -o newcrushmap
5.将新编译的crushmap注入到原ceph集群中。
ceph osd setcrushmap  -i  newcrushmap
```

## crushmap 解析

```shell
Devices：osd设备
types：bucket类型
buckets：bucket实例
rules: 包含了crush rules来决定存储池中的数据的存放方式。指定了复制和放置的策略，默认包含了默认存储池rbd的一条规则。
其中有一个step take：获取一个bucket名称，开始遍历其树。
```

## 修改集群配置

```shell
启动 Ceph 存储集群时，各守护进程都从同一个配置文件（即默认的 ceph.conf ）里查找它自己的配置。  
ceph.conf 中可配置参数很多，有时我们需要根据实际环境对某些参数进行修改。  
修改的方式分为两种：  
直接修改 ceph.conf 配置文件中的参数值，修改完后需要重启 Ceph 进程才能生效。   
或在运行中动态地进行参数调整，无需重启进程。

查看运行时配置  
ceph daemon {daemon-type}.{id} config show | less  
ceph daemon osd.0 config show | less  
Ceph 集群提供两种方式的调整，使用 tell 的方式和 daemon 设置的方式。  
但是集群重启之后恢复到默认的配置，要想永久的实现需要配置ceph.conf文件  
tell 方式设置  
下面是使用 tell 命令的修改方法：（此方法需要绑定monitor） 
ceph tell {daemon-type}.{id or *} injectargs --{name} {value} [--{name} {value}]  
ceph tell osd.0 injectargs --debug-osd 20 --debug-ms 1  
在 ceph.conf 文件里配置时用空格分隔关键词；但在命令行使用的时候要用下划线或连字符（ _ 或 - ）分隔，例如 debug osd 变成 debug-osd 。  
daemon 方式设置  
获取当前值：  
ceph daemon osd.1 config get mon_osd_full_ratio  
修改配置值：  
ceph daemon osd.1 config set mon_osd_full_ratio 0.97  
查看当前配置值：  
ceph daemon osd.1 config get mon_osd_full_ratio
调节日志：  
ceph tell osd.0 injectargs --debug-osd 0/5  （日志级别/内存日志级别）
ceph daemon osd.0 config set debug_osd 0/5
```

## ceph 出现osd down的处理

```shell
ceph-disk activate all 将本节点下的osd进行down的进行重启。
```

## Bucket和Object的访问控制权限(ACL)类型

```shell
Bucket目前有以下三种访问权限：public-read-write，public-read和private，它们的含义如下:  
public-read-write：任何人（包括匿名访问）都可以对该Bucket中的Object进行List、Put和Delete操作。   
public-read：任何人（包括匿名访问）只能对该Bucket中的Object进行List操作，而不能进行Put和Delete操作。      
注意:对Bucket有读操作不表示对Object有读操作。    
private：只有该Bucket的创建者拥有所有权限。其他人没有访问权限。
```

## Object目前有以下两种访问权限：

```shell
public-read和private，它们的含义如下：   
public-read：任何人（包括匿名访问）都可以对该Object进行读操作（即下载）
private：只有Object的拥有者可以对该Object进行操作。
```

## 存储空间(Bucket)有公开读权限，匿名用户可以访问该存储空间（Bucket）下的文件（Object）

```shell
对Bucket有读操作权限并不表示对Object有读操作权限，Bucket的读操作权限只包含对Bucket下的Object有List权限，如果想让匿名用户可以访问某一个Object,还需要将此Object的权限设置为“公开”。
```

## ceph-deploy搭建ceph集群

```shell
1.mkdir my-cluster ，   cd my-cluster  
2.如果安装的过程中出现问题：  
ceph-deploy purgedata {ceph-node} [{ceph-node}]  
ceph-deploy forgetkeys  
ceph-deploy purge {ceph-node} [{ceph-node}] 清除安装包  
3.创建monitor  
ceph-deploy new node1  
会生成一个Ceph 配置文件、一个monitor 密钥环和一个日志文件。  
4.安装ceph  
ceph-deploy install node1 node2 node3  
5.初始化monitor并收集秘钥  
ceph-deploy mon create-initial
完成上述操作后，当前目录里应该会出现这些密钥环：  
{cluster-name}.client.admin.keyring  
{cluster-name}.bootstrap-osd.keyring  
{cluster-name}.bootstrap-mds.keyring  
{cluster-name}.bootstrap-rgw.keyring  
6.1 把目录用于osd的守护进程  
ssh node2  
sudo mkdir /var/local/osd0  
exit  
ssh node3  
sudo mkdir /var/local/osd1  
exit  
准备osd：  
ceph-deploy osd prepare node2:/var/local/osd0 node3:/var/local/osd1  
激活osd：  
ceph-deploy osd activate node2:/var/local/osd0 node3:/var/local/osd1  
把配置文件和admin 密钥拷贝到管理节点和Ceph 节点  
ceph-deploy admin admin-node node1 node2 node3  
sudo chmod +r /etc/ceph/ceph.client.admin.keyring  
6.2 将整块磁盘作为osd的守护进程  
ceph-deploy osd (--zap-disk) create test-98:/dev/sdb  test-98:/dev/sdc  test-95:/dev/sdb test-95:/dev/sdc   test-55:/dev/sdb  test-55:/dev/sdc 
--zap-disk 擦除分区    
7.分发key到osd节点上
ceph-deploy admin node1 node2 node3   
8.ceph health
```

## 添加osd

```shell
1.ceph-deploy添加osd  
ssh node1  
sudo mkdir /var/local/osd2  
exit  
ceph-deploy osd prepare node1:/var/local/osd2  
ceph-deploy osd activate node1:/var/local/osd2  
```

## 添加monitor

```shell
ceph-deploy mon add node2 node3  
新增Monitor 后，Ceph 会自动开始同步并形成法定人数。你可以用下面的命令检查法定人数  
状态：  
ceph quorum_status --format json-pretty
```

## 只支持手动删除osd

```shell
ceph osd out {osd number}
systemctl stop ceph-osd@{osd number}
ceph osd crush remove osd.{osd number}
ceph auth del osd.{osd number}
ceph osd rm osd.{osd number}

最后删除host桶
ceph osd crush remove {hostname}
```

## ceph配置

```shell
运行时更改配置文件的内容：  
ceph tell {daemon-type}.{id or *} injectargs --{name}
{value} [--{name} {value}]  
ceph tell osd.0 injectargs --debug-osd 20 --debug-ms 1  
ceph daemon {daemon-type}.{id} config show | less
ceph daemon osd.0 config show | less
```



## 桶类型

```shell
Ceph 支持四种桶，每种都是性能和组织简易间的折衷。如果你不确定用哪种桶，我们建
议straw ，关于桶类型的详细讨论见CRUSH - 可控、可伸缩、分布式地归置多副本数据，
特别是Section 3.4 。  
支持的桶类型有：  
1. Uniform: 这种桶用完全相同的权重汇聚设备。例如，公司采购或淘汰硬件时，一般都
有相同的物理配置（如批发）。当存储设备权重都相同时，你可以用uniform 桶类
型，它允许CRUSH 按常数把副本映射到uniform 桶。权重不统一时，你应该采用其
它算法。  
2. List: 这种桶把它们的内容汇聚为链表。它基于RUSH P 算法，一个列表就是一个自然、
直观的扩张集群：对象会按一定概率被重定位到最新的设备、或者像从前一样仍保留
在较老的设备上。结果是优化了新条目加入桶时的数据迁移。然而，如果从链表的中
间或末尾删除了一些条目，将会导致大量没必要的挪动。所以这种桶适合永不或极少
缩减的场景。  
3. Tree: 它用一种二进制搜索树，在桶包含大量条目时比list 桶更高效。它基
于RUSH R 算法， tree 桶把归置时间减少到了O(log n) ，这使得它们更适合管理更大
规模的设备或嵌套桶。  
4. Straw: list 和tree 桶用分而治之策略，给特定条目一定优先级（如位于链表开头的条
目）、或避开对整个子树上所有条目的考虑。这样提升了副本归置进程的性能，但是
也导致了重新组织时的次优结果，如增加、拆除、或重设某条目的权重。straw 桶类
型允许所有条目模拟拉稻草的过程公平地相互“竞争”副本归置。  
```

## crushMap rule

```shell
rule ssd {  
    ruleset 0   规则代号  
    type replicated   类型为副本模式，另外一种模式为纠删码EC   
    min_size 1   如果一个归置组副本数小于此数， CRUSH 将不应用此规则。  
    max_size 10  如果一个归置组副本数大于此数， CRUSH 将不应用此规则。  
    step take ssd  选取桶名为入口并迭代到树底。  
    step chooseleaf firstn 0 type rack  选取指定类型桶的数量，这个数字通常是存储池的副本数（即pool
size ）。选择{bucket-type} 类型的一堆桶，并从各桶的子树里选择一个叶
子节点。集合内桶的数量通常是存储池的副本数（即pool size ）。  
    step emit  输出当前值并清空堆栈。通常用于规则末尾，也适用于相同规则应用到不
同树的情况。  
}

1.从任何一个monitor中获取crushmap：
ceph osd getcrushmap -o crushmap.bin
2.反编译使之能够阅读
crushtool -d crushmap.bin -o crushmap.txt
3.修改文件
4.编译文件
crushtool -c crushmap.txt -o newcrushmap
5.将新编译的crushmap注入到原ceph集群中。
ceph osd setcrushmap  -i  newcrushmap
```

## 集群运行图

```shell
Ceph 依赖于Ceph 客户端和OSD ，因为它们知道集群的拓扑，这个拓扑由5 张图共同描述，
统称为“集群运行图”：  
1. Montior Map： 包含集群的fsid 、位置、名字、地址和端口，也包括当前版本、创
建时间、最近修改时间。要查看监视器图，用ceph mondump 命令。  
2. OSD Map： 包含集群fsid 、创建时间、最近修改时间、存储池列表、副本数量、
归置组数量、OSD 列表及其状态（如up 、in ）。要查看OSD 运行图，
用ceph osd dump 命令。  
3. PG Map：：** 包含归置组版本、其时间戳、最新的OSD 运行图版本、占满率、以及
各归置组详情，像归置组ID 、up set 、acting set 、PG 状态
（如active+clean ），和各存储池的数据使用情况统计。  
4. CRUSH Map：：** 包含存储设备列表、故障域树状结构（如设备、主机、机架、行、
房间、等等）、和存储数据时如何利用此树状结构的规则。要查看CRUSH 规则，执
行ceph osd getcrushmap -o {filename} 命令；然后用crushtool -
d {comp-crushmap-filename} -o{decomp-crushmap-filename} 反
编译；然后就可以用cat 或编辑器查看了。   
5. MDS Map： 包含当前MDS 图的版本、创建时间、最近修改时间，还包含了存储元数
据的存储池、元数据服务器列表、还有哪些元数据服务器是up 且in 的。要查看
MDS 图，执行ceph mds dump 。
```

## 物理机关机维护

```shell
ceph osd set noout  
ceph osd set nobackfill  
ceph osd set norecover
```

## 开启debug模式

```shell
1.ceph.conf文件中进行配置  
2.在线修改：  
ceph tell osd.{osd number} injectargs '--debug-osd 0/5'  
ceph --admin-daemon /var/run/ceph/ceph-osd.{osd number}.asok config set debug_osd 0/5  
ceph --admin-daemon /var/run/ceph/ceph-osd.{osd number}.asok config show |grep -i debug_osd  
```

## config文件推送

```shell
请不要直接修改某个节点的/etc/ceph/ceph.conf文件，而是在部署机下修改ceph.conf，
采用推送的方式更加方便安全，修改完成之后，使用下面的命名将conf文件推送到各个节点上：
ceph-deploy --overwrite-conf config push ceph-1 ceph-2 ceph-3  
此时需要修改各个节点的monitor服务：
systemctl restart ceph-mon@{hostname}.service
```

## 线上环境的ceph调优

```shell
ceph osd set nodeep-scrub
```

## 关机

```shell
ceph osd set noout
stop osd
stop mon
shutdown
```

## 开机

```shell
boot
start mon
start osd
all osd up -> ceph osd unset noout
```

## 查看线上环境网卡带宽

```shell
ethtool eth2,查看speed这一项
```

## 关于前端机CPU,网卡的监控

```shell
top. dstat查看网卡信息 
systemctl restart ceph-radosgw@radosgw.gateway 
查看Linux内核信息(内核版本)：uname -a 
dig www.baidu.com +trace追踪路由解析 
输入nslookup命令后回车，将进入DNS解析查询界面。

radosgw-admin列出所有用户 
radosgw-admin metadata list user 
radosgw-admin metadata list bucket
```

### 数据清除

```shell
清除安装包 
ceph-deploy purge ceph1 ceph2 ceph3

清除配置信息 
ceph-deploy purgedata ceph1 ceph2 ceph3 
ceph-deploy forgetkeys

每个节点删除残留的配置文件 
rm -rf /var/lib/ceph/osd/* 
rm -rf /var/lib/ceph/mon/* 
rm -rf /var/lib/ceph/mds/* 
rm -rf /var/lib/ceph/bootstrap-mds/* 
rm -rf /var/lib/ceph/bootstrap-osd/* 
rm -rf /var/lib/ceph/bootstrap-mon/* 
rm -rf /var/lib/ceph/tmp/* 
rm -rf /etc/ceph/* 
rm -rf /var/run/ceph/*

查看pool的详细状态信息 
ceph osd pool ls detail
```

## radosgw中的pool

```shell
rbd 
.rgw.root 包含realm，zonegroup和zone 
default.rgw.control 在RGW上电时，在control pool创建若干个对象用于watch-notify，主要作用为当一个zone对应多个RGW，且cache使能时， 保证数据的一致性，其基本原理为利用librados提供的对象watch-notify功能，当有数据更新时，通知其他RGW刷新cache， 后面会有文档专门描述RGW cache。 
default.rgw.data.root 
包含bucekt和bucket元数据，bucket创建了两个对象一个：一个是< bucket_name > 另一个是.bucket.meta.< bucket_name >.< marker > 这个marker是创建bucket中生成的。 同时用户创建的buckets在.rgw.buckets.index都对应一个object对象，其命名是格式：.dir.< marker > 
default.rgw.gc RGW中大文件数据一般在后台删除，该pool用于记录那些待删除的文件对象 
default.rgw.log 各种log信息 
default.rgw.users.uid 保存用户信息，和用户下的bucket信息 
default.rgw.users.keys 包含注册用户的access_key 
default.rgw.users.swift 包含注册的子用户(用于swift) 
default.rgw.buckets.index 包含bucket信息，和default.rgw.data.root对应 
default.rgw.buckets.data 包含每个bucket目录下的object
```

## 磁盘使用

```shell
ceph osd df tree 查看各个osd磁盘使用情况
```



```shell
如果在某些地方碰到麻烦，想从头再来，可以用下列命令清除配置：

ceph-deploy purgedata {ceph-node} [{ceph-node}] //清除节点所有的数据在/var/lib/ceph

ceph-deploy forgetkeys  //删除密钥

用下列命令可以连 Ceph 安装包一起清除：

ceph-deploy purge {ceph-node} [{ceph-node}]

新增监视器到 Ceph 集群。

ceph-deploy mon add {ceph-node}

要定位对象，只需要对象名和存储池名字即可，例如：

ceph osd map {poolname} {object-name}

ceph -v //查看ceph的版本

ceph -s //查看集群的状态

ceph -w //监控集群的实时更改

ceph health //查看集群是否健康

ceph health detail //先显示集群是否健康的详细信息

ceph time-sync-status //查看mon节点的时间同步情况

ceph osd df //查看osd的使用信息

ceph osd dump //osd的map信息

ceph osd find osd.o//查看osd.0节点ip和主机名

ceph osd tree //查看osd的状态和编号以及分布情况

ceph osd  metadata 0//查看osd元数据的详细信息

/var/run/ceph //存放所有的sock

运行状态导出集群monmap（集群正常时确认集群monIP和进程名）

ceph mon getmap -o /mnt/monmap

ceph mon dump //查看mon的信息

查看当前集群主mon

# ceph quorum_status -f json-pretty|grep 'leader'

ceph mon stat //查看mon状态

ceph osd stat //查看osd的状态

ceph osd dump //查看osd的map信息

ceph osd pool ls //查看集群中的存储池名称

ceph osd pool set mytest size 3 //可以修改mytest池的副本数为3

ceph osd pool ls detail //查看池的的详细信息

ceph osd pool stats //查看池的IO情况

ceph pg dump  //查看pg的详细信息

ceph pg map 1.6c //查看单个pg和osd的映射信息

ceph pg {pg-id} query //获取pg的详细信息

 

1.修改ceph配置文件的方式有三种通过修改配置文件重启的方法是永久的临时的方法有tell可以在任意的节点去修改，还有一种就是登录到需要修改的机器用set修改

ceph --show-config //查看默认配置

3.查看进程的生效配置信息：

ls /var/run/ceph/（下面是ceph的套接字文件socket）可以从套接字文件中获取生效的配置信息，也可以通过进程获取配置信息

ceph daemon osd.0 config show         

ceph daemon /var/run/ceph/ceph-mon.sds1.asok config show          

修改进程的配置：（临时生效）

1、任何存储节点修改用tell

ceph tell osd.0 injectargs '--debug-osd 0/5'

ceph tell mon.* injectargs '--osd_recovery_max_active 5'

2、需要到该进程节点上面修改

ceph osd find osd.0 //查到osd.0的ip后登录到该机器完后修改

Ceph daemon osd.0 config get debug_ms //查看日志级别

Ceph daemon osd.0 config Set debug_ms 5 //修改日志级别为5

ceph daemon osd.0 config set debug_osd 0/5
```





```shell
ceph是分布式存储，其中对于数据的存储规则是一个重点和难点。比如每个数据块的数据备份是3份，3份数据是怎么分布的？ceph的crush 就是解决数据分布规则的问题。

    应用端直接使用的是pool，pool是由存储的基本单位pg组成，pg分布在磁盘逻辑单元osd上，osd一般是对应一块物理硬盘，osd分布在物理主机host，host分布在机框chassis中，机框chassis分布在机架rack中，几家rack分布在机柜阵列raw中，后面可以继续归属，->pdupod->room->datacenter 。其中host/chasis/rack 等等在ceph属于中叫做bucket（桶），各个级别的bucket是默认的，当有特殊需求的时候，可以自定义新的级别bucket，比如新定义一个bucket级别host-SSD ，专门将SSD盘的OSD归入这个bucket中。

    OSD归类完成之后，数据的分布需要使用规则，比如回到上面的问题，每个数据块的数据备份是3份，3份数据是怎么分布的？首先，应用端使用pool，假定3个基本数据单元需要存放到3个pg中，这个时候就需要确定使用哪3个pg，需要遵从rule，这个rule 也是crush定义的。

    下面以新建一个容纳ssd磁盘的bucket，以及相对应的rule为例，简单罗列一下crush的相关命令：

创建ssd root

ceph osd crush add-bucket ssd root

//创建一个新的桶叫ssd ，级别是root最高级

创建hostgroup

ceph osd crush add-bucket ssd-hosts chasis

//创建一个新的桶叫ssd-hosts ，级别是机框chasis

ceph osd crush move ssd-hosts root=ssd

//将ssd-hosts归入ssd

创建host

ceph osd crush add-bucket ssd-m1 host

//创建一个新的桶叫ssd-m1 ，级别是主机host

ceph osd crush add-bucket ssd-compute host

//创建一个新的桶叫ssd-compute ，级别是host

ceph osd crush move ssd-m1 chasis=ssd-hosts

//将ssd-m1归入ssd-hosts

ceph osd crush move ssd-compute chasis=ssd-hosts

//将ssd-compute归入ssd-hosts

移动osd

ceph osd crush set osd.0 1.0 host=ssd-m1

//将osd.0 移动到主机host=ssd-m1 中

ceph osd crush set osd.1 1.0 host=ssd-compute

//将osd.1 移动到主机host=ssd-compute 中

创建crush rule

ceph osd crush rule create-simple ssd ssd host firstn

//创建crush rule，rule名称是ssd，root=ssd，tpye=host，mode=firstn 

显示rule规则

ceph osd crush rule dump
[
    {
       "rule_id": 0,
        "rule_name": "replicated_ruleset",
        "ruleset": 0,
        "type": 1,
        "min_size": 1,
        "max_size": 10,
        "steps": [
            {
                "op": "take",
                "item": -1,
                "item_name": "default"
            },
            {
                "op": "chooseleaf_firstn",
                "num": 0,
                "type": "host"
            },
            {
                "op": "emit"
            }
        ]
    },
    {
        "rule_id": 1,
        "rule_name": "ssd",
        "ruleset": 1,
        "type": 1,
        "min_size": 1,
        "max_size": 10,
        "steps": [
            {
                "op": "take",
                "item": -9,
                "item_name": "ssd"
            },
            {
                "op": "chooseleaf_firstn",
                "num": 0,
                "type": "host"
            },
            {
                "op": "emit"
            }
        ]
    }
]

    可以看到有2个规则，1个是默认规则，1个是规则ssd 。


创建pool以及使用rule

规则有了之后，接下来就是使用了。在创建pool的时候，可以指定rule。

ceph osd pool create ssd 128 128

ceph osd pool set ssd crush_ruleset 1  //这个ruleid 1 就是上面新创建的规则
```



# 参考

ceph命令手册: http://docs.ceph.org.cn/man/8/ceph/

crush详解: https://zhuanlan.zhihu.com/p/63725901

crush算法的原理与实现:rule的定义与执行流程 https://zhuanlan.zhihu.com/p/58888246