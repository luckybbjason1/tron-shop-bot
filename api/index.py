"""
Cloudflare Pages 함수 - 서버리스 봇
"""
import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 관리자 ID
ADMIN_IDS = [int(x.strip()) for x in os.getenv('ADMIN_IDS', '').split(',')]

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

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

def create_response(status: int, data: dict) -> dict:
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(data)
    }

async def handler(event):
    """Cloudflare Pages 함수 핸들러"""
    path = event['request']['url'].split('/api/')[-1] if '/api/' in event['request']['url'] else ''
    method = event['request']['method']
    
    logger.info(f"Request: {method} /{path}")
    
    # CORSpreflight
    if method == 'OPTIONS':
        return create_response(200, {})
    
    # 라우팅
    if path == 'products' and method == 'GET':
        return create_response(200, {"products": PRODUCTS})
    
    elif path == 'payment/create' and method == 'POST':
        body = json.loads(event['request']['body'] or '{}')
        order_id = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{os.urandom(3).hex().upper()}"
        order = {
            "order_id": order_id,
            "user_id": body.get('user_id'),
            "product_id": body.get('product_id'),
            "amount": body.get('amount'),
            "currency": body.get('currency', 'TRX'),
            "payment_address": os.getenv('TRON_WALLET_ADDRESS'),
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        orders[order_id] = order
        return create_response(200, order)
    
    elif path.startswith('order/') and method == 'GET':
        order_id = path.split('/')[-1]
        if order_id in orders:
            return create_response(200, orders[order_id])
        return create_response(404, {"error": "Order not found"})
    
    elif path == 'admin/orders' and method == 'GET':
        user_id = int(event['request']['headers'].get('x-user-id', 0))
        if not is_admin(user_id):
            return create_response(403, {"error": "Forbidden"})
        return create_response(200, {"orders": list(orders.values())})
    
    elif path == 'health' and method == 'GET':
        return create_response(200, {"status": "ok", "timestamp": datetime.now().isoformat()})
    
    return create_response(404, {"error": "Not found"})

# AWS Lambda 형식 호환
def lambda_handler(event, context):
    import asyncio
    return asyncio.get_event_loop().run_until_complete(handler(event))
