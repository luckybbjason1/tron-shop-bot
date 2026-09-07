# TRON Shop - Cloudflare Workers 部署

## 方案变更
由于 Railway 免费版资源限制，改用 **Cloudflare Workers** 托管 API。

## 部署步骤

### 1. 安装 Wrangler CLI
```bash
# 在 Termux 中安装 (需要 Android ARM64 版本)
npm install -g wrangler
```

### 2. 登录 Cloudflare
```bash
wrangler login
```

### 3. 创建 Workers 项目
```bash
cd ~/tg-shop-bot
wrangler deploy
```

### 4. 获取 API URL
部署后会显示类似:
```
https://tron-shop-api.your-account.workers.dev
```

### 5. 更新 Mini App
将 `APP_URL` 更新为 Workers URL。

## 当前状态

| 组件 | 状态 | URL |
|------|------|-----|
| GitHub | ✅ | https://github.com/luckybbjason1/tron-shop-bot |
| Mini App (待部署) | ⏳ | https://tron-shop-miniapp.pages.dev |
| API (Workers) | ⏳ | 待部署 |
| Bot | ✅ | Token: 897924...VMac |

## 环境变量
部署时添加:
- `BOT_TOKEN`: 8979245044:AAEEL7N4l8T2ovFgNe3JuKDywHUnbuTVMac
- `TRON_WALLET_ADDRESS`: TWk75rL7Y7yS2eLZhLEpA7UeVVWpTJTih4
- `ADMIN_IDS`: 8427378474,8733970362
