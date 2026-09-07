// Cloudflare Workers API for TRON Shop
const PRODUCTS = [
  { id: 1, name: "一般 텔레그램 계정", price_trx: 50, price_usdt: 10, stock: 50, icon: "📱", desc: "생성일 1년 이상, 전화번호 검증 완료 계정" },
  { id: 2, name: "프리미엄 텔레그램 계정", price_trx: 150, price_usdt: 30, stock: 20, icon: "⭐", desc: "생성일 3년 이상, 고급 프로필, 검증 완료" },
  { id: 3, name: "텔레그램 채널 계정", price_trx: 80, price_usdt: 15, stock: 15, icon: "📢", desc: "가입자 1000명 이상 채널 소유 계정" },
  { id: 4, name: "인스타그램 계정", price_trx: 100, price_usdt: 20, stock: 30, icon: "📷", desc: "팔로워 5000명 이상, 활동적인 계정" },
  { id: 5, name: "인스타그램 프리미엄", price_trx: 200, price_usdt: 40, stock: 10, icon: "💎", desc: "팔로워 2만 명 이상, 업계 인증 계정" },
  { id: 6, name: "페이스북 계정", price_trx: 60, price_usdt: 12, stock: 40, icon: "📘", desc: "실명 프로필, 친구 1000명 이상" },
  { id: 7, name: "페이스북 비즈니스 계정", price_trx: 120, price_usdt: 24, stock: 15, icon: "🏢", desc: "비즈니스 인증, 광고주 계정" }
];

const ADMIN_IDS = [8427378474, 8733970362];
const PAYMENT_ADDRESS = "TWk75rL7Y7yS2eLZhLEpA7UeVVWpTJTih4";
const orders = {};

function json(response, status = 200) {
  return new Response(JSON.stringify(response), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, X-User-Id"
    }
  });
}

addEventListener("fetch", event => {
  event.respondWith(handleRequest(event.request));
});

async function handleRequest(request) {
  const url = new URL(request.url);
  const path = url.pathname;

  if (request.method === "OPTIONS") {
    return json({});
  }

  if (path === "/api/health") {
    return json({ status: "ok", timestamp: new Date().toISOString() });
  }

  if (path === "/api/products") {
    return json({ products: PRODUCTS });
  }

  if (path === "/api/payment/create" && request.method === "POST") {
    const data = await request.json();
    const orderId = "ORD" + Date.now() + Math.random().toString(36).substr(2, 6).toUpperCase();
    const order = {
      order_id: orderId,
      user_id: data.user_id,
      product_id: data.product_id,
      amount: data.amount,
      currency: data.currency || "TRX",
      payment_address: PAYMENT_ADDRESS,
      status: "pending",
      created_at: new Date().toISOString(),
      expires_at: new Date(Date.now() + 15 * 60 * 1000).toISOString()
    };
    orders[orderId] = order;
    return json(order);
  }

  if (path.startsWith("/api/order/")) {
    const orderId = path.split("/").pop();
    const order = orders[orderId];
    if (order) {
      return json(order);
    }
    return json({ error: "Not found" }, 404);
  }

  if (path === "/api/admin/orders" && request.method === "GET") {
    const userId = parseInt(request.headers.get("X-User-Id") || "0");
    if (!ADMIN_IDS.includes(userId)) {
      return json({ error: "Forbidden" }, 403);
    }
    return json({ orders: Object.values(orders) });
  }

  if (path === "/api/payment/verify" && request.method === "POST") {
    const data = await request.json();
    const order = orders[data.order_id];
    if (order) {
      order.status = "paid";
      order.transaction_hash = data.transaction_hash;
      order.paid_at = new Date().toISOString();
      return json({ order_id: data.order_id, status: "paid" });
    }
    return json({ error: "Not found" }, 404);
  }

  return json({ error: "Not found" }, 404);
}
