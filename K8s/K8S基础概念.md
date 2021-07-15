[TOC]





## 参考

[ConfigMap](https://kubernetes.io/zh/docs/concepts/configuration/configmap/)

[Pods,Deployment,StatefulSet,DaemonSet,](https://kubernetes.io/zh/docs/concepts/workloads/pods/)

[一关系图让你理解K8s中的概念，Pod、Service、Job等到底有啥关系](https://zhuanlan.zhihu.com/p/105006577)



## 什么是K8S,K8S解决了什么问题

假设有许多主机，K8S基于这些主机，将这些主机的资源（CPU、内存、存储等）当成一个虚拟资源池，对上提供服务。

提供服务一般是运行容器，对于用户来说，无需知道某个容器运行在哪台主机上，这一点是由K8S来负责调度的。

> 调度的具体规则？如何使用各个主机的物理资源？如何通信？如何处理同步问题？

对于在这个资源池上抽象出来的多个容器之间的通信问题，K8S也抽象出来许多组件来处理。例如对于网络，是由Service来处理的。

涉及到注册中心、地址表、负载均衡器（对外提供固定IP，对内灵活处理）



## K8S与Docker有什么关系

多个 Docker容器可以共存于同一pod中。这非常适合一些高级场景,我们会在范例5.7 中进行介绍。每个容器都有自己的文件系统和进程,与普通容器一样。
・pod定义了一个共的网络接ロ。与普通容器不一样的是,同一个pod中的容器都共享同一个网络接口。这样,容器之间就可以通过 Localhost来进行简单且高效的互相访问。
这也意味着同一个pod中的不同容器不能使用同一个网络端口号。
存储卷也是pod定义的一部分。如果需要,可以将这些卷映射到多个容器中。也有一些特殊类型的卷,这些卷是基于用户的需求以及集群所具备的能力。





