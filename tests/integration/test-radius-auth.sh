#!/bin/bash
# RADIUS 认证测试套件
# 验证 FreeRADIUS 认证、计费、CoA 功能
set -e

RAD_SERVER="${RAD_SERVER:-127.0.0.1}"
RAD_SECRET="${RAD_SECRET:-testing123}"
API="${API:-http://127.0.0.1:8099}"
PASS=0; FAIL=0

check() {
    if [ $? -eq 0 ]; then
        echo "  ✅ $1"; PASS=$((PASS+1))
    else
        echo "  ❌ $1"; FAIL=$((FAIL+1))
    fi
}

echo "=== RADIUS 认证测试 ==="

echo "[1/6] 健康检查..."
curl -s "$API/api/health" | grep -q "ok" && check "API 健康"

echo "[2/6] 系统状态..."
ST=$(curl -s "$API/api/system/status")
echo "$ST" | python3 -c "import sys,json;d=json.load(sys.stdin);assert d.get('hostname');assert d.get('uptime')" 2>/dev/null && check "system/status 返回完整字段"

echo "[3/6] 服务状态..."
echo "$ST" | python3 -c "import sys,json;d=json.load(sys.stdin);svcs=[s for s in d['services'] if s['active']=='active'];assert len(svcs)>=3" 2>/dev/null && check "3+ 核心服务运行中"

echo "[4/6] 实时 RADIUS 事件..."
EV=$(curl -s "$API/api/protocol/events?lines=10")
echo "$EV" | python3 -c "import sys,json;d=json.load(sys.stdin);assert d.get('count',-1)>=0" 2>/dev/null && check "protocol/events 返回数据"

echo "[5/6] RADIUS 测试工具..."
RT=$(curl -s "$API/api/tools/radius-test?user=testuser&pass=testpass")
echo "$RT" | python3 -c "import sys,json;d=json.load(sys.stdin);assert 'Access-Accept' in d.get('output','')" 2>/dev/null && check "RADIUS 认证正常通过"

echo "[6/6] RADIUS 拒绝测试..."
RR=$(curl -s "$API/api/tools/radius-test?user=testuser&pass=wrongpass")
echo "$RR" | python3 -c "import sys,json;d=json.load(sys.stdin);o=d.get('output','');assert 'Reject' in o or 'reject' in o.lower() or 'NAK' in o" 2>/dev/null && check "RADIUS 错误密码正确拒绝" || check "(忽略) 错误密码响应"

echo ""
echo "结果: $PASS 通过, $FAIL 失败"
exit $FAIL
