# TRON Shop Bot - 区块链支付验证指南

## 📚 GitHub 最佳实践来源

### 1. TronScan API
- **文档**: https://docs.tronscan.org
- **特点**: 稳定的区块链浏览器 API
- **优势**: 支持 TRC-20 转账监控
- **限制**: 免费 API 有速率限制

### 2. TronGrid API
- **文档**: https://developers.tron.network/docs/api
- **特点**: TRON 官方节点 API
- **优势**: 实时数据，高可用性
- **限制**: 需要 API Key

### 3. n8n 支付监控工作流
- **仓库**: Automations-Project/n8n-usdt-and-trc20-wallet-tracker
- **特点**: 成熟的支付监控方案
- **优势**: 自动轮询 + 过滤 + 聚合

---

## 🔧 已实现功能

### 1. 实时余额查询
```python
validator.get_usdt_balance()  # USDT 余额
validator.get_trx_balance()   # TRX 余额
```

### 2. 交易监控
```python
validator.get_recent_transactions(limit=50)  # 最近 50 笔交易
```

### 3. 支付验证
```python
validator.check_order_payment(order_id, expected_amount, currency='USDT')
# 返回: {'verified': True/False, 'message': '...'}
```

### 4. 自动发货
```python
validator.deliver_order(order_id, account_data)
```

---

## 📋 使用方式

### 完整购买流程

1. **用户选择商品**
   ```
   /start → 选择类别 → 选择账号 → 选择数量 (1-3)
   ```

2. **生成订单**
   - 订单号: `ORD202409071234567890`
   - 金额: 根据账号类型和数量计算
   - 支付地址: `TWk75rL7Y7yS2eLZhLEpA7UeVVWpTJTih4`

3. **用户支付**
   - 发送 TRX 或 USDT(TRC20)
   - 金额必须匹配订单

4. **系统验证**
   - 点击 "결제 확인" 按钮
   - 系统扫描链上交易
   - 匹配金额和时间戳
   - 确认 19+ 个区块确认

5. **自动发货**
   - 从库存中选择可用账号
   - 更新账号状态为 "sold"
   - 发送账号信息给用户

---

## 🔐 API 密钥获取

### TronScan API Key (推荐)
1. 访问: https://tronscan.org/api-key
2. 注册账号
3. 创建 API Key
4. 添加到 `.env`:
   ```
   TRONSCAN_API_KEY=your_api_key_here
   ```

### TronGrid API Key (可选)
1. 访问: https://developers.tron.network
2. 注册并申请 API Key
3. 添加到 `.env`:
   ```
   TRON_GRID_API_KEY=your_api_key_here
   ```

---

## ⚠️ 注意事项

### 免费版的限制
- TronScan: 1000 请求/天
- TronGrid: 500 请求/分钟

### 解决方案
1. 使用内存缓存（已实现）
2. 降低轮询频率
3. 申请生产级 API Key

### 安全建议
- 不要在 GitHub 提交 API Key
- 使用环境变量存储
- 定期轮换密钥

---

## 🔄 替代方案

### 方案 1: Webhook 监听
```python
# 使用 TronGrid 的 WebSocket API
# 实时接收转账通知
```

### 方案 2: 自托管节点
```bash
# 运行自己的 Tron 节点
# 完全控制，无速率限制
```

### 方案 3: 第三方服务
- **Tatum**: https://tatum.io
- **Covalent**: https://www.covalenthq.com
- **Alchemy**: https://www.alchemy.com

---

## 📊 当前状态

```
✅ 余额查询: 正常
✅ 交易监控: 正常 (需 API Key)
✅ 支付验证: 正常 (模拟模式)
✅ 自动发货: 正常
```

---

## 🚀 下一步优化

1. 添加 WebSocket 实时监听
2. 实现订单过期自动取消
3. 添加支付超时提醒
4. 集成多币种支持 (BTC, ETH)
5. 添加管理员手动确认功能
