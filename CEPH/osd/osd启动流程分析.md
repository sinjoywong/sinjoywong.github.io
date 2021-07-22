> 原文位置：https://www.cnblogs.com/wujiajun1997/p/14916729.html

# 简介

OSD作为Ceph的核心组件，承担着数据的存储，复制，恢复等功能。本文基于`Luminous`版本通浅析OSD的初始化流程，了解OSD的主要功能、主要数据结构和其他组件的配合情况等。OSD守护进程的启动流程在`ceph_osd.cc`中的主函数中，具体和OSD相关的初始化主要集中在下面几个函数：

- int OSD::pre_init()
- int OSD::init()
- void OSD::final_init()

后文对这三个函数的主要流程进行分析。

# pre_init

pre_init在OSD实例被创建后调用，主要的目的有两个：

- 通过`test_mount_in_use`检查OSD路径是否已经被使用。如果已经被使用，返回`-EBUSY`。
- 如果组件需要使用动态参数变更的机制，需要继承`md_config_t`，并通过`add_observer`加入被观察的key，当这个key的value发生改变时，可以及时观测到。

```c
cct->_conf->add_observer(this);
```

# init

在pre_init后进入init流程，init作为初始化的主要函数，涉及点比较多。主要从如下三个方面入手：

- 主要流程
- 对OSDMap的处理
- 对pg的处理

## 主要流程[#](https://www.cnblogs.com/wujiajun1997/p/14916729.html#主要流程)

- 对OSD和OSDServer的`SafeTimer`进行初始化，`SafeTimer`主要用于周期性执行tick线程；后面通过`add_event_after`启动tick线程。

```cpp
tick_timer.init();
tick_timer_without_osd_lock.init();
service.recovery_request_timer.init();
service.recovery_sleep_timer.init();
```

- 进行store层的`mount`接口进行挂载。

- 通过`getloadavg`获取负载信息，在scrub中需要检测是否负载超出限制。

- 对长对象名称的处理，通过构造name和key达到上限值的对象，调用`validate_hobject_key`进行测试。

- 通过`OSD::read_superblock`读取元数据，decode到osd对应的`superblock`成员。

  ==疑问2021.7.22：什么时候写superblock?写的时候是否写到osd磁盘里？==

  >```c++
  >class OSDSuperblock {
  >public:
  >  uuid_d cluster_fsid, osd_fsid;
  >  int32_t whoami;    // my role in this fs.
  >  epoch_t current_epoch;             // most recent epoch
  >  epoch_t oldest_map, newest_map;    // oldest/newest maps we have.
  >  double weight;
  >
  >  CompatSet compat_features;
  >
  >  // last interval over which i mounted and was then active
  >  epoch_t mounted;     // last epoch i mounted
  >  epoch_t clean_thru;  // epoch i was active and clean thru
  >
  >  OSDSuperblock() : 
  >    whoami(-1), 
  >    current_epoch(0), oldest_map(0), newest_map(0), weight(0),
  >    mounted(0), clean_thru(0) {
  >  }
  >
  >  void encode(bufferlist &bl) const;
  >  void decode(bufferlist::const_iterator &bl);
  >  void dump(Formatter *f) const;
  >  static void generate_test_instances(list<OSDSuperblock*>& o);
  >};
  >WRITE_CLASS_ENCODER(OSDSuperblock)
  >```

- 通过`osd_compat`进行一些特性方面的检查。
- 确认`snap mapper`对象是否存在，不存在的话新建。snap mapper对象保存了对象和对象快照信息。
- 确认`disk perf`和`net perf`对象的存在，不存在的话新建。`disk perf`和`net perf`对象保存了磁盘和网络相关的信息。
- 初始化`ClassHandler`，用来管理动态链接库。
- **通过`get_map`获取superblock记录的epoch对应的OSDMap。具体分析见后文【对OSDMap的处理】。**
- 通过`OSD::check_osdmap_features`检查获取到的OSDMap的特性。
- 通过`OSD::create_recoverystate_perf`创建recovery的pref，然后加入`perfcounters_collection`中，用来追踪recovery阶段的性能。
- 通过`OSD::clear_temp_objects` 遍历所有pg的object，清除OSD down之前的曾经的临时对象。??
- 在`sharded wq`中初始化OSDMap的引用。`sharded wq`是线程池`osd_op_tp`对应的工作队列，内含多个shard对应一组线程负责一个pg。
- **加载OSD上已有的pg，具体分析见后文【对pg的处理】。**
- pref相关 `OSD::create_logger`。
- 将OSD加入`client_messenger`和`cluster_messenger`。前者负责集群外通信，后者负责集群内通信。任何组件想要通讯都需要继承`Dispatcher`，加入`messenger`中并复写相关函数。

```cpp
client_messenger->add_dispatcher_head(this);
cluster_messenger->add_dispatcher_head(this);
```

- 将心跳`Dispatcher`加入到心跳`messenger`中，这些`messenger`对应的群内外的前后心跳。

```cpp
hb_front_client_messenger->add_dispatcher_head(&heartbeat_dispatcher);
hb_back_client_messenger->add_dispatcher_head(&heartbeat_dispatcher);
hb_front_server_messenger->add_dispatcher_head(&heartbeat_dispatcher);
hb_back_server_messenger->add_dispatcher_head(&heartbeat_dispatcher);
```

- 将`objecter`加入到`objecter_messenger`。
- 通过`MonClient::init`初始化`monclient`，任何和`monitor`的通讯需要`monclient`。
- 初始化`mgrclient`，并加入`client_messenger`中。

```cpp
mgrc.init();
client_messenger->add_dispatcher_head(&mgrc);
```

- 设置`logclient`，`logclient`和`monitor`交互，保证了节点间日志的一致性。

```cpp
monc->set_log_client(&log_client);
update_log_config();
```

- 初始化`OSDService`，设置`OSDMap`和`superblock`等成员。在OSDservice的初始化过程中，初始化或开启了一些`timer`和`finisher`。

```cpp
service.init();
service.publish_map(osdmap);
service.publish_superblock(superblock);
service.max_oldest_map = superblock.oldest_map;
```

- 开启一些线程池，并通过`OSD::set_disk_tp_priority`设置线程池优先级。

```cpp
peering_tp.start();
osd_op_tp.start();
remove_tp.start();
recovery_tp.start();
command_tp.start();

set_disk_tp_priority();
```

- 通过`heartbeat_thread.create()`开启心跳。

- 通过调用`MonClient::authenticate`进行`monclient`的鉴权。

- 在OSD启动后，之前的

  ```
  crush
  ```

  可能需要更新。

  - 通过`OSD::update_crush_device_class`更新设备类型，该功能在`Luminous`中引入，可以区分osd是hdd/ssd。读取osd挂载目录的crush_device_class来决定设备类型，没有读取到读默认值，调用mon命令进行应用。
  - 通过`OSD::update_crush_location()`更新`crush`。更新OSD的weight和location，调用mon命令来创建或者移动`bucket`。

- 通过调用`OSDService::final_init()`开启objecter。

- 调用`OSD::consume_map()`。距离分析可以参考另外一篇blog。

- 发送一些`MMonSubscribe`类型的消息。

```cpp
monc->sub_want("osd_pg_creates", last_pg_create_epoch, 0);
monc->sub_want("mgrmap", 0, 0);
monc->renew_subs();
```

- 调用`OSD::start_boot`进入boot流程，关于OSD的boot和状态转化，可以参考我的[另一篇blog](https://www.cnblogs.com/wujiajun1997/p/14962725.html)。

## 对OSDMap的处理[#](https://www.cnblogs.com/wujiajun1997/p/14916729.html#对osdmap的处理)

在初始化过程中，有两个地方进行了OSDMap的获取：

- 获取`superblock`记录的`epoch`对应的OSDMap。
- 加载pg时获取对应的OSDMap。

获取的调用链为：

```cpp
OSD::get_map-->OSDService::get_map-->OSDService::try_get_map
OSDMapRef OSDService::try_get_map(epoch_t epoch)
{
  Mutex::Locker l(map_cache_lock);
  OSDMapRef retval = map_cache.lookup(epoch);
  if (retval) {
    dout(30) << "get_map " << epoch << " -cached" << dendl;
    if (logger) {
      logger->inc(l_osd_map_cache_hit);
    }
    return retval;
  }
  ...
  OSDMap *map = new OSDMap;
  if (epoch > 0) {
    dout(20) << "get_map " << epoch << " - loading and decoding " << map << dendl;
    bufferlist bl;
    if (!_get_map_bl(epoch, bl) || bl.length() == 0) {
      derr << "failed to load OSD map for epoch " << epoch << ", got " << bl.length() << " bytes" << dendl;
      delete map;
      return OSDMapRef();
    }
    map->decode(bl);
  } else {
    dout(20) << "get_map " << epoch << " - return initial " << map << dendl;
  }
  // 加入map_cache缓存
  return _add_map(map);
}
```

- 在`try_get_map`中使用了`map_cache_lock`保护，该所用于保护从cache中获取map的一致性。
- 首先从`map_cache`中查找，如果未找到再通过`OSDService::_get_map_bl`将map从`map_bl_cache`（和前面的MapCache不同）中读取或从磁盘中读取并加入到缓存中。

> Q：这几种cache是在什么时候加入的？
> A：在OSD处理OSDMap消息时（handle_osd_map）中，将map和增量map加入map_bl_cache和map_bl_inc_cache。map_cahche由_add_map添加。

```cpp
bool OSDService::_get_map_bl(epoch_t e, bufferlist& bl)
{
  // * 先检查一下cache中有没有
  bool found = map_bl_cache.lookup(e, &bl);
  if (found) {
    if (logger)
      logger->inc(l_osd_map_bl_cache_hit);
    return true;
  }
  if (logger)
    logger->inc(l_osd_map_bl_cache_miss);
  found = store->read(coll_t::meta(),
		      OSD::get_osdmap_pobject_name(e), 0, 0, bl,
		      CEPH_OSD_OP_FLAG_FADVISE_WILLNEED) >= 0;
  // * 加入map_cache_bl缓存
  if (found) {
    _add_map_bl(e, bl);
  }
  return found;
}
```

# 对pg的处理

前文提到。调用`OSD::load_pgs`对OSD上已有的pg进行加载：

- 通过store层的`list_collections`从硬盘中读取PG（`current`目录下），并遍历。
- **在**`**OSD::load_pgs**`**中有一个优化点，可以通过多线程来加速加载。**

```cpp
for (vector<coll_t>::iterator it = ls.begin();
         it != ls.end();
         ++it) {
      spg_t pgid;
      //对PGTemp和需要清理的pg进行清理
      //recursive_remove_collection函数主要进行了一下几个删除步骤
      // 1. 遍历PG对应的Objects，删除对应的Snap
      // 2. 遍历PG对应的Objects，删除Object
      // 3. 删除PG对应的coll_t
      if (it->is_temp(&pgid) ||
         (it->is_pg(&pgid) && PG::_has_removal_flag(store, pgid))) {
        dout(10) << "load_pgs " << *it << " clearing temp" << dendl;
        recursive_remove_collection(cct, store, pgid, *it);
        continue;
      }
      ...
      // 获取OSD Down前最后的pg对应的OSDMap epoch
      epoch_t map_epoch = 0;
      // 从Omap对象中获取
      int r = PG::peek_map_epoch(store, pgid, &map_epoch);
      ...
       
      if (map_epoch > 0) {
        OSDMapRef pgosdmap = service.try_get_map(map_epoch);
        ...
        //如果获取到了PG对应的OSMap
        pg = _open_lock_pg(pgosdmap, pgid);
      } else {
        //如果没有，就用之前获取的OSDMap
        pg = _open_lock_pg(osdmap, pgid);
      }
      ...
      //读取pg状态和pg log
      pg->read_state(store);
    
      //pg不存在？判断依据是info的history中created_epoch为0
      if (pg->dne()) {
        // 删除pg相关操作
        ...
      }
    ...
    PG::RecoveryCtx rctx(0, 0, 0, 0, 0, 0);
    // 进入Reset状态
    pg->handle_loaded(&rctx);
}
```

> Q：PG为什么会不存在？
> A：可能是在加载的过程中防止PG被移除

- 上述代码中，获取了OSD上pg对应的OSDMap后执行了`_open_lock_pg`，这一步获取了PG对象且对对象进行了加锁，下面来分析一下代码。

```cpp
PG *OSD::_open_lock_pg(
  OSDMapRef createmap,
  spg_t pgid, bool no_lockdep_check)
{
  assert(osd_lock.is_locked());
  //构造PG
  PG* pg = _make_pg(createmap, pgid);
  {
    //读取PGMap的写锁，因为要修改PGMap
    RWLock::WLocker l(pg_map_lock);
    // PG上锁
    pg->lock(no_lockdep_check);
    pg_map[pgid] = pg;
    // PG的引用计数+1
    pg->get("PGMap");  // because it's in pg_map
    // 维护pg_epochs和pg_epoch结构
    service.pg_add_epoch(pg->info.pgid, createmap->get_epoch());
  }
  return pg;
}
```

> **Q：在OSD启动的过程中，已经通过superblock对应的epoch尝试获取了OSDMap，为什么还需要在加载OSD的PG时，获取PG对应的OSDMap？**
> Q：什么时候应该上PG锁？
> A：这里需要拷贝复制，为了保证前后一致性，需要上锁
> Q：pg的引用计数什么时候增加？
> A：类似只能指针的原理，pg作为等号右边的值，给别的变量拷贝赋值了，引用计数+1

- 分析一下`PG::read_state`，主要功能是读取pg log和pg state

```cpp
void PG::read_state(ObjectStore *store, bufferlist &bl)
{
  // 通过PG::read_info读取PG状态
  // PG的元数据信息保存在一个object的omap中
  // 具体分析过程
  int r = read_info(store, pg_id, coll, bl, info, past_intervals,
		    info_struct_v);
  assert(r >= 0);
  ...
  ostringstream oss;
  pg_log.read_log_and_missing(
    store,
    coll,
    info_struct_v < 8 ? coll_t::meta() : coll,
    ghobject_t(info_struct_v < 8 ? OSD::make_pg_log_oid(pg_id) : pgmeta_oid),
    info,
    force_rebuild_missing,
    oss,
    cct->_conf->osd_ignore_stale_divergent_priors,
    cct->_conf->osd_debug_verify_missing_on_start);
  if (oss.tellp())
    osd->clog->error() << oss.str();

  if (force_rebuild_missing) {
    dout(10) << __func__ << " forced rebuild of missing got "
	     << pg_log.get_missing()
	     << dendl;
  }

  // log any weirdness
  log_weirdness();
}
```

# final_init

在`OSD::final_init`中注册`admin socket`命令，这些命令格式为`ceph daemon osd.X xxx`，比如：

```cpp
ceph daemon osd.0 dump_disk_perf
```

# 总结

了解OSD的启动流程，对理解整个OSD模块很有帮助。在启动流程中基本涵盖了OSD工作流程中的各种组件和结构，因为篇幅所限很多地方没有展开，有些地方也存在一些疑问。希望后续能对内容继续深入，逐个击破。