## 涉及知识

1. 如何自定义一个组件
2. 添加节点的时候，server和agent是如何交互的
   1. agent端如何向server注册？ambari-agent.ini
   2. server的bootstrap做了什么：scp脚本到agent
   3. server如何管理yum repo： metainfo.xml
   4. server如何把yum repo写到agent：db中以及配置文件中
   5. agent如何感知server的任务：CUSTOM_COMMAND，
   6. agent端如何配置repo: hook, beforeANY, beforeINSTALL, afterINSTALL, resource_management, install_packages, 

