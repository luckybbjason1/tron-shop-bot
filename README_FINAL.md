# 🛒 TRON 商城 Bot - 部署完成

## ✅ 已完成

### 核心组件
- **Bot**: @Shop_idbot (8979245044:AAFPB55Qd5TRWZncE2G9_Td7kb3f_UyhR3c)
- **API**: https://951951.org/api/ (Cloudflare Workers, tron-shop-api-v2)
- **收款地址**: TWk75rL7Y7yS2eLZhLEpA7UeVVWpTJTih4
- **管理员**: 8427378474, 8733970362
- **商品**: 7个 (Telegram/Instagram/Facebook 账号)

### 项目位置
- 代码: ~/tg-shop-bot/
- GitHub: https://github.com/luckybbjason1/tron-shop-bot
- Bot 运行中

## 📦 商品列表

| 图标 | 商品名 | TRX | USDT | 库存 |
|------|--------|-----|------|------|
| 📱 | 一般 텔레그램 계정 | 50 | 10 | 50 |
| ⭐ | 프리미엄 텔레그램 계정 | 150 | 30 | 20 |
| 📢 | 텔레그램 채널 계정 | 80 | 15 | 15 |
| 📷 | 인스타그램 계정 | 100 | 20 | 30 |
| 💎 | 인스타그램 프리미엄 | 200 | 40 | 10 |
| 📘 | 페이스북 계정 | 60 | 12 | 40 |
| 🏢 | 페이스북 비즈니스 계정 | 120 | 24 | 15 |

## ⚠️ 待完成

### 1. 设置 Telegram 菜单按钮
```
@BotFather → /menubutton
选择 @Shop_idbot
URL: https://951951.org/
```

### 2. 测试完整流程
1. 在 Telegram 搜索 @Shop_idbot
2. 点击 /start
3. 点击 "🛒 打开商城" 按钮
4. 选择商品 → 选择支付 (TRX/USDT)
5. 发送转账
6. 点击 "支付确认"

## 📁 文件位置
- 项目: ~/tg-shop-bot/
- API 代码: ~/tg-shop-bot/api/worker.js
- Bot 代码: ~/tg-shop-bot/bot/main.py
- 配置: ~/tg-shop-bot/.env
