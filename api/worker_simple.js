// Simple TRON Shop API
const WALLET = "TWk75rL7Y7yS2eLZhLEpA7UeVVWpTJTih4";
const ADMIN_IDS = ["8427378474", "8733970362"];
const DATA_URL = "https://raw.githubusercontent.com/luckybbjason1/tron-shop-bot/main/data/accounts.json";

const BASE_PRICES = {
  telegram_basic: { trx: 50, usdt: 10 },
  telegram_premium: { trx: 150, usdt: 30 },
  telegram_channel: { trx: 80, usdt: 15 },
  instagram_basic: { trx: 100, usdt: 20 },
  instagram_premium: { trx: 200, usdt: 40 },
  facebook_basic: { trx: 60, usdt: 12 },
  facebook_business: { trx: 120, usdt: 24 }
};

let accountInventory = [];
let orders = {};

async function loadData() {
  try {
    const resp = await fetch(DATA_URL);
    if (resp.ok) {
      const data = await resp.json();
      accountInventory = data.accounts || [];
      orders = data.orders || {};
      console.log("Loaded " + accountInventory.length + " accounts");
    }
  } catch (e) {
    console.log("Error: " + e.message);
  }
}

function response(data, status=200) {
  return new Response(JSON.stringify(data), {
    headers: {
      "Content-Type": "application/json",
      "Access-Control-Allow-Origin": "*"
    },
    status
  });
}

async function handleRequest(request) {
  const url = new URL(request.url);
  const path = url.pathname;
  
  if (path === '/api/health') {
    await loadData();
    return response({status: 'ok', accounts: accountInventory.length});
  }
  
  if (path === '/api/products') {
    await loadData();
    const available = accountInventory.filter(a => a.status === 'available');
    const products = available.map(acc => ({
      id: acc.id,
      type: acc.type,
      phone: acc.phone || '',
      verify_link: acc.verify_link || '',
      price_trx: BASE_PRICES[acc.type]?.trx || 50
    }));
    return response({products, total: products.length});
  }
  
  if (path === '/api/payment/create') {
    const body = await request.json();
    const orderId = 'ORD' + Date.now();
    return response({order_id: orderId, payment_address: WALLET});
  }
  
  if (path.startsWith('/api/admin/')) {
    const userId = request.headers.get('X-User-Id');
    if (!ADMIN_IDS.includes(userId)) {
      return response({error: 'Unauthorized'}, 401);
    }
    
    await loadData();
    
    if (path === '/api/admin/stats') {
      return response({total: accountInventory.length, available: accountInventory.filter(a => a.status === 'available').length});
    }
    
    if (path === '/api/admin/add-account') {
      const body = await request.json();
      body.id = 'ACC' + Date.now();
      body.status = 'available';
      accountInventory.push(body);
      return response({success: true, account: body});
    }
    
    if (path === '/api/admin/batch-add') {
      const body = await request.json();
      const accounts = body.accounts || [];
      const added = accounts.map(a => ({...a, id: 'ACC' + Date.now() + Math.random().toString(36).substr(2,4), status: 'available'}));
      accountInventory.push(...added);
      return response({success: true, count: added.length});
    }
    
    return response({error: 'Not found'}, 404);
  }
  
  return response({error: 'Not found'}, 404);
}

addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request));
});
