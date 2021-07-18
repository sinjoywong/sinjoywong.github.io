

[TOC]



## 参考

《第一本docker书》

[浅谈docker中镜像和容器在本地的存储](https://zhuanlan.zhihu.com/p/95900321)

## 问题积累

1. docker 容器的生命周期？
2. f



## 基本概念

1. docker文件系统层

### 镜像

什么是镜像？

Docker镜像是由文件系统叠加而成。最底端是一个引导文件系统，即`bootfs` ，这很像典型的Linux/Unix的引导文件系统。Docker用户几乎永远不会和引导文件系统有什么交互。实际上，当一个容器启动后，它将会被移到内存中，而引导文件系统则会被卸载（unmount），以留出更多的内存供`initrd` 磁盘镜像使用。

到目前为止，Docker看起来还很像一个典型的Linux虚拟化栈。实际上，Docker镜像的第二层是root文件系统`rootfs` ，它位于引导文件系统之上。`rootfs` 可以是一种或多种操作系统（如Debian或者Ubuntu文件系统）。

在传统的Linux引导过程中，root文件系统会最先以只读的方式加载，当引导结束并完成了完整性检查之后，它才会被切换为读写模式。但是在Docker里，root文件系统永远只能是只读状态，并且Docker利用联合加载[ 1 ](text00014.html#anchor41)（union mount）技术又会在root文件系统层上加载更多的只读文件系统。联合加载指的是一次同时加载多个文件系统，但是在外面看起来只能看到一个文件系统。联合加载会将各层文件系统叠加到一起，这样最终的文件系统会包含所有底层的文件和目录。

Docker将这样的文件系统称为镜像。一个镜像可以放到另一个镜像的顶部。位于下面的镜像称为父镜像（parent image），可以依次类推，直到镜像栈的最底部，最底部的镜像称为基础镜像（base image）

<img src=".docker%E5%9F%BA%E7%A1%80%E6%A6%82%E5%BF%B5.assets/image-20210713193312574.png" alt="image-20210713193312574" style="zoom: 25%;" />

当Docker第一次启动一个容器时，初始的读写层是空的。当文件系统发生变化时，这些变化都会应用到这一层上。比如，如果想修改一个文件，这个文件首先会从该读写层下面的只读层复制到该读写层。该文件的只读版本依然存在，但是已经被读写层中的该文件副本所隐藏。

通常这种机制被称为写时复制（copy on write），这也是使Docker如此强大的技术之一。每个只读镜像层都是只读的，并且以后永远不会变化。当创建一个新容器时，Docker会构建出一个镜像栈，并在栈的最顶端添加一个读写层。这个读写层再加上其下面的镜像层以及一些配置数据，就构成了一个容器。在上一章我们已经知道，容器是可以修改的，它们都有自己的状态，并且是可以启动和停止的。容器的这种特点加上镜像分层框架（image-layering framework），使我们可以快速构建镜像并运行包含我们自己的应用程序和服务的容器。

容器化基本过程：

<img src=".docker%E5%9F%BA%E7%A1%80%E6%A6%82%E5%BF%B5.assets/image-20210714113644391.png" alt="image-20210714113644391" style="zoom: 25%;" />

### 构建镜像

docker commit, docker build, dockerfile

#### 使用docker commit构建镜像

```shell
#在修改镜像后
docker commit <container_id> <image_name>
#可以将上面的定制容器提交为一个image。

[root@VM-0-2-centos docker]# docker images
REPOSITORY    TAG            IMAGE ID            CREATED             SIZE
first_image  latest         3d0e6f4c6d09        3 minutes ago       209MB
centos       latest         300e315adb2f        7 months ago        209MB

#之后便可以用这个自定义的image：
[root@VM-0-2-centos docker]# docker run -i -t first_image /bin/bash
[root@d3a19acb0c7c /]# bash /data/hello_world.sh
hello world
[root@d3a19acb0c7c /]#
```

#### 使用Dockerfile构建镜像

并不推荐使用`docker commit` 的方法来构建镜像。相反，推荐使用被称为`Dockerfile` 的定义文件和`docker build` 命令来构建镜像。`Dockerfile` 使用基本的基于DSL（Domain Specific Language)）语法的指令来构建一个Docker镜像，我们推荐使用`Dockerfile` 方法来代替`docker commit` ，因为通过前者来构建镜像更具备可重复性、透明性以及幂等性。

一旦有了`Dockerfile，我们就可以` 使用`docker build` 命令基于该`Dockerfile` 中的指令构建一个新的镜像。

该`Dockerfile` 由一系列指令和参数组成。每条指令，如`FROM` ，都必须为大写字母，且后面要跟随一个参数：`FROM ubuntu:14.04` 。`Dockerfile` 中的指令会按顺序从上到下执行，所以应该根据需要合理安排指令的顺序。



每条指令都会创建一个新的镜像层并对镜像进行提交。Docker大体上按照如下流程执行`Dockerfile` 中的指令。

- Docker从基础镜像运行一个容器。
- 执行一条指令，对容器做出修改。
- 执行类似`docker commit` 的操作，提交一个新的镜像层。

- Docker再基于刚提交的镜像运行一个新容器。
- 执行`Dockerfile` 中的下一条指令，直到所有指令都执行完毕。

每个`Dockerfile` 的第一条指令必须是`FROM` 。`FROM` 指令指定一个已经存在的镜像，后续指令都将基于该镜像进行，这个镜像被称为基础镜像（base iamge）。

> 默认情况下，`RUN` 指令会在shell里使用命令包装器`/bin/sh -c` 来执行。如果是在一个不支持shell的平台上运行或者不希望在shell中运行（比如避免shell字符串篡改），也可以使用`exec` 格式的`RUN` 指令，如代码清单4-23所示
>
> `RUN [ "apt-get", " install", "-y", "nginx" ]`

接着设置了`EXPOSE` 指令，这条指令告诉Docker该容器内的应用程序将会使用容器的指定端口。这并不意味着可以自动访问任意容器运行中服务的端口（这里是`80` ）。出于安全的原因，Docker并不会自动打开该端口，而是需要用户在使用`docker run` 运行容器时来指定需要打开哪些端口。一会儿我们将会看到如何从这一镜像创建一个新容器。

可以指定多个`EXPOSE` 指令来向外部公开多个端口。



我们通过指定`-t` 选项为新镜像设置了仓库和名称，

```shell
[root@VM-0-2-centos tmp]# cat Dockerfile
FROM  centos
MAINTAINER bigbang "bingbang@xxx.com"
RUN mkdir /data/
RUN echo "hello" > /data/hello.log
EXPOSE 80


[root@VM-0-2-centos tmp]# docker build -t="centos/test1" .
Sending build context to Docker daemon  2.048kB
Step 1/5 : FROM  centos
latest: Pulling from library/centos
Digest: sha256:5528e8b1b1719d34604c87e11dcd1c0a20bedf46e83b5632cdeac91b8c04efc1
Status: Downloaded newer image for centos:latest
 ---> 300e315adb2f
Step 2/5 : MAINTAINER bigbang "bingbang@xxx.com"
 ---> Running in b4ba708e4b14
Removing intermediate container b4ba708e4b14
 ---> df8bb2b8aea6
Step 3/5 : RUN mkdir /data/
 ---> Running in 86ec3b92937a
Removing intermediate container 86ec3b92937a
 ---> 61350c287849
Step 4/5 : RUN echo "hello" > /data/hello.log
 ---> Running in 4fb3a9b701c5
Removing intermediate container 4fb3a9b701c5
 ---> 401adda941b6
Step 5/5 : EXPOSE 80
 ---> Running in 536ef0e85817
Removing intermediate container 536ef0e85817
 ---> d84d66814d54
Successfully built d84d66814d54
Successfully tagged centos/test1:latest
[root@VM-0-2-centos tmp]# docker images
REPOSITORY          TAG                 IMAGE ID            CREATED             SIZE
centos/test1        latest              d84d66814d54        4 seconds ago       209MB
centos              latest              300e315adb2f        7 months ago        209MB

#可以设定标签。默认为latest：
[root@VM-0-2-centos tmp]# docker build -t="centos/test1:v2" .
Sending build context to Docker daemon  2.048kB
Step 1/5 : FROM  centos
 ---> 300e315adb2f
Step 2/5 : MAINTAINER bigbang "bingbang@xxx.com"
 ---> Using cache
 ---> df8bb2b8aea6
Step 3/5 : RUN mkdir /data/
 ---> Using cache
 ---> 61350c287849
Step 4/5 : RUN echo "hello" > /data/hello.log
 ---> Using cache
 ---> 401adda941b6
Step 5/5 : EXPOSE 80
 ---> Using cache
 ---> d84d66814d54
Successfully built d84d66814d54
Successfully tagged centos/test1:v2
[root@VM-0-2-centos tmp]# docker images
REPOSITORY          TAG                 IMAGE ID            CREATED             SIZE
centos/test1        latest              d84d66814d54        3 minutes ago       209MB
centos/test1        v1                  d84d66814d54        3 minutes ago       209MB
centos/test1        v2                  d84d66814d54        3 minutes ago       209MB
```

> 自Docker 1.5.0开始，也可以通过`-f` 标志指定一个区别于标准Dockerfile的构建源的位置。例如，`dockerbuild-t"jamtur01/static_- web" -f path/to/file` ，这个文件可以不必命名为Dockerfile，但是必须要位于构建上下文之中

#### `Dockerfile` 和构建缓存

由于每一步的构建过程都会将结果提交为镜像，所以Docker的构建镜像过程就显得非常聪明。它会将之前的镜像层看作缓存。比如，在我们的调试例子里，我们不需要在第1步到第3步之间进行任何修改，因此Docker会将之前构建时创建的镜像当做缓存并作为新的开始点。实际上，当再次进行构建时，Docker会直接从第4步开始。当之前的构建步骤没有变化时，这会节省大量的时间。如果真的在第1步到第3步之间做了什么修改，Docker则会从第一条发生了变化的指令开始。

> 使用场景：构建缓存带来的一个好处就是，我们可以实现简单的`Dockerfile` 模板（比如在`Dockerfile` 文件顶部增加包仓库或者更新包，从而尽可能确保缓存命中）。

然而，有些时候需要确保构建过程不会使用缓存。比如，如果已经缓存了前面的第3步，即`apt-get update` ，那么Docker将不会再次刷新APT包的缓存。这时用户可能需要取得每个包的最新版本。

要想略过缓存功能，可以使用`docker build` 的`--no-cache` 标志。

#### 构建历史

```shell
[root@VM-0-2-centos tmp]# docker history d84d66814d54
IMAGE               CREATED             CREATED BY                                      SIZE                COMMENT
d84d66814d54        19 minutes ago      /bin/sh -c #(nop)  EXPOSE 80                    0B
401adda941b6        19 minutes ago      /bin/sh -c echo "hello" > /data/hello.log       6B
61350c287849        19 minutes ago      /bin/sh -c mkdir /data/                         0B
df8bb2b8aea6        19 minutes ago      /bin/sh -c #(nop)  MAINTAINER bigbang "bingb…   0B
300e315adb2f        7 months ago        /bin/sh -c #(nop)  CMD ["/bin/bash"]            0B
<missing>           7 months ago        /bin/sh -c #(nop)  LABEL org.label-schema.sc…   0B
<missing>           7 months ago        /bin/sh -c #(nop) ADD file:bd7a2aed6ede423b7…   209MB
```

#### Dockerfile指令

```shell
这些指令包括CMD 、ENTRYPOINT 、ADD 、COPY 、VOLUME 、WORKDIR 、USER 、ONBUILD 、LABEL 、STOPSIGNAL 、ARG 和ENV 等。可以在http://docs.docker.com/reference /builder/ 查看Dockerfile 中可以使用的全部指令的清单。
```

CMD: 

在`Dockerfile` 中只能指定一条`CMD` 指令。如果指定了多条`CMD` 指令，也只有最后一条`CMD` 指令会被使用。如果想在启动容器时运行多个进程或者多条命令，可以考虑使用类似Supervisor这样的服务管理工具。



ENTRYPOINT:



WORKDIR:

`WORKDIR` 指令用来在从镜像创建一个新容器时，在容器内部设置一个工作目录，`ENTRYPOINT` 和/或`CMD` 指定的程序会在这个目录下执行。

可以通过`-w` 标志在运行时覆盖工作目录，如代码清单4-57所示。

> 其中`-it` 参数告诉Docker开启容器的交互模式并将读者当前的Shell连接到容器终端（在容器章节中会详细介绍）

```shell
$ sudo docker run -ti -w /var/log ubuntu pwd　
/var/log
```

该命令会将容器内的工作目录设置为`/var/log` 。

ENV:

`ENV` 指令用来在镜像构建过程中设置环境变量。这些环境变量也会被持久保存到从我们的镜像创建的任何容器中。也可以使用`docker run` 命令行的`-e` 标志来传递环境变量。这些变量将只会在运行时有效。

```shell
sudo docker run -ti -e "WEB_PORT=8080" ubuntu env　
HOME=/　
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin　
HOSTNAME=792b171c5e9f　
TERM=xterm　
WEB_PORT=808
```

VOLUME:

`VOLUME` 指令用来向基于镜像创建的容器添加卷。一个卷是可以存在于一个或者多个容器内的特定的目录，这个目录可以绕过联合文件系统，并提供如下共享数据或者对数据进行持久化的功能。

- 卷可以在容器间共享和重用。
- 一个容器可以不是必须和其他容器共享卷。
- 对卷的修改是立时生效的。
- 对卷的修改不会对更新镜像产生影响。
- 卷会一直存在直到没有任何容器再使用它。

卷功能让我们可以将数据（如源代码）、数据库或者其他内容添加到镜像中而不是将这些内容提交到镜像中，并且允许我们在多个容器间共享这些内容。我们可以利用此功能来测试容器和内部的应用程序代码，管理日志，或者处理容器内部的数据库。我们将在第5章和第6章看到相关的例子。

```shell
VOLUME ["/opt/project"]
#这条指令将会为基于此镜像创建的任何容器创建一个名为/opt/project 的挂载点。
```

> `docker cp` 是和`VOLUME` 指令相关并且也是很实用的命令。该命令允许从容器复制文件和复制文件到容器上。可以从Docker命令行文档（https://docs.docker.com/engine/reference/ commandline/cp/ ）中获得更多信息。



卷在Docker里非常重要，也很有用。卷是在一个或者多个容器内被选定的目录，可以绕过分层的联合文件系统（Union File System），为Docker提供持久数据或者共享数据。这意味着对卷的修改会直接生效，并绕过镜像。当提交或者创建镜像时，卷不被包含在镜像里。

```shell
$ sudo docker run -d -p 80 --name website \
-v $PWD/website:/var/www/html/website \
jamtur01/nginx nginx
```



- 希望同时对代码做开发和测试；
- 代码改动很频繁，不想在开发过程中重构镜像；
- 希望在多个容器间共享代码。

`-v选项通过` 指定一个目录或者登上与容器上与该目录分离的本地宿主机来工作，这两个目录用`:` 分隔。如果容器目录不存在，Docker会自动创建一个。





ADD:

`ADD` 指令用来将构建环境下的文件和目录复制到镜像中。比如，在安装一个应用程序时。`ADD` 指令需要源文件位置和目的文件位置两个参数，

```shell
#这里的ADD 指令将会将构建目录下的software.lic 文件复制到镜像中的/opt/`` ``application/software.lic 。指向源文件的位置参数可以是一个URL，或者构建上下文或环境中文件名或者目录。不能对构建目录或者上下文之外的文件进行ADD 操作。

ADD software.lic /opt/application/software.lic
```

在`ADD` 文件时，Docker通过目的地址参数末尾的字符来判断文件源是目录还是文件。如果目标地址以/结尾，那么Docker就认为源位置指向的是一个目录。如果目的地址以`/` 结尾，那么Docker就认为源位置指向的是目录。如果目的地址不是以`/` 结尾，那么Docker就认为源位置指向的是文件。

最后值得一提的是，`ADD` 在处理本地归档文件（tar archive）时还有一些小魔法。如果将一个归档文件（合法的归档文件包括gzip、bzip2、xz）指定为源文件，Docker会自动将归档文件解开（unpack），如代码清单4-71所示。

代码清单4-71　将归档文件作为`ADD` 指令中的源文件

```
ADD latest.tar.gz /var/www/wordpress/
```

这条命令会将归档文件`latest.tar.gz` 解开到`/var/www/wordpress/` 目录下。

Docker解开归档文件的行为和使用带`-x` 选项的`tar` 命令一样：该指令执行后的输出是原目的目录已经存在的内容加上归档文件中的内容。如果目的位置的目录下已经存在了和归档文件同名的文件或者目录，那么目的位置中的文件或者目录不会被覆盖。

> 目前Docker还不支持以URL方式指定的源位置中使用归档文件。这种行为稍显得有点儿不统一，在以后的版本中应该会有所变化。

最后，如果目的位置不存在的话，Docker将会为我们创建这个全路径，包括路径中的任何目录。新创建的文件和目录的模式为0755，并且UID和GID都是0。

> `ADD` 指令会使得构建缓存变得无效，这一点也非常重要。如果通过`ADD` 指令向镜像添加一个文件或者目录，那么这将使`Dockerfile` 中的后续指令都不能继续使用之前的构建缓存。

COPY:

`COPY` 指令非常类似于`ADD` ，它们根本的不同是`COPY` 只关心在构建上下文中复制本地文件，而不会去做文件提取（extraction）和解压（decompression）的工作。`COPY` 指令的使用如代码清单4-72所示。

代码清单4-72　使用`COPY` 指令

```
COPY conf.d/ /etc/apache2/
```

这条指令将会把本地`conf.d` 目录中的文件复制到`/etc/apache2/` 目录中。

文件源路径必须是一个与当前构建环境相对的文件或者目录，本地文件都放到和`Dockerfile` 同一个目录下。不能复制该目录之外的任何文件，因为构建环境将会上传到Docker守护进程，而复制是在Docker守护进程中进行的。任何位于构建环境之外的东西都是不可用的。`COPY` 指令的目的位置则必须是容器内部的一个绝对路径。

任何由该指令创建的文件或者目录的UID和GID都会设置为0。

如果源路径是一个目录，那么这个目录将整个被复制到容器中，包括文件系统元数据；如果源文件为任何类型的文件，则该文件会随同元数据一起被复制。在这个例子里，源路径以`/` 结尾，所以Docker会认为它是目录，并将它复制到目的目录中。

如果目的位置不存在，Docker将会自动创建所有需要的目录结构，就像`mkdir -p` 命令那样。

### 容器的生命周期

示例中使用`docker container run`来启动容器，这也是启动新容器的标准命令。命令中使用了`-it` 参数使容器具备交互性并与终端进行连接。

```shell
$ docker container run -it ubuntu:latest /bin/bash
Unable to find image 'ubuntu:latest' locally
latest: Pulling from library/ubuntu
952132ac251a: Pull complete
82659f8f1b76:  Pull complete
c19118ca682d:  Pull complete
8296858250fe:  Pull complete
24e0251a0e2c:  Pull complete
Digest: sha256:f4691c96e6bbaa99d9...e95a60369c506dd6e6f6ab
Status: Downloaded newer image for

 ubuntu:latest
root@3027eb644874:/#
```

启动Ubuntu容器之时，让容器运行Bash Shell（`/bin/bash` ）。这使得Bash Shell成为**容器中运行的且唯一运行的进程** 。读者可以通过`ps -elf` 命令在容器内部查看。

这意味着如果通过输入exit退出Bash Shell，那么容器也会退出（终止）。原因是容器如果不运行任何进程则无法存在——杀死Bash Shell即杀死了容器唯一运行的进程，导致这个容器也被杀死。这对于Windows容器来说也是一样的——**杀死容器中的主进程，则容器也会被杀死** 。

按下`Ctrl-PQ` 组合键则会退出容器但并不终止容器运行。这样做会切回到Docker主机的Shell，并保持容器在后台运行。可以使用`docker container ls` 命令来观察当前系统正在运行的容器列表。

当前容器仍然在运行，并且可以通过`docker container exec` 命令将终端重新连接到Docker，理解这一点很重要。

```
$ docker container exec -it 3027eb644874 bash
root@3027eb644874:/#
```

正如读者所见，Shell提示符切换到了容器。如果读者再次运行`ps` 命令，会看到两个Bash或者PowerShell进程，这是因为`docker container exec` 命令创建了新的Bash或者PowerShell进程并且连接到容器。这意味着在当前Shell输入`exit` 并不会导致容器终止，因为原Bash或者PowerShell进程还在运行当中。

输入exit退出容器，并通过命令`docker container ps` 来确认容器依然在运行中。果然容器还在运行。

如果在自己的Docker主机上运行示例，则需要使用下面两个命令来停止并删除容器（读者需要将ID替换为自己容器的ID）。

```
$ docker container stop 3027eb64487
3027eb64487

$ docker container rm 3027eb64487
3027eb64487

```



### 容器的卷与持久化

在容器中持久化数据的方式推荐采用卷。

总体来说，用户创建卷，然后创建容器，接着将卷挂载到容器上。卷会挂载到容器文件系统的某个目录之下，任何写到该目录下的内容都会写到卷中。即使容器被删除，卷与其上面的数据仍然存在

如图13.1所示，Docker卷挂载到容器的`/code` 目录。任何写入`/code` 目录的数据都会保存到卷当中，并且在容器删除后依然存在。

<img src=".docker%E5%9F%BA%E7%A1%80%E6%A6%82%E5%BF%B5.assets/image-20210714115123630.png" alt="image-20210714115123630" style="zoom:50%;" />

`/code` 目录是一个Docker卷。容器其他目录均使用临时的本地存储。卷与目录`/code` 之间采用带箭头的虚线连接，这是为了表明卷与容器是非耦合的关系。

默认情况下，Docker创建新卷时采用内置的`local` 驱动。恰如其名，本地卷只能被所在节点的容器使用。使用`-d` 参数可以指定不同的驱动。

> 第三方驱动可以通过插件方式接入。这些驱动提供了高级存储特性，并为Docker集成了外部存储系统。

使用`local` 驱动创建的卷在Docker主机上均有其专属目录，在Linux中位于`/var/lib/docker/volumes` 目录下。

这意味着可以在Docker主机文件系统中查看卷，甚至在Docker主机中对其进行读取数据或者写入数据操作。在第9章中就有一个示例——复制某个文件到Docker主机的卷目录下，在容器该卷中立刻就能看到对应的文件。

读者可以在Docker服务以及容器中使用`myvol` 卷了。例如，可以在`docker container run` 命令后增加参数`--flag` 将卷挂载到新建容器中。稍后通过几个例子进行说明。

```shell
[root@VM-0-2-centos website]# docker container  run -idt --name voltainer --mount source=bizvol,target=/vol ubuntu

[root@VM-0-2-centos website]# docker container exec -it voltainer sh

# df -h
Filesystem      Size  Used Avail Use% Mounted on
overlay          50G   17G   31G  35% /
tmpfs            64M     0   64M   0% /dev
tmpfs           1.9G     0  1.9G   0% /sys/fs/cgroup
shm              64M     0   64M   0% /dev/shm
/dev/vda1        50G   17G   31G  35% /vol
tmpfs           1.9G     0  1.9G   0% /proc/acpi
tmpfs           1.9G     0  1.9G   0% /proc/scsi
tmpfs           1.9G     0  1.9G   0% /sys/firmware
```



