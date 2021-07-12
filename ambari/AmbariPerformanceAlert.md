>
>
>1. Ambari判断了哪些指标？
>2. 如何获取这些指标？
>3. 如何上报？
>4. 如何构建？

搜索PERFORMANCE_OVERVIEW_TEMPLATE，

https://community.cloudera.com/t5/Support-Questions/Ambari-Performance-Warning-REST-API-Cluster/td-p/139424

https://docs.ksyun.com/documents/5812

https://docs.cloudera.com/HDPDocuments/Ambari-latest/managing-and-monitoring-ambari/content/amb_ambari_alerts.html

## 现象

查看alert_current可以找到当前告警信息，并且可以找到包含“性能概览”的一条告警：

```shell
MySQL [ambari]> select * from alert_current;

| alert_id | definition_id | history_id | maintenance_state | original_timestamp | latest_timestamp | latest_text                                                                                         | occurrences | firmness |
|     1950 |           190 |      12353 | OFF               |      1625562796961 |    1626061581574 | 性能概览:
{{var}}|@|{"var":"  Database Access (Request By Status): 1ms (OK)
  Database Access (Task Status Aggregation): 1ms (OK)
  REST API (Cluster): 132ms (OK)"}     |        1649 | HARD  
```

从上可以看到性能概览的告警定义在definition_id=190处，此时便可以查到该告警的定义信息：

```shell
MySQL [ambari]> select * from alert_definition where definition_id=190

| definition_id | cluster_id | definition_name  | service_name | component_name | scope   | label  | help_url | description  | enabled | schedule_interval | source_type | alert_source                                                                                                                                                                                            | hash  | ignore_host | repeat_tolerance | repeat_tolerance_enabled |


| 190 |  2 | ambari_server_performance | AMBARI | AMBARI_SERVER  | SERVICE | Ambari Server Performance | NULL | This alert is triggered if the Ambari Server detects that there is a potential performance problem with Ambari. This type of issue can arise for many reasons, but is typically attributed to slow database queries and host resource exhaustion. | 1 | 5 | SERVER |
{"class":"org.apache.ambari.server.alerts.AmbariPerformanceRunnable","parameters":[{"name":"request.by.status.warning.threshold","display_name":"Get Request Progress","units":"ms","value":3000.0,"description":"The time to find requests in progress before a warning alert is triggered.","type":"NUMERIC","threshold":"WARNING"},{"name":"request.by.status.critical.threshold","display_name":"Get Request Progress","units":"ms","value":5000.0,"description":"The time to find requests in progress before a critical alert is triggered.","type":"NUMERIC","threshold":"CRITICAL"},{"name":"task.status.aggregation.warning.threshold","display_name":"Get Request Status","units":"ms","value":3000.0,"description":"The time to calculate a request\u0027s status from its tasks before a warning alert is triggered.","type":"NUMERIC","threshold":"WARNING"},{"name":"task.status.aggregation.critical.threshold","display_name":"Get Request Status","units":"ms","value":5000.0,"description":"The time to calculate a request\u0027s status from its tasks before a critical alert is triggered.","type":"NUMERIC","threshold":"CRITICAL"},{"name":"rest.api.cluster.warning.threshold","display_name":"Get Cluster","units":"ms","value":5000.0,"description":"The time to get a cluster via the REST API before a warning alert is triggered.","type":"NUMERIC","threshold":"WARNING"},{"name":"rest.api.cluster.critical.threshold","display_name":"Get Cluster","units":"ms","value":7000.0,"description":"The time to get a cluster via the REST API before a critical alert is triggered.","type":"NUMERIC","threshold":"CRITICAL"}],"type":"SERVER"} | 8564a745-d063-422e-8a64-a72973fadf6c | 0 | 1 | 0 |

```





## 代码流程

```java
/**
     * Query for requests by {@link RequestStatus#IN_PROGRESS}.
     */
    REQUEST_BY_STATUS("Database Access (Request By Status)",
        "request.by.status.warning.threshold", 3000, "request.by.status.critical.threshold", 5000) {
      /**
       * {@inheritDoc}
       */
      @Override
      void execute(AmbariPerformanceRunnable runnable, Cluster cluster) throws Exception {
        runnable.m_actionManager.getRequestsByStatus(RequestStatus.IN_PROGRESS,
            BaseRequest.DEFAULT_PAGE_SIZE, false);
      }
    },

    /**
     * Query for requests by {@link RequestStatus#IN_PROGRESS}.
     */
    HRC_SUMMARY_STATUS("Database Access (Task Status Aggregation)",
        "task.status.aggregation.warning.threshold", 3000,
        "task.status.aggregation.critical.threshold", 5000) {
      /**
       * {@inheritDoc}
       */
      @Override
      void execute(AmbariPerformanceRunnable runnable, Cluster cluster) throws Exception {
        List<Long> requestIds = runnable.m_requestDAO.findAllRequestIds(
            BaseRequest.DEFAULT_PAGE_SIZE, false);

        for (long requestId : requestIds) {
          runnable.m_hostRoleCommandDAO.findAggregateCounts(requestId);
        }
      }
    },

    /**
```







```java
calculatePerformanceResult(PerformanceArea area, long time, List<AlertParameter> parameters);



```

