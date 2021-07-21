https://www.kubernetes.org.cn/7189.html





cent0s7单机部署：https://cloud.tencent.com/developer/article/1519545

https://www.kubernetes.org.cn/doc-5

以mysql为例，详细版：https://www.cnblogs.com/zuoyang/p/9639961.html



```json
apiVersion: v1
kind: ReplicationController
metadata:
  name: myweb
spec:
  replicas: 2
  selector:
    app: myweb
  template:
    metadata:
      labels:
        app: myweb
    spec:
      containers:
        - name: myweb
          image: kubeguide/tomcat-app:v1
          ports:
          - containerPort: 8080
          env:
```







```shell
wget http://mirror.centos.org/centos/7/os/x86_64/Packages/python-rhsm-certificates-1.19.10-1.el7_4.x86_64.rpm
rpm2cpio python-rhsm-certificates-1.19.10-1.el7_4.x86_64.rpm | cpio -iv --to-stdout ./etc/rhsm/ca/redhat-uep.pem | tee /etc/rhsm/ca/redhat-uep.pem
```



## 部署kubernetes 1.16.1

https://misa.gitbook.io/k8s-ocp-yaml/kubernetes-docs/2019-10-14-kubernetes-1.16-install-online

## 单节点master上允许调度pod:

https://github.com/calebhailey/homelab/issues/3

https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/create-cluster-kubeadm/#master-isolation

## 重新初始化

```shell
kubeadm reset 

kubeadm init --image-repository registry.aliyuncs.com/google_containers --kubernetes-version=v1.16.1 --pod-network-cidr=10.244.0.0/16 
```

deployment, yaml: https://blog.csdn.net/DY1316434466/article/details/105440172

## 停止k8s所有服务

因为k8s需要占用大量资源，且不允许开启swap，因此在不用的时候建议将k8s服务都停掉：

```shell
kubeadm reset
```

