# RadosGW的OpsLog功能调研

[TOC]

## 简单使用

1. ceph.conf的global中添加rgw_enable_ops_log=true（rgw_ops_log_rados默认为true，这里就没有另外配置了）
2. 创建一个名为create-bucket的桶，并上传了一个小文件（RadosGW在100.99.52.69上）

```
# radosgw-admin log list查看记录OpsLog的对象名
# 可以看到对象名的格式是YYYY-MM-DD-HH-${bucket-id}-${bucket-name}
[root@100 /data/console]# radosgw-admin -c $(ls /data/cos/ceph.*.conf | head -1) log list 2>/dev/null | grep create-bucket
    "2021-05-26-14-f2a395ec-0368-4031-8ebd-010d5cd185b4.76990.2-create-bucket",
    "2021-05-26-15-f2a395ec-0368-4031-8ebd-010d5cd185b4.76990.2-create-bucket",

# 可以用radosgw-admin log show对某年某月某日某时内的操作进行查询
# 在14～15点范围内只有一个create_bucket的操作
[root@100 /data/console]# radosgw-admin log show --bucket=create-bucket --date=2021-05-26-14 --bucket-id=f2a395ec-0368-4031-8ebd-010d5cd185b4.76990.2 2>/dev/null
{
    "bucket_id": "f2a395ec-0368-4031-8ebd-010d5cd185b4.76990.2",
    "bucket_owner": "admin",
    "bucket": "create-bucket",
    "log_entries": [
        {
            "bucket": "create-bucket",
            "time": "2021-05-26 06:36:39.895979Z",
            "time_local": "2021-05-26 14:36:39.895979",
            "remote_addr": "10.10.103.64, 9.218.225.101, 182.254.33.180, 100.121.146.109, 100.99.52.68",
            "user": "admin",
            "operation": "create_bucket",
            "uri": "PUT /create-bucket HTTP/1.1",
            "http_status": "200",
            "error_code": "",
            "bytes_sent": 0,
            "bytes_received": 0,
            "object_size": 0,
            "total_time": 14468,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
            "referrer": ""
        }
    ],
    "log_sum": {
        "bytes_sent": 0,
        "bytes_received": 0,
        "total_time": 14468,
        "total_entries": 1
    }
}

# 在15～14点的范围内有get_lifecycle、get_bucket_tags、stat_bucket、get_cors、list_bucket、get_acls、init_multipart、put_obj、complete_multipart操作
[root@100 /data/console]# radosgw-admin log show --bucket=create-bucket --date=2021-05-26-15 --bucket-id=f2a395ec-0368-4031-8ebd-010d5cd185b4.76990.2 2>/dev/null
{
    "bucket_id": "f2a395ec-0368-4031-8ebd-010d5cd185b4.76990.2",
    "bucket_owner": "admin",
    "bucket": "create-bucket",
    "log_entries": [
        {
            "bucket": "create-bucket",
            "time": "2021-05-26 07:42:04.752865Z",
            "time_local": "2021-05-26 15:42:04.752865",
            "remote_addr": "10.10.103.64, 9.218.225.101, 121.51.15.82, 100.121.146.53, 100.99.52.68",
            "user": "admin",
            "operation": "get_lifecycle",
            "uri": "GET /create-bucket?lifecycle HTTP/1.1",
            "http_status": "404",
            "error_code": "NoSuchLifecycleConfiguration",
            "bytes_sent": 303,
            "bytes_received": 0,
            "object_size": 0,
            "total_time": 4,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
            "referrer": ""
        },
        {
            "bucket": "create-bucket",
            "time": "2021-05-26 07:42:04.772865Z",
            "time_local": "2021-05-26 15:42:04.772865",
            "remote_addr": "10.10.103.64, 9.218.225.101, 182.254.33.144, 100.121.146.109, 100.99.52.68",
            "user": "admin",
            "operation": "get_bucket_tags",
            "uri": "GET /create-bucket?tagging HTTP/1.1",
            "http_status": "404",
            "error_code": "NoSuchTagSetError",
            "bytes_sent": 230,
            "bytes_received": 0,
            "object_size": 0,
            "total_time": 0,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
            "referrer": ""
        },
        {
            "bucket": "create-bucket",
            "time": "2021-05-26 07:42:04.768865Z",
            "time_local": "2021-05-26 15:42:04.768865",
            "remote_addr": "10.10.103.64, 9.218.225.101, 121.51.15.83, 100.121.146.109, 100.99.52.68",
            "user": "admin",
            "operation": "stat_bucket",
            "uri": "HEAD /create-bucket HTTP/1.1",
            "http_status": "200",
            "error_code": "",
            "bytes_sent": 0,
            "bytes_received": 0,
            "object_size": 0,
            "total_time": 4,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
            "referrer": ""
        },
        {
            "bucket": "create-bucket",
            "time": "2021-05-26 07:42:04.900865Z",
            "time_local": "2021-05-26 15:42:04.900865",
            "remote_addr": "10.10.103.64, 9.218.225.101, 182.254.33.144, 100.121.146.109, 100.99.52.68",
            "user": "admin",
            "operation": "get_cors",
            "uri": "GET /create-bucket?cors HTTP/1.1",
            "http_status": "404",
            "error_code": "NoSuchCORSConfiguration",
            "bytes_sent": 236,
            "bytes_received": 0,
            "object_size": 0,
            "total_time": 4,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
            "referrer": ""
        },
        {
            "bucket": "create-bucket",
            "time": "2021-05-26 07:42:06.872865Z",
            "time_local": "2021-05-26 15:42:06.872865",
            "remote_addr": "10.10.103.64, 9.218.225.101, 182.254.33.180, 100.121.146.53, 100.99.52.68",
            "user": "admin",
            "operation": "list_bucket",
            "uri": "GET /create-bucket?delimiter=%2F HTTP/1.1",
            "http_status": "200",
            "error_code": "",
            "bytes_sent": 274,
            "bytes_received": 0,
            "object_size": 0,
            "total_time": 4,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
            "referrer": ""
        },
        {
            "bucket": "create-bucket",
            "time": "2021-05-26 07:42:06.888865Z",
            "time_local": "2021-05-26 15:42:06.888865",
            "remote_addr": "10.10.103.64, 9.218.225.101, 121.51.15.82, 100.121.146.102, 100.99.52.68",
            "user": "admin",
            "operation": "get_acls",
            "uri": "GET /create-bucket?acl HTTP/1.1",
            "http_status": "200",
            "error_code": "",
            "bytes_sent": 425,
            "bytes_received": 0,
            "object_size": 0,
            "total_time": 0,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
            "referrer": ""
        },
        {
            "bucket": "create-bucket",
            "time": "2021-05-26 07:42:49.601727Z",
            "time_local": "2021-05-26 15:42:49.601727",
            "remote_addr": "10.10.103.64, 9.218.225.101, 182.254.33.180, 100.121.146.109, 100.99.52.68",
            "user": "admin",
            "operation": "init_multipart",
            "uri": "POST /create-bucket/abcmaz.jpg?uploads HTTP/1.1",
            "http_status": "200",
            "error_code": "",
            "bytes_sent": 254,
            "bytes_received": 0,
            "object_size": 0,
            "total_time": 4,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
            "referrer": ""
        },
        {
            "bucket": "create-bucket",
            "time": "2021-05-26 07:42:49.789727Z",
            "time_local": "2021-05-26 15:42:49.789727",
            "remote_addr": "10.10.103.64, 9.218.225.101, 182.254.33.144, 100.121.146.53, 100.99.52.68",
            "user": "admin",
            "operation": "put_obj",
            "uri": "PUT /create-bucket/abcmaz.jpg?partNumber=1&uploadId=2~IP5anq798Mfz-sd9sM8FzUBJq2O1Or7 HTTP/1.1",
            "http_status": "200",
            "error_code": "",
            "bytes_sent": 0,
            "bytes_received": 85,
            "object_size": 85,
            "total_time": 8,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
            "referrer": ""
        },
        {
            "bucket": "create-bucket",
            "time": "2021-05-26 07:42:49.977727Z",
            "time_local": "2021-05-26 15:42:49.977727",
            "remote_addr": "10.10.103.64, 9.218.225.101, 121.51.15.83, 100.121.146.53, 100.99.52.68",
            "user": "admin",
            "operation": "complete_multipart",
            "uri": "POST /create-bucket/abcmaz.jpg?uploadId=2~IP5anq798Mfz-sd9sM8FzUBJq2O1Or7 HTTP/1.1",
            "http_status": "200",
            "error_code": "",
            "bytes_sent": 324,
            "bytes_received": 0,
            "object_size": 0,
            "total_time": 4,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
            "referrer": ""
        },
        {
            "bucket": "create-bucket",
            "time": "2021-05-26 07:42:50.169727Z",
            "time_local": "2021-05-26 15:42:50.169727",
            "remote_addr": "10.10.103.64, 9.218.225.101, 121.51.15.83, 100.121.146.53, 100.99.52.68",
            "user": "admin",
            "operation": "list_bucket",
            "uri": "GET /create-bucket?delimiter=%2F HTTP/1.1",
            "http_status": "200",
            "error_code": "",
            "bytes_sent": 560,
            "bytes_received": 0,
            "object_size": 0,
            "total_time": 4,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
            "referrer": ""
        },
        {
            "bucket": "create-bucket",
            "time": "2021-05-26 07:42:50.225727Z",
            "time_local": "2021-05-26 15:42:50.225727",
            "remote_addr": "10.10.103.64, 9.218.225.101, 121.51.15.82, 100.121.146.52, 100.99.52.68",
            "user": "admin",
            "operation": "get_acls",
            "uri": "GET /create-bucket?acl HTTP/1.1",
            "http_status": "200",
            "error_code": "",
            "bytes_sent": 425,
            "bytes_received": 0,
            "object_size": 0,
            "total_time": 0,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
            "referrer": ""
        }
    ],
    "log_sum": {
        "bytes_sent": 3031,
        "bytes_received": 85,
        "total_time": 36,
        "total_entries": 11
    }
}

# 只有一个记录的话，存放记录的rados object有454字节
[root@100 /data/console]# rados -p default.rgw.log stat 2021-05-26-14-f2a395ec-0368-4031-8ebd-010d5cd185b4.76990.2-create-bucketdefault.rgw.log/2021-05-26-14-f2a395ec-0368-4031-8ebd-010d5cd185b4.76990.2-create-bucket mtime 2021-05-26 14:36:54.000000, size 454

# 有9个记录的话，存放记录的rados object有5281字节，所以如果对象名不太长的情况下，每条记录500字节左右
[root@100 /data/console]# rados -p default.rgw.log stat 2021-05-26-15-f2a395ec-0368-4031-8ebd-010d5cd185b4.76990.2-create-bucket
default.rgw.log/2021-05-26-15-f2a395ec-0368-4031-8ebd-010d5cd185b4.76990.2-create-bucket mtime 2021-05-26 15:42:50.000000, size 5281
```

另外还有2个和OpsLog相关的配置

- rgw_ops_log_socket_path: OpsLog可以写向本地的一个Unix socket，这里可以制定路径（默认是没有指定的）。
- rgw_ops_log_data_backlog：如果OpsLog是写向一个Unix socket，这是Radosgw本地缓存的上限，如果Unix socket一直没处理数据，导致RadosGW一侧堆积了记录超过了这个上限，RadosGW就开始丢弃记录。

## 实现代码

OpsLog的主要逻辑在rgw_log_op()中，从如下简化的调用栈知道，这里就是在，每个请求处理结束后，进行了记录。记录操作调用了append_async，有利于尽快释放当前的处理线程。

```c++
process_request()
  op->verify_requester(auth_registry)
  handler->postauth_init()
  rgw_process_authenticated(handler, op, req, s)
  rgw_log_op(store, rest, s, (op ? op->name() : "unknown"), olog)
    store->append_async(obj, bl.length(), bl)
```

## 潜在的问题

1. 在长时间高并发下，OpsLog的rados object可能很大，假设100并发持续一小时，每条记录1KB，那么就有351MB了，已经超过osd_max_object_size的默认值128MB。

  - 为了避免这样的情况，恐怕需要以更细的力度切割OpsLog的rados object
  - 可能需要定制一定的策略，比如不记录GET、不记录分片上传，来减少记录数量

2. 由于一个Bucket在一个小时内只使用一个Ops Log rados object，在高并发下则这个rados object肯定会成为性能瓶颈

3. OpsLog是全局bucket都启用，是否要改为Bucket级别的配置。

4. 如果在CAM场景下，目前的逻辑只记录到主帐号级别，是否需要记录到子帐号级别

5. OpsLog是放在default.rgw.log中，以往都是认为这个Pool的使用量很小，所以分配的PG也少，如果要启用OpsLog可能需要扩大该Pool的PG数目

6. 目前RadosGW并没有定期清理OpsLog的机制，都是需要管理员手动用radosgw log rm一个删除，如果产品化，则需要考虑清理的策略和实现的机制。

7. 由于记录都直接append到rados object的，不大可能使用marker进行分段输出，只能全量输出（在持续高并发的场景下，这个输出量可能挺大的）

8. radosgw-admin log list是在Pool里进行全量list，效率不高

   