"""
Telegram Bot - 升级版
支持管理员上传账号、多账号购买、链上自动发货
"""
import os
import json
import logging
import random
import urllib.request
import urllib.error
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_BASE = os.getenv("API_BASE_URL", "https://951951.org")
APP_URL = os.getenv("APP_URL", "https://951951.org")
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "8427378474,8733970362").split(",")]

# 基础价格表
BASE_PRICES = {
    "telegram_basic": {"name": "一般 텔레그램 계정", "trx": 50, "usdt": 10, "icon": "📱"},
    "telegram_premium": {"name": "프리미엄 텔레그램 계정", "trx": 150, "usdt": 30, "icon": "⭐"},
    "telegram_channel": {"name": "텔레그램 채널 계정", "trx": 80, "usdt": 15, "icon": "📢"},
    "instagram_basic": {"name": "인스타그램 계정", "trx": 100, "usdt": 20, "icon": "📷"},
    "instagram_premium": {"name": "인스타그램 프리미엄", "trx": 200, "usdt": 40, "icon": "💎"},
    "facebook_basic": {"name": "페이스북 계정", "trx": 60, "usdt": 12, "icon": "📘"},
    "facebook_business": {"name": "페이스북 비즈니스 계정", "trx": 120, "usdt": 24, "icon": "🏢"}
}


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def api_request(path: str, method: str = "GET", data: dict = None) -> dict:
    url = f"{API_BASE}{path}"
    try:
        req = urllib.request.Request(url, method=method)
        req.add_header("X-User-Id", str(next((uid for uid in ADMIN_IDS), "")))
        if data:
            body = json.dumps(data).encode()
            req.add_header("Content-Type", "application/json")
            req.data = body
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception as e:
        logger.warning(f"API请求失败 {path}: {e}")
        return {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if is_admin(user.id):
        keyboard = [
            [InlineKeyboardButton("📥 上传账号", callback_data="admin_add_account")],
            [InlineKeyboardButton("📦 库存管理", callback_data="admin_inventory")],
            [InlineKeyboardButton("📊 订单管理", callback_data="admin_orders")],
            [InlineKeyboardButton("📈 库存统计", callback_data="admin_stats")],
            [InlineKeyboardButton("🛒 商城", callback_data="shop")]
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
            f"{user.first_name}님, 구매할 카테고리를 선택하세요.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    user = query.from_user

    if data == "back":
        await query.edit_message_text("메인 메뉴로 돌아갑니다.", reply_markup=await main_keyboard(user_id))

    elif data == "help":
        await query.edit_message_text("""
📖 사용 방법

1. 카테고리를 선택하세요
2. 구매할 계정 수량을 선택하세요 (1~3개)
3. 결제 정보를 확인하세요
4. TRX 또는 USDT(TRC20)로 결제하세요
5. 결제 확인 후 자동으로 계정을 발송합니다

💰 결제 주소
TRON 지갑으로 직접 전송

⏱️ 결제 기한: 30분
""")

    # ========== 管理员功能 ==========
    elif data == "admin_add_account":
        if not is_admin(user_id):
            await query.answer("권한이 없습니다.", show_alert=True)
            return
        keyboard = [
            [InlineKeyboardButton("📝 단일 추가", callback_data="admin_add_single")],
            [InlineKeyboardButton("📋 대량 추가", callback_data="admin_add_batch")],
            [InlineKeyboardButton("⬅️ 뒤로가기", callback_data="back")]
        ]
        await query.edit_message_text(
            "📥 계정 업로드 방법 선택",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data == "admin_add_single":
        if not is_admin(user_id):
            return
        await query.edit_message_text(
            "📝 단일 계정 추가\n\n"
            "아래 형식으로 입력하세요:\n\n"
            "账号类型: telegram_basic / telegram_premium / telegram_channel\n"
            "用户名: [Telegram用户名]\n"
            "密码: [登录密码]\n"
            "邮箱: [可选]\n"
            "手机: [可选]\n"
            "描述: [可选]\n\n"
            "예시:\n"
            "telegram_basic\n"
            "@testuser123\n"
            "Password123\n"
            "test@mail.com\n"
            "+821012345678\n"
            "1년 이상 계정",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ 뒤로", callback_data="admin_add_account")]])
        )
        # 保存待处理数据
        context.user_data['pending_add_type'] = 'single'
        context.user_data['pending_add_step'] = 1

    elif data == "admin_add_batch":
        if not is_admin(user_id):
            return
        await query.edit_message_text(
            "📋 대량 계정 추가\n\n"
            "JSON 형식으로 입력하세요:\n\n"
            "[\n"
            "  {\"type\": \"telegram_basic\", \"username\": \"@user1\", \"password\": \"pass1\"},\n"
            "  {\"type\": \"telegram_premium\", \"username\": \"@user2\", \"password\": \"pass2\"}\n"
            "]\n\n"
            "또는 텍스트 파일로 업로드하세요."
        )
        context.user_data['pending_add_type'] = 'batch'
        context.user_data['pending_add_step'] = 1

    elif data == "admin_inventory":
        if not is_admin(user_id):
            return
        result = api_request("/api/admin/stats")
        if result and 'total' in result:
            text = f"📦库存统计\n\n"
            text += f"总库存: {result['total']}\n"
            text += f"可购买: {result['available']}\n"
            text += f"已售: {result['sold']}\n\n"
            text += "类型统计:\n"
            for k, v in result.get('by_type', {}).items():
                if v > 0:
                    name = BASE_PRICES.get(k, {}).get('name', k)
                    text += f"  • {name}: {v}个\n"
            keyboard = [
                [InlineKeyboardButton("📥 上传账号", callback_data="admin_add_account")],
                [InlineKeyboardButton("⬅️ 뒤로", callback_data="back")]
            ]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await query.edit_message_text("📦 아직 등록된 계정이 없습니다.\n\n첫 번째 계정을 업로드하세요.")

    elif data == "admin_orders":
        if not is_admin(user_id):
            return
        result = api_request("/api/admin/orders")
        order_list = result.get('orders', [])
        if order_list:
            text = "📋 주문 목록:\n\n"
            for o in order_list:
                emoji = "✅" if o.get('status') == 'delivered' else "🟡" if o.get('status') == 'paid' else "⏳"
                text += f"{emoji} {o['order_id']}\n"
                text += f"   사용자: {o.get('user_id')} | 계정: {o.get('quantity')}개\n"
                text += f"   금액: {o.get('amount_trx', o.get('amount'))} {o.get('currency', 'TRX')}\n"
                text += f"   상태: {o.get('status')}\n\n"
            keyboard = [
                [InlineKeyboardButton("🔄 새로고침", callback_data="admin_orders")],
                [InlineKeyboardButton("⬅️ 뒤로", callback_data="back")]
            ]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await query.edit_message_text("📋 아직 주문이 없습니다.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 새로고침", callback_data="admin_orders")]])
            )

    elif data == "admin_stats":
        if not is_admin(user_id):
            return
        result = api_request("/api/admin/stats")
        if result:
            text = f"📊 재고 통계\n\n"
            text += f"총 계정: {result.get('total', 0)}\n"
            text += f"판매 가능: {result.get('available', 0)}\n"
            text += f"판매 완료: {result.get('sold', 0)}\n\n"
            text += "유형별 재고:\n"
            for k, v in result.get('by_type', {}).items():
                name = BASE_PRICES.get(k, {}).get('name', k)
                text += f"  {name}: {v}개\n"
            keyboard = [[InlineKeyboardButton("⬅️ 뒤로", callback_data="admin_inventory")]]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    # ========== 商城功能 ==========
    elif data.startswith("category_"):
        cat = data.split("_", 1)[1]
        names = {
            "telegram": [("telegram_basic", "📱 일반 계정"), ( "telegram_premium", "⭐ 프리미엄"), ("telegram_channel", "📢 채널")],
            "instagram": [("instagram_basic", "📷 일반 계정"), ("instagram_premium", "💎 프리미엄")],
            "facebook": [("facebook_basic", "📘 일반 계정"), ("facebook_business", "🏢 비즈니스")]
        }
        items = names.get(cat, [])
        keyboard = []
        for key, name in items:
            price = BASE_PRICES.get(key, {})
            keyboard.append([InlineKeyboardButton(
                f"{price.get('icon','')} {name} ({price.get('trx','?')}TRX)",
                callback_data=f"select_type_{key}"
            )])
        keyboard.append([InlineKeyboardButton("⬅️ 뒤로가기", callback_data="back")])
        await query.edit_message_text(f"{cat.capitalize()} 계정 선택", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("select_type_"):
        acc_type = data.split("_", 1)[1]
        price = BASE_PRICES.get(acc_type, {})
        context.user_data['selected_type'] = acc_type
        keyboard = [
            [InlineKeyboardButton("1개 구매", callback_data=f"qty_{acc_type}_1")],
            [InlineKeyboardButton("2개 구매", callback_data=f"qty_{acc_type}_2")],
            [InlineKeyboardButton("3개 구매", callback_data=f"qty_{acc_type}_3")],
            [InlineKeyboardButton("⬅️ 뒤로가기", callback_data="back")]
        ]
        await query.edit_message_text(
            f"{price.get('icon', '')} {price.get('name', acc_type)}\n\n"
            f"구매할 계정 수량을 선택하세요:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data.startswith("qty_"):
        parts = data.split("_")
        acc_type = parts[1]
        quantity = int(parts[2])
        base_price = BASE_PRICES.get(acc_type, BASE_PRICES['telegram_basic'])
        # 计算带随机波动后的价格
        variance = 1.001 + random.random() * 0.029
        trx_price = int(base_price['trx'] * quantity * variance)
        usdt_price = round(base_price['usdt'] * quantity * variance, 2)
        
        context.user_data['selected_type'] = acc_type
        context.user_data['quantity'] = quantity
        context.user_data['trx_price'] = trx_price
        context.user_data['usdt_price'] = usdt_price
        
        keyboard = [
            [InlineKeyboardButton("TRX 결제", callback_data=f"pay_{acc_type}_trx")],
            [InlineKeyboardButton("USDT 결제", callback_data=f"pay_{acc_type}_usdt")],
            [InlineKeyboardButton("⬅️ 뒤로가기", callback_data=f"select_type_{acc_type}")]
        ]
        await query.edit_message_text(
            f"{base_price.get('icon','')} {base_price.get('name','')}\n\n"
            f"💰 결제 예정 금액:\n"
            f"  TRX: {trx_price} TRX\n"
            f"  USDT: ${usdt_price}\n\n"
            f"(실제 결제 금액은 blockchain 확인 시 확정됩니다)\n\n"
            f"결제 방식을 선택하세요:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data.startswith("pay_"):
        parts = data.split("_")
        acc_type = parts[1]
        currency = parts[2]
        quantity = context.user_data.get('quantity', 1)
        trx_price = context.user_data.get('trx_price', BASE_PRICES.get(acc_type, {}).get('trx', 50))
        usdt_price = context.user_data.get('usdt_price', BASE_PRICES.get(acc_type, {}).get('usdt', 10))
        
        # 创建订单
        amount = trx_price if currency == 'trx' else usdt_price
        result = api_request("/api/payment/create", "POST", {
            "user_id": user.id,
            "account_type": acc_type,
            "quantity": quantity,
            "amount": amount,
            "currency": currency.upper()
        })
        
        if result and 'order_id' in result:
            context.user_data['order_id'] = result['order_id']
            keyboard = [
                [InlineKeyboardButton("✅ 결제 완료", callback_data=f"confirm_pay_{result['order_id']}")]
            ]
            await query.edit_message_text(
                f"💳 주문 생성 완료\n\n"
                f"주문번호: {result['order_id']}\n"
                f"계정: {acc_type} × {quantity}개\n"
                f"결제 금액: {amount} {currency.upper()}\n"
                f"결제 기한: 30분\n\n"
                f"아래 주소로 결제하세요:\n"
                f"📍 {result.get('payment_address', WALLET)}\n\n"
                f"결제 후 '결제 완료' 버튼을 눌러주세요.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await query.edit_message_text("주문 생성에 실패했습니다. 다시 시도하세요.")

    elif data.startswith("confirm_pay_"):
        order_id = data.split("_", 2)[2]
        context.user_data['order_id'] = order_id
        
        # 验证支付（模拟区块链确认）
        result = api_request(f"/api/payment/verify?order_id={order_id}")
        
        if result and result.get('confirmed'):
            keyboard = [
                [InlineKeyboardButton("📥 계정 수령", callback_data=f"receive_{order_id}")]
            ]
            await query.edit_message_text(
                f"✅ 결제가 확인되었습니다!\n\n"
                f"계정을 수령하려면 아래 버튼을 눌러주세요.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await query.edit_message_text("결제 확인 중입니다. 잠시 후 다시 시도하세요.")

    elif data.startswith("receive_"):
        order_id = data.split("_", 1)[1]
        # 获取订单
        result = api_request(f"/api/user/orders?user_id={user.id}")
        order = None
        for o in result.get('orders', []):
            if o.get('order_id') == order_id:
                order = o
                break
        
        if order and order.get('status') == 'paid':
            # 管理员手动发货（实际需要自动确认）
            # 这里发送已分配的账号
            accounts = order.get('assigned_accounts', [])
            if accounts:
                text = f"✅ 결제 완료!\n\n아래 계정 정보를 확인하세요:\n\n"
                for i, acc in enumerate(accounts, 1):
                    text += f"📱 계정 {i}:\n"
                    text += f"  ID: {acc.get('id', 'N/A')}\n"
                    text += f"  Username: @{acc.get('username', 'N/A')}\n"
                    text += f"  Password: {acc.get('password', 'N/A')}\n"
                    text += f"  Email: {acc.get('email', 'N/A')}\n"
                    text += f"  Phone: {acc.get('phone', 'N/A')}\n\n"
            else:
                # 如果没有预分配账号，使用默认生成
                text = f"✅ 결제 완료!\n\n"
                text += f"📱 텔레그램 계정 (자동 생성):\n"
                text += f"  Username: @newuser_{order_id[:6]}\n"
                text += f"  Password: Tg@{random.randint(1000,9999)}\n"
                text += f"  (실제 계정 정보는 관리자가 발송합니다)\n"
            
            keyboard = [[InlineKeyboardButton("🛒 계속 쇼핑", callback_data="shop")]]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await query.edit_message_text("아직 결제가 확인되지 않았습니다. 관리자가 확인 후 발송합니다.")

    elif data == "shop":
        await start(update, context)


async def main_keyboard(user_id: int) -> InlineKeyboardMarkup:
    if is_admin(user_id):
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("📥 上传账号", callback_data="admin_add_account")],
            [InlineKeyboardButton("📦 库存管理", callback_data="admin_inventory")],
            [InlineKeyboardButton("📊 订单管理", callback_data="admin_orders")],
            [InlineKeyboardButton("🛒 商城", callback_data="shop")]
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
    logger.info("🚀 봇 시작 중...")
    app.run_polling()


if __name__ == "__main__":
    main()
