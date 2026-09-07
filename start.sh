#!/bin/bash
# TRON 쇼핑몰 봇 시작 스크립트

set -e
cd "$(dirname "$0")"

echo "🚀 TRON 쇼핑몰 봇 시작"
echo "========================"

# API 서버 시작
echo "📡 API 서버 시작 (포트 5000)..."
python3 api/http_server.py &
API_PID=$!
echo "  PID: $API_PID"

sleep 1

# Bot 시작
echo "🤖 텔레그램 봇 시작..."
python3 bot/main.py &
BOT_PID=$!
echo "  PID: $BOT_PID"

echo ""
echo "✅ 모든 서비스 시작 완료!"
echo "   API:    http://localhost:5000"
echo "   봇:     Telegram에서 시작"
echo ""
echo "종료: kill $API_PID $BOT_PID"
echo "      또는 Ctrl+C"

trap "kill $API_PID $BOT_PID 2>/dev/null; echo ''; echo '✅ 종료됨'; exit" INT TERM

wait
