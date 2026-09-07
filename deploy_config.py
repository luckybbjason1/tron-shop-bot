import json
from datetime import datetime

# Cloudflare Pages 구성
config = {
    "name": "tron-shop-bot",
    "framework": None,
    "build": {
        "command": "pip install -r requirements.txt",
        "output": "api",
        "directory": "api"
    },
    "env": {
        "BOT_TOKEN": "8979245044:AAEEL7N4l8T2ovFgNe3JuKDywHUnbuTVMac",
        "TRON_NETWORK": "mainnet",
        "TRON_WALLET_ADDRESS": "TWk75rL7Y7yS2eLZhLEpA7UeVVWpTJTih4",
        "USDT_CONTRACT_ADDRESS": "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",
        "ADMIN_IDS": "8427378474,8733970362",
        "APP_URL": "https://tron-shop.pages.dev"
    }
}

print(json.dumps(config, indent=2))
