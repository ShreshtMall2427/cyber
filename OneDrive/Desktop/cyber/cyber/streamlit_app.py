import os
import json
import httpx
import streamlit as st
import time
import random

# Base API URL
API_URL = "http://localhost:3000"

st.set_page_config(
    page_title="CYBERWARE // Autonomous Agentic Commerce",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Corporate Light Theme Styles Injection
st.markdown(
    """
    <style>
    /* Global Background & Base Colors */
    .stApp {
        background-color: #f8fafc !important;
        color: #0f172a !important;
    }
    
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
        font-weight: 700 !important;
        color: #0f172a !important;
        letter-spacing: -0.5px;
    }
    
    /* Logo Styling */
    .logo-glow {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1e40af;
        margin-bottom: 2px;
        letter-spacing: -1px;
    }
    
    .logo-version {
        font-size: 0.75rem;
        color: #64748b;
        font-weight: 600;
        letter-spacing: 1px;
        margin-bottom: 20px;
    }
    
    /* Product Showcase Cards */
    .product-box {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 15px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        transition: all 0.2s ease-in-out;
    }
    
    .product-box:hover {
        border-color: #cbd5e1;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        transform: translateY(-1px);
    }
    
    .price-text {
        font-size: 1.25rem;
        font-weight: 700;
        color: #1e40af;
        margin-bottom: 8px;
    }
    
    /* Audit Log Stream Cards */
    .audit-log-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 4px solid #64748b;
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 12px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02);
    }
    .audit-log-card.gated {
        border-left-color: #ef4444;
    }
    .audit-log-card.completed {
        border-left-color: #10b981;
    }
    .audit-log-card.bypass {
        border-left-color: #f59e0b;
    }
    .audit-log-card.exception {
        border-left-color: #ec4899;
    }
    
    /* Transaction Safety Container */
    .safety-gate-card {
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        border-top: 4px solid #1e40af;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -4px rgba(0, 0, 0, 0.05);
    }
    
    .safety-gate-title {
        color: #1e40af;
        font-weight: 700;
        font-size: 1.1rem;
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 1px solid #f1f5f9;
    }
    
    .safety-warning-alert {
        background-color: #fef2f2;
        border: 1px solid #fee2e2;
        padding: 10px 14px;
        border-radius: 8px;
        color: #991b1b;
        font-size: 0.875rem;
        margin-bottom: 12px;
        font-weight: 500;
    }
    
    .safety-pass-alert {
        background-color: #f0fdf4;
        border: 1px solid #dcfce7;
        padding: 10px 14px;
        border-radius: 8px;
        color: #166534;
        font-size: 0.875rem;
        margin-bottom: 12px;
        font-weight: 500;
    }
    
    </style>
    """,
    unsafe_allow_html=True
)

# --- HELPER FUNCTIONS ---
def get_api(endpoint: str):
    try:
        r = httpx.get(f"{API_URL}{endpoint}")
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        st.error(f"Cannot connect to FastAPI backend at {API_URL}. Ensure uvicorn main.py is running.")
    return None

def post_api(endpoint: str, data: dict):
    try:
        r = httpx.post(f"{API_URL}{endpoint}", json=data)
        return r
    except Exception as e:
        st.error(f"Network error during POST request: {str(e)}")
    return None

# --- INITIALIZE STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "model", "text": "Welcome to **CYBERWARE** secure neural marketplace node. I am your autonomous AI Broker.\n\nI can help you search our agent-optimized JSON catalog, recommend contextually relevant hardware, configure checkout carts, and securely execute test transactions. Ask me about our products!"}
    ]

if "active_checkout" not in st.session_state:
    st.session_state.active_checkout = None  # None or Dict with item details

if "checkout_step" not in st.session_state:
    st.session_state.checkout_step = "none"  # "none", "gating", "payment"

if "order_data" not in st.session_state:
    st.session_state.order_data = None

# Load catalog
catalog_data = get_api("/api/catalog")
products_list = catalog_data["products"] if catalog_data else []

# Load initial settings
backend_settings = get_api("/api/settings")

# --- SIDEBAR: SETTINGS & ERROR INJECTION ---
st.sidebar.markdown('<div class="logo-glow">CYBERWARE</div>', unsafe_allow_html=True)
st.sidebar.markdown('<div class="logo-version">// STREAMLIT_PORTAL</div>', unsafe_allow_html=True)

if backend_settings:
    st.sidebar.markdown("### 🔐 STACK HUD STATUS")
    
    # LLM status indicator
    if backend_settings["groqApiKeySet"]:
        st.sidebar.success("🟢 LLM: GROQ ACTIVE")
    else:
        st.sidebar.warning("🟡 LLM: MOCK SIMULATOR")
        
    # Payment status indicator
    if backend_settings["razorpayApiKeySet"]:
        st.sidebar.success("🟢 PAYMENT: RAZORPAY TEST")
    else:
        st.sidebar.warning("🟡 PAYMENT: MOCK OVERLAY")
        
    st.sidebar.info(f"SPENT TODAY: ₹{backend_settings['spentToday']:,} / Max ₹{backend_settings['dailyTotalLimit']:,}")

    # Safety limits inputs
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🛡️ SAFETY LIMIT VALUES")
    single_tx_limit = st.sidebar.number_input("Single Transaction Limit (₹)", value=int(backend_settings["singleTxLimit"]), step=1000)
    daily_total_limit = st.sidebar.number_input("Daily Spent Limit (₹)", value=int(backend_settings["dailyTotalLimit"]), step=5000)
    
    # Check if limits changed, update backend
    if (single_tx_limit != backend_settings["singleTxLimit"] or daily_total_limit != backend_settings["dailyTotalLimit"]):
        post_api("/api/settings", {
            "singleTxLimit": single_tx_limit,
            "dailyTotalLimit": daily_total_limit
        })
        st.sidebar.success("Applied limits update.")
        st.rerun()

    # spent today counter reset
    if st.sidebar.button("Reset Daily spent counters"):
        post_api("/api/settings", {"resetSpentToday": True})
        st.sidebar.success("Counters reset.")
        st.rerun()

    # Fault Injection switches
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🧪 FAULT INJECTION HUB")
    
    decline_payment = st.sidebar.toggle("Simulate Razorpay Payment Failure", value=backend_settings["simulatePaymentDecline"])
    limit_breach = st.sidebar.toggle("Simulate API Rate Limiting (429)", value=backend_settings["simulateRateLimit"])
    missing_stock = st.sidebar.toggle("Simulate Missing Inventory", value=backend_settings["simulateMissingInventory"])
    invalid_params = st.sidebar.toggle("Simulate Invalid Tool params", value=backend_settings["simulateInvalidToolParam"])
    
    # Check for toggles change, sync with FastAPI
    if (decline_payment != backend_settings["simulatePaymentDecline"] or
        limit_breach != backend_settings["simulateRateLimit"] or
        missing_stock != backend_settings["simulateMissingInventory"] or
        invalid_params != backend_settings["simulateInvalidToolParam"]):
        
        post_api("/api/settings", {
            "simulatePaymentDecline": decline_payment,
            "simulateRateLimit": limit_breach,
            "simulateMissingInventory": missing_stock,
            "simulateInvalidToolParam": invalid_params
        })
        st.sidebar.success("Injected fault state synced.")
        st.rerun()
else:
    st.sidebar.error("FastAPI backend is offline. Startup port 3000 first.")

# --- THREE COLUMN GRID LAYOUT ---
col1, col2, col3 = st.columns([1.1, 1.3, 1.1])

# --- COLUMN 1: PRODUCT SHOWCASE ---
with col1:
    st.markdown("### PRODUCT INVENTORY")
    st.caption("Structured JSON Catalog Optimized")
    st.markdown("---")
    
    for p in products_list:
        with st.container():
            st.markdown(
                f"""
                <div class="product-box">
                    <h4>{p['name']}</h4>
                    <div class="price-text">₹{p['price']:,}</div>
                    <p style="font-size:0.75rem; color:#64748b;">{p['description']}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Specs in expander
            with st.expander("Technical specs details"):
                for spec in p["specs"]:
                    st.write(f"- {spec}")
            
            # Stock check
            if p["stock"] <= 3:
                st.markdown(f"<span style='color:#ff334b; font-size:0.7rem;'>[LOW STOCK: {p['stock']} remaining]</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"<span style='color:#39ff14; font-size:0.7rem;'>[IN STOCK: {p['stock']} available]</span>", unsafe_allow_html=True)
            
            # Quick buy button
            if st.button(f"Initialize interface check", key=f"buy_btn_{p['id']}", use_container_width=True):
                st.session_state.messages.append({"role": "user", "text": f"I want to purchase {p['name']}"})
                
                # Call agent
                with st.spinner("Processing purchase sequence..."):
                    res = post_api("/api/chat", {
                        "message": f"I want to purchase the product with ID '{p['id']}'",
                        "chatHistory": st.session_state.messages[:-1]
                    })
                    if res and res.status_code == 200:
                        data = res.json()
                        resp_text = data["parts"][0]["text"]
                        st.session_state.messages.append({"role": "model", "text": resp_text})
                        
                        # Check if payment checkout was triggered
                        if data.get("action") == "trigger_payment" and data.get("params"):
                            st.session_state.active_checkout = {
                                "productId": data["params"]["productId"],
                                "quantity": data["params"].get("quantity", 1),
                                "productName": p["name"],
                                "price": p["price"],
                                "agentMessage": resp_text
                            }
                            st.session_state.checkout_step = "gating"
                st.rerun()

# --- COLUMN 2: AUTONOMOUS CHAT & TRANSACTION SAFETY MODAL ---
with col2:
    st.markdown("### AUTONOMOUS BROKER CORE")
    st.caption("Agentic Upsells & Gated Money Actions")
    st.markdown("---")

    # TRANSACTION SAFETY MODAL / OVERLAY CONTAINER
    if st.session_state.checkout_step != "none" and st.session_state.active_checkout:
        checkout_info = st.session_state.active_checkout
        total_cost = checkout_info["price"] * checkout_info["quantity"]
        
        st.markdown(
            f"""
            <div class="safety-gate-card">
                <div class="safety-gate-title">🛡️ TRANSACTION SAFETY GATE PANEL</div>
                <p style="font-size:0.85rem; margin-bottom: 10px;">
                    Initiating purchase request: <strong>{checkout_info['quantity']}x {checkout_info['productName']}</strong>
                </p>
                <div style="font-size:1.1rem; font-weight:bold; margin-bottom:12px; color:#ff007f;">
                    Total Amount Due: ₹{total_cost:,}
                </div>
            """,
            unsafe_allow_html=True
        )
        
        # 1. Evaluate Spending Limit Status
        is_blocked = False
        limit_status_text = ""
        
        if total_cost > single_tx_limit:
            is_blocked = True
            st.markdown(
                f"""
                <div class="safety-warning-alert">
                    ❌ spending limit check failed: Exceeded max single transaction budget limit (₹{total_cost:,} &gt; Limit ₹{single_tx_limit:,}).
                </div>
                """,
                unsafe_allow_html=True
            )
        elif backend_settings and backend_settings["spentToday"] + total_cost > daily_total_limit:
            is_blocked = True
            st.markdown(
                f"""
                <div class="safety-warning-alert">
                    ❌ spending limit check failed: Exceeded maximum daily spend limit (₹{backend_settings['spentToday'] + total_cost:,} &gt; Max ₹{daily_total_limit:,}).
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                """
                <div class="safety-pass-alert">
                    ✅ spending limit check passed: Transaction is safe under limit parameters.
                </div>
                """,
                unsafe_allow_html=True
            )

        # 2. Extract and display AI Explainability/Rationale Log
        # Search for JSON reasoning logs in the last agent message
        agent_msg = checkout_info["agentMessage"]
        reasoning_data = None
        
        try:
            # Parse json block from markdown code section
            if "```json" in agent_msg:
                json_part = agent_msg.split("```json")[1].split("```")[0].strip()
                reasoning_data = json.loads(json_part)
        except Exception:
            pass
            
        if reasoning_data and "reasoning_steps" in reasoning_data:
            with st.expander("🔍 step-by-step AI Rationale payload", expanded=True):
                for step in reasoning_data["reasoning_steps"]:
                    st.markdown(f"<span style='font-size:0.75rem; color:#cbd5e1;'>- {step}</span>", unsafe_allow_html=True)
                st.markdown(f"<p style='font-size:0.75rem; color:#00f0ff; margin-top:8px;'><b>Rationale:</b> {reasoning_data.get('decision_rationale', '')}</p>", unsafe_allow_html=True)
        else:
            # Fallback if no JSON found
            with st.expander("🔍 AI decision reasoning monologue", expanded=True):
                st.caption("Analyzing agent monologue trail...")
                st.markdown("<p style='font-size:0.75rem;'>Initiating transaction order to complete merchant purchase request.</p>", unsafe_allow_html=True)

        # Close HTML card block
        st.markdown("</div>", unsafe_allow_html=True)

        # Gated Actions Buttons
        if st.session_state.checkout_step == "gating":
            act_col1, act_col2, act_col3 = st.columns(3)
            
            with act_col1:
                # Cancel Button
                if st.button("Reject Payment (Cancel)", use_container_width=True):
                    st.session_state.active_checkout = None
                    st.session_state.checkout_step = "none"
                    st.session_state.messages.append({"role": "system", "text": "Transaction cancelled. Order rejected by merchant."})
                    st.rerun()
                    
            with act_col2:
                # Gated Approval Buttons
                if is_blocked:
                    if st.button("Approve Payment (User Bypass)", type="primary", use_container_width=True):
                        # Bypass limits
                        with st.spinner("Authorizing gated bypass..."):
                            res = post_api("/api/checkout/approve-gate", {
                                "productId": checkout_info["productId"],
                                "quantity": checkout_info["quantity"],
                                "thought": f"User authorized gated transaction bypass of ₹{total_cost:,}"
                            })
                            if res and res.status_code == 200:
                                st.session_state.order_data = res.json()
                                st.session_state.checkout_step = "payment"
                                st.rerun()
                else:
                    if st.button("Proceed Checkout", type="primary", use_container_width=True):
                        # Proceed standard order
                        with st.spinner("Initializing checkout orders..."):
                            res = post_api("/api/checkout/initiate", {
                                "productId": checkout_info["productId"],
                                "quantity": checkout_info["quantity"],
                                "thought": f"Checking out approved transaction of ₹{total_cost:,}"
                            })
                            if res and res.status_code == 200:
                                st.session_state.order_data = res.json()
                                st.session_state.checkout_step = "payment"
                                st.rerun()
                            elif res and res.status_code == 429:
                                # Catch rate limit failure recovery
                                st.error("Rate Limit failure simulation caught.")
                                st.session_state.checkout_step = "none"
                                st.session_state.active_checkout = None
                                st.session_state.messages.append({"role": "model", "text": "⚠️ **Rate limit Exception:** Backend interface rate limit exceeded. Recovery activated: Please try again or request manual override."})
                                st.rerun()
                            elif res and res.status_code == 404:
                                # Catch missing stock failure
                                st.error("Stock out failure simulation caught.")
                                st.session_state.checkout_step = "none"
                                st.session_state.active_checkout = None
                                st.session_state.messages.append({"role": "model", "text": "⚠️ **Out of Stock Exception:** Requested quantity exceeds stock capacity. Recovery activated: I recommend adjusting quantity or selecting another model."})
                                st.rerun()

        elif st.session_state.checkout_step == "payment" and st.session_state.order_data:
            order_info = st.session_state.order_data
            
            st.info("RAZORPAY TEST GATEWAY INTERFACE ACTIVE")
            pay_col1, pay_col2 = st.columns(2)
            
            with pay_col1:
                if st.button("Decline Simulated Payment", use_container_width=True):
                    # Verify verify endpoint with failed parameters
                    post_api("/api/payment/verify", {
                        "orderId": order_info["orderId"],
                        "paymentId": "pay_failed_streamlit",
                        "productId": order_info["productId"],
                        "quantity": order_info["quantity"],
                        "mode": order_info["mode"]
                    })
                    st.session_state.checkout_step = "none"
                    st.session_state.active_checkout = None
                    st.session_state.messages.append({"role": "system", "text": "Simulated payment cancelled by customer."})
                    
                    # Notify agent
                    with st.spinner("Processing recovery dialogue..."):
                        agent_res = post_api("/api/chat", {
                            "message": "The mock payment transaction was cancelled by user. Recommend recovery steps.",
                            "chatHistory": st.session_state.messages[:-1]
                        })
                        if agent_res and agent_res.status_code == 200:
                            st.session_state.messages.append({"role": "model", "text": agent_res.json()["parts"][0]["text"]})
                    st.rerun()
                    
            with pay_col2:
                if st.button("Complete Simulated Payment", type="primary", use_container_width=True):
                    with st.spinner("Verifying signature..."):
                        verify_res = post_api("/api/payment/verify", {
                            "orderId": order_info["orderId"],
                            "paymentId": f"pay_mock_streamlit_{random.randint(1000, 9999)}" if 'random' in globals() else f"pay_mock_streamlit_{int(time.time())}",
                            "productId": order_info["productId"],
                            "quantity": order_info["quantity"],
                            "mode": order_info["mode"]
                        })
                        
                        st.session_state.checkout_step = "none"
                        st.session_state.active_checkout = None
                        
                        if verify_res and verify_res.status_code == 200:
                            st.session_state.messages.append({"role": "system", "text": "Payment verification success. stock decremented."})
                            # Ask agent to confirm completion
                            agent_res = post_api("/api/chat", {
                                "message": f"Payment successfully completed. order ID: {order_info['orderId']}. Thank the client.",
                                "chatHistory": st.session_state.messages[:-1]
                            })
                            if agent_res and agent_res.status_code == 200:
                                st.session_state.messages.append({"role": "model", "text": agent_res.json()["parts"][0]["text"]})
                        else:
                            # Catch decline payments exception recovery
                            error_details = verify_res.json().get("detail", "Payment failed") if verify_res else "Bank decline"
                            st.session_state.messages.append({"role": "system", "text": f"Payment declined: {error_details}"})
                            # Recover
                            agent_res = post_api("/api/chat", {
                                "message": f"The mock payment verification returned decline: '{error_details}'. Handle alternative payment path.",
                                "chatHistory": st.session_state.messages[:-1]
                            })
                            if agent_res and agent_res.status_code == 200:
                                st.session_state.messages.append({"role": "model", "text": agent_res.json()["parts"][0]["text"]})
                                
                    st.rerun()

    # RENDER CHAT STREAM
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["text"])

    # Chat User input
    user_prompt = st.chat_input("Enter transmission commands here...")
    if user_prompt:
        st.session_state.messages.append({"role": "user", "text": user_prompt})
        st.rerun()  # Trigger display update before calling agent
        
if user_prompt:
    with st.spinner("Broker thinking..."):
        res = post_api("/api/chat", {
            "message": user_prompt,
            "chatHistory": st.session_state.messages[:-1]
        })
        if res and res.status_code == 200:
            data = res.json()
            resp_text = data["parts"][0]["text"]
            st.session_state.messages.append({"role": "model", "text": resp_text})
            
            # Check if checkout action is triggered
            if data.get("action") == "trigger_payment" and data.get("params"):
                p_id = data["params"]["productId"]
                p = next((prod for prod in products_list if prod["id"] == p_id), None)
                if p:
                    st.session_state.active_checkout = {
                        "productId": p_id,
                        "quantity": data["params"].get("quantity", 1),
                        "productName": p["name"],
                        "price": p["price"],
                        "agentMessage": resp_text
                    }
                    st.session_state.checkout_step = "gating"
        elif res and res.status_code == 429:
            st.session_state.messages.append({"role": "model", "text": "⚠️ **Rate Limit Exception:** API call rate limits exceeded. Graceful fallback recovery active."})
    st.rerun()

# --- COLUMN 3: SYSTEM AUDIT & PERSISTENT LOGS ---
with col3:
    st.markdown("### SYSTEM AUDIT TRAILS")
    
    # Reload/refresh logs
    log_actions_row = st.columns(2)
    with log_actions_row[0]:
        refresh_logs = st.button("🔄 Refresh stream", use_container_width=True)
    with log_actions_row[1]:
        if st.button("Clear database", use_container_width=True):
            post_api("/api/audit-logs/clear", {})
            st.rerun()
            
    st.caption("Live SQLite relational logger stream")
    st.markdown("---")
    
    audit_logs = get_api("/api/audit-logs")
    
    if audit_logs:
        for log in audit_logs:
            # Check for block or completed styling
            log_status = log["safetyCheck"]["status"]
            card_class = "passed"
            display_status = "PASSED"
            
            if "BLOCKED" in log_status:
                card_class = "gated"
                display_status = "BLOCKED BY GATE"
            elif log_status == "FORCE_APPROVED_BY_USER":
                card_class = "bypass"
                display_status = "USER BYPASS"
            elif log_status == "COMPLETED":
                card_class = "completed"
                display_status = "COMPLETED"
            elif "FAILED" in log_status:
                card_class = "gated"
                display_status = "EXCEPTION FAIL"
                
            st.markdown(
                f"""
                <div class="audit-log-card {card_class}">
                    <span style="font-size:0.65rem; color:#64748b;">{log['timestamp']} // ID: {log['id']}</span><br>
                    <strong>ACTION: {log['action']}</strong> // <span style="font-family:monospace; font-size:0.7rem; font-weight:bold;">{display_status}</span>
                    <p style="font-size:0.75rem; color:#a0aec0; margin: 4px 0;"><b>AI:</b> {log['thought']}</p>
                    <p style="font-size:0.75rem; color:#fff; background:rgba(0,240,255,0.05); padding: 4px; border-left:1.5px solid #00f0ff;"><b>RATIONALE:</b> {log['explainability']}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Payload in expander
            with st.expander(f"View payload json details"):
                st.json(log["params"])
    else:
        st.caption("No log files in stack.")
