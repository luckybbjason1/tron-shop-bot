# 🛒 TRON 쇼핑몰 봇 - 배포 완료

## ✅ 설정 완료
- **Bot Token**: `8979245044:AAEEL7N4l8T2ovFgNe3JuKDywHUnbuTVMac`
- **관리자 IDs**: 8427378474, 8733970362
- **수령 주소**: `TWk75rL7Y7yS2eLZhLEpA7UeVVWpTJTih4`
- **Mini App**: `https://tron-shop.pages.dev`

## 📁 파일 위치
```
~/tg-shop-bot/
├── bot/main.py           # 텔레그램 봇
├── api/index.py          # Cloudflare Pages 함수
├── miniapp/index.html    # Mini App
├── .env                  # 환경변수
└── DEPLOY.md            # 배포 가이드
```

## 🚀 Cloudflare Pages 배포 순서

### 1. Git 저장소 생성
```bash
cd ~/tg-shop-bot
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/tron-shop-bot.git
git push -u origin main
```

### 2. Cloudflare Pages 연결
1. https://dash.cloudflare.com → Pages → Create
2. Connect to Git → 저장소 선택
3. 빌드 설정:
   - Framework: None
   - Build command: `pip install -r requirements.txt`
   - Output directory: `api`
4. Environment Variables 추가:
   ```
   BOT_TOKEN=8979245044:AAEEL7N4l8T2ovFgNe3JuKDywHUnbuTVMac
   TRON_WALLET_ADDRESS=TWk75rL7Y7yS2eLZhLEpA7UeVVWpTJTih4
   ADMIN_IDS=8427378474,8733970362
   APP_URL=https://tron-shop.pages.dev
   ```

### 3. Mini App 배포
```bash
# miniapp 폴더를 별도 Pages 프로젝트로 배포
wrangler pages deploy miniapp --project-name=tron-shop-miniapp
```

### 4. Telegram 메뉴 버튼 설정
```
@BotFather → /setmenubutton → 봇 선택
URL: https://tron-shop.pages.dev/miniapp
```

## 📱 사용 흐름
1. Telegram에서 봇 시작 → `/start`
2. 상품 카테고리 선택 (텔레그램/인스타/페이스북)
3. Mini App 열기 → 결제 수단 선택 (TRX/USDT)
4. 지갑 주소 복사 → TRON 지갑으로 결제 전송
5. 봇이 결제 확인 → 상품 배송

## ⚠️ 주의사항
- Cloudflare Pages는 serverless이므로 주문 데이터는 메모리만 유지
- 실제 운영 시 PostgreSQL + VPS 전환 권장
- Mini App은 HTTPS 도메인 필요

## 🔧 로컬 테스트
```bash
cd ~/tg-shop-bot
python3 bot/main.py  # 봇 테스트
python3 api/index.py  # API 테스트
```
