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





```shell
systemctl start etcd
systemctl start docker
systemctl start kube-apiserver.service
systemctl start kube-controller-manager.service
systemctl start kube-scheduler.service
systemctl start kubelet.service
systemctl start kube-proxy.service


systemctl enable etcd
systemctl enable docker
systemctl enable kube-apiserver.service
systemctl enable kube-controller-manager.service
systemctl enable kube-scheduler.service
systemctl enable kubelet.service
systemctl enable kube-proxy.service
```





部署kubernetes 1.16.1

https://misa.gitbook.io/k8s-ocp-yaml/kubernetes-docs/2019-10-14-kubernetes-1.16-install-online





单节点master上允许调度pod:

https://github.com/calebhailey/homelab/issues/3

https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/create-cluster-kubeadm/#master-isolation





重新初始化：
kubeadm reset 
kubeadm init --kubernetes-version=v1.11.2 --pod-network-cidr=10.244.0.0/16 --apiserver-advertise-address=192.168.11.90 --token-ttl 0
