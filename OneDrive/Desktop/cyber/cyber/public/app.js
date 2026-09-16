// Globals
let activeCartItem = null;
let currentChatHistory = [];
let auditLogsCache = [];
let pollingIntervalId = null;

// DOM Elements
const catalogContainer = document.getElementById('catalog-products-container');
const chatHistoryList = document.getElementById('chat-history-list');
const chatInputForm = document.getElementById('chat-input-box');
const chatInputText = document.getElementById('chat-input-text');
const auditLogsContainer = document.getElementById('audit-logs-container');
const spentLimitBadge = document.getElementById('spent-limit-badge');
const llmStatusBadge = document.getElementById('llm-status-badge');
const paymentStatusBadge = document.getElementById('payment-status-badge');

// Checkout Widget Elements
const checkoutWidget = document.getElementById('checkout-widget-overlay');
const checkoutTitle = document.getElementById('checkout-product-title');
const checkoutQty = document.getElementById('checkout-product-qty');
const checkoutPrice = document.getElementById('checkout-product-price');
const checkoutTotal = document.getElementById('checkout-product-total');
const safetyGateBanner = document.getElementById('safety-gate-banner');
const safetyGateReason = document.getElementById('safety-gate-reason');
const checkoutCancelBtn = document.getElementById('checkout-cancel-btn');
const checkoutConfirmBtn = document.getElementById('checkout-confirm-btn');
const checkoutAuthorizeBtn = document.getElementById('checkout-authorize-btn');

// Settings HUD Modal Elements
const openSettingsBtn = document.getElementById('open-settings-btn');
const closeSettingsBtn = document.getElementById('close-settings-btn');
const cancelSettingsBtn = document.getElementById('cancel-settings-btn');
const saveSettingsBtn = document.getElementById('save-settings-btn');
const settingsModal = document.getElementById('settings-modal');
const resetSpentBtn = document.getElementById('reset-spent-today-btn');
const spentTodayDisplay = document.getElementById('spent-today-counter-display');

// Settings Inputs
const inputGroqKey = document.getElementById('input-groq-key');
const inputRazorpayId = document.getElementById('input-razorpay-id');
const inputRazorpaySecret = document.getElementById('input-razorpay-secret');
const inputSingleLimit = document.getElementById('input-single-limit');
const inputDailyLimit = document.getElementById('input-daily-limit');
const checkFailDecline = document.getElementById('check-fail-decline');
const checkFailRate = document.getElementById('check-fail-rate');
const checkFailStock = document.getElementById('check-fail-stock');
const checkFailParams = document.getElementById('check-fail-params');

// Mock Razorpay Modal Elements
const mockPaymentModal = document.getElementById('mock-payment-modal');
const mockSummaryProd = document.getElementById('mock-payment-summary-prod');
const mockSummaryQty = document.getElementById('mock-payment-summary-qty');
const mockSummaryTotal = document.getElementById('mock-payment-summary-total');
const mockPaymentCancelBtn = document.getElementById('mock-payment-cancel-btn');
const mockPaymentSuccessBtn = document.getElementById('mock-payment-success-btn');

// --- INITIALIZATION ---
window.addEventListener('DOMContentLoaded', () => {
  fetchCatalog();
  fetchSettings();
  startAuditLogPolling();
  
  // Event Listeners
  chatInputForm.addEventListener('submit', handleSendMessage);
  openSettingsBtn.addEventListener('click', openSettingsModal);
  closeSettingsBtn.addEventListener('click', closeSettingsModal);
  cancelSettingsBtn.addEventListener('click', closeSettingsModal);
  saveSettingsBtn.addEventListener('click', saveSettings);
  resetSpentBtn.addEventListener('click', resetSpentCounter);
  
  checkoutCancelBtn.addEventListener('click', hideCheckoutWidget);
  checkoutConfirmBtn.addEventListener('click', () => initiateCheckout(false));
  checkoutAuthorizeBtn.addEventListener('click', () => initiateCheckout(true));
  
  // Prevent closing on modal content click
  settingsModal.addEventListener('click', (e) => {
    if (e.target === settingsModal) closeSettingsModal();
  });
});

// --- CATALOG API ---
async function fetchCatalog() {
  try {
    const res = await fetch('/api/catalog');
    const data = await res.json();
    renderCatalog(data.products);
  } catch (err) {
    catalogContainer.innerHTML = `<div class="error-text">Failed to fetch inventory node.</div>`;
    console.error(err);
  }
}

function renderCatalog(products) {
  catalogContainer.innerHTML = '';
  products.forEach(p => {
    const card = document.createElement('div');
    card.className = 'product-card';
    card.id = `prod-card-${p.id}`;
    
    // Build specs list
    const specsLi = p.specs.map(spec => `<li>${spec}</li>`).join('');
    
    card.innerHTML = `
      <div class="product-image-container">
        <img src="${p.image}" alt="${p.name}" onerror="this.src='https://placehold.co/150x150/0b1020/00f0ff?text=${encodeURIComponent(p.name)}'">
      </div>
      <div class="product-details">
        <div>
          <h3>${p.name}</h3>
          <div class="product-price">₹${p.price.toLocaleString('en-IN')}</div>
          <p class="product-description">${p.description}</p>
          <ul class="product-specs">${specsLi}</ul>
        </div>
        <div class="product-meta-row">
          <span class="product-stock ${p.stock <= 3 ? 'low-stock' : 'in-stock'}">
            [${p.stock <= 3 ? 'LOW STOCK' : 'IN STOCK'}: ${p.stock} units]
          </span>
          <button class="btn btn-primary btn-sm" onclick="triggerPurchaseFromCatalog('${p.id}')">BUY</button>
        </div>
      </div>
    `;
    catalogContainer.appendChild(card);
  });
}

function triggerPurchaseFromCatalog(productId) {
  appendMessage('user', `I would like to purchase the product with ID: ${productId}`);
  sendMessageToAgent(`I would like to purchase the product with ID: ${productId}`);
}

// --- SETTINGS & DEVELOPER HUD ---
async function fetchSettings() {
  try {
    const res = await fetch('/api/settings');
    const data = await res.json();
    
    // Update Badge Statuses
    updateStatusBadges(data);
    
    // Load inputs in settings modal
    inputSingleLimit.value = data.singleTxLimit;
    inputDailyLimit.value = data.dailyTotalLimit;
    checkFailDecline.checked = data.simulatePaymentDecline;
    checkFailRate.checked = data.simulateRateLimit;
    checkFailStock.checked = data.simulateMissingInventory;
    checkFailParams.checked = data.simulateInvalidToolParam;
    
    // Update local labels
    spentLimitBadge.textContent = `SPENT TODAY: ₹${data.spentToday.toLocaleString('en-IN')}`;
    spentTodayDisplay.textContent = `₹${data.spentToday.toLocaleString('en-IN')}`;
    
  } catch (err) {
    console.error('Settings fetch error:', err);
  }
}

function updateStatusBadges(settings) {
  // LLM Status badge
  const llmInd = llmStatusBadge.querySelector('.status-indicator');
  const llmLabel = llmStatusBadge.querySelector('.status-label');
  if (settings.groqApiKeySet) {
    llmInd.className = 'status-indicator green';
    llmLabel.textContent = 'LLM: GROQ LIVE';
  } else {
    llmInd.className = 'status-indicator yellow';
    llmLabel.textContent = 'LLM: MOCK SIMULATOR';
  }
  
  // Payment Status badge
  const payInd = paymentStatusBadge.querySelector('.status-indicator');
  const payLabel = paymentStatusBadge.querySelector('.status-label');
  if (settings.razorpayApiKeySet) {
    payInd.className = 'status-indicator green';
    payLabel.textContent = 'PAYMENT: RAZORPAY TEST';
  } else {
    payInd.className = 'status-indicator yellow';
    payLabel.textContent = 'PAYMENT: MOCK MODAL';
  }
}

function openSettingsModal() {
  settingsModal.style.display = 'flex';
}

function closeSettingsModal() {
  settingsModal.style.display = 'none';
}

async function saveSettings() {
  try {
    const payload = {
      groqApiKey: inputGroqKey.value,
      razorpayKeyId: inputRazorpayId.value,
      razorpayKeySecret: inputRazorpaySecret.value,
      singleTxLimit: inputSingleLimit.value,
      dailyTotalLimit: inputDailyLimit.value,
      simulatePaymentDecline: checkFailDecline.checked,
      simulateRateLimit: checkFailRate.checked,
      simulateMissingInventory: checkFailStock.checked,
      simulateInvalidToolParam: checkFailParams.checked
    };
    
    const res = await fetch('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    
    if (res.ok) {
      await fetchSettings();
      closeSettingsModal();
      // Add a status message to chat history
      appendMessage('system', 'System configuration changes applied successfully via Developer HUD.');
    } else {
      alert('Failed to save settings node.');
    }
  } catch (err) {
    console.error(err);
  }
}

async function resetSpentCounter() {
  try {
    const res = await fetch('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ resetSpentToday: true })
    });
    if (res.ok) {
      await fetchSettings();
      appendMessage('system', 'Daily limit spent counter reset to ₹0.');
    }
  } catch (err) {
    console.error(err);
  }
}

// --- CONVERSATIONAL COMMERCE CHAT ---
function appendMessage(role, text) {
  const messageDiv = document.createElement('div');
  messageDiv.className = `message ${role}`;
  
  const senderSpan = document.createElement('span');
  senderSpan.className = 'message-sender';
  senderSpan.textContent = role === 'user' ? 'CLIENT // GUEST' : (role === 'system' ? 'SYSTEM CORE' : 'AI COMMERCE BROKER');
  
  const contentDiv = document.createElement('div');
  contentDiv.className = 'message-content';
  
  // Format markdown-like elements (e.g. bold, bullet points)
  let formattedText = text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>');
    
  contentDiv.innerHTML = formattedText;
  
  messageDiv.appendChild(senderSpan);
  messageDiv.appendChild(contentDiv);
  chatHistoryList.appendChild(messageDiv);
  
  // Scroll to bottom
  chatHistoryList.scrollTop = chatHistoryList.scrollHeight;
}

function appendTypingIndicator() {
  const indicator = document.createElement('div');
  indicator.className = 'message model typing-indicator-container';
  indicator.id = 'typing-indicator';
  indicator.innerHTML = `
    <span class="message-sender">AI COMMERCE BROKER</span>
    <div class="message-content">
      <div class="typing-indicator">
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
      </div>
    </div>
  `;
  chatHistoryList.appendChild(indicator);
  chatHistoryList.scrollTop = chatHistoryList.scrollHeight;
}

function removeTypingIndicator() {
  const indicator = document.getElementById('typing-indicator');
  if (indicator) indicator.remove();
}

function handleSendMessage(e) {
  e.preventDefault();
  const text = chatInputText.value.trim();
  if (!text) return;
  
  appendMessage('user', text);
  chatInputText.value = '';
  
  sendMessageToAgent(text);
}

async function sendMessageToAgent(message) {
  appendTypingIndicator();
  
  try {
    const payload = {
      message: message,
      chatHistory: currentChatHistory
    };
    
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    
    removeTypingIndicator();
    
    if (!res.ok) {
      // Failure Recovery: Graceful handle on HTTP errors
      const errData = await res.json().catch(() => ({}));
      const errMsg = errData.error || 'Server error interface latency.';
      appendMessage('model', `⚠️ **Transaction Recovery Protocol Active:** My cognitive connection was disrupted. Rationale: ${errMsg}. Let's try searching the catalog or adjusting parameters in settings.`);
      return;
    }
    
    const data = await res.json();
    
    // Append Agent message to chat
    const responseText = data.parts ? data.parts[0].text : 'Node connected. Awaiting command.';
    appendMessage('model', responseText);
    
    // Save to current history
    currentChatHistory.push({ role: 'user', text: message });
    currentChatHistory.push({ role: 'model', text: responseText });
    if (currentChatHistory.length > 20) {
      currentChatHistory.shift();
      currentChatHistory.shift(); // Keep history size small
    }
    
    // Process tool-calling actions
    if (data.action === 'trigger_payment' && data.params) {
      showCheckoutWidget(data.params.productId, data.params.quantity || 1);
    }
    
  } catch (err) {
    removeTypingIndicator();
    appendMessage('model', `⚠️ **Network Link Disconnected:** I cannot interface with the LLM routing node. Please make sure the backend server.js is running.`);
    console.error(err);
  }
}

// --- CHECKOUT & TRANSACTION GATING ---
async function showCheckoutWidget(productId, quantity) {
  try {
    const res = await fetch('/api/catalog');
    const data = await res.json();
    const product = data.products.find(p => p.id === productId);
    
    if (!product) return;
    
    activeCartItem = {
      productId: productId,
      quantity: quantity,
      productName: product.name,
      price: product.price
    };
    
    // Populate widget details
    checkoutTitle.textContent = product.name;
    checkoutQty.textContent = quantity;
    checkoutPrice.textContent = `₹${product.price.toLocaleString('en-IN')}`;
    
    const totalAmount = product.price * quantity;
    checkoutTotal.textContent = `₹${totalAmount.toLocaleString('en-IN')}`;
    
    // Hide warning by default
    safetyGateBanner.style.display = 'none';
    checkoutAuthorizeBtn.style.display = 'none';
    checkoutConfirmBtn.style.display = 'inline-flex';
    
    // Verify Gated limits pre-checkout to flag block warning immediately
    const checkRes = await fetch('/api/settings');
    const settings = await checkRes.json();
    
    let isBlocked = false;
    if (totalAmount > settings.singleTxLimit) {
      safetyGateReason.textContent = `Exceeded single transaction safety gate threshold (₹${totalAmount.toLocaleString('en-IN')} > Max Limit ₹${settings.singleTxLimit.toLocaleString('en-IN')}).`;
      isBlocked = true;
    } else if (settings.spentToday + totalAmount > settings.dailyTotalLimit) {
      safetyGateReason.textContent = `Exceeded daily total spending limit (₹${(settings.spentToday + totalAmount).toLocaleString('en-IN')} > Max limit ₹${settings.dailyTotalLimit.toLocaleString('en-IN')}).`;
      isBlocked = true;
    }
    
    if (isBlocked) {
      safetyGateBanner.style.display = 'block';
      checkoutConfirmBtn.style.display = 'none';
      checkoutAuthorizeBtn.style.display = 'inline-flex';
    }
    
    checkoutWidget.style.display = 'block';
    
  } catch (err) {
    console.error(err);
  }
}

function hideCheckoutWidget() {
  checkoutWidget.style.display = 'none';
  activeCartItem = null;
}

// Initiate the checkout API. If bypassGating is true, manually hits the override endpoint
async function initiateCheckout(bypassGating = false) {
  if (!activeCartItem) return;
  
  const thoughtText = `Initiating money checkout sequence for ${activeCartItem.quantity}x ${activeCartItem.productName}.`;
  const endpoint = bypassGating ? '/api/checkout/approve-gate' : '/api/checkout/initiate';
  
  try {
    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        productId: activeCartItem.productId,
        quantity: activeCartItem.quantity,
        thought: thoughtText
      })
    });
    
    const data = await res.json();
    
    if (!res.ok) {
      // Failure Recovery: API level error (429 rate limit, 404 stock, etc.)
      const errorMsg = data.error || 'Payment execution interface failed.';
      appendMessage('system', `⚠️ FAILURE EVENT DETECTED // ERROR CODE: ${data.code || 'UNKNOWN_ERROR'}\n${errorMsg}`);
      hideCheckoutWidget();
      
      // Let agent follow up on recovery response
      sendMessageToAgent(`The checkout failed with error: "${errorMsg}". Assist me with alternative solutions.`);
      return;
    }
    
    if (data.status === 'gated') {
      // Double check in case limits changed during execution
      safetyGateReason.textContent = `Blocked: Exceeded security thresholds. Explicit bypass required.`;
      safetyGateBanner.style.display = 'block';
      checkoutConfirmBtn.style.display = 'none';
      checkoutAuthorizeBtn.style.display = 'inline-flex';
      appendMessage('system', 'Transaction BLOCKED by Transaction Safety Gating limits. Merchant approval required.');
      return;
    }
    
    if (data.status === 'approved') {
      hideCheckoutWidget();
      
      // Complete checkout depending on Live Razorpay Test Mode or Mock Modal Mode
      if (data.mode === 'live') {
        launchRazorpayCheckout(data);
      } else {
        launchMockCheckout(data);
      }
    }
    
  } catch (err) {
    appendMessage('system', 'Network connection loss during checkout initiation.');
    console.error(err);
  }
}

// LAUNCH REAL RAZORPAY WINDOW (TEST MODE)
function launchRazorpayCheckout(orderData) {
  const options = {
    key: orderData.keyId,
    amount: orderData.amount * 100,
    currency: orderData.currency,
    name: 'CYBERWARE SECURE GATE',
    description: `Purchase of ${orderData.quantity}x ${orderData.productName}`,
    order_id: orderData.orderId,
    handler: async function (response) {
      // Send payment confirmation back to server for verification
      try {
        const verifyRes = await fetch('/api/payment/verify', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            orderId: response.razorpay_order_id,
            paymentId: response.razorpay_payment_id,
            signature: response.razorpay_signature,
            productId: orderData.productId,
            quantity: orderData.quantity,
            mode: 'live'
          })
        });
        
        const verifyData = await verifyRes.json();
        
        if (verifyRes.ok) {
          appendMessage('system', `💳 payment verified: Signature verified successfully. Receipt: ${response.razorpay_payment_id}`);
          fetchCatalog(); // update stock list
          fetchSettings(); // update spent
          
          // Let AI confirm checkout conversion
          sendMessageToAgent(`Payment completed successfully. Order ID: ${response.razorpay_order_id}, Payment ID: ${response.razorpay_payment_id}. Confirm order and thank customer.`);
        } else {
          appendMessage('system', `❌ signature error: Verify mismatch. Reason: ${verifyData.error}`);
        }
      } catch (err) {
        console.error(err);
      }
    },
    prefill: {
      name: 'Guest Merchant',
      email: 'buyer@cyberware.dev',
      contact: '9999999999'
    },
    theme: {
      color: '#00f0ff'
    }
  };
  
  const rzp = new Razorpay(options);
  rzp.on('payment.failed', function (response) {
    appendMessage('system', `❌ PAYMENT ACTION DECLINED: Reason: ${response.error.description}`);
    sendMessageToAgent(`Payment failed at Razorpay checkout overlay. Reason: "${response.error.description}". Handle the recovery.`);
  });
  rzp.open();
}

// LAUNCH SIMULATED MOCK MODAL OVERLAY
function launchMockCheckout(orderData) {
  mockSummaryProd.textContent = orderData.productName;
  mockSummaryQty.textContent = orderData.quantity;
  mockSummaryTotal.textContent = `₹${orderData.amount.toLocaleString('en-IN')}`;
  
  mockPaymentModal.style.display = 'flex';
  
  // Set up click handlers
  mockPaymentCancelBtn.onclick = async () => {
    mockPaymentModal.style.display = 'none';
    appendMessage('system', 'Payment failed: Checkout session declined by customer.');
    
    // Simulate Decline verify API trigger to record failure in logs
    await fetch('/api/payment/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        orderId: orderData.orderId,
        paymentId: 'pay_failed_' + Math.random().toString(36).substr(2, 9),
        productId: orderData.productId,
        quantity: orderData.quantity,
        mode: 'mock'
      })
    });
    
    sendMessageToAgent(`The simulated payment was cancelled by customer. Adjust checkout parameters to recover.`);
  };
  
  mockPaymentSuccessBtn.onclick = async () => {
    mockPaymentModal.style.display = 'none';
    
    try {
      const verifyRes = await fetch('/api/payment/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          orderId: orderData.orderId,
          paymentId: 'pay_mock_' + Math.random().toString(36).substr(2, 9),
          productId: orderData.productId,
          quantity: orderData.quantity,
          mode: 'mock'
        })
      });
      
      const verifyData = await verifyRes.json();
      
      if (verifyRes.ok) {
        appendMessage('system', `💳 payment verified: Simulated verification validated successfully.`);
        fetchCatalog(); // update stock list
        fetchSettings(); // update spent
        
        sendMessageToAgent(`Mock Payment completed successfully. Order ID: ${orderData.orderId}. Confirm order and thank customer.`);
      } else {
        // Recovery handle for Decline Payment simulation toggle
        appendMessage('system', `❌ PAYMENT TRANSACTION DECLINED: ${verifyData.error || 'Payment failed'}`);
        sendMessageToAgent(`The mock payment verification failed with: "${verifyData.error || 'Decline'}". Suggest how customer can retry.`);
      }
      
    } catch (err) {
      console.error(err);
    }
  };
}

// --- SYSTEM AUDIT & THINKING LOGS STREAM ---
function startAuditLogPolling() {
  fetchAuditLogs();
  pollingIntervalId = setInterval(fetchAuditLogs, 1500);
}

async function fetchAuditLogs() {
  try {
    const res = await fetch('/api/audit-logs');
    const logs = await res.json();
    
    // Only re-render if count or items change to avoid layout flickering
    if (JSON.stringify(logs) === JSON.stringify(auditLogsCache)) {
      return;
    }
    
    auditLogsCache = logs;
    renderAuditLogs(logs);
    
  } catch (err) {
    console.error('Audit log fetch error:', err);
  }
}

function renderAuditLogs(logs) {
  if (logs.length === 0) {
    auditLogsContainer.innerHTML = `<div class="audit-placeholder">No transaction actions in current stack.</div>`;
    return;
  }
  
  auditLogsContainer.innerHTML = '';
  logs.forEach(log => {
    const item = document.createElement('div');
    
    // Assign status class based on safety checks
    let statusClass = 'passed';
    let displayStatus = 'PASSED';
    
    if (log.safetyCheck.status.includes('BLOCKED')) {
      statusClass = 'gated-block';
      displayStatus = 'BLOCKED BY GATE';
    } else if (log.safetyCheck.status === 'FORCE_APPROVED_BY_USER') {
      statusClass = 'gate-bypass';
      displayStatus = 'USER BYPASS';
    } else if (log.safetyCheck.status === 'COMPLETED') {
      statusClass = 'completed';
      displayStatus = 'COMPLETED';
    } else if (log.safetyCheck.status.includes('FAILED')) {
      statusClass = 'gated-block';
      displayStatus = 'FAIL EXCEPTION';
    }
    
    item.className = `audit-item ${statusClass}`;
    
    const dateFormatted = new Date(log.timestamp).toLocaleTimeString();
    
    item.innerHTML = `
      <div class="audit-timestamp">${dateFormatted} // ID: ${log.id}</div>
      <div class="audit-header-title">
        <span>ACTION: ${log.action}</span>
        <span class="status ${statusClass}">${displayStatus}</span>
      </div>
      <div class="audit-thought"><strong>AI Monologue:</strong> ${log.thought}</div>
      <div class="audit-payload"><pre>${JSON.stringify(log.params, null, 2)}</pre></div>
      <div class="audit-explainability"><strong>RATIONALE:</strong> ${log.explainability}</div>
    `;
    
    auditLogsContainer.appendChild(item);
  });
}

// Clear logs button callback
document.getElementById('clear-logs-btn').addEventListener('click', async () => {
  try {
    const res = await fetch('/api/audit-logs/clear', { method: 'POST' });
    if (res.ok) {
      fetchAuditLogs();
    }
  } catch (err) {
    console.error(err);
  }
});
