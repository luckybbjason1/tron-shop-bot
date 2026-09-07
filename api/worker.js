// Cloudflare Workers - TRON Shop API
const PRODUCTS = [
  {id:1, name:"一般 텔레그램 계정", price_trx:50, price_usdt:10, stock:50, icon:"📱", desc:"생성일 1년 이상, 전화번호 검증 완료 계정"},
  {id:2, name:"프리미엄 텔레그램 계정", price_trx:150, price_usdt:30, stock:20, icon:"⭐", desc:"생성일 3년 이상, 고급 프로필, 검증 완료"},
  {id:3, name:"텔레그램 채널 계정", price_trx:80, price_usdt:15, stock:15, icon:"📢", desc:"가입자 1000명 이상 채널 소유 계정"},
  {id:4, name:"인스타그램 계정", price_trx:100, price_usdt:20, stock:30, icon:"📷", desc:"팔로워 5000명 이상, 활동적인 계정"},
  {id:5, name:"인스타그램 프리미엄", price_trx:200, price_usdt:40, stock:10, icon:"💎", desc:"팔로워 2만 명 이상, 업계 인증 계정"},
  {id:6, name:"페이스북 계정", price_trx:60, price_usdt:12, stock:40, icon:"📘", desc:"실명 프로필, 친구 1000명 이상"},
  {id:7, name:"페이스북 비즈니스 계정", price_trx:120, price_usdt:24, stock:15, icon:"🏢", desc:"비즈니스 인증, 광고주 계정"}
];

const WALLET = "TWk75rL7Y7yS2eLZhLEpA7UeVVWpTJTih4";
let orders = {};

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

async function handleRequest(request) {
  const url = new URL(request.url);
  const path = url.pathname;
  
  // CORS preflight
  if (request.method === 'OPTIONS') {
    return response({ok: true});
  }
  
  // API endpoints
  if (path === '/api/health') {
    return response({status: 'ok', timestamp: new Date().toISOString()});
  }
  
  if (path === '/api/products') {
    return response({products: PRODUCTS});
  }
  
  if (path === '/api/payment/create') {
    if (request.method !== 'POST') {
      return response({error: 'Method not allowed'}, 405);
    }
    const body = await request.json();
    const orderId = 'ORD' + Date.now() + Math.random().toString(36).substr(2, 6).toUpperCase();
    const order = {
      order_id: orderId,
      user_id: body.user_id,
      product_id: body.product_id,
      amount: body.amount,
      currency: body.currency,
      payment_address: WALLET,
      status: 'pending',
      created_at: new Date().toISOString(),
      expires_at: new Date(Date.now() + 15 * 60 * 1000).toISOString()
    };
    orders[orderId] = order;
    return response(order);
  }
  
  if (path === '/api/payment/verify') {
    const orderId = url.searchParams.get('order_id');
    const order = orders[orderId];
    if (!order) {
      return response({error: 'Order not found'}, 404);
    }
    return response({confirmed: true, order_id: orderId});
  }
  
  if (path.startsWith('/api/admin/')) {
    const userId = request.headers.get('X-User-Id');
    if (!userId || !['8427378474', '8733970362'].includes(userId)) {
      return response({error: 'Unauthorized'}, 401);
    }
    return response({orders: Object.values(orders)});
  }
  
  return response({error: 'Not found'}, 404);
}

addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request));
});
