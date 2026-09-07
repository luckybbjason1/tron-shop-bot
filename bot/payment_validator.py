"""
TRON 链上支付验证器 - 生产环境版本
使用 TronScan API 监控链上交易
"""
import os
import json
import logging
import time
import sqlite3
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from dotenv import load_dotenv
from contextlib import contextmanager

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TronPaymentValidator:
    """TRON 链上支付验证器 - 生产环境版本"""
    
    # TRON 主网配置
    TRON_GRID_API = "https://api.trongrid.io"
    TRONSCAN_API = "https://apilist.tronscanapi.com/api"
    USDT_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
    
    # 速率限制配置
    API_RATE_LIMIT = 10  # 每秒最大请求数
    API_COOLDOWN = 0.1   # 请求间隔（秒）
    
    def __init__(self, db_path: str = "data/payments.db"):
        self.wallet_address = os.getenv("TRON_WALLET_ADDRESS", "")
        self.api_key = os.getenv("TRON_GRID_API_KEY", "")
        self.tronscan_key = os.getenv("TRONSCAN_API_KEY", "")
        
        # 数据库配置
        self.db_path = db_path
        self._init_database()
        
        # 速率限制
        self._last_request_time = 0
        
        # 内存缓存（可选，用于加速）
        self._recent_transfers = []
        self._cache_time = 0
    
    @contextmanager
    def _get_db_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")  # 提升并发性能
            conn.execute("PRAGMA synchronous=NORMAL")
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def _init_database(self):
        """初始化数据库表"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 订单表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    order_id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    account_type TEXT NOT NULL,
                    quantity INTEGER DEFAULT 1,
                    amount REAL NOT NULL,
                    currency TEXT DEFAULT 'USDT',
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    paid_at TIMESTAMP,
                    delivered_at TIMESTAMP,
                    tx_id TEXT,
                    verified INTEGER DEFAULT 0,
                    delivered INTEGER DEFAULT 0
                )
            ''')
            
            # 交易记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    tx_id TEXT PRIMARY KEY,
                    from_address TEXT,
                    to_address TEXT,
                    amount REAL,
                    currency TEXT,
                    timestamp TIMESTAMP,
                    confirmed INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # API 调用日志表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    endpoint TEXT,
                    status_code INTEGER,
                    response_time REAL,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建索引
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_orders_status 
                ON orders(status, created_at)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_orders_user 
                ON orders(user_id, status)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_transactions_to 
                ON transactions(to_address, timestamp)
            ''')
            
            logger.info("数据库初始化完成")
    
    def _rate_limit_check(self):
        """速率限制检查"""
        now = time.time()
        elapsed = now - self._last_request_time
        
        if elapsed < self.API_COOLDOWN:
            time.sleep(self.API_COOLDOWN - elapsed)
        
        self._last_request_time = time.time()
    
    def _make_request(self, url: str, headers: Dict = None, timeout: int = 10) -> Optional[Dict]:
        """通用请求方法（带速率限制和错误处理）"""
        self._rate_limit_check()
        
        start_time = time.time()
        try:
            req = urllib.request.Request(url)
            if headers:
                for k, v in headers.items():
                    req.add_header(k, v)
            
            # 启用 SSL 验证
            import ssl
            context = ssl.create_default_context()
            context.check_hostname = True
            context.verify_mode = ssl.CERT_REQUIRED
            
            with urllib.request.urlopen(req, timeout=timeout, context=context) as resp:
                data = json.loads(resp.read())
                
            # 记录 API 调用
            self._log_api_call(url, resp.status, time.time() - start_time)
            
            return data
        except urllib.error.HTTPError as e:
            self._log_api_call(url, e.code, time.time() - start_time, str(e))
            logger.error(f"HTTP 错误 {e.code}: {e.reason}")
            return None
        except urllib.error.URLError as e:
            self._log_api_call(url, 0, time.time() - start_time, str(e))
            logger.error(f"URL 错误: {e.reason}")
            return None
        except json.JSONDecodeError as e:
            self._log_api_call(url, 0, time.time() - start_time, str(e))
            logger.error(f"JSON 解析失败: {e}")
            return None
        except Exception as e:
            self._log_api_call(url, 0, time.time() - start_time, str(e))
            logger.error(f"请求失败: {e}")
            return None
    
    def _log_api_call(self, endpoint: str, status_code: int, response_time: float, error: str = None):
        """记录 API 调用日志"""
        try:
            with self._get_db_connection() as conn:
                conn.execute(
                    """INSERT INTO api_logs (endpoint, status_code, response_time, error_message)
                       VALUES (?, ?, ?, ?)""",
                    (endpoint, status_code, response_time, error)
                )
        except Exception as e:
            logger.warning(f"记录 API 日志失败: {e}")
    
    def get_usdt_balance(self) -> float:
        """获取 USDT 余额"""
        if not self.wallet_address:
            return 0.0
        
        try:
            url = f"{self.TRON_GRID_API}/v1/accounts/{self.wallet_address}/tokens?limit=20"
            if self.api_key:
                url += f"&api_key={self.api_key}"
            
            data = self._make_request(url)
            if not data or 'data' not in data:
                return 0.0
            
            for token in data['data']:
                if token.get('token_abbr') == 'USDT' or token.get('token_id') == self.USDT_CONTRACT:
                    try:
                        return float(token.get('balance', 0)) / 1_000_000
                    except (ValueError, TypeError):
                        continue
            return 0.0
        except Exception as e:
            logger.error(f"获取 USDT 余额失败: {e}")
            return 0.0
    
    def get_trx_balance(self) -> float:
        """获取 TRX 余额"""
        if not self.wallet_address:
            return 0.0
        
        try:
            url = f"{self.TRON_GRID_API}/v1/accounts/{self.wallet_address}"
            data = self._make_request(url)
            if data and 'balance' in data:
                return int(data['balance']) / 1_000_000
            return 0.0
        except Exception as e:
            logger.error(f"获取 TRX 余额失败: {e}")
            return 0.0
    
    def get_recent_transactions(self, limit: int = 50) -> List[Dict]:
        """获取最近的 USDT 转账（带缓存）"""
        now = time.time()
        
        # 检查缓存（5秒内使用缓存）
        if self._recent_transfers and (now - self._cache_time) < 5:
            return self._recent_transfers[-limit:]
        
        if not self.wallet_address:
            return []
        
        try:
            url = f"{self.TRONSCAN_API}/transfer?limit={limit}&toAddress={self.wallet_address}&token=USDT"
            
            headers = {}
            if self.tronscan_key:
                headers['apikey'] = self.tronscan_key
            
            data = self._make_request(url, headers)
            if not data or 'data' not in data:
                return []
            
            transfers = []
            for tx in data['data']:
                try:
                    amount = float(tx.get('value', 0)) / 1_000_000
                    if amount <= 0:
                        continue
                    
                    transfer = {
                        'tx_id': tx.get('hash', ''),
                        'from': tx.get('from', ''),
                        'to': tx.get('to', ''),
                        'amount': amount,
                        'timestamp': int(tx.get('createTime', 0)) / 1000,
                        'confirmed': tx.get('confirmations', 0) > 19,
                        'type': 'usdt_transfer'
                    }
                    transfers.append(transfer)
                    
                    # 存储到数据库
                    self._save_transaction(transfer)
                except Exception as e:
                    logger.warning(f"解析转账失败: {e}")
                    continue
            
            # 更新缓存
            self._recent_transfers = transfers
            self._cache_time = now
            
            return transfers
        except Exception as e:
            logger.error(f"获取最近交易失败: {e}")
            return []
    
    def _save_transaction(self, transfer: Dict):
        """保存交易记录到数据库"""
        try:
            with self._get_db_connection() as conn:
                conn.execute(
                    """INSERT OR IGNORE INTO transactions 
                       (tx_id, from_address, to_address, amount, currency, timestamp, confirmed)
                       VALUES (?, ?, ?, ?, 'USDT', ?, ?)""",
                    (
                        transfer['tx_id'],
                        transfer['from'],
                        transfer['to'],
                        transfer['amount'],
                        transfer['timestamp'],
                        1 if transfer['confirmed'] else 0
                    )
                )
        except Exception as e:
            logger.warning(f"保存交易失败: {e}")
    
    def create_order(self, order_id: str, user_id: int, account_type: str, 
                     quantity: int, amount: float, currency: str = 'USDT') -> bool:
        """创建待支付订单（持久化到数据库）"""
        # 验证输入
        if quantity < 1 or quantity > 10:
            raise ValueError(f"数量必须在 1-10 之间，当前: {quantity}")
        
        if amount <= 0:
            raise ValueError(f"金额必须大于 0，当前: {amount}")
        
        try:
            with self._get_db_connection() as conn:
                conn.execute(
                    """INSERT INTO orders 
                       (order_id, user_id, account_type, quantity, amount, currency, status, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)""",
                    (
                        order_id,
                        user_id,
                        account_type,
                        quantity,
                        amount,
                        currency.upper(),
                        datetime.now().isoformat()
                    )
                )
            
            logger.info(f"创建订单: {order_id}, 用户: {user_id}, 金额: {amount} {currency}")
            return True
        except sqlite3.IntegrityError:
            logger.error(f"订单已存在: {order_id}")
            return False
        except Exception as e:
            logger.error(f"创建订单失败: {e}")
            return False
    
    def check_order_payment(self, order_id: str, expected_amount: float, 
                           currency: str = 'USDT') -> Dict:
        """
        检查订单支付是否完成
        
        返回:
            {
                'verified': bool,
                'order_id': str,
                'amount': float,
                'currency': str,
                'tx_id': str,
                'message': str,
                'status': str  # 'verified', 'pending', 'expired'
            }
        """
        try:
            with self._get_db_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM orders WHERE order_id = ?",
                    (order_id,)
                )
                order = cursor.fetchone()
                
                if not order:
                    return {
                        'verified': False,
                        'order_id': order_id,
                        'message': '订单不存在',
                        'status': 'not_found'
                    }
                
                order = dict(order)
                
                # 检查是否已验证
                if order['verified']:
                    return {
                        'verified': True,
                        'order_id': order_id,
                        'amount': order['amount'],
                        'currency': order['currency'],
                        'tx_id': order.get('tx_id', ''),
                        'message': '已确认',
                        'status': 'verified'
                    }
                
                # 检查是否过期（30分钟）
                created_at = datetime.fromisoformat(order['created_at'])
                if datetime.now() - created_at > timedelta(minutes=30):
                    return {
                        'verified': False,
                        'order_id': order_id,
                        'message': '订单已过期，请重新下单',
                        'status': 'expired'
                    }
                
                # 获取最近交易
                transfers = self.get_recent_transactions(limit=50)
                
                # 查找匹配的交易
                for tx in transfers:
                    # 检查金额是否匹配（允许 0.01 误差）
                    if abs(tx['amount'] - expected_amount) < 0.01:
                        # 检查时间是否在新订单创建后
                        if tx['timestamp'] >= created_at.timestamp():
                            # 检查确认状态
                            if tx['confirmed']:
                                # 更新订单状态
                                self._mark_order_verified(order_id, tx['tx_id'])
                                
                                return {
                                    'verified': True,
                                    'order_id': order_id,
                                    'amount': tx['amount'],
                                    'currency': currency,
                                    'tx_id': tx['tx_id'],
                                    'message': f'支付确认！交易: {tx["tx_id"][:16]}...',
                                    'status': 'verified'
                                }
                            else:
                                return {
                                    'verified': False,
                                    'order_id': order_id,
                                    'message': '交易待确认，请稍后再试',
                                    'status': 'pending'
                                }
                
                # 未找到匹配交易
                return {
                    'verified': False,
                    'order_id': order_id,
                    'amount': expected_amount,
                    'currency': currency,
                    'message': '未找到匹配的交易，请确认支付已完成',
                    'status': 'pending'
                }
                
        except Exception as e:
            logger.error(f"检查订单支付失败: {e}")
            return {
                'verified': False,
                'order_id': order_id,
                'message': f'检查失败: {str(e)}',
                'status': 'error'
            }
    
    def _mark_order_verified(self, order_id: str, tx_id: str):
        """标记订单已验证"""
        try:
            with self._get_db_connection() as conn:
                conn.execute(
                    """UPDATE orders 
                       SET verified = 1, tx_id = ?, paid_at = CURRENT_TIMESTAMP
                       WHERE order_id = ?""",
                    (tx_id, order_id)
                )
            logger.info(f"订单 {order_id} 已验证，交易: {tx_id}")
        except Exception as e:
            logger.error(f"标记订单验证失败: {e}")
    
    def deliver_order(self, order_id: str, account_ids: List[str]) -> bool:
        """自动发货"""
        try:
            with self._get_db_connection() as conn:
                # 更新订单状态
                conn.execute(
                    """UPDATE orders 
                       SET delivered = 1, delivered_at = CURRENT_TIMESTAMP
                       WHERE order_id = ? AND verified = 1""",
                    (order_id,)
                )
                
                # 更新账号状态
                placeholders = ','.join(['?' for _ in account_ids])
                conn.execute(
                    f"""UPDATE accounts 
                        SET status = 'sold', sold_to = ?, sold_at = CURRENT_TIMESTAMP
                        WHERE id IN ({placeholders}) AND status = 'available'""",
                    [order_id] + account_ids
                )
            
            logger.info(f"订单 {order_id} 已发货，账号: {account_ids}")
            return True
        except Exception as e:
            logger.error(f"发货失败: {e}")
            return False
    
    def get_order_status(self, order_id: str) -> Dict:
        """获取订单状态"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM orders WHERE order_id = ?",
                    (order_id,)
                )
                order = cursor.fetchone()
                
                if not order:
                    return {
                        'exists': False,
                        'message': '订单不存在'
                    }
                
                order = dict(order)
                return {
                    'exists': True,
                    'order_id': order_id,
                    'status': 'delivered' if order['delivered'] else ('verified' if order['verified'] else 'pending'),
                    'amount': order['amount'],
                    'currency': order['currency'],
                    'created_at': order['created_at'],
                    'verified': order['verified'],
                    'tx_id': order.get('tx_id', ''),
                    'delivered': order['delivered']
                }
        except Exception as e:
            logger.error(f"获取订单状态失败: {e}")
            return {
                'exists': False,
                'message': f'获取失败: {str(e)}'
            }
    
    def cleanup_old_orders(self, max_age_hours: int = 2) -> int:
        """清理过期订单"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.execute(
                    """DELETE FROM orders 
                       WHERE status = 'pending' 
                       AND created_at < datetime('now', '-{} hours')""".format(max_age_hours)
                )
                deleted = cursor.rowcount
            
            if deleted > 0:
                logger.info(f"清理了 {deleted} 个过期订单")
            return deleted
        except Exception as e:
            logger.error(f"清理过期订单失败: {e}")
            return 0
    
    def get_user_orders(self, user_id: int, limit: int = 10) -> List[Dict]:
        """获取用户订单"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.execute(
                    """SELECT * FROM orders 
                       WHERE user_id = ? 
                       ORDER BY created_at DESC 
                       LIMIT ?""",
                    (user_id, limit)
                )
                
                orders = []
                for row in cursor.fetchall():
                    order = dict(row)
                    # 移除敏感信息
                    order.pop('tx_id', None)
                    orders.append(order)
                
                return orders
        except Exception as e:
            logger.error(f"获取用户订单失败: {e}")
            return []


# 全局实例
validator = TronPaymentValidator()
