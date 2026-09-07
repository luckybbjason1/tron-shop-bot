"""
Telegram Bot - Mini App 연동 버전
HTTP API 서버와 연동하여 결제 처리
"""
import os
import json
import logging
import urllib.request
import urllib.error
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_BASE = os.getenv("API_BASE_URL", "http://localhost:5000")
APP_URL = os.getenv("APP_URL", "https://tron-shop-miniapp.pages.dev")
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "8427378474,8733970362").split(",")]


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def api_get(path: str) -> dict:
    url = f"{API_BASE}{path}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read())
    except Exception as e:
        logger.warning(f"API GET {path} 실패: {e}")
        return {}


def api_post(path: str, data: dict) -> dict:
    url = f"{API_BASE}{path}"
    try:
        body = json.dumps(data).encode()
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception as e:
        logger.error(f"API POST {path} 실패: {e}")
        return {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if is_admin(user.id):
        keyboard = [
            [InlineKeyboardButton("📊 주문 관리", callback_data="admin_orders")],
            [InlineKeyboardButton("📦 상품 목록", callback_data="admin_products")],
            [InlineKeyboardButton("🛒 쇼핑몰", callback_data="shop")]
        ]
        await update.message.reply_text(
            f"👋 {user.first_name}님, 관리자 권한으로 접속했습니다.\n\n"
            f"관리자 메뉴를 사용하세요.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        keyboard = [
            [InlineKeyboardButton("📱 텔레그램 계정", callback_data="category_telegram")],
            [InlineKeyboardButton("📷 인스타그램 계정", callback_data="category_instagram")],
            [InlineKeyboardButton("📘 페이스북 계정", callback_data="category_facebook")],
            [InlineKeyboardButton("ℹ️ 도움말", callback_data="help")]
        ]
        await update.message.reply_text(
            f"🛒 TRON 쇼핑몰에 오신 것을 환영합니다!\n\n"
            f"{user.first_name}님, 구매할 상품을 선택하세요.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data == "back":
        await query.edit_message_text("메인 메뉴로 돌아갑니다.", reply_markup=await main_keyboard(user_id))

    elif data == "help":
        await query.edit_message_text("""
📖 사용 방법

1. 상품을 선택하세요
2. Mini App에서 결제 정보를 확인하세요
3. TRX 또는 USDT(TRC20)로 결제하세요
4. 결제 완료 후 상품을 수령하세요

💰 결제 주소
TRON 지갑으로 직접 전송

⚠️ 결제 후 24시간 이내에 상품을 수령하세요
""")

    elif data.startswith("category_"):
        cat = data.split("_", 1)[1]
        names = {"telegram": "텔레그램 계정", "instagram": "인스타그램 계정", "facebook": "페이스북 계정"}
        products = api_get("/api/products").get("products", [])
        filtered = [p for p in products if cat in p.get("name", "").lower() or
                    (cat == "telegram" and "텔레그램" in p.get("name", "")) or
                    (cat == "instagram" and "인스타그램" in p.get("name", "")) or
                    (cat == "facebook" and "페이스북" in p.get("name", ""))]
        if not filtered:
            filtered = [p for p in products if (cat == "telegram" and "텔레그램" in p["name"]) or
                                                      (cat == "instagram" and "인스타그램" in p["name"]) or
                                                      (cat == "facebook" and "페이스북" in p["name"])]
        keyboard = []
        for p in filtered:
            keyboard.append([InlineKeyboardButton(
                f"{p.get('icon','')} {p['name']} ({p['price_trx']}TRX/${p['price_usdt']})",
                callback_data=f"product_{p['id']}"
            )])
        keyboard.append([InlineKeyboardButton("⬅️ 뒤로가기", callback_data="back")])
        await query.edit_message_text(names.get(cat, cat), reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("product_"):
        pid = int(data.split("_", 1)[1])
        products = api_get("/api/products").get("products", [])
        product = next((p for p in products if p["id"] == pid), None)
        if product:
            msg = f"""
{product.get('icon','')} {product['name']}

{product.get('desc','')}

💰 가격: {product['price_trx']} TRX / ${product['price_usdt']} USDT
📦 재고: {product.get('stock','?')}개
"""
            keyboard = [
                [InlineKeyboardButton(
                    "🛒 Mini App으로 구매하기",
                    web_app=WebAppInfo(url=f"{APP_URL}?product={pid}")
                )],
                [InlineKeyboardButton("⬅️ 뒤로가기", callback_data="back")]
            ]
            await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "admin_orders":
        if not is_admin(user_id):
            await query.answer("접근 권한이 없습니다.", show_alert=True)
            return
        result = api_get("/api/admin/orders")
        order_list = result.get("orders", [])
        if order_list:
            text = "📋 주문 목록:\n\n"
            for o in order_list:
                emoji = "✅" if o.get("status") == "paid" else "⏳"
                text += f"{emoji} {o['order_id']}\n   상품ID: {o.get('product_id')} | 금액: {o.get('amount')} {o.get('currency')}\n   상태: {o.get('status')}\n\n"
            await query.edit_message_text(text)
        else:
            await query.edit_message_text("아직 주문 내역이 없습니다.")

    elif data == "admin_products":
        if not is_admin(user_id):
            await query.answer("접근 권한이 없습니다.", show_alert=True)
            return
        products = api_get("/api/products").get("products", [])
        text = "📦 상품 목록:\n\n"
        for p in products:
            text += f"{p['id']}. {p['name']} — {p['price_trx']}TRX / ${p['price_usdt']}USDT | 재고:{p.get('stock','?')}\n"
        keyboard = [[InlineKeyboardButton("⬅️ 뒤로가기", callback_data="back")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "shop":
        await start(update, context)


async def main_keyboard(user_id: int) -> InlineKeyboardMarkup:
    if is_admin(user_id):
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 주문 관리", callback_data="admin_orders")],
            [InlineKeyboardButton("📦 상품 목록", callback_data="admin_products")],
            [InlineKeyboardButton("🛒 쇼핑몰", callback_data="shop")]
        ])
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 텔레그램 계정", callback_data="category_telegram")],
        [InlineKeyboardButton("📷 인스타그램 계정", callback_data="category_instagram")],
        [InlineKeyboardButton("📘 페이스북 계정", callback_data="category_facebook")],
        [InlineKeyboardButton("ℹ️ 도움말", callback_data="help")]
    ])


async def error_handler(update, context):
    logger.error(f"오류: {context.error}")


def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN을 .env에 설정하세요")
        return
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_error_handler(error_handler)
    logger.info("봇 시작 중...")
    app.run_polling()


if __name__ == "__main__":
    main()
