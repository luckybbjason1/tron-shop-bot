// Cloudflare Workers - TRON Shop API v3
const WALLET = "TWk75rL7Y7yS2eLZhLEpA7UeVVWpTJTih4";
const ADMIN_IDS = ["8427378474", "8733970362"];

// 账号库存 - 管理员上传的账号
let accountInventory = [];
// 订单存储
let orders = {};

// 基础价格表（每账号）
const BASE_PRICES = {
  telegram_basic: { trx: 50, usdt: 10 },
  telegram_premium: { trx: 150, usdt: 30 },
  telegram_channel: { trx: 80, usdt: 15 },
  instagram_basic: { trx: 100, usdt: 20 },
  instagram_premium: { trx: 200, usdt: 40 },
  facebook_basic: { trx: 60, usdt: 12 },
  facebook_business: { trx: 120, usdt: 24 }
};

function response(data, status=200) {
  return new Response(JSON.stringify(data), {
    headers: {
      "Content-Type": "application/json",
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, X-User-Id"
    },
    status
  });
}

// 计算价格（带随机波动 1.001~1.03 倍）
function calculatePrice(basePrice, quantity) {
  const variance = 1.001 + Math.random() * 0.029; // 1.001 ~ 1.03
  const trx = Math.round(basePrice.trx * quantity * variance);
  const usdt = Math.round(basePrice.usdt * quantity * variance * 100) / 100;
  return { trx, usdt };
}

async function handleRequest(request) {
  const url = new URL(request.url);
  const path = url.pathname;
  
  // CORS preflight
  if (request.method === 'OPTIONS') {
    return response({ok: true});
  }
  
  // 健康检查
  if (path === '/api/health') {
    return response({status: 'ok', timestamp: new Date().toISOString()});
  }
  
  // 获取账号列表
  if (path === '/api/accounts') {
    return response({accounts: accountInventory});
  }
  
  // 管理员：添加账号
  if (path === '/api/admin/add-account') {
    const userId = request.headers.get('X-User-Id');
    if (!ADMIN_IDS.includes(userId)) {
      return response({error: 'Unauthorized'}, 401);
    }
    if (request.method !== 'POST') {
      return response({error: 'Method not allowed'}, 405);
    }
    const body = await request.json();
    const accountId = 'ACC' + Date.now() + Math.random().toString(36).substr(2, 4).toUpperCase();
    const account = {
      id: accountId,
      type: body.type || 'telegram_basic',
      username: body.username || '未知',
      password: body.password || '未知',
      email: body.email || '无',
      phone: body.phone || '无',
      description: body.description || '',
      created_at: new Date().toISOString(),
      status: 'available', // available, sold
      sold_to: null
    };
    accountInventory.push(account);
    return response({success: true, account});
  }
  
  // 管理员：批量添加账号
  if (path === '/api/admin/batch-add') {
    const userId = request.headers.get('X-User-Id');
    if (!ADMIN_IDS.includes(userId)) {
      return response({error: 'Unauthorized'}, 401);
    }
    if (request.method !== 'POST') {
      return response({error: 'Method not allowed'}, 405);
    }
    const body = await request.json();
    const accounts = body.accounts || [];
    const added = [];
    for (const acc of accounts) {
      const accountId = 'ACC' + Date.now() + Math.random().toString(36).substr(2, 4).toUpperCase();
      added.push({
        id: accountId,
        type: acc.type,
        username: acc.username,
        password: acc.password,
        email: acc.email || '无',
        phone: acc.phone || '无',
        description: acc.description || '',
        created_at: new Date().toISOString(),
        status: 'available',
        sold_to: null
      });
    }
    accountInventory.push(...added);
    return response({success: true, count: added.length});
  }
  
  // 管理员：删除账号
  if (path === '/api/admin/delete-account') {
    const userId = request.headers.get('X-User-Id');
    if (!ADMIN_IDS.includes(userId)) {
      return response({error: 'Unauthorized'}, 401);
    }
    if (request.method !== 'POST') {
      return response({error: 'Method not allowed'}, 405);
    }
    const body = await request.json();
    const index = accountInventory.findIndex(a => a.id === body.account_id);
    if (index !== -1) {
      accountInventory.splice(index, 1);
      return response({success: true});
    }
    return response({error: 'Not found'}, 404);
  }
  
  // 管理员：获取库存统计
  if (path === '/api/admin/stats') {
    const userId = request.headers.get('X-User-Id');
    if (!ADMIN_IDS.includes(userId)) {
      return response({error: 'Unauthorized'}, 401);
    }
    const available = accountInventory.filter(a => a.status === 'available').length;
    const sold = accountInventory.filter(a => a.status === 'sold').length;
    return response({
      total: accountInventory.length,
      available,
      sold,
      by_type: {
        telegram_basic: accountInventory.filter(a => a.type === 'telegram_basic' && a.status === 'available').length,
        telegram_premium: accountInventory.filter(a => a.type === 'telegram_premium' && a.status === 'available').length,
        instagram_basic: accountInventory.filter(a => a.type === 'instagram_basic' && a.status === 'available').length,
        instagram_premium: accountInventory.filter(a => a.type === 'instagram_premium' && a.status === 'available').length,
        facebook_basic: accountInventory.filter(a => a.type === 'facebook_basic' && a.status === 'available').length,
        facebook_business: accountInventory.filter(a => a.type === 'facebook_business' && a.status === 'available').length,
      }
    });
  }
  
  // 管理员：查看所有订单
  if (path === '/api/admin/orders') {
    const userId = request.headers.get('X-User-Id');
    if (!ADMIN_IDS.includes(userId)) {
      return response({error: 'Unauthorized'}, 401);
    }
    return response({orders: Object.values(orders)});
  }
  
  // 管理员：确认订单并释放账号
  if (path === '/api/admin/confirm-order') {
    const userId = request.headers.get('X-User-Id');
    if (!ADMIN_IDS.includes(userId)) {
      return response({error: 'Unauthorized'}, 401);
    }
    if (request.method !== 'POST') {
      return response({error: 'Method not allowed'}, 405);
    }
    const body = await request.json();
    const orderId = body.order_id;
    const order = orders[orderId];
    if (!order) {
      return response({error: 'Order not found'}, 404);
    }
    if (order.status !== 'paid') {
      return response({error: 'Order not paid yet'}, 400);
    }
    // 分配账号
    const quantity = order.quantity || 1;
    const availableAccounts = accountInventory.filter(a => a.status === 'available');
    if (availableAccounts.length < quantity) {
      order.status = 'insufficient_stock';
      return response({error: '库存不足', available: availableAccounts.length, needed: quantity});
    }
    // 分配账号
    const assignedAccounts = availableAccounts.slice(0, quantity);
    for (const acc of assignedAccounts) {
      acc.status = 'sold';
      acc.sold_to = orderId;
      acc.sold_at = new Date().toISOString();
    }
    order.assigned_accounts = assignedAccounts.map(a => ({
      id: a.id,
      username: a.username,
      password: a.password,
      email: a.email,
      phone: a.phone
    }));
    order.status = 'delivered';
    order.delivered_at = new Date().toISOString();
    return response({success: true, accounts: order.assigned_accounts});
  }
  
  // 创建订单（支持多账号购买）
  if (path === '/api/payment/create') {
    if (request.method !== 'POST') {
      return response({error: 'Method not allowed'}, 405);
    }
    const body = await request.json();
    const orderId = 'ORD' + Date.now() + Math.random().toString(36).substr(2, 6).toUpperCase();
    const accountType = body.account_type || 'telegram_basic';
    const basePrice = BASE_PRICES[accountType] || BASE_PRICES.telegram_basic;
    const quantity = body.quantity || 1;
    const price = calculatePrice(basePrice, quantity);
    
    const order = {
      order_id: orderId,
      user_id: body.user_id,
      account_type: accountType,
      quantity: quantity,
      amount_trx: price.trx,
      amount_usdt: price.usdt,
      currency: body.currency || 'TRX',
      payment_address: WALLET,
      status: 'pending',
      created_at: new Date().toISOString(),
      expires_at: new Date(Date.now() + 30 * 60 * 1000).toISOString(),
      assigned_accounts: null,
      delivered_at: null
    };
    orders[orderId] = order;
    return response(order);
  }
  
  // 确认支付
  if (path === '/api/payment/verify') {
    const orderId = url.searchParams.get('order_id');
    const order = orders[orderId];
    if (!order) {
      return response({error: 'Order not found'}, 404);
    }
    // 模拟区块链确认（实际应检查 TRON 交易）
    order.status = 'paid';
    order.paid_at = new Date().toISOString();
    return response({confirmed: true, order});
  }
  
  // 获取用户订单
  if (path === '/api/user/orders') {
    const userId = url.searchParams.get('user_id');
    const userOrders = Object.values(orders).filter(o => o.user_id === parseInt(userId));
    return response({orders: userOrders});
  }
  
  return response({error: 'Not found'}, 404);
}

addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request));
});
