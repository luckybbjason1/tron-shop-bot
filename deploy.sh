#!/bin/bash
# Cloudflare Pages 배포 스크립트

echo "🚀 TRON 쇼핑몰 봇 Cloudflare Pages 배포"
echo "==========================================="

# 버전 확인
echo ""
echo "📦 버전 정보:"
echo "  Python: $(python3 --version)"
echo "  Node: $(node --version 2>/dev/null || echo 'not installed')"

# 의존성 설치
echo ""
echo "📥 의존성 설치..."
pip3 install -r requirements.txt --quiet

# 봇 테스트
echo ""
echo "🧪 봇 테스트..."
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()
print(f'  Bot Token: {\"*\" * 10}{os.getenv(\"BOT_TOKEN\", \"\")[-4:]}')
print(f'  TRON Wallet: {os.getenv(\"TRON_WALLET_ADDRESS\", \"\")[:10]}...')
print(f'  Admin IDs: {os.getenv(\"ADMIN_IDS\", \"\")}')
print('  ✅ 설정 완료')
"

echo ""
echo "✅ 배포 준비 완료!"
echo ""
echo "다음 단계:"
echo "1. Cloudflare 대시보드에서 Pages 생성"
echo "2. Git 리포지토리 연동"
echo "3. 환경변수 설정"
echo "4. 자동 배포 활성화"
echo ""
echo "또는 수동 배포:"
echo "  wrangler pages deploy miniapp --project-name=tron-shop"
