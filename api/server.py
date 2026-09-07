"""
Flask API 서버 - 쇼핑몰 백엔드
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import os
import json
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# 설정
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# 주문 데이터
orders = {}

# 상품 데이터
PRODUCTS = [
    {"id": 1, "name": "일반 텔레그램 계정", "price_trx": 50, "price_usdt": 10, "stock": 50},
    {"id": 2, "name": "프리미엄 텔레그램 계정", "price_trx": 150, "price_usdt": 30, "stock": 20},
    {"id": 3, "name": "텔레그램 채널 계정", "price_trx": 80, "price_usdt": 15, "stock": 15},
    {"id": 4, "name": "인스타그램 계정", "price_trx": 100, "price_usdt": 20, "stock": 30},
    {"id": 5, "name": "인스타그램 프리미엄", "price_trx": 200, "price_usdt": 40, "stock": 10},
    {"id": 6, "name": "페이스북 계정", "price_trx": 60, "price_usdt": 12, "stock": 40},
    {"id": 7, "name": "페이스북 비즈니스 계정", "price_trx": 120, "price_usdt": 24, "stock": 15}
]

@app.route('/api/products', methods=['GET'])
def get_products():
    """상품 목록 반환"""
    return jsonify({"products": PRODUCTS})

@app.route('/api/payment/create', methods=['POST'])
def create_payment():
    """결제 생성"""
    data = request.json
    user_id = data.get('user_id')
    product_id = data.get('product_id')
    amount = data.get('amount')
    currency = data.get('currency', 'TRX')
    
    # 주문 ID 생성
    order_id = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{os.urandom(3).hex().upper()}"
    
    order = {
        "order_id": order_id,
        "user_id": user_id,
        "product_id": product_id,
        "amount": amount,
        "currency": currency,
        "payment_address": os.getenv("TRON_WALLET_ADDRESS", ""),
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + __import__('datetime').timedelta(minutes=15)).isoformat()
    }
    
    orders[order_id] = order
    return jsonify(order)

@app.route('/api/payment/verify', methods=['POST'])
def verify_payment():
    """결제 검증"""
    data = request.json
    order_id = data.get('order_id')
    tx_hash = data.get('transaction_hash')
    
    if order_id not in orders:
        return jsonify({"error": "주문을 찾을 수 없습니다"}), 404
    
    # TRON에서 트랜잭션 검증 (실제 구현 필요)
    # orders[order_id]["status"] = "paid"
    # orders[order_id]["transaction_hash"] = tx_hash
    
    return jsonify({
        "order_id": order_id,
        "status": "confirmed",
        "message": "결제가 확인되었습니다"
    })

@app.route('/api/order/<order_id>', methods=['GET'])
def get_order(order_id):
    """주문 상세 조회"""
    if order_id in orders:
        return jsonify(orders[order_id])
    return jsonify({"error": "주문을 찾을 수 없습니다"}), 404

@app.route('/api/admin/orders', methods=['GET'])
def get_all_orders():
    """전체 주문 목록 (관리자)"""
    password = request.headers.get('X-Admin-Password')
    if password != ADMIN_PASSWORD:
        return jsonify({"error": "접근 권한이 없습니다"}), 403
    
    return jsonify({"orders": list(orders.values())})

@app.route('/api/admin/products', methods=['GET'])
def get_products_admin():
    """상품 목록 (관리자)"""
    password = request.headers.get('X-Admin-Password')
    if password != ADMIN_PASSWORD:
        return jsonify({"error": "접근 권한이 없습니다"}), 403
    
    return jsonify({"products": PRODUCTS})

@app.route('/api/health', methods=['GET'])
def health_check():
    """헬스체크"""
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})

if __name__ == '__main__':
    port = int(os.getenv("API_PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
