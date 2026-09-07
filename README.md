# Telegram 쇼핑몰 봇 - TRON 결제 연동

## 📋 프로젝트 구조
```
tg-shop-bot/
├── bot/
│   └── main.py              # 메인 봇 코드
├── api/
│   └── server.py            # Flask API 서버
├── miniapp/
│   └── index.html           # Telegram Mini App
├── contracts/
│   └── (스마트 컨트랙트)
├── run_server.py            # 실행 스크립트
├── requirements.txt
└── .env.example
```

## 🚀 빠른 시작

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 환경변수 설정
```bash
cp .env.example .env
# .env 파일 편집하여 실제 값 입력
```

### 3. 봇 생성 (Telegram에서)
1. @BotFather에게 `/newbot` 명령어 전송
2. 봇 이름 및 유저네임 설정
3. 생성된 토큰을 `.env` 파일에 저장

### 4. Mini App 설정
1. @BotFather에게 `/newapp` 명령어 전송
2. 봇 선택 및 웹앱 URL 설정
3. 생성된 URL을 `.env` 파일에 저장

### 5. 서버 실행
```bash
python3 run_server.py
```

## 💰 TRON 결제 설정

### 네트워크 선택
- **Mainnet**: 실제 TRON 네트워크
- **Shasta**: 테스트 네트워크 (추천)

### USDT TRC20
- 계약 주소: `TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t`
- 6자리 소수점 (1 USDT = 1,000,000 SUN)

## 📱 사용 방법

### 봇 명령어
- `/start` - 시작
- `/help` - 도움말

### 결제 흐름
1. 사용자가 상품 선택
2. Mini App에서 결제 수단 선택 (TRX/USDT)
3. 지갑 주소 복사 또는 QR 코드 스캔
4. TRON 지갑으로 결제 전송
5. 봇이 트랜잭션 확인
6. 상품 배송 (수동 처리 필요)

## ⚠️ 보안 주의사항
- `TRON_WALLET_PRIVATE_KEY`는 절대 공개 저장소에 커밋하지 마세요
- 운영 서버에서는 HTTPS 사용 필수
- 정기적으로 백업 생성

## 🔧 확장 가능성
- 데이터베이스 연동 (SQLite/PostgreSQL)
- 자동 상품 배송 시스템
- 다중 지갑 분산 결제
- 실시간 가격 알림
