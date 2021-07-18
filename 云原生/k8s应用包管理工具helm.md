## 问题收集

1. chart是如何与k8s交互的？如何建立chart、镜像、容器、k8s的观若曦？
2. chart是如何简化k8s的部署的？
3. 自定义chart



对于复杂的应用中间件，要在K8s上部署，需要研究Docker镜像的运行需求，环境变量等内容，并未这些容器定制存储、网络等设置，最后设计编写Deployment、Configmap、Service和Ingress等yaml配置，再提交给K8s部署。这些复杂步骤可以由Helm应用包管理工具来实现。

Helm以chart的方式对应用进行描述，可以方便地创建、版本化、共享和发布复杂的应用软件。

> rook/ceph是如何使用chart的？

基本概念：

* Chart：包含了运行一个应用需要的工具和资源定义，还可能包含K8s集群中的服务定义，类似于rpm文件。
* Release：在K8s集群上运行的一个Chart实例。在同一个集群上，一个Chart可以安装多次，每次安装都会生成新的Release，会有独立的Release名称。
* Repository：用于存放和共享Chart的仓库。

基本流程：在仓库中查找需要的Chart，然后将Chart以Release的形式安装到K8s集群中。

