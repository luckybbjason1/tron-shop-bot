# 🛒 TRON 商城 Bot - 部署指南

## ✅ 已完成
- GitHub 仓库: https://github.com/luckybbjason1/tron-shop-bot
- 代码已推送 (commit 941e031)
- Railway 配置文件已添加 (Procfile, railway.toml, app.py)

## ⚠️ Railway API Token 问题

你提供的 token `8c151e57-...` 格式不正确：
- Railway API tokens 以 `rail_` 开头
- 你的 token 是 UUID 格式，可能是项目 ID

**获取正确的 Railway API token:**
1. 登录 https://railway.app
2. 点击右上角头像 → **Account Settings**
3. 左侧菜单 **API**
4. 点击 **Generate Token**
5. 复制生成的 token (以 `rail_` 开头)

## 🚀 手动部署方案

### 方案 1: Railway (推荐)
1. 打开 https://railway.app/new
2. 选择 **Deploy from GitHub repo**
3. 选择 `luckybbjason1/tron-shop-bot`
4. 添加环境变量:
   ```
   BOT_TOKEN=8979245044:AAEEL7N4l8T2ovFgNe3JuKDywHUnbuTVMac
   TRON_WALLET_ADDRESS=TWk75rL7Y7yS2eLZhLEpA7UeVVWpTJTih4
   ADMIN_IDS=8427378474,8733970362
   APP_URL=https://xxx.tron-shop-miniapp.pages.dev
   ```
5. Deploy

### 方案 2: Render.com
1. 登录 https://render.com
2. 创建 New Web Service
3. 连接 GitHub 仓库
4. 设置环境变量
5. Deploy

### 方案 3: 本地运行 + ngrok
```bash
# 安装 ngrok
pip3 install pyngrok

# 运行服务器
cd ~/tg-shop-bot
python3 run_server.py &

# 在另一个终端
python3 -c "from pyngrok import ngrok; print(ngrok.connect(5000).public_url)"
```

## 📱 Mini App 部署

### Cloudflare Pages (手动)
1. https://dash.cloudflare.com → Pages
2. 点击 `tron-shop-miniapp` 项目
3. **Deploy** → **Direct upload**
4. 上传 `~/tg-shop-bot/miniapp.zip`

### 或者使用 Vercel
```bash
# 安装 Vercel CLI
npm install -g vercel

# 部署 Mini App
cd ~/tg-shop-bot/miniapp
vercel --prod
```

## 📋 Telegram Bot 设置

```
@BotFather → /menubutton
选择你的 bot
URL: (Mini App 部署后的 URL)
```

## 🔧 本地测试

```bash
cd ~/tg-shop-bot
./start.sh
```

测试 API:
```bash
curl http://localhost:5000/api/products
curl -X POST http://localhost:5000/api/payment/create \
  -H "Content-Type: application/json" \
  -d '{"user_id":8427378474,"product_id":1,"amount":50,"currency":"TRX"}'
```
