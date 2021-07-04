# 问题考虑

1. 社区版的硬盘点灯，主要是基于orchestrator interface作为接口，以cephadm, rook等作为后端，根本实现是依赖了一个libstoragemgmt库生成的lsmcli实现的。目前仍在开发中（仅在O版）。

2. 社区版引入这个device manager功能更多的是想要通过orch实现硬件管理、甚至是故障预测功能，点灯只是其中的一个小功能。

3. libstoragemgmt库是个中立的库，里面通过plugins的形式实现了不同厂商硬盘的管理。本质上是集成了众多厂商的管理工具，然后对外提供统一的接口来管理。

4. 进行点灯的时候，需要enclosure id和slot id。这是在libstoragemgmt库内部来实现的，外部只需传入磁盘id。

5. libstoragemgmt库中涉及到的所有可执行文件都需要手动下载安装。在内网环境可以下好所有rpm包以及依赖，通过自定义repo的方式安装。

6. 社区O版专门开放了自定义接口，来允许使用lsmcli之外的工具，这可以说明libstoragemgmt本身所能支持的硬件是有限的。

   

## libstoragemgmt能够支持的

1. HP的卡（即能够用ssacli管理的卡）
2. Adaptec的卡（即能够用arcconf管理的卡）

## libstoragemgmt不能支持的

1. 可能不支持NVMe：

```
 static int _sas_addr_get(char *err_msg, const char *disk_path, char *tp_sas_addr) {
   ...
   /* TODO(Gris Ge): Add support of NVMe enclosure */
     
```

1. LSI MegaRAID插件代码中未实现点灯功能。（minghaocong在原有的CSP硬盘点灯中完成过，该库为什么没有实现？）
2. 不支持Intel的卡，需要用`ledmon`。

# 社区O版硬盘点灯实现

> ceph社区中硬盘点灯功能仅在O版开发，计划完成后backport到N版中。

## 上层接口：orchestrator

orchestrator模块使用统一的接口来管理集群，作为ceph mgr的粘合器，然后调用到具体实现的方法中，例如salt, rook, ssh等任何实现了点灯功能的代码。

> 路线图：[mgr/orchestrator: device lights](https://tracker.ceph.com/issues/39091)
>
> ceph-mgr orchestrator modules: https://www.bookstack.cn/read/ceph-en/67cc4a96b2677b91.md
>
> 主要代码提交：[mgr/orchestrator:device lights](https://github.com/ceph/ceph/pull/26768/files)[mgr/dashboard: Add support for blinking enclosure LEDs](https://github.com/ceph/ceph/pull/31851)

基本架构如下所示：[CEPH-MGR ORCHESTRATOR MODULES](https://docs.ceph.com/en/latest/mgr/orchestrator_modules/?highlight=led)

![image-20201222123554566](file:///Users/shelocwang/Documents/DevDocument/%E8%B0%83%E7%A0%94%E6%8A%A5%E5%91%8A/.1.CSP%E8%B0%83%E7%A0%94%EF%BC%9A%E7%A1%AC%E7%9B%98%E7%82%B9%E7%81%AF%E5%8A%9F%E8%83%BD.assets/image-20201222123554566.png?lastModify=1625363573)

以上都是管理接口，最终的实现是调用了`lsmcli`。该可执行文件由libstoragemgmt库生成。这是一个通用的存储介质管理库，通过plugin的方式支持不同厂家命令行调用的扩展。

他们实现了硬盘标识、硬盘状态监测、故障预测、依赖组件众多功能。此处仅考虑点灯功能。

**举例：cephadm的接口设计**

> orchestrator -> cephadm -> lsmcli，支持自定义接口。

实现是调用了lsmcli，

```shell
 lsmcli local-disk-ident-led-on --path $path
```

也可以通过自定义的方式来通过特定的程序执行（ https://github.com/ceph/ceph/pull/37901/files）：

```shell
ceph config-key set mgr/cephadm/blink_device_light_cmd '<my jinja2 template>'
ceph config-key set mgr/cephadm/<host>/blink_device_light_cmd '<my jinja2 template>'
```

其实现方式为：

```python
#src/pybind/mgr/cephadm/module.py
@forall_hosts
def blink(host, dev, path):
  # 通过渲染模板来获得命令
  cmd_line = self.template.render('blink_device_light_cmd.j2',
                                  {
                                    'on': on,
                                    'ident_fault': ident_fault,
                                    'dev': dev,
                                    'path': path
                                  },
                                  host=host)
  cmd_args = shlex.split(cmd_line)

  out, err, code = self._run_cephadm(
    host, 'osd', 'shell', ['--'] + cmd_args,
    error_ok=True)
```

而默认这个模板渲染出来的是通过lsmcli来实现的磁盘点灯功能：

```shell
# blink_device_light_cmd.j2
lsmcli local-disk-{{ ident_fault }}-led-{{'on' if on else 'off'}} --path '{{ path or dev }}'
```

### 代码流程

```python
#src/pybind/mgr/orchestrator/module.py
@_cli_write_command(
        prefix='device light',
        cmd_args='name=enable,type=CephChoices,strings=on|off '
                 'name=devid,type=CephString '
                 'name=light_type,type=CephChoices,strings=ident|fault,req=false '
                 'name=force,type=CephBool,req=false',
        desc='Enable or disable the device light. Default type is `ident`\n'
             'Usage: device light (on|off) <devid> [ident|fault] [--force]')
    def _device_light(self, enable, devid, light_type=None, force=False):
        # type: (str, str, Optional[str], bool) -> HandleCommandResult
        light_type = light_type or 'ident'
        on = enable == 'on'
        if on:
            return self.light_on(light_type, devid)
        else:
            return self.light_off(light_type, devid, force)
          
def light_on(self, fault_ident, devid):
        # type: (str, str) -> HandleCommandResult
        assert fault_ident in ("fault", "ident")
        locs = self._get_device_locations(devid)
        if locs is None:
            return HandleCommandResult(stderr='device {} not found'.format(devid),
                                       retval=-errno.ENOENT)

        getattr(self, fault_ident).add(devid)
        self._save()
        self._refresh_health()
        completion = self.blink_device_light(fault_ident, True, locs)
        self._orchestrator_wait([completion])
        return HandleCommandResult(stdout=str(completion.result))
```

 与libstoragemgmt交互的python接口，通过lsmcli获得状态：

```python
#lsmdisk.py,
def _query_lsm(self, func, path):
  """Common method used to call the LSM functions, returning the function's result or None"""

  # if disk is None, lsm is unavailable so all calls should return None
  if self.disk is None:
    return None

  method = getattr(self.disk, func)
  try:
    output = method(path)
    except LsmError as err:
      logger.error("LSM Error: {}".format(err._msg))
      self.error_list.add(err._msg)
      return None
    else:
      return output
    
#获取LED状态
@property
def led_status(self):
  """Fetch LED status, store in the LSMDisk object and return current status (int)"""
  if self.led_bits is None:
    self.led_bits = self._query_lsm('led_status_get', self.dev_path) or 1
    return self.led_bits
  else:
    return self.led_bits

#检查是否支持led fault:
@property
def led_fault_support(self):
  """Query the LED state to determine FAULT support: Unknown, Supported, Unsupported (str)"""
  if self.led_status == 1:
    return "Unknown"

  fail_states = (
    lsm_Disk.LED_STATUS_FAULT_ON + 
    lsm_Disk.LED_STATUS_FAULT_OFF + 
    lsm_Disk.LED_STATUS_FAULT_UNKNOWN
  )

  if self.led_status & fail_states == 0:
    return "Unsupported"

  return "Supported"
```

## libstoragemgmt库简介

这是个通用库，对外提供一个API，通过插件的形式支持不同厂家的存储硬件管理功能。该库生成了`usr/bin/lsmcli`供其他用户调用。

> [libstorageMgmt](https://libstorage.github.io/libstoragemgmt-doc/doc/user_guide.html#supported-hardware) is a vendor neutral library that provides an API and tools for managing SAN arrays and local hardware RAID adapters. This is a community open source project (LGPL 2.1+ license), providing, but not limited to, the following features:
>
> - Storage system, pool, volume, filesystem, disk monitoring.
> - Volume create, delete, resize, and mask.
> - Volume snapshot, replication create and delete.
> - NFS file system create, delete, resize and expose.
> - Access group create, edit, and delete.
>
> Server resources such as CPU and interconnect bandwidth are not utilized because the operations are all done on the array.
>
> https://libstorage.github.io/libstoragemgmt-doc/doc/user_guide.html
>
> 安装：https://libstorage.github.io/libstoragemgmt-doc/doc/install.html

ceph中是通过调用lsmcli的方式来调用libstoragemgmt:

```shell
# ceph Octopus源代码
# blink_device_light_cmd.j2
lsmcli local-disk-{{ ident_fault }}-led-{{'on' if on else 'off'}} --path '{{ path or dev }}'
```

支持的API:

```shell
lsmcli volume-cache-info vci volume-ident-led-on vilon \
                volume-ident-led-off viloff local-disk-list ldl \
                system-read-cache-pct-update srcpu \
                local-disk-ident-led-on ldilon \
                local-disk-ident-led-off ldiloff \
                local-disk-fault-led-on ldflon \
                local-disk-fault-led-off ldfloff"
```

python的命令行脚本：

```python
# libstoragemgmt库源代码
# tools/lsmcli/cmdline.py
aliases = dict(
    ldilon='local-disk-ident-led-on',
    ldiloff='local-disk-ident-led-off',
    ldflon='local-disk-fault-led-on',
    ldfloff='local-disk-fault-led-off',
)
...
_CONNECTION_FREE_COMMANDS = ['local-disk-list',
                             'local-disk-ident-led-on',
                             'local-disk-ident-led-off',
                             'local-disk-fault-led-on',
                             'local-disk-fault-led-off']
```

对不同硬件的支持是通过在libstoragemgmt中的plugin的形式实现的。

在libstoragemgmt中搜索volume_ident_led_on， lsm_plug_volume_ident_led_on，可以看到相同的接口的不同实现：

![image-20210704095846052](.O%E7%89%88%E7%A1%AC%E7%9B%98%E7%82%B9%E7%81%AF%E5%8A%9F%E8%83%BD%E8%B0%83%E7%A0%94.assets/image-20210704095846052-5363928.png)

是通过plugin的形式各自添加的：

![image-20210704095912854](.O%E7%89%88%E7%A1%AC%E7%9B%98%E7%82%B9%E7%81%AF%E5%8A%9F%E8%83%BD%E8%B0%83%E7%A0%94.assets/image-20210704095912854-5363954.png)

那么是如何知道使用哪个库中的可执行文件呢？

查看[官方文档](https://libstorage.github.io/libstoragemgmt-doc/doc/user_guide.html)可以发现，是通过不同的URI来指出的，这一点也可以从库的支持情况表中发现。

## libstoragemgmt库的支持情况

[Current plugins and supported storage products](https://libstorage.github.io/libstoragemgmt-doc/doc/user_guide.html)



| Plugin        | URI Syntax                                         | Support Products                                             |
| ------------- | -------------------------------------------------- | ------------------------------------------------------------ |
| Simulator C   | `simc://`                                          | Only for development or testing client applications          |
| Simulator     | `sim://`                                           | Only for development or testing client applications          |
| ONTAP         | `ontap://<user>@<host>`                            | [NetApp ONTAP](https://libstorage.github.io/libstoragemgmt-doc/doc/array_conf/NetApp_Conf.html) |
| SMI-S         | `smispy://<user>@<host>`                           | [EMC VMAX/DMX/VNX/CX](https://libstorage.github.io/libstoragemgmt-doc/doc/array_conf/EMC_Conf.html) |
| SMI-S         | `smispy://<user>@<host>`                           | [NetApp ONTAP](https://libstorage.github.io/libstoragemgmt-doc/doc/array_conf/NetApp_Conf.html) |
| SMI-S         | `smispy://<user>@<host>`                           | [IBM XIV/DS/SVC](https://libstorage.github.io/libstoragemgmt-doc/doc/array_conf/IBM_Conf.html) |
| SMI-S         | `smispy://<user>@<host>?namespace=root/lsiarray13` | [NetApp E-Series](https://libstorage.github.io/libstoragemgmt-doc/doc/array_conf/NetAppE_Conf.html) |
| SMI-S         | `smispy://<user>@<host>`                           | [Huawei HVS](https://libstorage.github.io/libstoragemgmt-doc/doc/array_conf/Huawei_Conf.html) |
| SMI-S         | `smispy://<user>@<host>`                           | [Other Array with SMI-S 1.4+](https://libstorage.github.io/libstoragemgmt-doc/doc/array_conf/SMIS_General_Conf.html) |
| Targetd       | `targetd://<user>@<host>`                          | [Linux Targetd](https://libstorage.github.io/libstoragemgmt-doc/doc/array_conf/TGT_Conf.html) |
| Nstor         | `nstor://<user>@<host>`                            | [NexentaStor 4.x/3.x](https://libstorage.github.io/libstoragemgmt-doc/doc/array_conf/Nstor_Conf.html) |
| LSI MegaRAID  | `megaraid://`                                      | [LSI MegaRAID](https://libstorage.github.io/libstoragemgmt-doc/doc/array_conf/LSI_Conf.html) |
| SMI-S         | `smispy://<user>@<host>?namespace=root/LsiMr13`    | [LSI MegaRAID](https://libstorage.github.io/libstoragemgmt-doc/doc/array_conf/LSI_Conf.html) |
| HP SmartArray | `hpsa://`                                          | [HP SmartArray](https://libstorage.github.io/libstoragemgmt-doc/doc/array_conf/HPSA_Conf.html) |

查看代码，可以看到代码中看起来是以RAID的方式命名的，但是实际上也支持HBA方式。搜索`HBA_MODE`和`System.MODE_HARDWARE_RAID`, `System.MODE_HBA`，举例说明：

```python
if 'Controller Mode' in ctrl_data:
  hwraid_mode = ctrl_data['Controller Mode']
  if 'RAID' in hwraid_mode:
    mode = System.MODE_HARDWARE_RAID
    elif 'HBA' in hwraid_mode:
      mode = System.MODE_HBA
      else:
        mode = System.MODE_UNKNOWN
        status_info += ' mode=[%s]' % str(hwraid_mode)
```



### 1. HP SmartArray：ssacli

> [ssacli替代了原来的hpssacli，但用法与之前相同](https://gist.github.com/mrpeardotnet/a9ce41da99936c0175600f484fa20d03)。

```python
# libstoragemgmt库源代码
#可执行文件
class SmartArray(IPlugin):
    _DEFAULT_BIN_PATHS = [
        "/usr/sbin/hpssacli", "/opt/hp/ssacli/bld/hpssacli",
        "/usr/sbin/ssacli", "/opt/hp/ssacli/bld/ssacli"]


# plugin/sa_plugin/hpsa.py, 即针对惠普硬盘的调用，实际上是调用了ssacli。
@_handle_errors
def volume_ident_led_on(self, volume, flags=Client.FLAG_RSVD):
  """
        Depend on command:
            ssacli ctrl slot=# ld # modify led=on
            ssacli ctrl slot=# show config detail
        """
  if not volume.plugin_data:
    raise LsmError(
      ErrorNumber.INVALID_ARGUMENT,
      "Ilegal input volume argument: missing plugin_data property")

    (ctrl_num, array_num, ld_num) = volume.plugin_data.split(":")

    try:
      #实际调用接口位置，此处获得了slot id:
      self._sacli_exec(["ctrl", "slot=%s" % ctrl_num, "ld %s" % ld_num, "modify", "led=on"], flag_convert=False)
      except ExecError:
        ctrl_data = next(iter(self._sacli_exec(["ctrl", "slot=%s" % ctrl_num, "show", "config", "detail"]).values()))

        for key_name in list(ctrl_data.keys()):
          if key_name != "Array: %s" % array_num:
            continue
            for array_key_name in list(ctrl_data[key_name].keys()):
              if array_key_name == "Logical Drive: %s" % ld_num:
                raise LsmError(ErrorNumber.PLUGIN_BUG,"volume_ident_led_on failed unexpectedly")
                raise LsmError(ErrorNumber.NOT_FOUND_VOLUME,"Volume not found")
                return None
   
#执行传入的 sacli_cmds ：
def _sacli_exec(self, sacli_cmds, flag_convert=True, flag_force=False):
  """
        If flag_convert is True, convert data into dict.
        """
  sacli_cmds.insert(0, self._sacli_bin)
  if flag_force:
    sacli_cmds.append('forced')
    try:
      output = cmd_exec(sacli_cmds) #此处
      except OSError as os_error:
        if os_error.errno == errno.ENOENT:
          raise LsmError(
            ErrorNumber.INVALID_ARGUMENT,
            "ssacli binary '%s' is not exist or executable." %
            self._sacli_bin)
          else:
            raise

            if flag_convert:
              return _parse_ssacli_output(output)
            else:
              return output
            
#实际执行：
def cmd_exec(cmds):
    """
    Execute provided command and return the STDOUT as string.
    Raise ExecError if command return code is not zero
    """
    cmd_popen = subprocess.Popen(
        cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env={"PATH": os.getenv("PATH")}, universal_newlines=True)
    str_stdout = "".join(list(cmd_popen.stdout)).strip()
    str_stderr = "".join(list(cmd_popen.stderr)).strip()
    errno = cmd_popen.wait()
    if errno != 0:
        raise ExecError(" ".join(cmds), errno, str_stdout, str_stderr)
    return str_stdout    
```

### 2. LSI MegaRAID：MegaCli

> 搜索megaraid_lsmplugin.1.in
>
> 参考： https://www.cnblogs.com/luxiaodai/p/9878747.html#_lab2_4_4、
>
> MegaCli 是LSI公司官方提供的SCSI卡管理工具，由于LSI被收购变成了现在的Broadcom，所以现在想下载MegaCli，需要去Broadcom官网查找Legacy产品支持，搜索MegaRAID即可。关于MegaCli 的使用可以看我的另一篇博文，这里就不再介绍了。
>
> 现在官方有storcli，storcli已经基本代替了megacli，整合了LSI和3ware所有产品。
>
> ==未发现有实现点灯功能的代码，但理论上是可以支持的（为什么没有实现？）==
>
> 实现参考：根据获取到的enclosure id和slot number进行磁盘点灯
>
> ```shell
> #开启磁盘定位灯
> # /opt/MegaRAID/storcli/storcli64 /c0/e64/s3 start locate
> Operating system = Linux 4.14.105-19-beta6
> Controller = 0
> Status = Success
> Description = Start Drive Locate Succeeded.
> #关闭磁盘定位灯
> # /opt/MegaRAID/storcli/storcli64 /c0/e64/s3 stop locate
> Operating system = Linux 4.14.105-19-beta6
> Controller = 0
> Status = Success
> Description = Stop Drive Locate Succeeded.
> ```

在代码中可以看到执行路径有4个：

```python
class MegaRAID(IPlugin):
	_DEFAULT_BIN_PATHS = [
        "/opt/MegaRAID/storcli/storcli64", "/opt/MegaRAID/storcli/storcli",
        "/opt/MegaRAID/perccli/perccli64", "/opt/MegaRAID/perccli/perccli"]
  ...
```

> 参考：磁盘点灯可用命令
>
> https://www.cnblogs.com/luxiaodai/p/9878747.html
>
> storcli64 /cx/ex/sx start locate
>
> storcli64 /cx/ex/sx stop locate
>
> （老版使用megacli）让故障磁盘闪灯
> megacli -PdLocate -start -physdrv[32:11] -a0
>
> 停止闪灯
> megacli -PdLocate -stop -physdrv[32:11] -a0
>
> https://www.cndba.cn/Expect-le/article/3243
>
> - ./perccli show 显示控制器和控制器相关信息的摘要。摘要包括按索引排序的控制器编号。
> - ./perccli /cx show logfile=log.txt /cx指定控制器，其中x是控制器索引 创建RAID控制器日志(ttylog)
> - ./perccli /cx/eall/sall show all > disks.txt 创建包含RAID控制器上所有插槽信息的RAID控制器日志
> - ./perccli /cx show eventloginfo > eventloginfo.txt 创建包含日志文件历史记录的RAID控制器日志

执行函数：



```python
# 将调用 _storcli_exec.
def _storcli_exec(self, storcli_cmds, flag_json=True):
  storcli_cmds.insert(0, self._storcli_bin) # 获得可执行文件地址
  if flag_json:
    storcli_cmds.append(MegaRAID._CMD_JSON_OUTPUT_SWITCH)
    try:
      output = cmd_exec(storcli_cmds) # 执行
      except OSError as os_error:
        if os_error.errno == errno.ENOENT:
          raise LsmError(
            ErrorNumber.INVALID_ARGUMENT,
            "storcli binary '%s' is not exist or executable." %
            self._storcli_bin)
          else:
            raise

            output = re.sub("[^\x20-\x7e]", " ", output)

            if flag_json:
              output_dict = json.loads(output)
              ctrl_output = output_dict.get('Controllers')
              if len(ctrl_output) != 1:
                raise LsmError(
                  ErrorNumber.PLUGIN_BUG,
                  "_storcli_exec(): Unexpected output from MegaRAID "
                  "storcli: %s" % output_dict)

                rc_status = ctrl_output[0].get('Command Status')
                if rc_status.get('Status') != 'Success':
                  detail_status = rc_status['Detailed Status'][0]
                  raise LsmError(
                    ErrorNumber.PLUGIN_BUG,
                    "MegaRAID storcli failed with error %d: %s" %
                    (detail_status['ErrCd'], detail_status['ErrMsg']))
                  real_data = ctrl_output[0].get('Response Data')
                  if real_data and 'Response Data' in list(real_data.keys()):
                    return real_data['Response Data']

                  return real_data
                else:
                  return output
```

需要关注的是如何获得enclosure id和slot id:

```python
#megaraid.py
@_handle_errors
def disks(self, search_key=None, search_value=None,flags=Client.FLAG_RSVD):
  rc_lsm_disks = []
  #模板
  mega_disk_path_regex = re.compile(
    r"""
                ^Drive \ (
                \/c[0-9]+\/             # Controller ID
                (:?e[0-9]+\/){0,1}      # Enclosure ID(optional)
                s[0-9]+                 # Slot ID
                )\ -\ Detailed\ Information$""", re.X)

  for ctrl_num in range(self._ctrl_count()):
    sys_id = self._sys_id_of_ctrl_num(ctrl_num)

    try:
      disk_show_output = self._storcli_exec(
        ["/c%d/eall/sall" % ctrl_num, "show", "all"])
      except ExecError:
        disk_show_output = {}

        try:
          #输出详细信息
          disk_show_output.update(
            self._storcli_exec(
              ["/c%d/sall" % ctrl_num, "show", "all"]))
          except (ExecError, TypeError):
            pass

          for drive_name in list(disk_show_output.keys()):
            re_match = mega_disk_path_regex.match(drive_name)
            if not re_match:
              continue
							#获得path
              mega_disk_path = re_match.group(1)
              # Assuming only 1 disk attached to each slot.
              disk_show_basic_dict = disk_show_output[
                "Drive %s" % mega_disk_path][0]
              disk_show_attr_dict = disk_show_output[drive_name][
                'Drive %s Device attributes' % mega_disk_path]
              disk_show_stat_dict = disk_show_output[drive_name][
                'Drive %s State' % mega_disk_path]

              disk_id = disk_show_attr_dict['SN'].strip()
              disk_name = "Disk %s %s %s" % (
                disk_show_basic_dict['DID'],
                disk_show_attr_dict['Manufacturer Id'].strip(),
                disk_show_attr_dict['Model Number'])
              disk_type = _disk_type_of(disk_show_basic_dict)
              blk_size = size_human_2_size_bytes(
                disk_show_basic_dict['SeSz'])
              blk_count = _blk_count_of(disk_show_attr_dict['Coerced size'])
              status = _disk_status_of(
                disk_show_basic_dict, disk_show_stat_dict)

              plugin_data = "%s:%s" % (
                ctrl_num, disk_show_basic_dict['EID:Slt'])
              vpd83 = disk_show_attr_dict["WWN"].lower()
              if vpd83 == 'na':
                vpd83 = ''
                rpm = _disk_rpm_of(disk_show_basic_dict)
                link_type = _disk_link_type_of(disk_show_basic_dict)

                rc_lsm_disks.append(
                  Disk(
                    disk_id, disk_name, disk_type, blk_size, blk_count,
                    status, sys_id, plugin_data, _vpd83=vpd83, _rpm=rpm,
                    _link_type=link_type))

                return search_property(rc_lsm_disks, search_key, search_value)
```



### 3. Adaptec 的RAID卡：arcconf

> [Adaptec RAID Controller](https://www.thomas-krenn.com/en/wiki/Adaptec_RAID_Controller)
>
> [arcconf官方命令行手册](http://download.adaptec.com/pdfs/user_guides/microsemi_cli_smarthba_smartraid_v3_00_23484_ug.pdf)，搜索IDENTIFY找到点灯相关内容

```python
# libstoragemgmt源代码
#可执行文件：
class Arcconf(IPlugin):
    _DEFAULT_BIN_PATHS = [
        "/usr/bin/arcconf",
        "/usr/sbin/arcconf",
        "/usr/Arcconf/arcconf"]

# plugin/arcconf_plugin/arcconf.py
def volume_ident_led_on(self, volume, flags=Client.FLAG_RSVD):
  """
        :param volume: volume id to be identified
        :param flags: for future use
        :return:
        Depends on command:
            arcconf identify <ctrlNo> logicaldrive <ldNo> time 3600
            default led blink time is set to 1 hour
  """
  if not volume.plugin_data:
    raise LsmError(
      ErrorNumber.INVALID_ARGUMENT,
      "Illegal input volume argument: missing plugin_data property")

    volume_info = volume.plugin_data.split(':')
    ctrl_id = str(volume_info[6])
    volume_id = str(volume_info[4])

    try:
      #实际的硬盘点灯功能：
      self._arcconf_exec(['IDENTIFY', ctrl_id, 'LOGICALDRIVE', volume_id,
                          'TIME', '3600'], flag_force=True)
      except ExecError:
        raise LsmError(ErrorNumber.PLUGIN_BUG,
                       'Volume-ident-led-on failed unexpectedly')

        return None
```

### 4. 模拟：simarray

> ==仅供模拟，未实现==

```python
#plugin/sim_plugins/simarray.py
@_handle_errors
def volume_ident_led_on(self, volume, flags=0):
  sim_volume_id = SimArray._lsm_id_to_sim_id(
    volume.id, LsmError(
      ErrorNumber.NOT_FOUND_VOLUME,
      "Volume not found"))
  sim_vol = self.bs_obj.sim_vol_of_id(sim_volume_id)

  return None
```

## 区分硬盘厂商

libstoragemgmt库的使用时需要通过URI来区分硬盘厂商，有三种方式：

1. export LSMCLI_URI
2. lsmenv sim lsmcli
3. $ENV{HOME}/.lsm_uri中设置

根据官方文档可以看到是通过一个环境变量来区分的。理论上是需要手动指定的。但是该库有perl脚本指定：

根据官方文档可以看到是通过一个环境变量来区分的。理论上是需要手动指定的。但是该库有perl脚本指定：

```perl
sub set_uri($) {
    my $uri = shift;
    $ENV{LSMCLI_URI}   = $uri;
    $ENV{LSM_TEST_URI} = $uri;
}


#调用：
sub call_out($) {
   ...
   print "URI: $uri\n";
   set_uri($uri);
   set_pass($pass);
   ...
}

#最终是在lsmenv时调用的：
sub main() {
    if ( $#ARGV < 0 ) {
        help();
    }

    chk_lsm_user();
    lsm_env_setup();
    if ( $ARGV[0] eq 'lsmd' ) {
        start_lsmd(0);
        exit 0;
    }
    elsif ( $ARGV[0] eq 'lsmdv' ) {
        start_lsmd(1);
        exit 0;
    }
    elsif ( $ARGV[0] eq '-l' ) {
        map { print "$_\n"; } @{ $URI_CFG->{sects} };
        exit 0;
    }
    elsif ( $ARGV[0] eq 'all' ) {
        map { call_out($_) } keys( %{$REF_PRE_BUILD_URI} );
        map { call_out($_) } @{ $URI_CFG->{sects} };
        exit 0;
    }
    elsif ( $ARGV[0] =~ /^-h$|^--help$/ ) {
        help();
    }
    elsif (( is_in_array( [ keys( %{$REF_PRE_BUILD_URI} ) ], $ARGV[0] ) )
        || ( is_in_array( $URI_CFG->{sects}, $ARGV[0] ) ) )
    {
        call_out( $ARGV[0] );#此处
        exit 0;
    }
    print "ERROR: Configuration for '$ARGV[0]' not found\n";
    help();
}

main();
```

继续查看代码，可以看到有如下注释，说明在使用lsmcli前需要先执行lsmenv配置URI相关参数。同时还指出可以使用配置文件

```perl
my $LSM_URI_FILE = "$ENV{HOME}/.lsm_uri";
```

来实现这个功能：

```perl
sub help() {
    my $help_str = <<END;

Usage:
    lsmenv is used for setting up envirionment variables for running lsmcli
    or lsmd in the develop code folder.
    It also read a config file: $LSM_URI_FILE to set up URI and password.

    The sample config file format is:

        [emc]   # dev_alias
        uri=smispy+ssl://admin\@emc-smi?no_ssl_verify=yes
        passwd=#1Password

    The sample command would be:
        lsmenv emc lsmcli list --type POOLS

    The URI for simulator plugins already prebuilded. Please use these command:
        lsmenv sim lsmcli
        lsmenv simc lsmcli

Commands:
    lsmenv lsmd
        # Run the lsmd
    lsmenv -l
        # List all device alias
    lsmenv <dev_alias> lsmcli ...
        # Run lsmcli command on certain device
    lsmenv all lsmcli ...
        # Run lsmcli command on all devices
    lsmenv <dev_alias> <any_command>
        # Run <any_command> with LSM envirionment variables.
END
    print $help_str;
    exit 1;
}
```

并且可以看到在执行lsmd前需要先运行lsmenv:

```perl
sub start_lsmd($) {
    my $flag_valgrind = shift;
    if ($> != 0){
        print "FAIL: Please run lsmenv as root to start lsmd\n";
        exit 1;
    }
	...
}
```

==没找到ceph在哪里设置的URI==]

难道是通过-u传入的？==（也不是）==

```shell
[root@node01 ~]# lsmcli local-disk-fault-led-on -h
usage: lsmcli local-disk-fault-led-on [-h] [-v] [-u <URI>] [-P] [-H]
                                      [-t <SEP>] [-e] [-f] [-w CHILD_WAIT]
                                      [--header] [-b] [-s] --path <DISK_PATH>

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  -u <URI>, --uri <URI>
                        Uniform resource identifier (env LSMCLI_URI)
  -P, --prompt          Prompt for password (env LSMCLI_PASSWORD)
  -H, --human           Print sizes in human readable format
                        (e.g., MiB, GiB, TiB)
  -t <SEP>, --terse <SEP>
                        Print output in terse form with "SEP" as a record separator
  -e, --enum            Display enumerated types as numbers instead of text
  -f, --force           Bypass confirmation prompt for data loss operations
  -w CHILD_WAIT, --wait CHILD_WAIT
                        Command timeout value in ms (default = 30s)
  --header              Include the header with terse
  -b                    Run the command async. Instead of waiting for completion.
                         Command will exit(7) and job id written to stdout.
  -s, --script          Displaying data in script friendly way with additional information(if exists)

cmd required arguments:
  --path <DISK_PATH>    Local disk path
```



使用模拟器测试：

```shell
[root@node01 ~]# lsmcli  plugin-info
Description: Storage simulator Version: 1.8.1

[root@node01 ~]# lsmcli list --type DISKS
```

![image-20201224211644605](.O%E7%89%88%E7%A1%AC%E7%9B%98%E7%82%B9%E7%81%AF%E5%8A%9F%E8%83%BD%E8%B0%83%E7%A0%94.assets/image-20201224211644605.png)

可以看到没有Disk Paths，因此无法传入测试（即使能够传入，代码也只是实现了个假的接口，直接返回）。

## 虚拟机测试

在虚拟机上安装ceph octopus版，

```shell
#部署mon相关省略，详见 https://docs.ceph.com/en/latest/cephadm/install/
...

#可以看到此处使用的后端为cephadm:
[root@node01 mnt]# ceph orch status
Backend: cephadm
Available: True

#添加osd前需清除磁盘
[root@node01 mnt]# ceph orch device zap node01 /dev/sdb --force
/bin/docker:stderr --> Zapping: /dev/sdb
/bin/docker:stderr Running command: /usr/bin/dd if=/dev/zero of=/dev/sdb bs=1M count=10 conv=fsync
/bin/docker:stderr --> Zapping successful for: <Raw Device: /dev/sdb>

#此处可以看到可用的磁盘
[root@node01 mnt]# ceph orch device ls
Hostname  Path      Type  Serial               Size   Health   Ident  Fault  Available  
node01    /dev/sdb  hdd   VB04e88ec7-8d54f5ef  8589M  Unknown  N/A    N/A    Yes        
node01    /dev/sdc  hdd   VB1e5e796d-c6d14ab9  8589M  Unknown  N/A    N/A    Yes       

#使用所有可用磁盘创建osd
[root@node01 mnt]# ceph orch apply osd --all-available-devices
Scheduled osd.all-available-devices update...

#可以看到available变成了No，表示已经被使用了
[root@node01 mnt]# ceph orch device ls
Hostname  Path      Type  Serial               Size   Health   Ident  Fault  Available  
node01    /dev/sdb  hdd   VB04e88ec7-8d54f5ef  8589M  Unknown  N/A    N/A    No         
node01    /dev/sdc  hdd   VB1e5e796d-c6d14ab9  8589M  Unknown  N/A    N/A    No

#查看osd：
[root@node01 mnt]# ceph device  ls
DEVICE                             HOST:DEV    DAEMONS     LIFE EXPECTANCY
VBOX_HARDDISK_VB04e88ec7-8d54f5ef  node01:sdb  osd.0                      
VBOX_HARDDISK_VB1e5e796d-c6d14ab9  node01:sdc  osd.1                      
VBOX_HARDDISK_VB5c565f9a-c54779d1  node01:sda  mon.node01   

#尝试点灯（不知是否是因为虚拟机的原因，失败）
[root@node01 mnt]# ceph device light on VBOX_HARDDISK_VB04e88ec7-8d54f5ef ident
_exception: Unable to affect ident light for node01:sdb. Command: lsmcli local-disk-ident-led-on --path /dev/disk/by-path/pci-0000:00:0d.0-ata-2.0
```

那么就可以参考cephadm中的代码，看官方如何实现osd与磁盘之间的关系，以便获取磁盘位置：

```python
#ceph Octopus, src/pybind/mgr/cephadm/module.py
 @trivial_completion
    def blink_device_light(self, ident_fault: str, on: bool, locs: List[orchestrator.DeviceLightLoc]) -> List[str]:
        """
        Blink a device light. Calling something like::

          lsmcli local-disk-ident-led-on --path $path

        If you must, you can customize this via::

          ceph config-key set mgr/cephadm/blink_device_light_cmd '<my jinja2 template>'
          ceph config-key set mgr/cephadm/<host>/blink_device_light_cmd '<my jinja2 template>'

        See templates/blink_device_light_cmd.j2
        """
        @forall_hosts
        def blink(host, dev, path):
            cmd_line = self.template.render('blink_device_light_cmd.j2',
                                            {
                                                'on': on,
                                                'ident_fault': ident_fault,
                                                'dev': dev,
                                                'path': path
                                            },
                                            host=host)
            cmd_args = shlex.split(cmd_line)

            out, err, code = self._run_cephadm(
                host, 'osd', 'shell', ['--'] + cmd_args,
                error_ok=True)
            if code:
                raise OrchestratorError(
                    'Unable to affect %s light for %s:%s. Command: %s' % (
                        ident_fault, host, dev, ' '.join(cmd_args)))
            self.log.info('Set %s light for %s:%s %s' % (
                ident_fault, host, dev, 'on' if on else 'off'))
            return "Set %s light for %s:%s %s" % (
                ident_fault, host, dev, 'on' if on else 'off')

        return blink(locs)
```

## ceph O 版点灯相关代码提交

```shell
[root@VM-146-97-centos ~/ceph]# git branch
  master
  nautilus
* octopus

[root@VM-146-97-centos ~/ceph]# git log --oneline | grep blink
fe8385a mgr/cephadm: Allow customizing mgr/cephadm/lsmcli_blink_lights_cmd per host
a060e06 mgr/cephadm: customize blink_device_light cmd via j2
e4e3ccf mgr/cephadm: Add extensive test for blink_device_light
4815cc8 mgr/orchestrator: use full device path for blinking lights (if available)
1393ff8 mgr/cephadm: remove redundant /dev when blinking device light
4c43214 mgr/dashboard: Add support for blinking enclosure LEDs
a9b5fa6 mgr/ssh: implement blink_device_light
a70ec42 mgr/orchestrator: Improve ceph CLI for blink lights
3ab4f8f doc/mgr/orchestrator: add `wal` to blink lights
8ed0e78 mgr/dashboard: Datatable error panel blinking on page loading
e4ba609 Merge pull request #796 from ceph/wip-fix-sumblink-distros
9e3650b osd: red is good enough; don't blink
```

[HBA卡与RAID卡](https://blog.csdn.net/weixin_33807284/article/details/92691551?utm_medium=distribute.pc_relevant_t0.none-task-blog-searchFromBaidu-1.control&depth_1-utm_source=distribute.pc_relevant_t0.none-task-blog-searchFromBaidu-1.control)

[光纤网卡、HBA卡与RAID卡](http://www.gzngn.com/gzgqsfq/48475.html)

[故障盘点灯操作](https://www.jianshu.com/p/b58f0cf730bd?utm_campaign=maleskine&utm_content=note&utm_medium=seo_notes&utm_source=recommendation)

[SSD中SATA, M2, PCIE和NVME分别是什么](https://www.zhihu.com/question/48972075)

[存储设备的target id与lun](https://blog.csdn.net/weixin_30312557/article/details/97634327?utm_medium=distribute.pc_relevant.none-task-blog-BlogCommendFromMachineLearnPai2-2.control&depth_1-utm_source=distribute.pc_relevant.none-task-blog-BlogCommendFromMachineLearnPai2-2.control)