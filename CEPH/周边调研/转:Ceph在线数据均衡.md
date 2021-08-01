## 在线进行数据均衡

[TOC]

### 背景

厂家标称的10T盘是1000进制（1000^4）^，而操作系统是使用1024进制（1024^4）， 所以10T盘在操作系统只有9TiB（严格来说1TB<1TiB，不过很多场合不这样严格区分）左右，即从绝对数角度的1000^4 /1024^4=90%左右。
Ceph在估算总容量时，默认假设一个盘最多只能用到95%，所以一个10T盘其实只有8.55TiB可用。
另外，由于数据分布不可能绝对的均衡，文件系统的内部数据结构也需要占用一些空间，这8.55TiB也不可能全部可用，目前对这种损耗没有绝对精确的计算方法，凭借经验大概取个D=90%吧。

所以，在适当均衡后，一个厂商标称容量为C的硬盘，大概可以看到`C*0.9*0.95*D=C*0.9*0.95*0.9=0.77C`的容量。

- 一个集群N副本，总共X块容量为C的HDD，则总容量大概为`0.77C*X/N`。
- 一个集群为K+M（这里好像是4+2）的EC，总共X块容量为C的HDD，则总容量大概为`0.77C*X*K/(K+M)`。

TCE-CSP中的Ceph在数据不均衡的情况下，会导致各个磁盘消耗量不同——有些磁盘已经消耗比较多，而另一些磁盘的容量却比较富余。由于Ceph计算总容量时，是基于木桶原理，这样D的折损会比较大。

在早期部署TCE-CSP时，由于文档不完善，没有指导一线在部署完成时就进行离线数据均衡。另为，由于扩容等原因，也可能导致数据分布不均衡。建议对这样的集群进行在线调权，实现数据均衡，提高集群的可用容量和性能。

举例说明；

### 步骤

```shell
1. 确认从控制台确认存储池剩余容量超过20%以上（数据均衡需要临时空间，剩余容量太小，可能无法安全进行数据均衡）

2. 将crush_reweight_online.py拷贝到一台CSP的物理服务器S，假设路径为/data/crush_reweight_online.py（下述的操作均假设在S上进行）

3. 创建/etc/ceph/ceph.conf软链接
ln -s $(ls /data/cos/ceph.*.conf | head -1) /etc/ceph/ceph.conf

4. 获取存储池名
POOL_NAME=$(ceph osd pool ls | grep buckets.data)

5. 检查当前的数据分布情况，一般“overload between max and average”在5%以下且多次--doit后没有明显下降，结束流程
python crush_reweight_online.py --poolname $POOL_NAME --check

6. 在正式调权以前，先模拟评估（dryrun）以下，大概哪些OSD的权重会被调整
python crush_reweight_online.py --poolname $POOL_NAME --overload 105 --dryrun

7. 如果发现被修改的OSD比较多可以调大--overload的值，一般一次修改的OSD个数10个左右为宜，以减少对业务的冲击
python crush_reweight_online.py --poolname $POOL_NAME --overload ${PROPPER_VALUE} --dryrun

8. 在第7补确认${PROPPER_VALUE}后，执行调权（该操作会发动数据迁移，建议在业务低峰期进行）
python crush_reweight_online.py --poolname $POOL_NAME --overload ${PROPPER_VALUE} --doit

9. 等待集群恢复active+clean
watch -d ceph -s

10. 回到步骤5
```

### crush_reweight_online.py

```python
import sys, commands, time
import argparse, json, collections

# Recommend to run this tool on mon host and the user should have sudo priviledge
# Assume all the pools have the same replica count
 
def parse_and_check_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--poolname", type = str, dest = 'poolname', help = "pool names to do crush reweight, separated by comma", required = True)
    parser.add_argument("--overload", type = int, dest = 'overload', help = "overload percentage of pg num per osd, default is 105", default=105)
    parser.add_argument("--dryrun", dest = 'dryrun', action = "store_true", help = "dryrun crush reweight and print the latest weight value")
    parser.add_argument("--doit", dest = 'doit', action = "store_true", help = "do crush reweight really")
    parser.add_argument("--check", dest = 'check', action = "store_true", help = "check and print osd's pg num")
    
    args = parser.parse_args()
    if (args.overload < 100):
        print("[ERR] --overload should be equal or greater than 100")
        sys.exit(1)
    
    if (args.check):
        print("[INFO] --check is set, will check each osd's pg num only, --dryrun or --doit will be ignored")
        action = "check"
    elif (args.dryrun):
        print("[INFO] --dryrun is set, will dryrun crush reweight only, --doit will be ignored")
        action = "dryrun"
    elif (args.doit):
        print("[INFO] --doit is set, will really do crush reweight")
        action = "doit"
    else:
        print("[ERR] --check, --dryrun or --doit should be set one of them")
        sys.exit(1)
    
    pool_id = get_pool_id(args.poolname)
    if (not pool_id):
        print("[ERR] --poolname doesn't find the correct pool id")
        sys.exit(1)
    return (pool_id, args.overload, action)
    
def get_pool_id(pool_name):
    ceph_cmd = "ceph osd lspools"
    pool_json = __run_ceph_cmd(ceph_cmd)
    pool_name_list = pool_name.split(",")
    pool_id_list = []
    for item in pool_json:
        if item['poolname'] in pool_name_list:
            pool_id_list.append(int(item['poolnum']))
    return pool_id_list

def get_osd_pg_stats(expected_pool_id):
    ceph_cmd = "ceph pg dump"
    pg_json = __run_ceph_cmd(ceph_cmd)
    
    pgs_per_osd = collections.defaultdict(int)
    acting_size = 0
    total_pgs = 0
    for p in pg_json['pg_stats']:
        current_pool_id = int(p['pgid'].split('.')[0])
        if (current_pool_id not in expected_pool_id):
            continue
        
        acting_size = len(p['acting'])
        if (acting_size == 0):
            print("[ERR] acting size from pg dump is 0")
            sys.exit(1)
            
        total_pgs += 1
        for osd in p['acting']:
            if not pgs_per_osd[osd]:
                pgs_per_osd[osd] = 0
            pgs_per_osd[osd] += 1
    return (pgs_per_osd, acting_size, total_pgs)

def get_osd_weight_stats():
    ceph_cmd = "ceph osd tree"
    osd_json = __run_ceph_cmd(ceph_cmd)
    
    weights_per_osd = collections.defaultdict(float)
    #total_osd_weights = 0
    for o in osd_json['nodes']:
        if o['type'] == 'osd':
            osd_id = o['id']
            crush_weight = float(o['crush_weight'])
            weights_per_osd[osd_id] = crush_weight
            #total_osd_weights += crush_weight
    return weights_per_osd

def is_ceph_health_ok():
    ceph_cmd = "ceph health"
    health_json = __run_ceph_cmd(ceph_cmd)
    if (health_json['overall_status'] == "HEALTH_OK"):
        return True
    return True

def do_check_only(pool_id):
    pgs_per_osd, acting_size, total_pgs = get_osd_pg_stats(pool_id)
    orderd_pgs_per_osd = sorted(pgs_per_osd.iteritems(), key = lambda t: t[1])
    min_osd = orderd_pgs_per_osd[0][0]
    min_pg = orderd_pgs_per_osd[0][1]
    max_osd = orderd_pgs_per_osd[-1][0]
    max_pg = orderd_pgs_per_osd[-1][1]
    avg_pg = (total_pgs * acting_size) / len(pgs_per_osd)
    max_gap = (max_pg - avg_pg) * 100.0 / avg_pg 
    print("########## current status ##########")
    print("[INFO] pool id: %s" % str(pool_id))
    print("[INFO] total pgs: %d" % total_pgs)
    print("[INFO] acting size: %d" % acting_size)
    print("[INFO] expected average pg/osd: %d" % avg_pg)
    print("[INFO] min pg/osd: %d on osd.%d" % (min_pg, min_osd))
    print("[INFO] max pg/osd: %d on osd.%d" % (max_pg, max_osd))
    print("[INFO] overload between max and average: %.5f%%" % max_gap)
    print("########## current status end ##########")

'''
    How do we do online crush reweight:
    1. get every osd's current pg num and the total pgs for the specified pool from pg dump
    2. get every osd's current crush reweight from osd tree
    3. calculate the expected max pg num per osd via formula: current avg pg num * expected overload
    4. from the osd who has the highest pg num, we decrease crush reweight if osd's current pg num is higher than the expected max pg num:
       4.1. calculate the new crush reweight via formula: current osd's crush reweight * (current avg pg num / current osd's pg num)
       4.2. accumulate the total decreased crush reweight
       4.3. do crush reweight for this osd
    5. from the osd who has the lowest pg num, we increase crush reweight if the total decreased crush weight is not *0*
       5.1. calculate the new crush reweight like 4.1
       5.2. reduce the total decreased crush reweight
       5.3. do crush reweight for this osd
    6. wait for some time to let cluster be aware of the change of crush reweight
    7. wait and check the cluster health to be OK
'''
def do_crush_reweight(pool_id, expected_overload, is_dryrun):
    pgs_per_osd, acting_size, total_pgs = get_osd_pg_stats(pool_id)
    avg_pg = (total_pgs * acting_size) / len(pgs_per_osd)
    expected_overload /= 100.0
    weights_per_osd = get_osd_weight_stats()
    
    print("[INFO] start crush reweight:")
    print("[INFO] expected average pg/osd: %f" % avg_pg)
    print("[INFO] expected overload: %f" % expected_overload)
    print("########## decrease weight ##########")
    des_pgs_per_osd = sorted(pgs_per_osd.iteritems(), key = lambda t: t[1], reverse=True)
    weights_changed = 0
    osd_changed = 0
    for osd_pg in des_pgs_per_osd:
        osd = osd_pg[0]
        cur_pg_num = osd_pg[1]
        if (cur_pg_num > avg_pg * expected_overload):
            new_weight = round(weights_per_osd[osd] * (float(avg_pg) / cur_pg_num), 5)
            weights_changed += (weights_per_osd[osd] - new_weight)
            osd_changed += 1
            print("OSD.%s: %d pgs, crush_weight: %.5f -> %.5f" % (osd, cur_pg_num, weights_per_osd[osd], new_weight))
            
            if (not is_dryrun):
                ceph_cmd = "ceph osd crush reweight osd.%d %.5f" % (osd, new_weight)
                __run_ceph_cmd(ceph_cmd, need_json = False)
        else:
            break
    
    print("%d osds changed, %.5f weights decreased" % (osd_changed, weights_changed))
    print("########## decrease weight end ##########")
    
    if (osd_changed == 0):
        print("[INFO] no need to do crush reweight")
        return 
     
    print("########## increase weight ##########")    
    asc_pgs_per_osd = sorted(pgs_per_osd.iteritems(), key = lambda t: t[1])
    osd_changed = 0
    for osd_pg in asc_pgs_per_osd:
        osd = osd_pg[0]
        cur_pg_num = osd_pg[1]
        if (weights_changed <= 0):
            break
        
        new_weight = round(weights_per_osd[osd] * (float(avg_pg) / cur_pg_num), 5)
        weights_changed -= (new_weight - weights_per_osd[osd])
        osd_changed += 1
        print("OSD.%s: %d pgs, crush_weight: %.5f -> %.5f" % (osd, cur_pg_num, weights_per_osd[osd], new_weight))
        
        if (not is_dryrun):
            ceph_cmd = "ceph osd crush reweight osd.%d %.5f" % (osd, new_weight)
            __run_ceph_cmd(ceph_cmd, need_json = False)
            
    print("%d osds changed" % osd_changed)
    print("########## increase weight end ##########")
    
    print("[INFO] crush reweight is done, but need to wait for cluster to be healthy")
    cnt = 10
    time.sleep(10)
    while (not is_ceph_health_ok() and cnt > 0):
        time.sleep(3)
        cnt -= 1
    
    if (cnt == 0):
        print("[WRN] cluster has not became healthy, pls have a manual check")
    else:
        print("[INFO] crush reweight is done and cluster is healthy now")
    
def __run_ceph_cmd(ceph_cmd, need_json = True):
    ceph_cmd += " --format=json 2>/dev/null"
    ret, json_out = commands.getstatusoutput(ceph_cmd)
    if (ret != 0):
        print("[ERR] ceph cmd fails:\ncmd:%s\nret val:%s" % (ceph_cmd, str(ret)))
        sys.exit(1)
    
    if (need_json):    
        try:
            json_data = json.loads(json_out)
        except Exception, e:
            print("[ERR] ceph cmd fails to output json format:\ncmd:%s\noutput:%s\nexception:%s" % (ceph_cmd, json_out, str(e)))
            sys.exit(1)
        return json_data
            
def main():
    pool_id, overload, action = parse_and_check_args()
    if (not is_ceph_health_ok()):
        print("[WRN] ceph cluster is not health OK, prefer not to do crush reweight")
        sys.exit(1)
    
    if (action == "check"):
        do_check_only(pool_id)
    elif (action == "dryrun"):
        do_crush_reweight(pool_id, overload, True)
    elif (action == "doit"):
        do_crush_reweight(pool_id, overload, False)
   

if __name__ == '__main__':
    main()


```





