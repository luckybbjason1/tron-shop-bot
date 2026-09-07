"""
轻量 HTTP API 服务器 — 供 Mini App 调用
替代 Cloudflare Pages Functions（Python 不被支持）
运行在 Termux 本地，Mini App 通过 ngrok/公网访问
"""
import os
import json
import logging
import threading
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

orders = {}
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "8427378474,8733970362").split(",")]

PRODUCTS = [
    {"id": 1, "name": "一般 텔레그램 계정", "price_trx": 50, "price_usdt": 10, "stock": 50, "icon": "📱", "desc": "생성일 1년 이상, 전화번호 검증 완료 계정"},
    {"id": 2, "name": "프리미엄 텔레그램 계정", "price_trx": 150, "price_usdt": 30, "stock": 20, "icon": "⭐", "desc": "생성일 3년 이상, 고급 프로필, 검증 완료"},
    {"id": 3, "name": "텔레그램 채널 계정", "price_trx": 80, "price_usdt": 15, "stock": 15, "icon": "📢", "desc": "가입자 1000명 이상 채널 소유 계정"},
    {"id": 4, "name": "인스타그램 계정", "price_trx": 100, "price_usdt": 20, "stock": 30, "icon": "📷", "desc": "팔로워 5000명 이상, 활동적인 계정"},
    {"id": 5, "name": "인스타그램 프리미엄", "price_trx": 200, "price_usdt": 40, "stock": 10, "icon": "💎", "desc": "팔로워 2만 명 이상, 업계 인증 계정"},
    {"id": 6, "name": "페이스북 계정", "price_trx": 60, "price_usdt": 12, "stock": 40, "icon": "📘", "desc": "실명 프로필, 친구 1000명 이상"},
    {"id": 7, "name": "페이스북 비즈니스 계정", "price_trx": 120, "price_usdt": 24, "stock": 15, "icon": "🏢", "desc": "비즈니스 인증, 광고주 계정"},
]

PAYMENT_ADDRESS = os.getenv("TRON_WALLET_ADDRESS", "TWk75rL7Y7yS2eLZhLEpA7UeVVWpTJTih4")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        logger.info(f"[API] {args[0]}")

    def _json(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if self.path == "/api/health":
            return self._json(200, {"status": "ok", "timestamp": datetime.now().isoformat()})

        if self.path == "/api/products":
            return self._json(200, {"products": PRODUCTS})

        if self.path.startswith("/api/order/"):
            order_id = self.path.split("/")[-1]
            order = orders.get(order_id)
            if order:
                return self._json(200, order)
            return self._json(404, {"error": "Not found"})

        if self.path == "/api/admin/orders":
            user_id = int(self.headers.get("X-User-Id", "0"))
            if user_id not in ADMIN_IDS:
                return self._json(403, {"error": "Forbidden"})
            return self._json(200, {"orders": list(orders.values())})

        return self._json(404, {"error": "Not found"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length else b"{}"
        data = json.loads(body) if body else {}

        if self.path == "/api/payment/create":
            order_id = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{os.urandom(3).hex().upper()}"
            order = {
                "order_id": order_id,
                "user_id": data.get("user_id"),
                "product_id": data.get("product_id"),
                "amount": data.get("amount"),
                "currency": data.get("currency", "TRX"),
                "payment_address": PAYMENT_ADDRESS,
                "status": "pending",
                "created_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(minutes=15)).isoformat(),
            }
            orders[order_id] = order
            logger.info(f"주문 생성: {order_id}")
            return self._json(200, order)

        if self.path == "/api/payment/verify":
            order_id = data.get("order_id")
            tx_hash = data.get("transaction_hash")
            if order_id in orders:
                orders[order_id]["status"] = "paid"
                orders[order_id]["transaction_hash"] = tx_hash
                orders[order_id]["paid_at"] = datetime.now().isoformat()
                logger.info(f"결제 확인: {order_id}")
                return self._json(200, {"order_id": order_id, "status": "paid"})
            return self._json(404, {"error": "Not found"})

        return self._json(404, {"error": "Not found"})


def run(port=5000):
    server = HTTPServer(("0.0.0.0", port), Handler)
    logger.info(f"API 서버 시작: http://0.0.0.0:{port}")
    server.serve_forever()


if __name__ == "__main__":
    port = int(os.getenv("API_PORT", 5000))
    run(port)
