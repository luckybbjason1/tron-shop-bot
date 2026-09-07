# 🛒 TRON 쇼핑몰 봇 - 최종 배포 가이드

## ✅ 설정 완료
- **Bot Token**: `8979245044:AAEEL7N4l8T2ovFgNe3JuKDywHUnbuTVMac`
- **관리자 IDs**: 8427378474, 8733970362
- **수령 주소**: `TWk75rL7Y7yS2eLZhLEpA7UeVVWpTJTih4`
- **Mini App URL**: `https://tron-shop.pages.dev`

## 📁 프로젝트 구조
```
~/tg-shop-bot/
├── bot/
│   └── main.py              # 텔레그램 봇
├── api/
│   └── index.py             # Cloudflare Pages 함수
├── miniapp/
│   └── index.html           # Mini App (React 없음, 순수 HTML)
├── .env                     # 환경변수
├── requirements.txt
├── deploy.sh
└── DEPLOY.md
```

## 🚀 Cloudflare Pages 배포

### 1단계: Git 저장소 만들기
```bash
cd ~/tg-shop-bot
git init
git add .
git commit -m "Initial commit"
git branch -M main

# GitHub 저장소 생성 후 연동
git remote add origin https://github.com/yourusername/tron-shop-bot.git
git push -u origin main
```

### 2단계: Cloudflare Pages 설정
1. https://dash.cloudflare.com -> **Pages** -> **Create a project**
2. **Connect to Git** 선택
3. 저장소 선택
4. 빌드 설정:
   ```
   Framework preset: None
   Build command: pip install -r requirements.txt
   Output directory: api
   ```
5. **Environment Variables** 추가:
   ```
   BOT_TOKEN = 8979245044:AAEEL7N4l8T2ovFgNe3JuKDywHUnbuTVMac
   TRON_NETWORK = mainnet
   TRON_WALLET_ADDRESS = TWk75rL7Y7yS2eLZhLEpA7UeVVWpTJTih4
   USDT_CONTRACT_ADDRESS = TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t
   ADMIN_IDS = 8427378474,8733970362
   APP_URL = https://tron-shop.pages.dev
   ```

### 3단계: Mini App 호스팅
Mini App HTML 파일을 Cloudflare Pages에 별도 배포:
```bash
# miniapp 폴더를 독립된 Pages 프로젝트로 배포
wrangler pages deploy miniapp --project-name=tron-shop-miniapp
```
생성된 URL을 `.env`의 `APP_URL`에 설정.

### 4단계: Telegram Bot 설정
```
@BotFather에서:
/newbot → bot 생성 완료
/mybots → 봇 선택 → Bot Settings → Menu Button → Configure menu button
URL: https://tron-shop.pages.dev/miniapp
```

## 📱 사용 방법
1. Telegram에서 봇 검색하여 시작
2. `/start` 명령어 실행
3. 상품 카테고리 선택
4. Mini App에서 TRX/USDT 결제
5. 지갑 주소로 결제 전송
6. 관리자가 트랜잭션 확인 후 상품 배송

## 🔒 보안 참고
- `.env` 파일은 절대 Git에 커밋하지 마세요
- `TRON_WALLET_PRIVATE_KEY`는 운영 서버에만 사용
- Cloudflare Pages는 serverless이므로 상태 유지 안됨 (주문 데이터는 주기적으로 백업 필요)

## ⚠️ 제한사항
- Cloudflare Pages 함수는 30초 제한
- 데이터베이스 없음 (임시 메모리 저장)
- 프로DUCTION에는 PostgreSQL + VPS 권장
