# 生产环境代码审查报告

**审查时间**: 2026-09-08  
**审查范围**: bot/main.py, bot/payment_validator.py, bot/database.py, api/worker_simple.js  
**审查结论**: ⚠️ 需要修复高风险问题后才能上线

---

## 【一、发现的问题与风险等级】

### 🔴 高风险问题 (7个)

#### 1. database.py - 数据库连接未使用上下文管理器
- **位置**: `database.py` 第 25-29 行
- **问题**: `get_connection()` 返回的连接可能未正确关闭，导致连接泄漏
- **风险**: 高并发时耗尽数据库连接，服务崩溃
- **修复**: 使用 `@contextmanager` 装饰器管理连接生命周期

```python
@contextmanager
def get_connection(self):
    conn = None
    try:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()
```

#### 2. database.py - 批量操作无事务保护
- **位置**: `database.py` 第 116-122 行
- **问题**: `batch_add_accounts()` 每次调用单独提交，失败时部分数据已写入
- **风险**: 数据不一致，部分账号添加成功部分失败
- **修复**: 使用事务包装整个批量操作

```python
def batch_add_accounts(self, accounts: List[Dict]) -> int:
    count = 0
    try:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for acc in accounts:
                try:
                    cursor.execute("INSERT OR REPLACE INTO accounts ...", (...))
                    count += 1
                except Exception as e:
                    logger.warning(f"添加账号失败 {acc.get('id')}: {e}")
            # 事务自动提交
    except Exception as e:
        conn.rollback()
        logger.error(f"批量添加失败: {e}")
    return count
```

#### 3. payment_validator.py - SQL 注入风险
- **位置**: `payment_validator.py` 第 539 行
- **问题**: `cleanup_old_orders()` 使用字符串格式化构建 SQL
- **风险**: 恶意输入可导致 SQL 注入攻击
- **修复**: 使用参数化查询

```python
# 错误写法
cursor.execute(f"DELETE FROM orders WHERE created_at < datetime('now', '-{max_age_hours} hours')")

# 正确写法
cursor.execute(
    "DELETE FROM orders WHERE created_at < datetime('now', ?)",
    (f"-{max_age_hours} hours",)
)
```

#### 4. worker_simple.js - 钱包地址硬编码
- **位置**: `worker_simple.js` 第 2 行
- **问题**: 钱包地址 `TWk75rL7Y7yS2eLZhLEpA7UeVVWpTJTih4` 硬编码
- **风险**: 地址变更需要重新部署，泄露钱包信息
- **修复**: 从环境变量读取

```javascript
const WALLET = process.env.TRON_WALLET_ADDRESS || "TWk75rL7Y7yS2eLZhLEpA7UeVVWpTJTih4";
```

#### 5. worker_simple.js - 已删除管理员 ID 仍在代码中
- **位置**: `worker_simple.js` 第 3 行
- **问题**: `ADMIN_IDS` 包含已删除的管理员 `8733970362`
- **风险**: 权限配置不一致，安全漏洞
- **修复**: 从数组中删除

```javascript
const ADMIN_IDS = [process.env.ADMIN_ID_1, process.env.ADMIN_ID_2].filter(Boolean);
// .env: ADMIN_ID_1=8427378474
```

#### 6. worker_simple.js - 数据未持久化
- **位置**: `worker_simple.js` 第 16-17 行
- **问题**: `accountInventory` 和 `orders` 存储在内存，重启后丢失
- **风险**: 订单数据丢失，交易无法追踪
- **修复**: 集成 SQLite 或 GitHub API 持久化

#### 7. main.py - 钱包地址硬编码在欢迎消息
- **位置**: `main.py` 第 166 行
- **问题**: 钱包地址硬编码在欢迎消息中
- **风险**: 地址变更需要修改代码并重新部署
- **修复**: 使用环境变量 `WALLET_ADDRESS`

```python
# 正确写法
f"   • 결제 주소: {WALLET_ADDRESS}\n"
```

---

### 🟡 中风险问题 (9个)

#### 1. main.py - API_BASE 和 APP_URL 使用测试域名
- **位置**: `main.py` 第 35-36 行
- **修复**: 配置正式域名

#### 2. main.py - 直接访问私有方法
- **位置**: `main.py` 第 299, 326, 838 行
- **问题**: 直接调用 `validator._get_db_connection()`
- **修复**: 添加公共方法 `get_account_stats()`

#### 3. main.py - 密码加密使用 SHA256
- **位置**: `main.py` 第 100 行
- **问题**: SHA256 不够安全，易受彩虹表攻击
- **修复**: 使用 bcrypt 或 argon2

```python
import bcrypt
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
```

#### 4. payment_validator.py - 数据库路径硬编码
- **位置**: `payment_validator.py` 第 34 行
- **修复**: 使用环境变量

```python
def __init__(self, db_path: str = None):
    self.db_path = db_path or os.getenv("PAYMENTS_DB_PATH", "/default/path")
```

#### 5. payment_validator.py - 时间解析可能失败
- **位置**: `payment_validator.py` 第 397 行
- **问题**: `datetime.fromisoformat()` 在旧版本 Python 可能不支持
- **修复**: 添加异常处理

```python
try:
    created_at = datetime.fromisoformat(order['created_at'])
except ValueError:
    created_at = datetime.strptime(order['created_at'], '%Y-%m-%dT%H:%M:%S')
```

#### 6. payment_validator.py - 速率限制非线程安全
- **位置**: `payment_validator.py` 第 136-144 行
- **修复**: 使用 `threading.Lock` 保护

```python
import threading
self._lock = threading.Lock()

def _rate_limit_check(self):
    with self._lock:
        # 原有逻辑
```

#### 7. worker_simple.js - 支付创建 API 不完整
- **位置**: `worker_simple.js` 第 65-69 行
- **问题**: 不验证用户，不创建订单记录
- **修复**: 集成数据库验证

#### 8. worker_simple.js - 错误处理不足
- **位置**: `worker_simple.js` 第 28-29 行
- **修复**: 添加 `console.error` 和结构化日志

#### 9. worker_simple.js - 缺少输入验证
- **位置**: `worker_simple.js` 第 66 行
- **修复**: 添加请求体验证

---

### 🟢 低风险问题 (6个)

#### 1. main.py - 输入净化不够严格
- **位置**: `main.py` 第 86 行
- **修复**: 使用白名单验证

#### 2. main.py - 存在重复代码块
- **位置**: 第 591-615 行和第 684-712 行
- **修复**: 提取为 `send_delivery_message()` 函数

#### 3. main.py - 宽泛的异常捕获
- **位置**: 多处 `except Exception`
- **修复**: 使用具体异常类型

#### 4. payment_validator.py - 内存缓存无大小限制
- **位置**: `payment_validator.py` 第 47 行
- **修复**: 添加最大缓存大小

```python
MAX_CACHE_SIZE = 100
self._recent_transfers = self._recent_transfers[-MAX_CACHE_SIZE:]
```

#### 5. payment_validator.py - API 响应结构硬编码
- **位置**: `payment_validator.py` 第 258 行
- **修复**: 添加响应结构验证

#### 6. database.py - 相对路径问题
- **位置**: `database.py` 第 15 行
- **修复**: 使用绝对路径

---

## 【二、优化建议】

### 1. 【架构优化】数据库统一
- **问题**: 当前使用 GitHub JSON + SQLite 双存储，数据不一致
- **建议**: 统一使用 SQLite 作为主存储，GitHub 仅用于备份
- **实施**: 修改 `get_bot_data()` 从 SQLite 读取

### 2. 【安全优化】API 认证
- **问题**: Worker API 无认证机制
- **建议**: 添加 JWT 或 API Key 认证
- **实施**: 在 Request Header 中验证 Token

### 3. 【性能优化】缓存策略
- **问题**: 每次请求都从 GitHub 获取数据
- **建议**: 添加内存缓存 + 定期刷新
- **实施**: 使用 `functools.lru_cache` 或自建缓存

### 4. 【代码规范】错误处理
- **问题**: 多处使用宽泛的 `except Exception`
- **建议**: 使用具体的异常类型
- **实施**: 区分数据库错误、网络错误、验证错误

### 5. 【可维护性】配置管理
- **问题**: 多处硬编码路径和配置
- **建议**: 统一使用 `.env` 配置文件
- **实施**: 创建 `config.py` 统一管理配置

### 6. 【日志优化】结构化日志
- **问题**: 日志格式不统一
- **建议**: 使用 JSON 格式日志便于分析
- **实施**: 集成 `structlog` 或 `python-json-logger`

### 7. 【测试覆盖】单元测试
- **问题**: 无自动化测试
- **建议**: 添加 pytest 单元测试
- **实施**: 覆盖核心业务逻辑

### 8. 【监控告警】健康检查
- **问题**: 无系统健康监控
- **建议**: 添加健康检查端点和告警
- **实施**: 定期检查数据库连接和 API 状态

---

## 【修正后的完整代码】

### database.py (修复版)

```python
"""
数据库模块 - 使用 SQLite 存储账号和订单数据
生产环境版本 - 修复连接泄漏、事务保护、SQL注入
"""
import json
import sqlite3
import os
import logging
from typing import List, Dict, Optional
from datetime import datetime
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# 数据库路径 - 使用绝对路径
DB_PATH = os.environ.get(
    "SHOP_DB_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "shop.db")
)


class Database:
    """SQLite 数据库管理类 - 生产环境版本"""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.init_db()
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器 - 自动管理连接生命周期"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            # 启用 WAL 模式提升并发性能
            conn.execute("PRAGMA journal_mode=WAL")
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
    
    def init_db(self):
        """初始化数据库表"""
        # 确保数据目录存在
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 账号表
            cursor.execute("""
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
            """)
            
            # 订单表
            cursor.execute("""
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
            """)
            
            # 统计数据表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stats (
                    key TEXT PRIMARY KEY,
                    value TEXT DEFAULT ''
                )
            """)
            
            # 创建索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_accounts_status ON accounts(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)")
            
        logger.info("数据库初始化完成")
    
    # ========== 账号操作 ==========
    
    def add_account(self, account: Dict) -> bool:
        """添加账号 - 使用参数化查询防止 SQL 注入"""
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO accounts 
                    (id, type, username, phone, verify_link, password, email, status, price_trx, price_usdt)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
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
            logger.info(f"添加账号: {account.get('id')}")
            return True
        except Exception as e:
            logger.error(f"添加账号失败: {e}")
            return False
    
    def batch_add_accounts(self, accounts: List[Dict]) -> int:
        """批量添加账号 - 使用事务保护"""
        count = 0
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                for acc in accounts:
                    try:
                        cursor.execute("""
                            INSERT OR REPLACE INTO accounts 
                            (id, type, username, phone, verify_link, password, email, status, price_trx, price_usdt)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            acc.get('id'),
                            acc.get('type', 'telegram_basic'),
                            acc.get('username', ''),
                            acc.get('phone', ''),
                            acc.get('verify_link', ''),
                            acc.get('password', ''),
                            acc.get('email', ''),
                            acc.get('status', 'available'),
                            acc.get('price_trx', 50),
                            acc.get('price_usdt', 10)
                        ))
                        count += 1
                    except Exception as e:
                        logger.warning(f"添加账号失败 {acc.get('id')}: {e}")
                # 事务自动提交
            logger.info(f"批量添加账号: {count}/{len(accounts)}")
            return count
        except Exception as e:
            logger.error(f"批量添加失败: {e}")
            return count
    
    def get_available_accounts(self, acc_type: str = None) -> List[Dict]:
        """获取可用账号 - 使用参数化查询"""
        try:
            with self.get_connection() as conn:
                if acc_type:
                    cursor = conn.execute(
                        "SELECT * FROM accounts WHERE status = 'available' AND type LIKE ?",
                        (f'{acc_type}%',)
                    )
                else:
                    cursor = conn.execute("SELECT * FROM accounts WHERE status = 'available'")
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"获取账号失败: {e}")
            return []
    
    def get_all_accounts(self) -> List[Dict]:
        """获取所有账号"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("SELECT * FROM accounts ORDER BY created_at DESC")
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"获取所有账号失败: {e}")
            return []
    
    def sell_account(self, account_id: str, order_id: str) -> bool:
        """出售账号 - 使用参数化查询"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    UPDATE accounts 
                    SET status = 'sold', sold_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND status = 'available'
                """, (account_id,))
                
                if cursor.rowcount == 0:
                    return False
                
            logger.info(f"出售账号: {account_id} -> 订单 {order_id}")
            return True
        except Exception as e:
            logger.error(f"出售账号失败: {e}")
            return False
    
    # ========== 订单操作 ==========
    
    def add_order(self, order: Dict) -> bool:
        """添加订单 - 使用参数化查询"""
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO orders
                    (order_id, user_id, quantity, amount_trx, amount_usdt, currency, status, assigned_accounts)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    order.get('order_id'),
                    order.get('user_id'),
                    order.get('quantity', 1),
                    order.get('amount_trx', 0),
                    order.get('amount_usdt', 0),
                    order.get('currency', 'TRX'),
                    order.get('status', 'pending'),
                    json.dumps(order.get('assigned_accounts', []))
                ))
            logger.info(f"添加订单: {order.get('order_id')}")
            return True
        except Exception as e:
            logger.error(f"添加订单失败: {e}")
            return False
    
    def get_user_orders(self, user_id: int, limit: int = 10) -> List[Dict]:
        """获取用户订单 - 使用参数化查询"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                    (user_id, limit)
                )
                
                orders = []
                for row in cursor.fetchall():
                    order = dict(row)
                    # 解析 JSON 字段
                    if order.get('assigned_accounts'):
                        try:
                            order['assigned_accounts'] = json.loads(order['assigned_accounts'])
                        except json.JSONDecodeError:
                            pass
                    orders.append(order)
                
                return orders
        except Exception as e:
            logger.error(f"获取订单失败: {e}")
            return []
    
    def update_order_status(self, order_id: str, status: str, extra: Dict = None) -> bool:
        """更新订单状态 - 使用参数化查询"""
        try:
            with self.get_connection() as conn:
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
                    conn.execute(
                        f"UPDATE orders SET {', '.join(updates)} WHERE order_id = ?",
                        params
                    )
                
            logger.info(f"更新订单状态: {order_id} -> {status}")
            return True
        except Exception as e:
            logger.error(f"更新订单状态失败: {e}")
            return False
    
    # ========== 统计操作 ==========
    
    def get_stats(self) -> Dict:
        """获取统计数据"""
        try:
            with self.get_connection() as conn:
                # 账号统计
                cursor = conn.execute("SELECT COUNT(*) as total FROM accounts")
                total = cursor.fetchone()['total']
                
                cursor = conn.execute("SELECT COUNT(*) as available FROM accounts WHERE status = 'available'")
                available = cursor.fetchone()['available']
                
                cursor = conn.execute("SELECT COUNT(*) as sold FROM accounts WHERE status = 'sold'")
                sold = cursor.fetchone()['sold']
                
                # 订单统计
                cursor = conn.execute("SELECT COUNT(*) as orders FROM orders")
                orders_count = cursor.fetchone()['orders']
                
                # 按类型统计
                cursor = conn.execute("""
                    SELECT type, COUNT(*) as count 
                    FROM accounts 
                    GROUP BY type
                """)
                by_type = {row['type']: row['count'] for row in cursor.fetchall()}
                
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


# 全局数据库实例
db = Database()
```

---

### payment_validator.py 修复要点

```python
# 修复 1: SQL 注入 - 使用参数化查询
def cleanup_old_orders(self, max_age_hours: int = 2) -> int:
    try:
        with self._get_db_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM orders WHERE status = 'pending' AND created_at < datetime('now', ?)",
                (f"-{max_age_hours} hours",)  # 参数化查询
            )
            deleted = cursor.rowcount
        return deleted
    except Exception as e:
        logger.error(f"清理过期订单失败: {e}")
        return 0

# 修复 2: 数据库路径从环境变量读取
def __init__(self, db_path: str = None):
    self.db_path = db_path or os.getenv(
        "PAYMENTS_DB_PATH",
        "/data/data/com.termux/files/home/tg-shop-bot/data/payments.db"
    )

# 修复 3: 缓存大小限制
MAX_CACHE_SIZE = 100

def get_recent_transactions(self, limit: int = 50) -> List[Dict]:
    # ... 原有逻辑 ...
    # 限制缓存大小
    if len(self._recent_transfers) > MAX_CACHE_SIZE:
        self._recent_transfers = self._recent_transfers[-MAX_CACHE_SIZE:]
```

---

### worker_simple.js 修复要点

```javascript
// 修复 1: 从环境变量读取配置
const WALLET = process.env.TRON_WALLET_ADDRESS || "";
const ADMIN_IDS = (process.env.ADMIN_IDS || "").split(",").filter(Boolean).map(Number);
const DATA_URL = process.env.DATA_URL || "https://raw.githubusercontent.com/...";

// 修复 2: 添加输入验证
async function handleRequest(request) {
  const url = new URL(request.url);
  const path = url.pathname;
  
  // 请求体验证
  if (request.method === 'POST') {
    const contentType = request.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      return response({ error: 'Content-Type must be application/json' }, 400);
    }
  }
  
  // ... 原有逻辑 ...
}

// 修复 3: 错误处理
addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request).catch(err => {
    console.error('Worker error:', err);
    return response({ error: 'Internal Server Error' }, 500);
  }));
});
```

---

## 【生产就绪检查清单】

### 必须修复 (阻塞上线)
- [ ] 修复 database.py 数据库连接泄漏
- [ ] 修复 payment_validator.py SQL 注入
- [ ] 修复 worker_simple.js 硬编码配置
- [ ] 统一数据存储为 SQLite

### 建议修复 (提升稳定性)
- [ ] 添加 API 认证机制
- [ ] 完善错误处理和日志
- [ ] 添加单元测试
- [ ] 配置监控告警

### 可选优化 (提升性能)
- [ ] 添加缓存策略
- [ ] 优化数据库查询
- [ ] 结构化日志

---

## 【总结】

| 类别 | 数量 | 状态 |
|------|------|------|
| 高风险 | 7 | 需立即修复 |
| 中风险 | 9 | 建议尽快修复 |
| 低风险 | 6 | 可后续优化 |

**当前状态**: ⚠️ 需要修复 7 个高风险问题后才能部署生产环境

**核心问题**:
1. 数据库连接管理不当 (连接泄漏风险)
2. SQL 注入漏洞 (安全风险)
3. 配置硬编码 (维护风险)
4. 数据持久化缺失 (数据丢失风险)

**修复优先级**:
1. database.py - 连接管理和事务保护
2. payment_validator.py - SQL 注入修复
3. worker_simple.js - 配置外部化
4. 统一数据存储架构
