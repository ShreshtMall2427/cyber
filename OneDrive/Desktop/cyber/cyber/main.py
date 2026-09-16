import os
import json
from pymongo import MongoClient
import hashlib
import hmac
import random
from typing import Dict, List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import dotenv
import httpx
import razorpay
from agent import GroqAgent

# Load environment variables
dotenv.load_dotenv()

app = FastAPI(title="Cyberware API Gateway", description="FastAPI transaction backend with guardrail limits and MongoDB logger")

# Enable CORS for local interfacing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")

# --- MONGO DATABASE SETUP ---
try:
    mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
    db = mongo_client["cyberware"]
    # Verify connection
    mongo_client.server_info()
    print("=============================================================")
    print("Successfully interfaced with MongoDB cluster.")
    print("=============================================================")
except Exception as e:
    print("=============================================================")
    print(f"Warning: MongoDB connection failed: {str(e)}.")
    print("Falling back to local in-memory audit logs stack.")
    print("=============================================================")
    db = None

in_memory_logs = []

def log_audit_event_db(thought: str, action: str, params: dict, safety_status: str, api_response: dict, explainability: str) -> dict:
    log_id = f"audit_{random.randint(100000000, 999999999)}"
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    log_entry = {
        "id": log_id,
        "timestamp": timestamp,
        "thought": thought,
        "action": action,
        "params": params,
        "safety_status": safety_status,
        "api_response": api_response,
        "explainability_rationale": explainability
    }
    
    if db is not None:
        try:
            db.audit_logs.insert_one(log_entry.copy())
        except Exception as e:
            print("MongoDB insert failed. Falling back to in-memory list:", e)
            in_memory_logs.append(log_entry)
    else:
        in_memory_logs.append(log_entry)
        
    return {
        "id": log_id,
        "timestamp": timestamp,
        "thought": thought,
        "action": action,
        "params": params,
        "safetyCheck": {"status": safety_status},
        "apiResponse": api_response,
        "explainability": explainability
    }

# --- CATALOG DATABASE ---
products = [
    {
        "id": "neuralink_band",
        "name": "Neuralink Band (BCI)",
        "price": 14999,
        "image": "/images/neuralink_band.jpg",
        "description": "High-bandwidth neural interface for direct mind-to-machine control and VR telemetry.",
        "specs": ["99.8% precision tracking", "USB-C wireless charging", "Bio-compatible flexible polymer strap", "8-hour active charge"],
        "stock": 5,
        "upsell_targets": ["optic_hud", "quantum_ssd"]
    },
    {
        "id": "optic_hud",
        "name": "Optic HUD Glasses",
        "price": 8499,
        "image": "/images/optic_hud.jpg",
        "description": "Holographic AR glasses with real-time AI translation, threat monitoring, and high-contrast display.",
        "specs": ["Micro-OLED display", "Dual-core HUD processor", "120Hz refresh rate", "Ambient light adaptation"],
        "stock": 12,
        "upsell_targets": ["neuralink_band"]
    },
    {
        "id": "haptic_sleeve",
        "name": "Haptic Arm Sleeve",
        "price": 19999,
        "image": "/images/haptic_sleeve.jpg",
        "description": "Premium carbon-fiber sleeve with haptic feedback arrays for immersive virtual feedback and control.",
        "specs": ["64 haptic feedback points", "Carbon-fiber reinforcement", "Under-arm breathable mesh", "Real-time telemetry sync"],
        "stock": 3,
        "upsell_targets": ["neuralink_band", "optic_hud"]
    },
    {
        "id": "quantum_ssd",
        "name": "Quantum Core SSD (4TB)",
        "price": 12500,
        "image": "/images/quantum_ssd.jpg",
        "description": "Sub-atomic crystal lattice storage drive boasting 10 TB/s reading speed and custom hardware encryption.",
        "specs": ["Lattice storage architecture", "PCIe Gen 6 compatible", "Crystal core housing", "256-bit quantum encryption"],
        "stock": 8,
        "upsell_targets": ["haptic_sleeve"]
    },
    {
        "id": "companion_droid",
        "name": "Mini AI Companion Droid",
        "price": 29999,
        "image": "/images/companion_droid.jpg",
        "description": "Conversational desktop droid equipped with facial tracking, autonomous security patrol, and home automation hub.",
        "specs": ["360-degree LIDAR scanner", "OLED expressive face screen", "Dual-microphone array", "Active battery dock charging"],
        "stock": 2,
        "upsell_targets": ["optic_hud", "quantum_ssd"]
    }
]

catalog_schema = {
    "title": "Cyberware Catalog",
    "description": "Product inventory represented in structured, machine-readable JSON schemas optimized for AI search.",
    "properties": {
        "products": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "Unique product identifier"},
                    "name": {"type": "string", "description": "Product title"},
                    "price": {"type": "number", "description": "Price in Indian Rupees (INR)"},
                    "image": {"type": "string", "description": "Relative path to image"},
                    "description": {"type": "string", "description": "Summary of the item"},
                    "specs": {"type": "array", "items": {"type": "string"}, "description": "Technical specifications"},
                    "stock": {"type": "integer", "description": "Available units remaining"},
                    "upsell_targets": {"type": "array", "items": {"type": "string"}, "description": "Suggested add-ons"}
                }
            }
        }
    }
}

# --- MEMORY CONFIGURATIONS ---
developer_settings = {
    "groq_api_key": os.getenv("GROQ_API_KEY", ""),
    "razorpay_key_id": os.getenv("RAZORPAY_KEY_ID", ""),
    "razorpay_key_secret": os.getenv("RAZORPAY_KEY_SECRET", ""),
    "single_tx_limit": 15000,
    "daily_total_limit": 50000,
    "spent_today": 0,
    "simulate_payment_decline": False,
    "simulate_rate_limit": False,
    "simulate_missing_inventory": False,
    "simulate_invalid_tool_param": False
}

# --- PYDANTIC MODEL SCHEMAS ---
class SettingsPayload(BaseModel):
    groqApiKey: Optional[str] = None
    razorpayKeyId: Optional[str] = None
    razorpayKeySecret: Optional[str] = None
    singleTxLimit: Optional[int] = None
    dailyTotalLimit: Optional[int] = None
    simulatePaymentDecline: Optional[bool] = None
    simulateRateLimit: Optional[bool] = None
    simulateMissingInventory: Optional[bool] = None
    simulateInvalidToolParam: Optional[bool] = None
    resetSpentToday: Optional[bool] = None

class CheckoutPayload(BaseModel):
    productId: str
    quantity: int
    thought: Optional[str] = ""

class PaymentVerifyPayload(BaseModel):
    orderId: str
    paymentId: str
    signature: Optional[str] = None
    productId: str
    quantity: int
    mode: str

class ChatPayload(BaseModel):
    message: str
    chatHistory: List[dict]

# --- API ENDPOINTS ---

# 1. Product Catalog
@app.get("/api/catalog")
def get_catalog():
    return {
        "schema": catalog_schema,
        "products": products
    }

# 2. Settings Fetch
@app.get("/api/settings")
def get_settings():
    return {
        "groqApiKeySet": bool(developer_settings["groq_api_key"]),
        "razorpayApiKeySet": bool(developer_settings["razorpay_key_id"] and developer_settings["razorpay_key_secret"]),
        "singleTxLimit": developer_settings["single_tx_limit"],
        "dailyTotalLimit": developer_settings["daily_total_limit"],
        "spentToday": developer_settings["spent_today"],
        "simulatePaymentDecline": developer_settings["simulate_payment_decline"],
        "simulateRateLimit": developer_settings["simulate_rate_limit"],
        "simulateMissingInventory": developer_settings["simulate_missing_inventory"],
        "simulateInvalidToolParam": developer_settings["simulate_invalid_tool_param"]
    }

# 3. Settings Save
@app.post("/api/settings")
def save_settings(payload: SettingsPayload):
    if payload.groqApiKey is not None:
        developer_settings["groq_api_key"] = payload.groqApiKey
    if payload.razorpayKeyId is not None:
        developer_settings["razorpay_key_id"] = payload.razorpayKeyId
    if payload.razorpayKeySecret is not None:
        developer_settings["razorpay_key_secret"] = payload.razorpayKeySecret
    if payload.singleTxLimit is not None:
        developer_settings["single_tx_limit"] = payload.singleTxLimit
    if payload.dailyTotalLimit is not None:
        developer_settings["daily_total_limit"] = payload.dailyTotalLimit
    if payload.simulatePaymentDecline is not None:
        developer_settings["simulate_payment_decline"] = payload.simulatePaymentDecline
    if payload.simulateRateLimit is not None:
        developer_settings["simulate_rate_limit"] = payload.simulateRateLimit
    if payload.simulateMissingInventory is not None:
        developer_settings["simulate_missing_inventory"] = payload.simulateMissingInventory
    if payload.simulateInvalidToolParam is not None:
        developer_settings["simulate_invalid_tool_param"] = payload.simulateInvalidToolParam
        
    if payload.resetSpentToday:
        developer_settings["spent_today"] = 0

    return {
        "status": "success",
        "settings": {
            "groqApiKeySet": bool(developer_settings["groq_api_key"]),
            "razorpayApiKeySet": bool(developer_settings["razorpay_key_id"] and developer_settings["razorpay_key_secret"]),
            "singleTxLimit": developer_settings["single_tx_limit"],
            "dailyTotalLimit": developer_settings["daily_total_limit"],
            "spentToday": developer_settings["spent_today"],
            "simulatePaymentDecline": developer_settings["simulate_payment_decline"],
            "simulateRateLimit": developer_settings["simulate_rate_limit"],
            "simulateMissingInventory": developer_settings["simulate_missing_inventory"],
            "simulateInvalidToolParam": developer_settings["simulate_invalid_tool_param"]
        }
    }

# 4. Fetch MongoDB Audit Logs
@app.get("/api/audit-logs")
def get_audit_logs():
    if db is not None:
        try:
            cursor = db.audit_logs.find({}, {"_id": 0}).sort("timestamp", -1).limit(100)
            logs = []
            for doc in cursor:
                logs.append({
                    "id": doc["id"],
                    "timestamp": doc["timestamp"],
                    "thought": doc["thought"],
                    "action": doc["action"],
                    "params": doc["params"],
                    "safetyCheck": {"status": doc["safety_status"]},
                    "apiResponse": doc["api_response"],
                    "explainability": doc["explainability_rationale"]
                })
            return logs
        except Exception as e:
            print("MongoDB Query Error:", e)
            
    # Fallback to sorted in-memory list
    return sorted(
        [
            {
                "id": r["id"],
                "timestamp": r["timestamp"],
                "thought": r["thought"],
                "action": r["action"],
                "params": r["params"],
                "safetyCheck": {"status": r["safety_status"]},
                "apiResponse": r["api_response"],
                "explainability": r["explainability_rationale"]
            }
            for r in in_memory_logs
        ],
        key=lambda x: x["timestamp"],
        reverse=True
    )[:100]

# 5. Clear MongoDB Audit Logs
@app.post("/api/audit-logs/clear")
def clear_audit_logs():
    global in_memory_logs
    in_memory_logs = []
    if db is not None:
        try:
            db.audit_logs.delete_many({})
        except Exception as e:
            print("MongoDB Delete Error:", e)
    return {"status": "success"}

# Helper to process order creation after checking/bypass limits
def process_checkout_approval(product: dict, quantity: int, total_amount: int, thought: str):
    use_real_razorpay = bool(developer_settings["razorpay_key_id"] and developer_settings["razorpay_key_secret"])
    
    if use_real_razorpay:
        try:
            client = razorpay.Client(auth=(developer_settings["razorpay_key_id"], developer_settings["razorpay_key_secret"]))
            
            data = {
                "amount": total_amount * 100,  # Razorpay amount is in paise
                "currency": "INR",
                "receipt": f"rcpt_{random.randint(100000, 999999)}",
                "notes": {
                    "productId": product["id"],
                    "quantity": str(quantity),
                    "reasoning": "Gated limits verified and passed"
                }
            }
            
            order = client.order.create(data=data)
            
            log_audit_event_db(
                thought,
                "razorpay_api_order_creation",
                {"productId": product["id"], "amount": total_amount},
                "PASSED",
                order,
                f"Razorpay order {order['id']} created. Safe to proceed with test checkouts."
            )
            
            return {
                "status": "approved",
                "mode": "live",
                "orderId": order["id"],
                "keyId": developer_settings["razorpay_key_id"],
                "amount": total_amount,
                "currency": "INR",
                "productName": product["name"],
                "productId": product["id"],
                "quantity": quantity
            }
            
        except Exception as e:
            log_audit_event_db(
                thought,
                "razorpay_api_order_creation",
                {"productId": product["id"], "amount": total_amount},
                "FAILED_RAZORPAY_API",
                {"error": str(e)},
                f"Failed to communicate with Razorpay Test APIs: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Razorpay Client Error: {str(e)}"
            )
    else:
        # MOCK PAYMENTS
        mock_order_id = f"order_mock_{random.randint(100000, 999999)}"
        mock_order_payload = {
            "id": mock_order_id,
            "amount": total_amount * 100,
            "currency": "INR",
            "receipt": f"rcpt_mock_{int(datetime.now().timestamp())}",
            "status": "created",
            "created_at": int(datetime.now().timestamp())
        }
        
        log_audit_event_db(
            thought,
            "mock_payment_order_creation",
            {"productId": product["id"], "amount": total_amount},
            "PASSED",
            mock_order_payload,
            f"Simulated payment order generated (Order ID: {mock_order_id}). Limit metrics cleared."
        )
        
        return {
            "status": "approved",
            "mode": "mock",
            "orderId": mock_order_id,
            "amount": total_amount,
            "currency": "INR",
            "productName": product["name"],
            "productId": product["id"],
            "quantity": quantity
        }

# 6. Gated Checkout API Route (Check limits and safety gate)
@app.post("/api/checkout/initiate")
def initiate_checkout(payload: CheckoutPayload):
    # Failure Recovery: Rate limit simulation
    if developer_settings["simulate_rate_limit"]:
        error_msg = "429 Too Many Requests: API rate limit exceeded on checkout gateway."
        log_audit_event_db(
            payload.thought,
            "initiate_checkout_api",
            {"productId": payload.productId, "quantity": payload.quantity},
            "FAILED_RATE_LIMIT",
            {"error": error_msg},
            "Transaction blocked immediately due to simulated backend rate limits."
        )
        raise HTTPException(status_code=429, detail=error_msg)
        
    # Failure Recovery: Invalid parameter check
    if developer_settings["simulate_invalid_tool_param"] or not payload.productId or payload.quantity <= 0:
        error_msg = "Invalid parameters: Product ID is empty or quantity is invalid."
        log_audit_event_db(
            payload.thought,
            "initiate_checkout_api",
            {"productId": payload.productId, "quantity": payload.quantity},
            "FAILED_INVALID_PARAMS",
            {"error": error_msg},
            "Transaction blocked at API level due to malformed tool-use arguments."
        )
        raise HTTPException(status_code=400, detail=error_msg)
        
    product = next((p for p in products if p["id"] == payload.productId), None)
    
    # Failure Recovery: Missing inventory check
    if developer_settings["simulate_missing_inventory"] or not product or product["stock"] < payload.quantity:
        stock_avail = product["stock"] if product else 0
        error_msg = f"Out of stock: Requested {payload.quantity} units of {payload.productId}, but only {stock_avail} available."
        log_audit_event_db(
            payload.thought,
            "initiate_checkout_api",
            {"productId": payload.productId, "quantity": payload.quantity},
            "FAILED_OUT_OF_STOCK",
            {"error": error_msg, "stockAvailable": stock_avail},
            f"Transaction declined because product '{payload.productId}' is currently out of stock."
        )
        raise HTTPException(status_code=404, detail=error_msg)
        
    total_amount = product["price"] * payload.quantity
    
    # --- SAFETY GATING & LIMITS CHECKS ---
    requires_approval = False
    gating_status = "PASSED"
    
    if total_amount > developer_settings["single_tx_limit"]:
        requires_approval = True
        gating_status = "BLOCKED_SINGLE_TX_LIMIT"
    elif developer_settings["spent_today"] + total_amount > developer_settings["daily_total_limit"]:
        requires_approval = True
        gating_status = "BLOCKED_DAILY_LIMIT"
        
    if requires_approval:
        rationale = f"Safety Gating Blocked: Order amount (₹{total_amount}) exceeded limits. Single TX Limit: ₹{developer_settings['single_tx_limit']}, Daily Limit Remaining: ₹{developer_settings['daily_total_limit'] - developer_settings['spent_today']}. Explicit approval required."
        
        log_audit_event_db(
            payload.thought,
            "safety_gate_evaluation",
            {"productId": payload.productId, "quantity": payload.quantity, "totalAmount": total_amount},
            gating_status,
            {"authorization": "PENDING"},
            rationale
        )
        
        return {
            "status": "gated",
            "requiresApproval": True,
            "reason": gating_status,
            "amount": total_amount,
            "currency": "INR",
            "productName": product["name"],
            "productId": product["id"],
            "quantity": payload.quantity
        }

    return process_checkout_approval(product, payload.quantity, total_amount, payload.thought)

# 7. Approve Gated transaction manually
@app.post("/api/checkout/approve-gate")
def approve_gated_checkout(payload: CheckoutPayload):
    product = next((p for p in products if p["id"] == payload.productId), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    total_amount = product["price"] * payload.quantity
    
    # Log the manual override in database
    log_audit_event_db(
        payload.thought or "User manually approved transaction via gated control panel.",
        "user_mfa_gating_bypass",
        {"productId": payload.productId, "quantity": payload.quantity, "totalAmount": total_amount},
        "FORCE_APPROVED_BY_USER",
        {"authStatus": "AUTHORIZED"},
        f"Merchant manually authorized the transaction of ₹{total_amount} for {payload.quantity}x {product['name']}. Limit constraints bypassed."
    )
    
    return process_checkout_approval(product, payload.quantity, total_amount, payload.thought)

# 8. Payment Verification (Signature Verification or simulated confirm)
@app.post("/api/payment/verify")
def verify_payment(payload: PaymentVerifyPayload):
    product = next((p for p in products if p["id"] == payload.productId), None)
    total_amount = product["price"] * payload.quantity if product else 0
    
    # Failure Recovery: Payment decline simulation check
    if developer_settings["simulate_payment_decline"]:
        error_msg = "Payment failed: The bank server declined the transaction (Simulated)."
        log_audit_event_db(
            "User completed checkout loop but payment gate simulated a decline.",
            "payment_verification",
            {"orderId": payload.orderId, "paymentId": payload.paymentId, "productId": payload.productId, "quantity": payload.quantity},
            "DECLINED_BY_BANK",
            {"status": "failed", "reason": "Declined"},
            f"Transaction declined by simulated payment handler. Product: {product['name'] if product else 'Unknown'}."
        )
        raise HTTPException(status_code=400, detail=error_msg)

    if payload.mode == "live":
        try:
            # Reconstruct signature verification in official Python SDK
            client = razorpay.Client(auth=(developer_settings["razorpay_key_id"], developer_settings["razorpay_key_secret"]))
            
            sig_data = {
                'razorpay_order_id': payload.orderId,
                'razorpay_payment_id': payload.paymentId,
                'razorpay_signature': payload.signature
            }
            
            # This verifies signature using SHA256 HMAC and raises SignatureVerificationError if mismatched
            client.utility.verify_payment_signature(sig_data)
            
            developer_settings["spent_today"] += total_amount
            if product:
                product["stock"] -= payload.quantity
                
            log_audit_event_db(
                "Real Razorpay transaction verified via official Python SDK.",
                "razorpay_signature_verification",
                {"orderId": payload.orderId, "paymentId": payload.paymentId, "productId": payload.productId, "quantity": payload.quantity},
                "COMPLETED",
                {"status": "verified", "signatureMatched": True},
                f"Successful payment signature check. Deducted stock. Total spent today: ₹{developer_settings['spent_today']}."
            )
            return {"status": "success", "paymentId": payload.paymentId}
            
        except Exception as e:
            log_audit_event_db(
                "Razorpay signature verification FAILED.",
                "razorpay_signature_verification",
                {"orderId": payload.orderId, "paymentId": payload.paymentId},
                "SIGNATURE_MISMATCH",
                {"status": "failed", "error": str(e)},
                f"Payment verification failed: Signature mismatch or key secret invalid: {str(e)}"
            )
            raise HTTPException(status_code=400, detail="Signature verification failed")
    else:
        # Mock payment verification
        developer_settings["spent_today"] += total_amount
        if product:
            product["stock"] -= payload.quantity
            
        log_audit_event_db(
            "Simulated payment success checkout completed.",
            "mock_payment_verification",
            {"orderId": payload.orderId, "paymentId": payload.paymentId, "productId": payload.productId, "quantity": payload.quantity},
            "COMPLETED",
            {"status": "success", "receiptGenerated": True},
            f"Successful mock payment. Order: {payload.orderId}. Stock updated for {product['name'] if product else 'Unknown'}. Total spent today: ₹{developer_settings['spent_today']}."
        )
        return {"status": "success", "paymentId": payload.paymentId}

# 9. Conversational AI Chat orchestrator endpoint (supports Live Groq and Mock fallback)
@app.post("/api/chat")
async def chat_handler(payload: ChatPayload):
    groq_key = developer_settings["groq_api_key"]
    
    if not groq_key:
        return handle_mock_agent_chat(payload.message, payload.chatHistory)
        
    try:
        agent = GroqAgent(api_key=groq_key, log_callback=log_audit_event_db)
        final_response = await agent.chat(payload.message, payload.chatHistory)
        return final_response
    except Exception as e:
        print("Groq Agent Loop Exception:", e)
        fallback_msg = "I apologize, but my core language subroutines are currently experiencing high latency or rate limits. Let me help you from my local buffer: I can show you our Neuralink Band (BCI), Optic HUD Glasses, Haptic Arm Sleeve, Quantum Core SSD, or Mini AI Companion Droid. Which one would you like to explore?"
        
        log_audit_event_db(
            "Groq API threw exception. Initiating local fail-safe agent response.",
            "groq_api_connection",
            {"error": str(e)},
            "SYSTEM_ERROR_FALLBACK",
            {"response": fallback_msg},
            f"System bypassed LLM failure to prevent session disconnection: {str(e)}"
        )
        return {
            "role": "model",
            "parts": [{"text": fallback_msg}],
            "thought": "LLM exception bypassed. local system recovery response triggered."
        }

# --- MOCK CHAT STATE ROUTER ---
def handle_mock_agent_chat(message: str, history: List[dict]):
    msg_lower = message.lower()
    response_text = ""
    thought_monologue = f"Scanning input for cyberware keywords. Found phrase: '{message}'.\n"
    action_requested = None
    action_params = {}
    recommended_upsell = None

    if any(k in msg_lower for k in ["search", "find", "show", "catalog", "products"]):
        thought_monologue += "Invoking catalog search tool. Param: '*'.\n"
        matches = products
        for term in ["band", "hud", "glasses", "sleeve", "ssd", "quantum", "droid", "companion", "robot"]:
            if term in msg_lower:
                matches = [p for p in products if term in p["name"].lower() or term in p["description"].lower()]
                thought_monologue += f"Filtered catalog by keyword '{term}'. Found {len(matches)} matches.\n"
                break
                
        thought_monologue += "Search completed. Compiling formatted product list for buyer discovery.\n"
        
        # Format JSON rationale block required by system prompt
        json_explainability = {
            "action": "search_catalog",
            "reasoning_steps": [
                "Step 1: Parse buyer query specifications.",
                "Step 2: Scan active JSON catalog database.",
                "Step 3: Filter matches by keyword and return products details."
            ],
            "decision_rationale": "Retrieved available matching products for catalog search query."
        }
        
        response_text = "🔍 **I found the following tech catalog configurations in our database:**\n\n" + \
            "\n\n".join([f"* **{p['name']}** - ₹{p['price']:,}\n  _{p['description']}_ (In Stock: {p['stock']})" for p in matches]) + \
            "\n\nWould you like me to add any of these configurations to your checkout buffer?\n\n" + \
            "```json\n" + json.dumps(json_explainability, indent=2) + "\n```"
            
        log_audit_event_db(
            "Parsed user request for product search. Simulating catalog search tool.",
            "search_catalog",
            {"keyword": msg_lower},
            "PASSED",
            {"matchedCount": len(matches)},
            "Agent catalog search performed and catalog JSON structure retrieved for conversational generation."
        )

    elif any(k in msg_lower for k in ["buy", "checkout", "purchase", "add", "cart"]):
        target_product = None
        if any(term in msg_lower for term in ["neuralink", "band", "bci"]):
            target_product = next((p for p in products if p["id"] == "neuralink_band"), None)
        elif any(term in msg_lower for term in ["hud", "optic", "glasses"]):
            target_product = next((p for p in products if p["id"] == "optic_hud"), None)
        elif any(term in msg_lower for term in ["sleeve", "haptic", "arm"]):
            target_product = next((p for p in products if p["id"] == "haptic_sleeve"), None)
        elif any(term in msg_lower for term in ["quantum", "ssd", "crystal"]):
            target_product = next((p for p in products if p["id"] == "quantum_ssd"), None)
        elif any(term in msg_lower for term in ["droid", "companion", "robot"]):
            target_product = next((p for p in products if p["id"] == "companion_droid"), None)

        if target_product:
            thought_monologue += f"Target product identified: '{target_product['name']}'. Invoking trigger_payment tool.\n"
            action_requested = "trigger_payment"
            action_params = {"productId": target_product["id"], "quantity": 1}
            
            upsell_id = target_product["upsell_targets"][0]
            upsell_product = next((p for p in products if p["id"] == "optic_hud" or p["id"] == upsell_id), None)
            
            # Format JSON explainability block required by system prompt
            json_explainability = {
                "action": "initiate_bounded_checkout",
                "reasoning_steps": [
                    f"Step 1: Check client purchase criteria for '{target_product['name']}'.",
                    "Step 2: Verify stock level and validate single transaction budget boundary.",
                    f"Step 3: Analyze complimentary upsell targets. Selected target: '{upsell_product['name'] if upsell_product else 'None'}'.",
                    "Step 4: Output purchase trigger and suggest pairing option to customer."
                ],
                "decision_rationale": "Initiated checkout for product selection and recommended synergistic upsell target."
            }
            
            if upsell_product:
                recommended_upsell = upsell_product
                thought_monologue += f"Upsell opportunity discovered: '{upsell_product['name']}'. Suggesting to merchant to increase order value.\n"
                response_text = f"Initiating transaction sequences for **{target_product['name']}** (₹{target_product['price']:,}).\n\n📈 **Agent Upsell Suggestion:** I highly recommend pairing this with the **{upsell_product['name']}** (₹{upsell_product['price']:,}) - _{upsell_product['description']}_. It is designed to work in synergy. Would you like to merge these items before checkout?\n\n" + \
                    "```json\n" + json.dumps(json_explainability, indent=2) + "\n```"
            else:
                response_text = f"Initiating transaction sequences for **{target_product['name']}** (₹{target_product['price']:,}). Click 'Proceed Checkout' to authorize.\n\n" + \
                    "```json\n" + json.dumps(json_explainability, indent=2) + "\n```"

            log_audit_event_db(
                f"User requested purchase of {target_product['name']}. Initiated payment tool simulation.",
                "initiate_checkout_tool",
                action_params,
                "PASSED",
                {"productSelected": target_product["id"], "price": target_product["price"]},
                f"AI Agent recommended upsell: '{upsell_product['name'] if upsell_product else 'None'}'. Cart state updated."
            )
        else:
            thought_monologue += "Purchase intent detected, but product not specified. Requesting clarification.\n"
            response_text = "I detected you want to initiate a purchase sequence! Which product configurations from our catalog (Neuralink Band, Optic HUD Glasses, Haptic Arm Sleeve, Quantum Core SSD, or Companion Droid) should I initialize?"
    else:
        thought_monologue += "No transaction commands detected. Generating conversational response emphasizing tech features and upsells.\n"
        response_text = """Welcome to **CYBERWARE** secure neural marketplace node. I am your autonomous AI Broker. 

I can help you search our agent-optimized JSON catalog, recommend contextually relevant hardware, configure checkout carts, and securely execute test transactions. 

Here are our top nodes in stock:
1. 🧠 **Neuralink Band (BCI)** - ₹14,999
2. 🕶️ **Optic HUD Glasses** - ₹8,499
3. 🦾 **Haptic Arm Sleeve** - ₹19,999
4. 💾 **Quantum Core SSD (4TB)** - ₹12,500
5. 🤖 **Mini AI Companion Droid** - ₹29,999

What system upgrades should we interface with today?"""

    return {
        "role": "model",
        "parts": [{"text": response_text}],
        "thought": thought_monologue,
        "action": action_requested,
        "params": action_params,
        "upsell": recommended_upsell
    }

# --- STATIC FILES ROUTING ---
# Serves the index.html and assets directly
app.mount("/images", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "public/images")), name="images")

@app.get("/styles.css")
def get_styles():
    return FileResponse(os.path.join(os.path.dirname(__file__), "public/styles.css"))

@app.get("/app.js")
def get_app():
    return FileResponse(os.path.join(os.path.dirname(__file__), "public/app.js"))

@app.get("/")
def get_index():
    return FileResponse(os.path.join(os.path.dirname(__file__), "public/index.html"))

# Startup execution
if __name__ == "__main__":
    import uvicorn
    print("=============================================================")
    print("CYBERWARE FASTAPI SERVER INITIATING ON http://localhost:3000")
    print(f"MongoDB connection URI: {MONGO_URI}")
    print("=============================================================")
    uvicorn.run("main:app", host="127.0.0.1", port=3000, reload=False)
