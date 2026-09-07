# 🛒 TRON 商城 Bot 完整操作指南

## 📱 目录

1. [Bot 基本操作](#1-bot-基本操作)
2. [管理员面板使用](#2-管理员面板使用)
3. [账号上传教程](#3-账号上传教程)
4. [用户购买流程](#4-用户购买流程)
5. [订单管理](#5-订单管理)
6. [价格随机化机制](#6-价格随机化机制)
7. [链上支付确认](#7-链上支付确认)
8. [故障排除](#8-故障排除)

---

## 1. Bot 基本操作

### 启动 Bot

```bash
cd ~/tg-shop-bot
python3 bot/main.py
```

### Bot 命令

| 命令 | 功能 |
|------|------|
| `/start` | 开始使用商城 |
| `/help` | 查看帮助 |
| `/products` | 查看商品列表 |
| `/orders` | 查看我的订单 |
| `/admin` | 管理员面板 |

### 管理员 vs 用户菜单

**管理员菜单:**
- 📥 上传账号
- 📦 库存管理
- 📊 订单管理
- 📈 库存统计
- 🛒 商城

**用户菜单:**
- 📱  텔레그램 계정
- 📷  인스타그램 계정
- 📘  페이스북 계정
- ℹ️  도움말

---

## 2. 管理员面板使用

### 2.1 上传账号

管理员可以通过两种方式上传账号：

#### 方式一：单个添加

1. 进入 Bot → `/admin`
2. 点击 "📥 上传账号"
3. 点击 "📝 单一添加"
4. 按照提示输入账号信息：
   ```
   账号类型: telegram_basic / telegram_premium / telegram_channel
   用户名: @testuser123
   密码: Password123
   邮箱: test@mail.com (可选)
   手机: +821012345678 (可选)
   描述: 1년 이상 계정 (可选)
   ```

#### 方式二：批量添加

1. 进入 Bot → `/admin`
2. 点击 "📥 上传账号"
3. 点击 "📋 大량添加"
4. 输入 JSON 格式：
   ```json
   [
     {"type": "telegram_basic", "username": "@user1", "password": "pass1"},
     {"type": "telegram_premium", "username": "@user2", "password": "pass2"},
     {"type": "instagram_basic", "username": "@insta1", "password": "insta1"}
   ]
   ```

### 2.2 库存管理

点击 "📦 库存管理" 查看当前库存：

```
📦 库存统计
总库存: 5
可购买: 5
已售: 0

类型统计:
  • 일반 텔레그램 계정: 3개
  • 프리미엄 텔레그램 계정: 2개
```

### 2.3 订单管理

点击 "📊 订单管理" 查看所有订单：

```
📋 订单列表:
✅ ORD1788755129967WEA6KF
   用户: 8427378474 | 账号: 2개
   金额: 101 TRX
   状态: 待发货

🟡 ORD1788755129967XXX
   用户: 8733970362 | 账号: 1개
   金额: 50 TRX
   状态: 已支付
```

---

## 3. 账号上传教程

### 3.1 支持的账号类型

| 类型代码 | 名称 | 基础价格 (TRX) | 基础价格 (USDT) |
|---------|------|---------------|-----------------|
| `telegram_basic` | 一般 텔레그램 계정 | 50 | 10 |
| `telegram_premium` | 프리미엄 텔레그램 계정 | 150 | 30 |
| `telegram_channel` | 텔레그램 채널 계정 | 80 | 15 |
| `instagram_basic` | 인스타그램 계정 | 100 | 20 |
| `instagram_premium` | 인스타그램 프리미엄 | 200 | 40 |
| `facebook_basic` | 페이스북 계정 | 60 | 12 |
| `facebook_business` | 페이스북 비즈니스 계정 | 120 | 24 |

### 3.2 批量上传示例

```json
[
  {
    "type": "telegram_basic",
    "username": "@korea_user1",
    "password": "KoreaPass1!",
    "email": "korea1@mail.com",
    "phone": "+821012345678",
    "description": "생성일 2년, 전화번호검증 완료"
  },
  {
    "type": "telegram_premium",
    "username": "@premium_kr",
    "password": "Premium#2024",
    "email": "premium@mail.com",
    "phone": "+821098765432",
    "description": "생성일 5년, 프로필 고급, 검증완료"
  },
  {
    "type": "instagram_basic",
    "username": "@insta_kr_01",
    "password": "Insta123!",
    "email": "insta@mail.com",
    "description": "팔로워 5000+, 활동적"
  }
]
```

### 3.3 使用 API 批量上传

```bash
curl -s -X POST "https://951951.org/api/admin/batch-add" \
  -H "X-User-Id: 8427378474" \
  -H "Content-Type: application/json" \
  -d '{
    "accounts": [
      {"type": "telegram_basic", "username": "@user1", "password": "pass1"},
      {"type": "telegram_basic", "username": "@user2", "password": "pass2"},
      {"type": "instagram_basic", "username": "@insta1", "password": "insta1"}
    ]
  }'
```

---

## 4. 用户购买流程

### 4.1 购买步骤

```
用户 → @Shop_idbot → /start
         ↓
    选择商品类型 (Telegram/Instagram/Facebook)
         ↓
    选择账号数量 (1/2/3个)
         ↓
    选择支付方式 (TRX/USDT)
         ↓
    发送支付到指定地址
         ↓
    点击 "✅ 支付确认"
         ↓
    接收账号信息
```

### 4.2 价格示例

**用户购买 2 个 텔레그램 일반 계정:**

```
基础价格: 50 TRX/개
数量: 2개
随机波动: 1.001 ~ 1.03

实际价格:
  TRX: 101 TRX (50 × 2 × 1.01)
  USDT: $20.27 (10 × 2 × 1.0135)
```

### 4.3 支付地址

```
💰 TRON 钱包地址:
   TWk75rL7Y7yS2eLZhLEpA7UeVVWpTJTih4

📅 支付期限: 30분
```

---

## 5. 订单管理

### 5.1 订单状态

| 状态 | 含义 | 操作 |
|------|------|------|
| `pending` | 待支付 | 等待用户支付 |
| `paid` | 已支付 | 等待管理员发货 |
| `delivered` | 已发货 | 用户已接收账号 |
| `insufficient_stock` | 库存不足 | 管理员需补充库存 |

### 5.2 管理员发货

当用户点击 "支付确认" 后，管理员需要：

1. 检查链上交易是否确认
2. 点击 "📊 订单管理"
3. 选择待发货订单
4. 系统自动从库存中分配账号
5. 发送账号信息给用户

### 5.3 自动发货 (可选)

配置 TronGrid API 密钥后，可以启用自动发货：

```bash
# 在 .env 中添加
TRON_GRID_API_KEY=your_api_key_here
```

---

## 6. 价格随机化机制

### 6.1 随机波动算法

```javascript
// 波动范围: 1.001 ~ 1.03 (0.1% ~ 3%)
const variance = 1.001 + Math.random() * 0.029;

// 计算实际价格
const trx = Math.round(basePrice.trx * quantity * variance);
const usdt = Math.round(basePrice.usdt * quantity * variance * 100) / 100;
```

### 6.2 为什么需要随机化？

**问题:** 如果两个用户同时购买相同数量的相同商品，价格会完全一样。

**解决方案:** 随机波动确保每个订单的价格都有细微差异。

**示例:**
```
用户A购买2个 텔레그램 일반 계정:
  波动: 1.012
  价格: 101.2 TRX → 101 TRX (取整)

用户B购买2个 텔레그램 일반 계정:
  波动: 1.003
  价格: 100.3 TRX → 100 TRX (取整)

用户C购买2个 텔레그램 일반 계정:
  波动: 1.028
  价格: 102.8 TRX → 103 TRX (取整)
```

这样即使同时有多个买家，他们的支付金额也会略有不同，便于追踪。

---

## 7. 链上支付确认

### 7.1 支付验证流程

```
用户支付 → 用户点击 "支付确认" → API调用 /api/payment/verify
                                              ↓
                                       检查链上交易
                                              ↓
                                       验证金额和地址
                                              ↓
                                       确认订单状态
                                              ↓
                                       分配账号发货
```

### 7.2 模拟验证 (当前)

当前实现为模拟验证（测试环境）：

```javascript
// api/worker.js
order.status = 'paid';
order.paid_at = new Date().toISOString();
return response({confirmed: true, order});
```

### 7.3 真实链上验证 (生产环境)

集成 TronGrid API 进行真实验证：

```javascript
// 检查 TRX 转账
async function verifyTRX(txHash, expectedAmount) {
  const tx = await fetch(`https://api.trongrid.io/v1/transactions/${txHash}`);
  const result = await tx.json();
  return result.ret && result.ret.length > 0;
}

// 检查 USDT 转账
async function verifyUSDT(txHash, expectedAmount) {
  const tx = await fetch(`https://api.trongrid.io/v1/transactions/${txHash}/raw`);
  const result = await tx.json();
  // 解析交易输入验证USDT转账
  return result.txID === txHash;
}
```

---

## 8. 故障排除

### 8.1 Bot 无法启动

```bash
# 检查依赖
pip3 list | grep python-telegram-bot

# 检查 .env 配置
cat ~/tg-shop-bot/.env | head -5

# 手动测试 Bot Token
curl -s "https://api.telegram.org/bot<YOUR_TOKEN>/getMe" | python3 -m json.tool
```

### 8.2 API 无法访问

```bash
# 检查 Worker 状态
curl -s "https://951951.org/api/health"

# 检查 Cloudflare Workers
CF_TOKEN="your_token"
curl -s "https://api.cloudflare.com/client/v4/accounts/<ACCOUNT_ID>/workers/scripts" \
  -H "Authorization: Bearer $CF_TOKEN"
```

### 8.3 库存不足

```bash
# 查看当前库存
curl -s "https://951951.org/api/admin/stats" -H "X-User-Id: 8427378474"

# 添加新账号
curl -s -X POST "https://951951.org/api/admin/add-account" \
  -H "X-User-Id: 8427378474" \
  -H "Content-Type: application/json" \
  -d '{"type":"telegram_basic","username":"@newuser","password":"newpass"}'
```

### 8.4 管理员无法访问

确保管理员 ID 在 `.env` 中正确配置：
```bash
ADMIN_IDS=8427378474,8733970362
```

---

## 📋 快速参考卡

### 管理员操作

```bash
# 启动 Bot
cd ~/tg-shop-bot && python3 bot/main.py

# 添加账号
curl -X POST https://951951.org/api/admin/add-account \
  -H "X-User-Id: 8427378474" \
  -H "Content-Type: application/json" \
  -d '{"type":"telegram_basic","username":"@user","password":"pass"}'

# 查看库存
curl -s https://951951.org/api/admin/stats -H "X-User-Id: 8427378474"
```

### 用户操作

```
1. 打开 Telegram，搜索 @Shop_idbot
2. 发送 /start
3. 选择商品类型
4. 选择购买数量 (1/2/3)
5. 选择支付方式 (TRX/USDT)
6. 发送支付到指定地址
7. 点击 "支付确认"
8. 接收账号信息
```

---

## 🔧 技术架构

```
用户设备
    ↓
Telegram Bot (@Shop_idbot)
    ↓
Cloudflare Workers (https://951951.org/api/)
    ↓
Python Bot (~/tg-shop-bot/bot/main.py)
    ↓
TRON 区块链 (支付验证)
```

---

## 📞 支持

如有问题，请检查：
1. Bot 是否运行: `ps aux | grep bot/main.py`
2. API 是否可用: `curl https://951951.org/api/health`
3. 库存是否充足: `curl https://951951.org/api/admin/stats`
4. GitHub 代码是否最新: `git pull`
