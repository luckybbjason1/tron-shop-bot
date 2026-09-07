"""
数据库模块 - 使用 SQLite 存储账号和订单数据
替代 GitHub JSON 文件
"""
import json
import sqlite3
import os
import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'shop.db')


class Database:
    """SQLite 数据库管理类"""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """初始化数据库表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 账号表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                username TEXT DEFAULT '',
                phone TEXT NOT NULL,
                verify_link TEXT DEFAULT '',
                password TEXT DEFAULT '',
                email TEXT DEFAULT '',
                status TEXT DEFAULT 'available',
                price_trx INTEGER DEFAULT 50,
                price_usdt INTEGER DEFAULT 10,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sold_at TIMESTAMP
            )
        ''')
        
        # 订单表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                quantity INTEGER DEFAULT 1,
                amount_trx INTEGER DEFAULT 0,
                amount_usdt INTEGER DEFAULT 0,
                currency TEXT DEFAULT 'TRX',
                status TEXT DEFAULT 'pending',
                assigned_accounts TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                paid_at TIMESTAMP,
                delivered_at TIMESTAMP
            )
        ''')
        
        # 统计数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stats (
                key TEXT PRIMARY KEY,
                value TEXT DEFAULT ''
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("数据库初始化完成")
    
    # ========== 账号操作 ==========
    
    def add_account(self, account: Dict) -> bool:
        """添加账号"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO accounts 
                (id, type, username, phone, verify_link, password, email, status, price_trx, price_usdt)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                account.get('id'),
                account.get('type', 'telegram_basic'),
                account.get('username', ''),
                account.get('phone', ''),
                account.get('verify_link', ''),
                account.get('password', ''),
                account.get('email', ''),
                account.get('status', 'available'),
                account.get('price_trx', 50),
                account.get('price_usdt', 10)
            ))
            
            conn.commit()
            conn.close()
            logger.info(f"添加账号: {account.get('id')}")
            return True
        except Exception as e:
            logger.error(f"添加账号失败: {e}")
            return False
    
    def batch_add_accounts(self, accounts: List[Dict]) -> int:
        """批量添加账号"""
        count = 0
        for acc in accounts:
            if self.add_account(acc):
                count += 1
        return count
    
    def get_available_accounts(self, acc_type: str = None) -> List[Dict]:
        """获取可用账号"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if acc_type:
                cursor.execute(
                    "SELECT * FROM accounts WHERE status = 'available' AND type LIKE ?",
                    (f'{acc_type}%',)
                )
            else:
                cursor.execute("SELECT * FROM accounts WHERE status = 'available'")
            
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"获取账号失败: {e}")
            return []
    
    def get_all_accounts(self) -> List[Dict]:
        """获取所有账号"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM accounts ORDER BY created_at DESC")
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"获取所有账号失败: {e}")
            return []
    
    def sell_account(self, account_id: str, order_id: str) -> bool:
        """出售账号"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE accounts 
                SET status = 'sold', sold_at = CURRENT_TIMESTAMP
                WHERE id = ? AND status = 'available'
            ''', (account_id,))
            
            if cursor.rowcount == 0:
                conn.close()
                return False
            
            conn.commit()
            conn.close()
            logger.info(f"出售账号: {account_id} -> 订单 {order_id}")
            return True
        except Exception as e:
            logger.error(f"出售账号失败: {e}")
            return False
    
    # ========== 订单操作 ==========
    
    def add_order(self, order: Dict) -> bool:
        """添加订单"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO orders
                (order_id, user_id, quantity, amount_trx, amount_usdt, currency, status, assigned_accounts)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                order.get('order_id'),
                order.get('user_id'),
                order.get('quantity', 1),
                order.get('amount_trx', 0),
                order.get('amount_usdt', 0),
                order.get('currency', 'TRX'),
                order.get('status', 'pending'),
                json.dumps(order.get('assigned_accounts', []))
            ))
            
            conn.commit()
            conn.close()
            logger.info(f"添加订单: {order.get('order_id')}")
            return True
        except Exception as e:
            logger.error(f"添加订单失败: {e}")
            return False
    
    def get_user_orders(self, user_id: int) -> List[Dict]:
        """获取用户订单"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,)
            )
            
            rows = cursor.fetchall()
            conn.close()
            
            orders = []
            for row in rows:
                order = dict(row)
                # 解析 JSON 字段
                if order.get('assigned_accounts'):
                    try:
                        order['assigned_accounts'] = json.loads(order['assigned_accounts'])
                    except:
                        pass
                orders.append(order)
            
            return orders
        except Exception as e:
            logger.error(f"获取订单失败: {e}")
            return []
    
    def update_order_status(self, order_id: str, status: str, extra: Dict = None) -> bool:
        """更新订单状态"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            if status:
                updates.append("status = ?")
                params.append(status)
            if extra:
                if 'assigned_accounts' in extra:
                    updates.append("assigned_accounts = ?")
                    params.append(json.dumps(extra['assigned_accounts']))
                if 'paid_at' in extra:
                    updates.append("paid_at = CURRENT_TIMESTAMP")
                if 'delivered_at' in extra:
                    updates.append("delivered_at = CURRENT_TIMESTAMP")
            
            if updates:
                params.append(order_id)
                cursor.execute(
                    f"UPDATE orders SET {', '.join(updates)} WHERE order_id = ?",
                    params
                )
            
            conn.commit()
            conn.close()
            logger.info(f"更新订单状态: {order_id} -> {status}")
            return True
        except Exception as e:
            logger.error(f"更新订单状态失败: {e}")
            return False
    
    # ========== 统计操作 ==========
    
    def get_stats(self) -> Dict:
        """获取统计数据"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 账号统计
            cursor.execute("SELECT COUNT(*) as total FROM accounts")
            total = cursor.fetchone()['total']
            
            cursor.execute("SELECT COUNT(*) as available FROM accounts WHERE status = 'available'")
            available = cursor.fetchone()['available']
            
            cursor.execute("SELECT COUNT(*) as sold FROM accounts WHERE status = 'sold'")
            sold = cursor.fetchone()['sold']
            
            # 订单统计
            cursor.execute("SELECT COUNT(*) as orders FROM orders")
            orders_count = cursor.fetchone()['orders']
            
            # 按类型统计
            cursor.execute("""
                SELECT type, COUNT(*) as count 
                FROM accounts 
                GROUP BY type
            """)
            by_type = {row['type']: row['count'] for row in cursor.fetchall()}
            
            conn.close()
            
            return {
                'total': total,
                'available': available,
                'sold': sold,
                'orders': orders_count,
                'by_type': by_type
            }
        except Exception as e:
            logger.error(f"获取统计失败: {e}")
            return {'total': 0, 'available': 0, 'sold': 0, 'orders': 0, 'by_type': {}}
    
    # ========== 数据导入 ==========
    
    def import_from_github(self, github_url: str) -> int:
        """从 GitHub 导入数据"""
        import urllib.request
        try:
            req = urllib.request.Request(github_url)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
            
            accounts = data.get('accounts', [])
            count = self.batch_add_accounts(accounts)
            
            logger.info(f"从 GitHub 导入 {count} 个账号")
            return count
        except Exception as e:
            logger.error(f"导入失败: {e}")
            return 0
    
    def export_to_github(self, github_url: str) -> bool:
        """导出数据到 GitHub (需要 API token)"""
        # 此功能需要在 Worker 中实现
        return False


# 全局数据库实例
db = Database()
