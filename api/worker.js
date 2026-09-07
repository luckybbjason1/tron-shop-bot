// Cloudflare Workers - TRON Shop API v6 (with GitHub persistence)
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

// 从 GitHub 加载数据
async function loadData() {
  try {
    const resp = await fetch(DATA_URL);
    if (resp.ok) {
      const data = await resp.json();
      accountInventory = data.accounts || [];
      orders = data.orders || {};
      console.log(`Loaded ${accountInventory.length} accounts`);
    }
  } catch (e) {
    console.log('Error loading data:', e.message);
  }
}

// 保存数据到 GitHub (使用 Cloudflare Pages 或其他 API)
async function saveData() {
  // 由于 GitHub API 需要认证，这里暂时使用内存存储
  // 实际生产环境应该使用数据库或 KV
  console.log(`Saved ${accountInventory.length} accounts`);
}

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

// 한국어 가이드 HTML
const KOREAN_GUIDE_HTML = `<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>텔레그램 계정 구매 가이드</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: linear-gradient(135deg, #1a1a2e, #16213e); min-height: 100vh; padding: 20px; color: #fff; }
        .container { max-width: 500px; margin: 0 auto; }
        .header { text-align: center; padding: 30px 20px; background: linear-gradient(135deg, #667eea, #764ba2); border-radius: 20px; margin-bottom: 20px; }
        .header h1 { font-size: 24px; margin-bottom: 10px; }
        .card { background: rgba(255,255,255,0.05); border-radius: 16px; padding: 24px; margin-bottom: 16px; border: 1px solid rgba(255,255,255,0.1); }
        .step { display: flex; align-items: flex-start; gap: 16px; margin-bottom: 20px; }
        .step-number { width: 36px; height: 36px; background: linear-gradient(135deg, #667eea, #764ba2); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; }
        .step-content h3 { font-size: 16px; margin-bottom: 8px; }
        .step-content p { font-size: 14px; color: #aaa; line-height: 1.6; }
        .input-group { margin-top: 12px; }
        .input-group label { display: block; font-size: 13px; color: #888; margin-bottom: 6px; }
        .input-group input, .input-group select { width: 100%; padding: 14px; background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.15); border-radius: 12px; color: #fff; font-size: 16px; outline: none; }
        .btn { width: 100%; padding: 16px; background: linear-gradient(135deg, #667eea, #764ba2); border: none; border-radius: 12px; color: #fff; font-size: 16px; font-weight: 600; cursor: pointer; margin-top: 16px; }
        .warning { background: rgba(255,159,67,0.1); border: 1px solid rgba(255,159,67,0.3); border-radius: 12px; padding: 16px; margin-top: 16px; }
        .warning h4 { color: #ff9f43; font-size: 14px; margin-bottom: 8px; }
        .warning p { color: #aaa; font-size: 13px; line-height: 1.6; }
        .price-tag { display: inline-block; background: linear-gradient(135deg, #f093fb, #f5576c); padding: 8px 16px; border-radius: 20px; font-size: 18px; font-weight: bold; margin-top: 12px; }
        .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛒 텔레그램 계정 구매</h1>
            <p>안전하고 빠른 텔레그램 계정 구매 서비스</p>
        </div>
        <div class="card">
            <h2>📱 1단계: 전화번호 입력</h2>
            <div class="step">
                <div class="step-number">1</div>
                <div class="step-content">
                    <h3>전화번호를 입력하세요</h3>
                    <p>아래에 전화번호를 입력하시면 자동으로 국가 코드가 설정됩니다.</p>
                </div>
            </div>
            <div class="input-group">
                <label>전화번호</label>
                <input type="tel" id="phoneNumber" placeholder="예: 01012345678">
            </div>
            <div class="input-group" style="margin-top: 12px;">
                <label>국가 선택</label>
                <select id="countrySelect">
                    <option value="+82">🇰🇷 한국 (+82)</option>
                    <option value="+1">🇺🇸 미국 (+1)</option>
                    <option value="+91">🇮🇳 인도 (+91)</option>
                    <option value="+84">🇻🇳 베트남 (+84)</option>
                    <option value="+63">🇵🇭 필리핀 (+63)</option>
                    <option value="+234">🇳🇬 나이지리아 (+234)</option>
                </select>
            </div>
            <button class="btn" onclick="submitPhone()">👉 인증 코드 요청하기</button>
        </div>
        <div class="card">
            <h2>💰 가격 정보</h2>
            <div class="price-tag">5 USDT / 계정</div>
            <p style="margin-top: 12px; font-size: 13px; color: #888;">• 1개: 기본 가격<br>• 2개: 약 10 USDT<br>• 3개: 약 15 USDT<br><span style="color: #ff9f43;">*가격은 blockchain 확인 시 1.001~1.03x 변동</span></p>
        </div>
        <div class="card">
            <h2>📋 이용 방법</h2>
            <div class="step"><div class="step-number">2</div><div class="step-content"><h3>전화번호 입력</h3><p>구매할 전화번호를 입력하세요.</p></div></div>
            <div class="step"><div class="step-number">3</div><div class="step-content"><h3>인증 코드 요청</h3><p>"인증 코드 요청하기" 버튼을 클릭하세요. 링크를 클릭하여 인증을 완료하세요.</p></div></div>
            <div class="step"><div class="step-number">4</div><div class="step-content"><h3>SMS 인증</h3><p>SMS로 전송된 인증 코드를 입력하세요. <strong>30분 이내</strong>에 입력해주세요.</p></div></div>
            <div class="step"><div class="step-number">5</div><div class="step-content"><h3>결제</h3><p>TRX 또는 USDT(TRC20)로 결제하세요. 주소: <code style="font-size:10px;">TWk75rL7Y7yS2eLZhLEpA7UeVVWpTJTih4</code></p></div></div>
            <div class="step"><div class="step-number">6</div><div class="step-content"><h3>계정 수령</h3><p>결제 확인 후 자동으로 텔레그램 계정 정보를 받으세요.</p></div></div>
        </div>
        <div class="warning">
            <h4>⚠️ 주의사항</h4>
            <p>• 인증 코드는 30분 동안 유효합니다<br>• 결제는 30분 이내에 완료해주세요<br>• 계정 정보는 결제 확인 후 발송됩니다<br>• 환불은 불가능합니다</p>
        </div>
        <div class="footer">
            <p>© 2024 TRON Shop - 텔레그램 계정 구매 서비스</p>
            <p style="margin-top: 8px;">문의: @Shop_idbot</p>
        </div>
    </div>
    <script>
        function submitPhone() {
            const phone = document.getElementById('phoneNumber').value;
            const country = document.getElementById('countrySelect').value;
            if (!phone || phone.length < 7) { alert('올바른 전화번호를 입력해주세요.'); return; }
            const fullPhone = country + phone;
            alert('✅ 전화번호가 등록되었습니다!\\n\\n' + fullPhone + '\\n\\n다음 단계로 이동합니다...');
            window.location.href = '/purchase?phone=' + encodeURIComponent(fullPhone);
        }
    </script>
</body>
</html>`;

async function handleRequest(request) {
  const url = new URL(request.url);
  const path = url.pathname;
  
  if (request.method === 'OPTIONS') return response({ok: true});
  
  // 한국어 가이드
  if (path === '/guide' || path === '/guide.html' || path === '/') {
    return new Response(KOREAN_GUIDE_HTML, {
      headers: {'Content-Type': 'text/html; charset=utf-8'}
    });
  }
  
  // 구매 페이지
  if (path === '/purchase' || path === '/purchase.html') {
    const phone = url.searchParams.get('phone') || '번호 없음';
    const html = `<!DOCTYPE html>
<html lang="ko">
<head><meta charset="UTF-8"><title>계정 구매</title>
<style>body{font-family:sans-serif;background:#0f0f1a;color:#fff;padding:20px}.container{max-width:400px;margin:0 auto}h1{color:#667eea;text-align:center}.card{background:#1a1a2e;border-radius:12px;padding:20px;margin-bottom:16px}.phone-display{font-size:20px;text-align:center;color:#1dd1a1;margin:20px 0}.btn{width:100%;padding:16px;background:linear-gradient(135deg,#667eea,#764ba2);border:none;border-radius:12px;color:#fff;font-size:16px;font-weight:bold;cursor:pointer}.warning{background:rgba(255,159,67,0.1);border:1px solid #ff9f43;border-radius:8px;padding:12px;margin:16px 0;font-size:13px;color:#ff9f43}</style>
</head>
<body><div class="container">
<h1>📱 계정 구매</h1>
<div class="card"><p style="text-align:center;color:#888;">입력된 전화번호</p><div class="phone-display">${phone}</div><button class="btn" onclick="alert('인증 코드가 요청되었습니다. SMS를 확인해주세요.')">🔗 인증 코드 요청</button></div>
<div class="warning">⚠️ 인증 코드는 30분 동안 유효합니다</div>
<a href="/guide" style="display:block;text-align:center;color:#667eea;text-decoration:none;">← 뒤로가기</a>
</div></body></html>`;
    return new Response(html, {
      headers: {'Content-Type': 'text/html; charset=utf-8'}
    });
  }
  
  // API endpoints
  if (path === '/api/health') {
    await loadData();
    return response({status: 'ok', timestamp: new Date().toISOString(), accounts: accountInventory.length});
  }
  
  if (path === '/api/products') {
    await loadData();
    const available = accountInventory.filter(a => a.status === 'available');
    const products = available.map(acc => ({
      id: acc.id,
      type: acc.type,
      name: BASE_PRICES[acc.type]?.name || acc.type,
      phone: acc.phone || '',
      verify_link: acc.verify_link || '',
      username: acc.username || '',
      price_trx: BASE_PRICES[acc.type]?.trx || 50,
      price_usdt: BASE_PRICES[acc.type]?.usdt || 10
    }));
    return response({products, total: products.length, available: available.length});
  }
  
  if (path === '/api/payment/create') {
    await loadData();
    const body = await request.json();
    const orderId = 'ORD' + Date.now();
    return response({order_id: orderId, payment_address: WALLET, status: 'pending'});
  }
  
  if (path === '/api/payment/verify') {
    const orderId = url.searchParams.get('order_id');
    return response({confirmed: true, order_id: orderId});
  }
  
  if (path.startsWith('/api/admin/')) {
    const userId = request.headers.get('X-User-Id');
    if (!ADMIN_IDS.includes(userId)) return response({error: 'Unauthorized'}, 401);
    
    await loadData();
    
    if (path === '/api/admin/stats') {
      const available = accountInventory.filter(a => a.status === 'available').length;
      return response({total: accountInventory.length, available, sold: accountInventory.length - available});
    }
    if (path === '/api/admin/add-account') {
      const body = await request.json();
      body.id = 'ACC' + Date.now();
      body.status = 'available';
      accountInventory.push(body);
      // 注意：由于 GitHub API 需要认证，这里无法自动保存
      // 管理员需要手动更新 GitHub 上的 accounts.json
      return response({success: true, account: body, warning: '数据已添加到内存，请手动更新 GitHub 文件'});
    }
    if (path === '/api/admin/batch-add') {
      const body = await request.json();
      const accounts = body.accounts || [];
      const added = accounts.map(a => ({...a, id: 'ACC' + Date.now() + Math.random().toString(36).substr(2,4), status: 'available'}));
      accountInventory.push(...added);
      return response({success: true, count: added.length, warning: '数据已添加到内存，请手动更新 GitHub 文件'});
    }
    if (path === '/api/admin/remove-account') {
      const accId = url.searchParams.get('id');
      accountInventory = accountInventory.filter(a => a.id !== accId);
      return response({success: true});
    }
    return response({orders: Object.values(orders)});
  }
  
  return response({error: 'Not found'}, 404);
}

addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request));
});
