import os
import json
import httpx
from typing import List, Dict, Any, Optional

# In-memory products list matching main.py
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

class GroqAgent:
    def __init__(self, api_key: str, log_callback=None):
        self.api_key = api_key
        self.model = "llama-3.3-70b-specdec"  # Standard high-performance Groq model supporting function calling
        self.log_callback = log_callback
        
    def _log(self, thought: str, action: str, params: dict, safety_status: str, api_response: dict, explainability: str):
        if self.log_callback:
            return self.log_callback(thought, action, params, safety_status, api_response, explainability)
        return {}

    # --- AGENT TOOLS ---
    def search_catalog(self, query: str) -> Dict[str, Any]:
        """Search the product inventory for matches against keyword or details."""
        query_lower = query.lower()
        matches = []
        for p in products:
            if (query_lower in p["id"].lower() or 
                query_lower in p["name"].lower() or 
                query_lower in p["description"].lower() or
                any(query_lower in spec.lower() for spec in p["specs"])):
                matches.append(p)
        return {"products": matches}

    def recommend_upsell(self, cart_items: List[str]) -> Dict[str, Any]:
        """Analyze cart items and return proactive upsell suggestions from complementary target groups."""
        suggestions = []
        for item_id in cart_items:
            p = next((prod for prod in products if prod["id"] == item_id), None)
            if p:
                for target_id in p["upsell_targets"]:
                    if target_id not in cart_items and target_id not in [s["id"] for s in suggestions]:
                        target_p = next((prod for prod in products if prod["id"] == target_id), None)
                        if target_p:
                            suggestions.append(target_p)
        return {"recommendations": suggestions}

    def initiate_bounded_checkout(self, item_id: str, quantity: int, user_max_budget: int) -> Dict[str, Any]:
        """Initiate order creation checking for stock limits and budget constraints."""
        product = next((p for p in products if p["id"] == item_id), None)
        
        # 1. Check if product exists
        if not product:
            raise ValueError(f"Product ID '{item_id}' not found in current inventory configuration.")
            
        # 2. Check stock limit
        if product["stock"] < quantity:
            raise ValueError(f"Insufficient stock: Requested {quantity} units of {product['name']}, but only {product['stock']} are in stock.")
            
        # 3. Check Bounded budget limits
        total_cost = product["price"] * quantity
        if total_cost > user_max_budget:
            raise ValueError(f"Budget boundary exceeded: Order amount (₹{total_cost:,}) exceeds your max budget of (₹{user_max_budget:,}).")
            
        return {
            "status": "checkout_approved",
            "productId": item_id,
            "productName": product["name"],
            "price": product["price"],
            "quantity": quantity,
            "totalAmount": total_cost,
            "upsellTargets": product["upsell_targets"]
        }

    # --- EXECUTE TOOL METHOD ---
    def execute_tool(self, name: str, args: dict) -> dict:
        if name == "search_catalog":
            return self.search_catalog(args.get("query", ""))
        elif name == "recommend_upsell":
            return self.recommend_upsell(args.get("cart_items", []))
        elif name == "initiate_bounded_checkout":
            return self.initiate_bounded_checkout(
                args.get("item_id"),
                int(args.get("quantity", 1)),
                int(args.get("user_max_budget", 999999))
            )
        else:
            raise ValueError(f"Unknown tool function: {name}")

    # --- SYSTEM COMPULSORY PROMPT ---
    def get_system_prompt(self) -> str:
        return """You are the CYBERWARE Autonomous AI Broker. You assist clients in discovering products, recommending upgrades, and initiating transactions.

CORE INSTRUCTIONS:
1. Proactively recommend complementary products (using the catalog's upsell_targets specs) to increase merchant revenue. Explain why they pair well together.
2. For EVERY monetary or transaction action (such as recommending an upsell or initiating checkout), you MUST generate a step-by-step JSON payload explaining *why* you recommended or initiated the purchase. You must print this JSON reason block cleanly inside your text message.
Format of JSON rationale block:
```json
{
  "action": "recommend_upsell" or "initiate_bounded_checkout",
  "reasoning_steps": [
    "Step 1: Check client purchase criteria...",
    "Step 2: Inspect item specifications...",
    "Step 3: Analyze complimentary upsell targets..."
  ],
  "decision_rationale": "Short explanation of the engineering decision."
}
```
3. Use tool calling to execute searches, get upselling recommendations, and trigger bounded checkouts.
4. Always talk in a tech-driven, cyberpunk theme. Format prices in Indian Rupees (e.g. ₹14,999)."""

    # --- MAIN COMPLETIONS LOOP ---
    async def chat(self, message: str, chat_history: List[Dict[str, str]]) -> Dict[str, Any]:
        # Form history list
        messages = [{"role": "system", "content": self.get_system_prompt()}]
        for item in chat_history:
            messages.append({"role": item["role"], "content": item["text"]})
        messages.append({"role": "user", "content": message})
        
        # Tools schema definitions for Groq API
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_catalog",
                    "description": "Searches product catalog using query terms.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search keyword or specifications."}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "recommend_upsell",
                    "description": "Suggests complementary items based on items already in the checkout cart list.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "cart_items": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of product IDs currently selected."
                            }
                        },
                        "required": ["cart_items"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "initiate_bounded_checkout",
                    "description": "Initiates payment checkout check. Evaluates against stock levels and the user budget boundaries.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "item_id": {"type": "string", "description": "ID of product to buy."},
                            "quantity": {"type": "integer", "description": "Number of units."},
                            "user_max_budget": {"type": "integer", "description": "Maximum budget in INR (e.g., 20000)."}
                        },
                        "required": ["item_id", "quantity", "user_max_budget"]
                    }
                }
            }
        ]

        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": messages,
                "tools": tools,
                "tool_choice": "auto"
            }
            
            thought_monologue = ""
            loop_count = 0
            
            try:
                while loop_count < 3:
                    loop_count += 1
                    response = await client.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=15.0
                    )
                    
                    if response.status_code != 200:
                        raise Exception(f"Groq API Error ({response.status_code}): {response.text}")
                        
                    res_json = response.json()
                    choice = res_json["choices"][0]
                    res_msg = choice["message"]
                    
                    # If model requests tool calls
                    if res_msg.get("tool_calls"):
                        tool_call = res_msg["tool_calls"][0]
                        tool_name = tool_call["function"]["name"]
                        tool_args = json.loads(tool_call["function"]["arguments"])
                        
                        thought_monologue += f"AI Thought: Invoked tool '{tool_name}' with arguments: {json.dumps(tool_args)}.\n"
                        
                        # EXECUTE TOOL WITH EXPLICIT RESILIENCE HANDLING
                        tool_response = {}
                        try:
                            # Verify if parameters look valid to avoid parameter issues
                            if tool_name == "initiate_bounded_checkout":
                                # Validate parameters type
                                qty = int(tool_args.get("quantity", 1))
                                budget = int(tool_args.get("user_max_budget", 999999))
                                
                            tool_response = self.execute_tool(tool_name, tool_args)
                            
                            self._log(
                                f"Agent executed tool successfully: {tool_name}",
                                tool_name,
                                tool_args,
                                "PASSED",
                                tool_response,
                                f"Tool call {tool_name} returned success status."
                            )
                            
                        except ValueError as val_err:
                            # RESILIENCE: Catch budget limits or stock out validation exception
                            error_desc = str(val_err)
                            tool_response = {"status": "failed", "error": error_desc, "code": "BOUNDARY_VIOLATED"}
                            
                            # Log resilience trigger in SQLite
                            self._log(
                                f"Boundary check exception caught in tool: {error_desc}",
                                tool_name,
                                tool_args,
                                "FAILED_GUARDRAIL",
                                tool_response,
                                f"Resilience Recovery Protocol: Intercepted tool error. Alerting client."
                            )
                            
                            # Graceful recovery: Feed the failure back to the LLM agent so it explains it
                            # and suggests an alternative
                            thought_monologue += f"Resilience Warning: Caught exception: {error_desc}. Bypassing failure...\n"
                            
                        except Exception as e:
                            # General exception
                            error_desc = f"System Error: {str(e)}"
                            tool_response = {"status": "failed", "error": error_desc, "code": "SYSTEM_EXCEPTION"}
                            
                            self._log(
                                f"Exception caught: {error_desc}",
                                tool_name,
                                tool_args,
                                "FAILED_SYSTEM",
                                tool_response,
                                f"System error caught: {error_desc}"
                            )
                            thought_monologue += f"Warning: General system error: {error_desc}\n"
                            
                        # Feed the tool execution results back to the completions session
                        payload["messages"].append(res_msg)
                        payload["messages"].append({
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "name": tool_name,
                            "content": json.dumps(tool_response)
                        })
                        
                        # If initiate_bounded_checkout was approved, return it to the frontend
                        if tool_name == "initiate_bounded_checkout" and tool_response.get("status") == "checkout_approved":
                            # Retrieve final text turn from agent explaining checkout
                            payload["messages"].append({
                                "role": "user",
                                "content": "The bounded checkout was approved. Present the checkout panel and confirm the reasoning JSON payload to the user."
                            })
                            final_resp = await client.post(
                                "https://api.groq.com/openai/v1/chat/completions",
                                headers=headers,
                                json=payload,
                                timeout=10.0
                            )
                            final_text = "Bounded checkout initialized. Complete payment below."
                            if final_resp.status_code == 200:
                                final_text = final_resp.json()["choices"][0]["message"]["content"]
                                
                            # Retrieve upsell recommendation to bundle
                            target_p = next((p for p in products if p["id"] == tool_args.get("item_id")), None)
                            upsell_id = target_p["upsell_targets"][0] if target_p else None
                            upsell_p = next((p for p in products if p["id"] == upsell_id), None)
                            
                            return {
                                "role": "model",
                                "parts": [{"text": final_text}],
                                "thought": thought_monologue + "Bounded checkout tool approved. Packaging payment metadata.",
                                "action": "trigger_payment",
                                "params": {"productId": tool_args.get("item_id"), "quantity": int(tool_args.get("quantity", 1))},
                                "upsell": upsell_p
                            }
                            
                    else:
                        # Return final text completions
                        return {
                            "role": "model",
                            "parts": [{"text": res_msg["content"]}],
                            "thought": thought_monologue or "Agent dialogue generated successfully."
                        }
                        
            except Exception as e:
                # API Timeouts or Rate limit exceptions: graceful recovery return
                timeout_msg = f"API Interface Timeout or Rate limit: {str(e)}."
                fallback_ans = "⚠️ **Cognitive Bypass Protocol Active:** Connection to the Groq LLM cluster timed out. Local backup recovery activated: I can assist you with Neuralink BCI Band, Optic HUD Glasses, Haptic Arm Sleeve, Quantum Core SSD, or Companion Droid. Let me know which device specs you want to interface."
                
                self._log(
                    f"LLM API Exception: {timeout_msg}",
                    "groq_api_call",
                    {"message": message},
                    "FAILED_API_TIMEOUT",
                    {"error": timeout_msg},
                    f"Cognitive safety layer outputted alternative recommendations to prevent conversation disruption."
                )
                return {
                    "role": "model",
                    "parts": [{"text": fallback_ans}],
                    "thought": f"API request error: {timeout_msg}. Recovery message triggered."
                }
                
        return {
            "role": "model",
            "parts": [{"text": "Transaction node ready. Review details in checkout."}],
            "thought": thought_monologue
        }
