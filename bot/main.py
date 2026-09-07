"""
Telegram Bot - Cloudflare Pages 연동
"""
import os
import json
import logging
import asyncio
import aiohttp
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",")]
API_URL = os.getenv("APP_URL", "https://tron-shop.pages.dev")

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """시작 명령어"""
    user = update.effective_user
    
    if is_admin(user.id):
        admin_menu = [
            [InlineKeyboardButton("📊 주문 관리", callback_data="admin_orders")],
            [InlineKeyboardButton("📦 상품 관리", callback_data="admin_products")]
        ]
        await update.message.reply_text(
            f"👋 {user.first_name}님, 관리자 권한으로 접속했습니다.\n\n"
            f"관리자 메뉴를 사용하세요.",
            reply_markup=InlineKeyboardMarkup(admin_menu)
        )
    else:
        keyboard = [
            [InlineKeyboardButton("📱 텔레그램 계정", callback_data="category_telegram")],
            [InlineKeyboardButton("📷 인스타그램 계정", callback_data="category_instagram")],
            [InlineKeyboardButton("📘 페이스북 계정", callback_data="category_facebook")],
            [InlineKeyboardButton("ℹ️ 도움말", callback_data="help")]
        ]
        await update.message.reply_text(
            f"🛒欢迎光临TRON商城!\n\n"
            f"{user.first_name}님, 구매할 상품을 선택하세요.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """콜백 핸들러"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    
    if data == "help":
        await query.edit_message_text("""
📖 사용 방법

1. 상품을 선택하세요
2. Mini App에서 결제 정보를 확인하세요
3. TRX 또는 USDT(TRC20)로 결제하세요
4. 결제 완료 후 상품을 수령하세요

💰 결제 방법
- TRX 직접 전송
- USDT (TRC20) 전송

⚠️ 주의사항
- 결제 후 24시간 이내에 상품을 수령하세요
""")
    
    elif data.startswith("category_"):
        category = data.split("_")[1]
        category_names = {
            "telegram": "텔레그램 계정",
            "instagram": "인스타그램 계정",
            "facebook": "페이스북 계정"
        }
        
        keyboard = []
        for p in PRODUCTS:
            if category == "telegram" and "텔레그램" in p["name"]:
                keyboard.append([InlineKeyboardButton(
                    f"{p['id']}. {p['name']} ({p['price_trx']} TRX)",
                    callback_data=f"product_{p['id']}"
                )])
            elif category == "instagram" and "인스타그램" in p["name"]:
                keyboard.append([InlineKeyboardButton(
                    f"{p['id']}. {p['name']} ({p['price_trx']} TRX)",
                    callback_data=f"product_{p['id']}"
                )])
            elif category == "facebook" and "페이스북" in p["name"]:
                keyboard.append([InlineKeyboardButton(
                    f"{p['id']}. {p['name']} ({p['price_trx']} TRX)",
                    callback_data=f"product_{p['id']}"
                )])
        
        keyboard.append([InlineKeyboardButton("⬅️ 뒤로가기", callback_data="back")])
        
        await query.edit_message_text(
            f"{category_names.get(category, category)} 카테고리",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif data.startswith("product_"):
        product_id = int(data.split("_")[1])
        product = next((p for p in PRODUCTS if p["id"] == product_id), None)
        
        if product:
            message = f"""
{product['id']}. {product['name']}

가격: {product['price_trx']} TRX / ${product['price_usdt']} USDT
재고: {product['stock']}개

Mini App에서 자세한 결제 과정을 확인하세요.
"""
            keyboard = [
                [InlineKeyboardButton(
                    "🛒 Mini App으로 구매하기",
                    web_app=WebAppInfo(url=f"{API_URL}/miniapp?product={product_id}")
                )],
                [InlineKeyboardButton("⬅️ 뒤로가기", callback_data="back")]
            ]
            await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif data == "back":
        await query.edit_message_text("메인 메뉴로 돌아가겠습니다.", reply_markup=await create_main_keyboard(user_id))
    
    elif data == "admin_orders":
        if not is_admin(user_id):
            await query.answer("접근 권한이 없습니다.", show_alert=True)
            return
        
        keyboard = [
            [InlineKeyboardButton("📋 전체 주문 목록", url=f"{API_URL}/api/admin/orders")],
            [InlineKeyboardButton("⬅️ 뒤로가기", callback_data="back")]
        ]
        await query.edit_message_text(
            "📊 주문 관리",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif data == "admin_products":
        if not is_admin(user_id):
            await query.answer("접근 권한이 없습니다.", show_alert=True)
            return
        
        products_text = "📦 상품 목록:\n\n"
        for p in PRODUCTS:
            products_text += f"{p['id']}. {p['name']} - {p['price_trx']} TRX / 재고: {p['stock']}\n"
        
        keyboard = [[InlineKeyboardButton("⬅️ 뒤로가기", callback_data="back")]]
        await query.edit_message_text(products_text, reply_markup=InlineKeyboardMarkup(keyboard))

async def create_main_keyboard(user_id: int):
    """메인 키보드 생성"""
    if is_admin(user_id):
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🛒 쇼핑몰", callback_data="shop")],
            [InlineKeyboardButton("📊 주문 관리", callback_data="admin_orders")],
            [InlineKeyboardButton("📦 상품 관리", callback_data="admin_products")]
        ])
    else:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("📱 텔레그램 계정", callback_data="category_telegram")],
            [InlineKeyboardButton("📷 인스타그램 계정", callback_data="category_instagram")],
            [InlineKeyboardButton("📘 페이스북 계정", callback_data="category_facebook")],
            [InlineKeyboardButton("ℹ️ 도움말", callback_data="help")]
        ])

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"오류: {context.error}")

def main():
    """메인 함수"""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN이 설정되지 않았습니다.")
        return
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_error_handler(error_handler)
    
    logger.info("봇 시작 중...")
    app.run_polling()

if __name__ == "__main__":
    main()
