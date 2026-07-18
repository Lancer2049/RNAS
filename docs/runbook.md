# RNAS Runbook — 运维手册

## 启动 / 停止

```bash
# 启动所有服务
systemctl start rnas.target

# 仅启动 API（开发模式）
cd /opt/rnas-fastapi && PYTHONPATH=/opt/rnas-fastapi:/opt/rnas-config \
  uvicorn main:app --host 0.0.0.0 --port 8099

# 停止
systemctl stop rnas.target
```

## 重启顺序

1. dnsmasq → 2. accel-ppp → 3. rnas-fastapi

```bash
systemctl restart rnas-dnsmasq && sleep 2 && \
systemctl restart rnas-accel-ppp && sleep 3 && \
systemctl restart rnas-fastapi
```

## 常见故障排查

| 症状 | 检查 | 命令 |
|------|------|------|
| API 返回 401 | JWT token 过期 | `curl -X POST .../api/auth/token -d '{...}'` |
| 会话列表为空 | accel-ppp 未运行 | `systemctl status rnas-accel-ppp` |
| apply 返回 423 | 另一个 apply 进行中 | 等待或 `rm /var/run/rnas-apply.lock` |
| apply 返回 500 | 健康检查失败 | `journalctl -u rnas-accel-ppp -n 50` |
| 配置漂移告警 | 手动改过配置文件 | `rnas-config status --root /etc/rnas` |
| 前端空白 | static/ 未部署 | `ls /opt/rnas-fastapi/static/index.html` |

## 回滚步骤

1. 查看可用快照：`GET /api/v1/config/snapshots`
2. 恢复快照：`POST /api/v1/config/snapshot/{name}/restore`
3. 验证：`GET /api/v1/health`

或手动从快照目录恢复：
```bash
cp -r /etc/rnas/snapshots/<name>/* /etc/rnas/
systemctl restart rnas-accel-ppp
```

## 备份 / 恢复

```bash
# 备份
tar czf rnas-backup-$(date +%Y%m%d).tar.gz \
  /etc/rnas/ /var/lib/rnas/*.db

# 恢复
tar xzf rnas-backup-YYYYMMDD.tar.gz -C /
systemctl restart rnas.target
```
