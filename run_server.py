"""
서버 실행 스크립트 - Telegram Bot + API
"""
import asyncio
import threading
import time
import os
from dotenv import load_dotenv

load_dotenv()

def run_api_server():
    """API 서버 실행"""
    from api.server import app
    port = int(os.getenv("API_PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

def run_bot():
    """봇 실행"""
    from bot.main import main
    main()

def main():
    """메인 실행"""
    print("=" * 50)
    print("🛒 TRON 쇼핑몰 봇 시작")
    print("=" * 50)
    print(f"🤖 Bot Token: {'*' * 10}{os.getenv('BOT_TOKEN', '')[-4:]}")
    print(f"🌐 API 포트: {os.getenv('API_PORT', 5000)}")
    print(f"🔗 Mini App: {os.getenv('APP_URL', 'http://localhost:3000')}")
    print("=" * 50)
    
    # API 서버 스레드
    api_thread = threading.Thread(target=run_api_server, daemon=True)
    api_thread.start()
    print("✅ API 서버 시작됨")
    
    time.sleep(2)
    
    # Bot 메인 스레드
    run_bot()

if __name__ == "__main__":
    main()
