```shell

ceph -c /data/cos/ceph.DATASTOR_A.conf daemon osd.0 status

ceph -c /data/cos/ceph.DATASTOR_A.conf daemon osd.0 config set osd_heartbeat_min_healthy_ratio 0

// minimum number of peers that must be reachable to mark ourselves
// back up after being wrongly marked down.

```



```c++
// (seconds) how long before we decide a peer has failed
// This setting is read by the MONs and OSDs and has to be set to a equal value in both settings of the configuration
OPTION(osd_heartbeat_grace, OPT_INT)
  

bool OSD::_is_healthy()
{
  if (!cct->get_heartbeat_map()->is_healthy()) {
    dout(1) << "is_healthy false -- internal heartbeat failed" << dendl;
    return false;
  }

  if (is_waiting_for_healthy()) {
    Mutex::Locker l(heartbeat_lock);
    utime_t cutoff = ceph_clock_now();
    cutoff -= cct->_conf->osd_heartbeat_grace;
    int num = 0, up = 0;
    for (map<int,HeartbeatInfo>::iterator p = heartbeat_peers.begin();
	 p != heartbeat_peers.end();
	 ++p) {
      if (p->second.is_healthy(cutoff))
	++up;
      ++num;
    }
    if ((float)up < (float)num * cct->_conf->osd_heartbeat_min_healthy_ratio) {
      dout(1) << "is_healthy false -- only " << up << "/" << num << " up peers (less than "
	      << int(cct->_conf->osd_heartbeat_min_healthy_ratio * 100.0) << "%)" << dendl;
      return false;
    }
  }

  return true;
}
```



状态判断

```c++
  bool is_waiting_for_healthy() const {
    return state == STATE_WAITING_FOR_HEALTHY;
  }

```



设置时机

```c++
void OSD::start_waiting_for_healthy()
{
  dout(1) << "start_waiting_for_healthy" << dendl;
  set_state(STATE_WAITING_FOR_HEALTHY);
  last_heartbeat_resample = utime_t();

  // subscribe to osdmap updates, in case our peers really are known to be dead
  osdmap_subscribe(osdmap->get_epoch() + 1, false);
}
```

![image-20210722000803016](.osd%20map.assets/image-20210722000803016.png)