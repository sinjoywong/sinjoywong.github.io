rgw写入日志/var/log/ceph/ceph.DATAACCESS-client.rgw.DATAACCESS.log
日志每天会依赖logrotate进行日志切换
logrotate的切换原理是，先将日志文件改名，然后发signal给rgw，要求rgw换日志文件。
rgw切换日志，需要暂停请求处理，如果在业务高峰期，发生这种操作，是有卡死的风险

logrotate是一个cron.daily，按/etc/anacrontab 的配置应该是在凌晨1点左右触发

