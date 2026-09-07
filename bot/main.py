"""
Telegram Bot - 生产环境版本
管理员账号上传, 多账号购买, 区块链自动配送支持
"""
import os
import json
import logging
import random
import re
import urllib.request
import urllib.error
import hashlib
import base64
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, BotCommand
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.error import TelegramError, Conflict

# 导入支付验证器
from payment_validator import validator

load_dotenv()

# 配置结构化日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 安全配置
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_BASE = os.getenv("API_BASE_URL", "https://951951.org")
APP_URL = os.getenv("APP_URL", "https://951951.org")
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "8427378474").split(",")]

# 价格配置（只保留 Telegram）
BASE_PRICES = {
    "telegram_basic": {"name": "一般 텔레그램 계정", "trx": 50, "usdt": 5, "icon": "📱"},
    "telegram_premium": {"name": "프리미엄 텔레그램 계정", "trx": 150, "usdt": 15, "icon": "⭐"},
    "telegram_channel": {"name": "텔레그램 채널 계정", "trx": 80, "usdt": 8, "icon": "📢"}
}

# 配置常量
WALLET_ADDRESS = os.getenv("TRON_WALLET_ADDRESS", "")
MAX_QUANTITY = 10  # 最大购买数量
ORDER_EXPIRY_MINUTES = 30  # 订单过期时间


def is_admin(user_id: int) -> bool:
    """检查是否为管理员"""
    return user_id in ADMIN_IDS


def get_bot_data() -> list:
    """从 GitHub 获取账号数据（带缓存）"""
    try:
        url = "https://raw.githubusercontent.com/luckybbjason1/tron-shop-bot/main/data/accounts.json"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        return data.get('accounts', [])
    except urllib.error.HTTPError as e:
        logger.error(f"获取数据失败 (HTTP {e.code}): {e.reason}")
        return []
    except urllib.error.URLError as e:
        logger.error(f"获取数据失败 (网络): {e.reason}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"数据解析失败: {e}")
        return []
    except Exception as e:
        logger.error(f"获取数据失败: {e}")
        return []


def sanitize_input(text: str, max_length: int = 500) -> str:
    """输入净化 - 防止注入攻击"""
    if not text:
        return ""
    # 限制长度
    text = text[:max_length]
    # 移除潜在的危险字符
    text = re.sub(r'[<>"\';]', '', text)
    return text


def encrypt_password(password: str, salt: str = None) -> str:
    """加密密码 - 使用随机盐值"""
    if not password:
        return ""
    
    # 生成随机盐值
    if salt is None:
        salt = os.urandom(16).hex()
    
    # 使用 bcrypt 替代 SHA256（生产环境应使用 bcrypt/argon2）
    hashed = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    # 返回盐值+哈希值
    return f"{salt}${hashed}"


def verify_password(password: str, hashed: str) -> bool:
    """验证密码"""
    if not password or not hashed:
        return False
    
    try:
        salt, hash_value = hashed.split('$')
        expected = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
        return expected == hash_value
    except ValueError:
        return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """启动命令"""
    user = update.effective_user
    if not user or not user.id:
        return

    # 检查是否为群组
    if update.effective_chat and update.effective_chat.type != 'private':
        await update.message.reply_text(
            "이 봇은 개인 채팅에서만 작동합니다.\n"
            "이 봇을 추가하지 마세요."
        )
        return

    if is_admin(user.id):
        keyboard = [
            [InlineKeyboardButton("📥 계정 업로드", callback_data="admin_add_account")],
            [InlineKeyboardButton("📦 재고 관리", callback_data="admin_inventory")],
            [InlineKeyboardButton("📊 주문 관리", callback_data="admin_orders")],
            [InlineKeyboardButton("📈 재고 통계", callback_data="admin_stats")],
            [InlineKeyboardButton("🛒 쇼핑몰", callback_data="shop")]
        ]
        await update.message.reply_text(
            f"👋 {sanitize_input(user.first_name)}님, 관리자 권한으로 접속했습니다.\n\n"
            f"관리자 메뉴를 사용하세요.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        welcome_text = """🛒 텔레그램 계정 구매 쇼핑몰에 오신 것을 환영합니다!

{first_name}님, 안전한 텔레그램 계정을 구매하세요.

📋 구매 방법:

1️⃣ 계정 선택
   • '📱 텔레그램 계정' 버튼을 클릭하세요
   • 원하는 국가의 계정을 선택하세요

2️⃣ 수량 선택
   • 구매할 계정 수량을 선택하세요 (1~3개)
   • 가격은 실시간으로 계산됩니다

3️⃣ 결제 정보 확인
   • 총 결제 금액을 확인하세요
   • TRON 지갑 주소를 확인하세요

4️⃣ 블록체인 결제
   • USDT(TRC20) 또는 TRX로 결제하세요
   • 결제 주소: TWk75rL7Y7yS2eLZhLEpA7UeVVWpTJTih4
   • 결제 기한: 30분

5️⃣ 계정 수령
   • 결제 확인 후 자동으로 계정을 발송합니다
   • 텔레그램 계정 정보 (전화번호 + 인증 링크)를 받으세요

💰 가격 정보:
   • 텔레그램 계정: 5 USDT / 개
   • 수량에 따라 가격 변동 (1.001x ~ 1.03x)

⚠️ 주의사항:
   • 인증 코드는 30분 동안 유효합니다
   • 결제는 30분 이내에 완료해주세요
   • 환불은 불가능합니다
   • 계정 정보는 결제 확인 후 발송됩니다

🔒 안전하고 빠른 구매 경험을 보장합니다!
""".format(first_name=sanitize_input(user.first_name))

        keyboard = [
            [InlineKeyboardButton("📱 텔레그램 계정", callback_data="category_telegram")]
        ]
        await update.message.reply_text(
            welcome_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理回调"""
    query = update.callback_query
    if not query:
        return
    
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    user = query.from_user
    
    # 输入验证
    if not data or len(data) > 100:
        await query.answer("❌ 잘못된 입력입니다", show_alert=True)
        return
    
    # 安全过滤
    data = sanitize_input(data)
    
    try:
        if data == "back":
            await query.edit_message_text(
                "메인 메뉴로 돌아갑니다.",
                reply_markup=await main_keyboard(user_id)
            )
        
        elif data == "help":
            await query.edit_message_text("""
📖 사용 방법

1. 카테고리를 선택하세요
2. 구매할 계정 수량을 선택하세요 (1~{}개)
3. 결제 정보를 확인하세요
4. TRX 또는 USDT(TRC20)로 결제하세요
5. 결제 확인 후 자동으로 계정을 발송합니다

💰 결제 주소
{}

⏱️ 결제 기한: {}분
""".format(MAX_QUANTITY, WALLET_ADDRESS[:20] + '...', ORDER_EXPIRY_MINUTES))
        
        # ========== 管理员功能 ==========
        elif data == "admin_add_account":
            if not is_admin(user_id):
                await query.answer("권한이 없습니다.", show_alert=True)
                return
            keyboard = [
                [InlineKeyboardButton("📝 단일 추가", callback_data="admin_add_single")],
                [InlineKeyboardButton("📋 대량 추가", callback_data="admin_add_batch")],
                [InlineKeyboardButton("📦 상품 목록", callback_data="admin_show_products")],
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
                "+821****5678\n"
                "1년 이상 계정",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ 뒤로", callback_data="admin_add_account")]
                ])
            )
            context.user_data['pending_add_type'] = 'single'
            context.user_data['pending_add_step'] = 1
        
        elif data == "admin_add_batch":
            if not is_admin(user_id):
                return
            await query.edit_message_text(
                "📋 대량 계정 추가\n\n"
                "JSON 형식으로 입력하세요:\n\n"
                "[\n"
                '  {"type": "telegram_basic", "username": "@user1", "password": "pass1"},\n'
                '  {"type": "telegram_premium", "username": "@user2", "password": "pass2"}\n'
                "]\n\n"
                "또는 텍스트 파일로 업로드하세요."
            )
            context.user_data['pending_add_type'] = 'batch'
            context.user_data['pending_add_step'] = 1
        
        elif data == "admin_inventory":
            if not is_admin(user_id):
                return
            # 从数据库获取统计
            try:
                with validator._get_db_connection() as conn:
                    cursor = conn.execute("SELECT COUNT(*) as total FROM accounts")
                    total = cursor.fetchone()['total']
                    cursor = conn.execute("SELECT COUNT(*) as available FROM accounts WHERE status = 'available'")
                    available = cursor.fetchone()['available']
                    cursor = conn.execute("SELECT COUNT(*) as sold FROM accounts WHERE status = 'sold'")
                    sold = cursor.fetchone()['sold']
            except Exception as e:
                logger.error(f"获取库存失败: {e}")
                total = available = sold = 0
            
            text = f"📦 재고 통계\n\n"
            text += f"총 재고: {total}\n"
            text += f"판매 가능: {available}\n"
            text += f"판매 완료: {sold}\n"
            
            keyboard = [
                [InlineKeyboardButton("📥 계정 업로드", callback_data="admin_add_account")],
                [InlineKeyboardButton("⬅️ 뒤로", callback_data="back")]
            ]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        
        elif data == "admin_orders":
            if not is_admin(user_id):
                return
            # 从数据库获取订单
            try:
                with validator._get_db_connection() as conn:
                    cursor = conn.execute(
                        "SELECT * FROM orders ORDER BY created_at DESC LIMIT 20"
                    )
                    orders = [dict(row) for row in cursor.fetchall()]
            except Exception as e:
                logger.error(f"获取订单失败: {e}")
                orders = []
            
            if orders:
                text = "📋 주문 목록:\n\n"
                for o in orders:
                    emoji = "✅" if o.get('delivered') else "🟡" if o.get('verified') else "⏳"
                    text += f"{emoji} {o['order_id'][:12]}...\n"
                    text += f"   사용자: {o.get('user_id')} | 계정: {o.get('quantity')}개\n"
                    text += f"   금액: {o.get('amount')} {o.get('currency')}\n"
                    text += f"   상태: {o.get('status')}\n\n"
                
                keyboard = [
                    [InlineKeyboardButton("🔄 새로고침", callback_data="admin_orders")],
                    [InlineKeyboardButton("⬅️ 뒤로", callback_data="back")]
                ]
                await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                await query.edit_message_text(
                    "📋 아직 주문이 없습니다.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔄 새로고침", callback_data="admin_orders")]
                    ])
                )
        
        elif data == "admin_stats":
            if not is_admin(user_id):
                return
            try:
                stats = validator.get_user_orders(0, limit=100)  # 获取所有订单
                total_orders = len(stats)
                total_revenue = sum(o.get('amount', 0) for o in stats if o.get('delivered'))
            except Exception as e:
                logger.error(f"获取统计失败: {e}")
                total_orders = 0
                total_revenue = 0
            
            text = f"📊 재고 통계\n\n"
            text += f"총 주문: {total_orders}\n"
            text += f"총 수익: {total_revenue:.2f} USDT\n"
            
            keyboard = [[InlineKeyboardButton("⬅️ 뒤로", callback_data="admin_inventory")]]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        
        elif data == "admin_show_products":
            if not is_admin(user_id):
                return
            accounts = get_bot_data()
            if accounts:
                text = "📦 상품 목록\n\n"
                for acc in accounts[:20]:
                    text += f"• {acc.get('phone', 'N/A')} | {acc.get('type', 'N/A')} | {acc.get('price_trx', 0)}TRX | {acc.get('status', 'N/A')}\n"
                text += f"\n총 {len(accounts)}개 상품"
            else:
                text = "📦 등록된 상품이 없습니다."
            
            keyboard = [[InlineKeyboardButton("⬅️ 뒤로", callback_data="admin_add_account")]]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        
        # ========== 商城功能 ==========
        elif data.startswith("category_"):
            cat = data.split("_", 1)[1]
            accounts = get_bot_data()
            cat_accounts = [a for a in accounts if a.get('type', '').startswith(cat)]
            
            if not cat_accounts:
                await query.edit_message_text(
                    f"📱 {cat.capitalize()} 계정\n\n"
                    f"현재 재고가 없습니다.\n"
                    f"관리자에게 문의하세요.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("⬅️ 뒤로가기", callback_data="back")]
                    ])
                )
                return
            
            text = f"📱 {cat.capitalize()} 계정 목록\n\n"
            keyboard = []
            for acc in cat_accounts[:10]:
                phone = acc.get('phone', 'N/A')
                price = acc.get('price_trx', 50)
                icon = "📱"
                
                btn_text = f"{icon} {phone} ({price}TRX)"
                keyboard.append([InlineKeyboardButton(
                    btn_text,
                    callback_data=f"buy_acc_{acc['id']}"
                )])
            
            if len(cat_accounts) > 10:
                text += f"... 총 {len(cat_accounts)}개 계정\n"
            else:
                text += f"총 {len(cat_accounts)}개 계정\n"
            
            keyboard.append([InlineKeyboardButton("⬅️ 뒤로가기", callback_data="back")])
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        
        elif data.startswith("buy_acc_"):
            acc_id = data.split("_", 2)[2]
            accounts = get_bot_data()
            account = next((a for a in accounts if a.get('id') == acc_id), None)

            if not account:
                await query.answer("계정을 찾을 수 없습니다.", show_alert=True)
                return

            # 检查账号是否仍可用
            if account.get('status') != 'available':
                await query.answer("❌ 이 계정은 이미 판매되었습니다.", show_alert=True)
                return

            phone = account.get('phone', '')
            link = account.get('verify_link', '')
            username = account.get('username', '')
            price_trx = account.get('price_trx', 50)
            price_usdt = account.get('price_usdt', 10)
            acc_type = account.get('type', 'telegram_basic')

            context.user_data['selected_account'] = account
            context.user_data['selected_type'] = acc_type
            context.user_data['quantity'] = 1
            context.user_data['trx_price'] = price_trx
            context.user_data['usdt_price'] = price_usdt

            text = f"""📱 {account.get('name', acc_type)}

📞 전화번호: {phone}
👤 사용자명: @{username if username else '없음'}
💰 가격: {price_trx} TRX / ${price_usdt} USDT
🔗 인증 링크: {link if link else '아직 생성되지 않음'}

📋 다음 단계:
1️⃣ 아래 버튼을 클릭하여 인증 링크를 엽니다
2️⃣ 텔레그램 앱에서 인증 코드를 받습니다
3️⃣ 인증 완료 후 결제를 진행합니다

계속 구매하시겠습니까?"""

            keyboard = [
                [InlineKeyboardButton("🔗 인증 링크 열기", url=link) if link else InlineKeyboardButton("⚠️ 인증 링크 없음", callback_data="back")],
                [InlineKeyboardButton("✅ 구매하기", callback_data=f"pay_{acc_type}_trx")],
                [InlineKeyboardButton("⬅️ 뒤로가기", callback_data="back")]
            ]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        
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
            
            # 验证数量
            try:
                quantity = int(parts[2])
                if quantity < 1 or quantity > MAX_QUANTITY:
                    await query.answer(f"❌ 수량은 1~{MAX_QUANTITY} 사이여야 합니다", show_alert=True)
                    return
            except ValueError:
                await query.answer("❌ 잘못된 수량입니다", show_alert=True)
                return
            
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
            order_id = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(1000, 9999)}"
            
            # 保存到验证器
            try:
                validator.create_order(order_id, user.id, acc_type, quantity, amount, currency.upper())
            except ValueError as e:
                await query.answer(f"❌ {str(e)}", show_alert=True)
                return
            except Exception as e:
                logger.error(f"创建订单失败: {e}")
                await query.answer("❌ 주문 생성에 실패했습니다. 다시 시도하세요.", show_alert=True)
                return
            
            # 发送支付信息
            text = f"""💳 주문 생성 완료

📋 주문 번호: {order_id}
📱 계정: {quantity}개
💰 금액: {amount} USDT
🔗 결제 주소: {WALLET_ADDRESS[:20]}...

⏱️ 결제 기한: {ORDER_EXPIRY_MINUTES}분
💡 결제 후 /orders 로 확인하세요
"""
            await query.edit_message_text(text)
        
        elif data.startswith("confirm_pay_"):
            order_id = data[12:]
            
            # 检查订单状态
            order_status = validator.get_order_status(order_id)
            
            if not order_status.get('exists'):
                await query.answer("❌ 주문을 찾을 수 없습니다", show_alert=True)
                return
            
            if order_status.get('status') == 'delivered':
                await query.answer("✅ 이미 배송 완료되었습니다", show_alert=True)
                return
            
            if order_status.get('status') == 'expired':
                await query.answer("⏰ 주문이 만료되었습니다. 새로 주문하세요.", show_alert=True)
                return
            
            # 检查支付
            expected_amount = order_status.get('amount', 0)
            result = validator.check_order_payment(order_id, expected_amount, 'USDT')
            
            if result.get('verified'):
                # 支付确认，自动发货
                accounts = get_bot_data()
                selected_accounts = [a for a in accounts if a.get('status') == 'available'][:quantity]
                
                if selected_accounts:
                    # 更新账号状态
                    account_ids = [acc['id'] for acc in selected_accounts]
                    
                    # 准备发货内容
                    delivery_text = "🎉 결제 확인! 계정을 발송합니다.\n\n"
                    for i, acc in enumerate(selected_accounts, 1):
                        delivery_text += f"\n📱 계정 {i}\n"
                        delivery_text += f"   번호: {acc.get('phone', 'N/A')}\n"
                        delivery_text += f"   링크: {acc.get('verify_link', 'N/A')}\n"
                        delivery_text += f"   비밀번호: {acc.get('password', 'N/A')}\n"
                    
                    delivery_text += "\n⚠️ 주의: 계정은 본인만 사용하세요."
                    
                    # 标记已发货
                    validator.deliver_order(order_id, account_ids)
                    
                    await query.edit_message_text(delivery_text)
                else:
                    await query.answer("❌ 재고가 없습니다. 관리자에게 문의하세요.", show_alert=True)
            else:
                message = result.get('message', '결제 확인 중...')
                await query.answer(f"⏳ {message}", show_alert=True)
        
        elif data.startswith("receive_"):
            # 已发货，直接结束
            keyboard = [[InlineKeyboardButton("🛒 계속 쇼핑", callback_data="shop")]]
            await query.edit_message_text(
                "✅ 주문이 완료되었습니다!",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        elif data == "shop":
            await start(update, context)
    
    except Exception as e:
        logger.error(f"回调处理错误: {e}")
        await query.answer("❌ 오류가 발생했습니다. 다시 시도하세요.", show_alert=True)


async def main_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """主键盘"""
    if is_admin(user_id):
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("📥 계정 업로드", callback_data="admin_add_account")],
            [InlineKeyboardButton("📦 재고 관리", callback_data="admin_inventory")],
            [InlineKeyboardButton("📊 주문 관리", callback_data="admin_orders")],
            [InlineKeyboardButton("📈 재고 통계", callback_data="admin_stats")],
            [InlineKeyboardButton("🛒 쇼핑몰", callback_data="shop")]
        ])
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 텔레그램 계정", callback_data="category_telegram")]
    ])


async def error_handler(update, context):
    """错误处理"""
    if context.error:
        if isinstance(context.error, Conflict):
            logger.warning("Bot 冲突，清理更新队列")
        else:
            logger.error(f"Bot 错误: {context.error}", exc_info=True)


async def products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """모든 상품 표시"""
    accounts = get_bot_data()
    
    if not accounts:
        await update.message.reply_text("📦 현재 상품이 없습니다")
        return
    
    text = "📦 상품 목록\n\n"
    for acc in accounts[:15]:
        text += f"• {acc.get('phone', 'N/A')} | {acc.get('type', 'N/A')} | {acc.get('price_trx', 0)}TRX | {acc.get('status', 'N/A')}\n"
    
    if len(accounts) > 15:
        text += f"\n... 총 {len(accounts)}개 상품"
    
    await update.message.reply_text(text)


async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """관리자 명령"""
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("⛔ 관리자 권한이 없습니다")
        return
    
    text = "👨‍💼 관리자 패널\n\n"
    text += "명령어:\n"
    text += "/products - 상품 목록 보기\n"
    text += "/orders - 내 주문 보기\n"
    text += "/stats - 통계 보기\n"
    text += "/add - 계정 추가 (관리자만)\n"
    
    await update.message.reply_text(text)


async def orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """주문 보기"""
    user = update.effective_user
    
    # 从数据库获取订单
    user_orders = validator.get_user_orders(user.id, limit=10)
    
    if not user_orders:
        await update.message.reply_text("📋 주문이 없습니다")
        return
    
    text = "📋 내 주문\n\n"
    for o in user_orders[:10]:
        emoji = "✅" if o.get('delivered') else "🟡" if o.get('verified') else "⏳"
        text += f"{emoji} {o['order_id'][:12]}...\n"
        text += f"   금액: {o.get('amount')} {o.get('currency')}\n"
        text += f"   상태: {o.get('status')}\n\n"
    
    await update.message.reply_text(text)


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """통계 보기"""
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("⛔ 관리자 권한이 없습니다")
        return
    
    try:
        # 获取账号数据
        accounts = get_bot_data()
        total = len(accounts)
        available = len([a for a in accounts if a.get('status') == 'available'])
        sold = len([a for a in accounts if a.get('status') == 'sold'])
        
        # 获取 TRON 余额
        usdt_balance = validator.get_usdt_balance()
        trx_balance = validator.get_trx_balance()
        
        # 获取订单统计
        try:
            with validator._get_db_connection() as conn:
                cursor = conn.execute("SELECT COUNT(*) as total FROM orders")
                total_orders = cursor.fetchone()['total']
                cursor = conn.execute("SELECT COUNT(*) as delivered FROM orders WHERE delivered = 1")
                delivered_orders = cursor.fetchone()['delivered']
                cursor = conn.execute("SELECT COALESCE(SUM(amount), 0) as revenue FROM orders WHERE delivered = 1")
                total_revenue = cursor.fetchone()['revenue']
        except Exception as e:
            logger.error(f"获取订单统计失败: {e}")
            total_orders = delivered_orders = total_revenue = 0
        
        text = "📊 통계 정보\n\n"
        text += f"📦 계정 통계:\n"
        text += f"  총 계정: {total}\n"
        text += f"  판매 가능: {available}\n"
        text += f"  판매 완료: {sold}\n\n"
        text += f"💰 지갑 잔고:\n"
        text += f"  USDT: {usdt_balance:.2f}\n"
        text += f"  TRX: {trx_balance:.2f}\n\n"
        text += f"📈 주문 통계:\n"
        text += f"  총 주문: {total_orders}\n"
        text += f"  완료 주문: {delivered_orders}\n"
        text += f"  총 수익: {total_revenue:.2f} USDT\n"
        
        await update.message.reply_text(text)
    except Exception as e:
        logger.error(f"통계 오류: {e}")
        await update.message.reply_text("⚠️ 통계를 가져올 수 없습니다")


def write_pid():
    """写入 PID 文件防止多实例"""
    pid_file = os.path.join(os.path.dirname(__file__), 'bot.pid')
    with open(pid_file, 'w') as f:
        f.write(str(os.getpid()))


def read_pid():
    """读取 PID 文件"""
    pid_file = os.path.join(os.path.dirname(__file__), 'bot.pid')
    try:
        with open(pid_file, 'r') as f:
            return int(f.read().strip())
    except:
        return None


def remove_pid():
    """删除 PID 文件"""
    pid_file = os.path.join(os.path.dirname(__file__), 'bot.pid')
    try:
        if os.path.exists(pid_file):
            os.remove(pid_file)
    except:
        pass


def main():
    """主函数"""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN을 .env에 설정하세요")
        return
    
    # 检查并写入 PID 文件
    old_pid = read_pid()
    if old_pid and old_pid != os.getpid():
        try:
            os.kill(old_pid, 0)
            logger.warning(f"기존 봇 프로세스 발견 (PID: {old_pid})")
        except ProcessLookupError:
            pass
        except Exception:
            pass
    
    write_pid()
    
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("products", products))
    app.add_handler(CommandHandler("admin", admin_cmd))
    app.add_handler(CommandHandler("orders", orders))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_error_handler(error_handler)
    
    # 注册命令
    app.bot.set_my_commands([
        BotCommand("start", "시작"),
        BotCommand("products", "상품 목록"),
        BotCommand("admin", "관리자"),
        BotCommand("orders", "내 주문"),
        BotCommand("stats", "통계")
    ])
    
    logger.info("🚀 봇 시작 중...")
    try:
        app.run_polling(drop_pending_updates=True)
    except KeyboardInterrupt:
        logger.info("키보드 인터럽트 감지")
    except Exception as e:
        logger.critical(f"폴링 중 오류: {e}", exc_info=True)
    finally:
        remove_pid()
        logger.info("봇 종료")


if __name__ == "__main__":
    main()
