## 问题收集

1. 什么是storage class
2. 哪些需要storage class
3. 如何使用storage class
4. storage class如何实现

5. 测试 

# aws s3 存储类

>  [aws s3： 存储类简介](https://amazonaws-china.com/cn/s3/storage-classes/)

>  [AWS S3：智能分层、S3标准IA、S3单区IA、S3 Glacier、S3 Glacier Archive](https://amazonaws-china.com/cn/s3/faqs/)

| 存储类                      | 应用场景                                                     | 性能                                                         | 如何使用                                                     | 其他                                                         | AZ   |
| --------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------ | ------------------------------------------------------------ | ------------------------------------------------------------ | ---- |
| S3 Standard                 |                                                              |                                                              |                                                              | 默认存储类                                                   | >=3  |
| **S3 Standard-IA**          | S3 标准 – IA 适用于不常访问但在需要时要求快速访问的数据。<br />S3 标准 – IA 非常适合长期文件存储、较旧的同步和共享存储以及其他老化数据。 | S3 标准 – IA 可提供与 S3 标准 和 S3 单区 – IA 存储类的性能相同的性能。 | 1. 通过在 x-amz-storage-class 标头中指定 STANDARD_IA，可以通过 PUT 操作直接将数据放入 S3 标准 – IA。<br />2. 设置生命周期策略，将对象从 S3 标准转移到 S3 标准 – IA 存储类。 | 使用 S3 标准 – IA 时，您应该会具有与使用 S3 标准存储类时相同的延迟和吞吐量性能。<br />2.对象最小大小：128KB。<br />3.最小存储时间：30天。 | >=3  |
| **S3 Intelligent-Tiering**  | 用于访问模式未知或难以了解不断变化的访问模式的数据。<br />它是第一个通过在访问模式发生变化时在两个访问层之间移动对象来自动节约成本的云存储类。<br />一个层针对频繁访问进行优化，另一个较低成本的层为不频繁访问而设计。<br />上传或转换到 S3 智能分层的对象将自动存储在频繁访问层中。<br />S3 智能分层的工作方式是监控访问模式，然后将连续 30 天未访问的对象移动到==不频繁访问层==。<br />如果稍后访问对象，S3 智能分层会将该对象移回==频繁访问层==。<br />这意味着存储在 S3 智能分层中的所有对象在需要时始终可用。 | S3 智能分层可提供与 S3 标准存储相同的性能。                  | 1. 指定 x-amz-存储类标头中的智能分层来直接放入 S3 智能分层中：<br />2.设置生命周期策略以将对象从 S3 标准或 S3 标准 – IA 转换到 S3 智能分层。 | 1. 延迟和吞吐量性能将与 S3 标准相同。<br />2. 对象的最小大小：128KB（更小的对象也可以存储，但是会被分到频繁访问层中。）<br />3.最小存储时间：30天。 | >=3  |
| **S3 One Zone-IA**          | 让客户可以选择将对象存储在单个可用区中。<br />S3 单区 – IA 存储以冗余方式将数据存储在==单个可用区==内，这种存储的成本比地理上冗余的 S3 标准 – IA 存储的成本低 20%（而后者是以冗余方式将数据存储在多个地理上分离的可用区内）<br /><br />用于访问频率较低的存储，如备份副本、灾难恢复副本或其他易于重新创建的数据。 | S3 单区 – IA 存储类可提供与 S3 标准和 S3 标准 – 不频繁访问存储类的性能相同的性能。 |                                                              | 1. S3 单区 – IA 存储类可提供与 S3 标准和 S3 标准 – 不频繁访问存储类的性能相同的性能<br />2. 对象的最小大小：128KB；<br />3. 最小存储时间：30天 | 1    |
| **S3 Glacier**              | 保持低廉成本，同时满足各种数据检索需求，Amazon S3 Glacier 提供三种访问存档的选项，各自的检索时间从数分钟到数小时不等。 |                                                              | 1. 直接通过S3 API将对象逐个上传到S3 Glacier存储类<br />2. 可以根据对象的使用年限，利用[生命周期规则](https://docs.aws.amazon.com/AmazonS3/latest/dev/object-lifecycle-mgmt.html)自动将 Amazon S3 对象集存档到 S3 Glacier<br />3. 要检索存储在 S3 Glacier 中的 Amazon S3 数据，需要通过 Amazon S3 API 或管理控制台启动检索任务。检索任务完成后，可以通过 Amazon S3 GET 对象请求来访问这些数据。<br />更多参考：[对象存档](https://docs.aws.amazon.com/AmazonS3/latest/dev/object-archival.html) | 2. 对象的最小大小：40KB；<br />3. 最小存储时间：90天         | >=3  |
| **S3 Glacier Deep Archive** | 用于长期保存每年访问一两次的数据提供了安全和持久的对象存储。S3 Glacier Deep Archive 的云存储成本最低 |                                                              |                                                              | 2. 对象的最小大小：40KB；<br />3. 最小存储时间：180天        | >=3  |
| RSS                         | 经常访问，且不重要的数据。                                   |                                                              |                                                              | 没有对象大小和存储时间的要求                                 | >=3  |

# 可用性比较

每个可用区均使用冗余电源和联网。在 AWS 区域内，可用区位于不同的冲积平原和地震断裂带，并且在地理位置上是分离的，以避免受到火灾的影响。 

**S3 标准**和 **S3 标准 – 不频繁访问**存储类通过以冗余方式将数据存储在多个可用区来避免受到这类灾难的影响。

**S3 单区 – IA** 可以保护用户免受可用区内设备故障的影响，但它无法保护用户免受因可用区毁坏而造成的 **S3 单区 – IA** 中存储的数据丢失。



# Ceph Storage Class

N版ceph

搜索关键词：RGW_ATTR_STORAGE_CLASS

> 这是storage class的功能https://docs.ceph.com/en/latest/radosgw/placement/#using-storage-classes，你可以参考minghaocong的写法，搞清楚怎么配、怎么用、怎么实现，并且把这三点通过wiki或ppt对大家说清楚
>
> 这个代码量可能不小，你先规划一下
> 这个要那社区的14.X版本才有，建议在vstart.sh里进行实验
>
> 升级N版  storage class  调研 通过PPT说清楚.

# 基本概念：

## pool 

## placement rule

## zone

`radosgw-admin -c $CONF zone get`可以获得当前的zone配置。

如下图所示，展示了有一个`placement_pools`的k-v项，其中包括了一对k-v，key为"default-placement"，表示该placement的名称，value指定了`index_pool`，`storage_classes`与对应的`data_pool`，以及一些其他pool（如分片上传的non-ec pool）：

![image-20210120151444847](.1.CSP%E8%B0%83%E7%A0%94%EF%BC%9AStorage%20Class.assets/image-20210120151444847.png)

## zonegroup

![image-20210120155621449](.1.CSP%E8%B0%83%E7%A0%94%EF%BC%9AStorage%20Class.assets/image-20210120155621449.png)

## s3 bucket的lifecycle



## Placement Target

>  在Jewel版本新增

Placement target表示哪个桶与哪个Pool相关联。 一个桶的placement target只有在创建的时候指定, 并且不能被修改(原因?).

命令`radosgw-admin bucket stats`可以显示其`placement_rule`.

zonegroup配置包含了一个placement target的列表, 其初始的placement target为 `default-placement`. zone配置功能之后将每个zonegroup placement target名称映射到其本地存储介质中. 

这个placement infomation包含了bucket index的`index_pool`名称,

 未完成的分片上传的元数据池`data_extra_pool`,

以及每个storage class一个的`data_pool`.

![image-20210120152106372](.1.CSP%E8%B0%83%E7%A0%94%EF%BC%9AStorage%20Class.assets/image-20210120152106372.png)

![image-20210120152054503](.1.CSP%E8%B0%83%E7%A0%94%EF%BC%9AStorage%20Class.assets/image-20210120152054503.png)



# storage classes

> N 版本新增

Storage class用于自定义Object data的存储位置(placement). S3 Bucket Lifecycle规则可以自动地在storage classes中转换。

storage class是在placement target中定义的术语. 每个zonegroup placement target都列出了可用的storage class, 其初始默认的名称为`STANDARD`.

zone的配置负责提供每个zonegroup的storage class的pool名称 `data_pool`.

# zone group/zone配置

查询zonegroup配置:

```shell
$ radosgw-admin zonegroup get
{
    "id": "ab01123f-e0df-4f29-9d71-b44888d67cd5",
    "name": "default",
    "api_name": "default",
    ...
    "placement_targets": [
        {
            "name": "default-placement",
            "tags": [],
            "storage_classes": [
                "STANDARD"
            ]
        }
    ],
    "default_placement": "default-placement",
    ...
}
```

查看zone placement 配置:

```shell
$ radosgw-admin zone get
{
    "id": "557cdcee-3aae-4e9e-85c7-2f86f5eddb1f",
    "name": "default",
    "domain_root": "default.rgw.meta:root",
    ...
    "placement_pools": [
        {
            "key": "default-placement",
            "val": {
                "index_pool": "default.rgw.buckets.index",
                "storage_classes": {
                    "STANDARD": {
                        "data_pool": "default.rgw.buckets.data"
                    }
                },
                "data_extra_pool": "default.rgw.buckets.non-ec",
                "index_type": 0
            }
        }
    ],
    ...
} 
```





**[x-amz-storage-class](https://docs.aws.amazon.com/AmazonS3/latest/API/API_PutObject.html#API_PutObject_RequestSyntax)**

> By default, Amazon S3 uses the STANDARD Storage Class to store newly created objects. The STANDARD storage class provides high durability and high availability. Depending on performance needs, you can specify a different Storage Class. Amazon S3 on Outposts only uses the OUTPOSTS Storage Class. For more information, see [Storage Classes](https://docs.aws.amazon.com/AmazonS3/latest/dev/storage-class-intro.html) in the *Amazon S3 Service Developer Guide* .
>
> Possible values:
>
> - `STANDARD`
> - `REDUCED_REDUNDANCY`
> - `STANDARD_IA`
> - `ONEZONE_IA`
> - `INTELLIGENT_TIERING`
> - `GLACIER`
> - `DEEP_ARCHIVE`
> - `OUTPOSTS`



1. 基于Storage Class，直接关联object data

在RGW N版，提供了storage class的功能。基于storage class完成不同object的不同存储策略。

> 添加storage class，我们添加在default-placement中：



```dart
# radosgw-admin zonegroup placement add --rgw-zonegroup pd --placement-id default-placement --storage-class COLD
    [
        {
            "key": "default-placement",
            "val": {
                "name": "default-placement",
                "tags": [],
                "storage_classes": [
                    "COLD",
                    "STANDARD"
                ]
            }
        },
        {
            "key": "temp",
            "val": {
                "name": "temp",
                "tags": [
                    "Tag"
                ],
                "storage_classes": [
                    "STANDARD"
                ]
            }
        }
    ]
```

> 设置storage class 的data pool，并且设置压缩策略：



```kotlin
# radosgw-admin zone placement add --rgw-zone upc --placement-id default-placement --storage-class COLD --data-pool upc.rgw.test.data --compression zlib    
    ...
    "placement_pools": [
      {
        "key": "default-placement",
        "val": {
          "index_pool": "upc.rgw.buckets.index",
          "storage_classes": {
            "COLD": {
              "data_pool": "upc.rgw.test.data",
              "compression_type": "zlib"
            },
            "STANDARD": {
              "data_pool": "upc.rgw.buckets.data"
            }
          },
          "data_extra_pool": "upc.rgw.buckets.non-ec",
          "index_type": 0
        }
      },
    ...

#radosgw-admin period update --commit
```

**测试**

使用storage class，有两种方式：

1. 编辑用户的元数据：

"default_storage_class": ""

1. 添加http头部：

   `#s3cmd --storage-class=COLD put cold_data s3://second`



```css
[root@luminous1 ~]# rados -p upc.rgw.test.data ls
1c60b268-0a5d-4718-ad02-e4b5bce824bf.136021.4__shadow_.6sYlWrtESVuQNVMTsCNSToM_MB293Ah_0
[root@luminous1 ~]# rados -p upc.rgw.buckets.data ls
1c60b268-0a5d-4718-ad02-e4b5bce824bf.136021.4_cold_data
```

发现其头部对象仍然在"STANDARD" class中，分片对象在对应"COLD" 的 data pool 中；但这里的头部对象并不存储数据。

```bash
# radosgw-admin bucket stats --bucket=second

"usage": {
    "rgw.main": {
        "size": 10485760,
        "size_actual": 10485760,
        "size_utilized": 10212,
        "size_kb": 10240,
        "size_kb_actual": 10240,
        "size_kb_utilized": 10,
        "num_objects": 1
    }
},

其中：size_utilized/size_kb_utilized 为实际占用的磁盘空间，可以看出压缩后的大小为10KB。原始大小"size": 10MB。
```

查看一下其头部对象的xattr:

```css
# rados -p upc.rgw.buckets.data listxattr 1c60b268-0a5d-4718-ad02-e4b5bce824bf.136021.4_cold_data
user.rgw.acl
user.rgw.compression
user.rgw.content_type
user.rgw.etag
user.rgw.idtag
user.rgw.manifest
user.rgw.pg_ver
user.rgw.source_zone
user.rgw.storage_class
user.rgw.tail_tag
user.rgw.x-amz-content-sha256
user.rgw.x-amz-date
user.rgw.x-amz-meta-s3cmd-attrs
```

压缩信息存储在了xattr:user.rgw.compression。利用getxattr检索发现即是"zlib"(compress算法)。

# 常用命令

```shell
zonegroup add              add a zone to a zonegroup
zonegroup create           create a new zone group info
zonegroup default          set default zone group
zonegroup rm               remove a zone group info
zonegroup get              show zone group info
zonegroup modify           modify an existing zonegroup
zonegroup set              set zone group info (requires infile)
zonegroup rm               remove a zone from a zonegroup
zonegroup rename           rename a zone group
zonegroup list             list all zone groups set on this cluster
zonegroup placement list   list zonegroup's placement targets
zonegroup placement get    get a placement target of a specific zonegroup
zonegroup placement add    add a placement target id to a zonegroup
zonegroup placement modify modify a placement target of a specific zonegroup
zonegroup placement rm     remove a placement target from a zonegroup
zonegroup placement default  set a zonegroup's default placement target
zone create                create a new zone
zone rm                    remove a zone
zone get                   show zone cluster params
zone modify                modify an existing zone
zone set                   set zone cluster params (requires infile)
zone list                  list all zones set on this cluster
zone rename                rename a zone
zone placement list        list zone's placement targets
zone placement get         get a zone placement target
zone placement add         add a zone placement target
zone placement modify      modify a zone placement target
zone placement rm          remove a zone placement target
```



### 添加storage class

```c++
//rgw_admin.cc
搜索：
OPT_ZONEGROUP_PLACEMENT_ADD
OPT_ZONEGROUP_PLACEMENT_MODIFY
```



### 读取storage class:





# 目前部署ceph时zone相关流程

搜索Erwa中：

create_placement.sh.j2

create_placement_from_mon.sh.j2

del_placement_from_mon.sh.j2

modify_placement_from_mon.sh.j2

start_elasticsearch_sync.sh.j2

set_default_placement.sh.j2

# 参考

1. ceph crushmap及rgw placement设置, storage class：https://www.jianshu.com/p/15a986d664fe
2. put object Storage Class Options: https://docs.aws.amazon.com/cli/latest/reference/s3api/put-object.html