## rook设计



[Introduction to a Cloud-Native Storage Orchestrator: Rook*](https://01.org/kubernetes/blogs/tingjie/2020/introduction-cloud-native-storage-orchestrator-rook)

[k8s部署rook ceph,cluster.yaml,单个image, 指定存储节点主机与磁盘，集群内部访问，集群外部访问](https://www.modb.pro/db/46629)



[![img](https://01.org/sites/default/files/resize/users/u25390/intro-to-rook-ceph-ceph-cluster-maint-490x322.png)





## MON

不允许每个节点上都运行重复的pod:

rook通过一个自定义参数`allowMultiplePerNode`来限制。

```json
mon:
    count: 3
    allowMultiplePerNode: false
```







## 配置更改：ConfigMap

```json
kubectl edit configmap rook-ceph-override -n rook-ceph
-------------------------------------
apiVersion: v1
kind: ConfigMap
metadata:
  name: rook-config-override
  namespace: rook-ceph
data:
  config: |
    [global]
    osd crush update on start = false
    osd pool default size = 2
```

 

保存在哪里？在哪里定义？

