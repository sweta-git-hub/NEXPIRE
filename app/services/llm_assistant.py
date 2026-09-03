"""
llm_assistant.py — NEXPIRE AI Assistant powered by Groq / LLM
============================================================
Provides an intelligent conversational engine for NEXPIRE that:
  1. Is strictly grounded in live database inventory (batches & stores).
  2. Enforces strict domain guardrails: Refuses to answer general/unrelated questions
     outside the scope of NEXPIRE surplus food rescue, pricing, claiming, and safety.
  3. Outputs structured JSON matching the frontend ChatResponse schema.
  4. Gracefully falls back to the deterministic rule-based engine if unconfigured or offline.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import date
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.batch import Batch
from app.models.store import Store

logger = logging.getLogger("nexpire.assistant.llm")


SYSTEM_PROMPT_TEMPLATE = """You are NEXPIRE's AI Assistant — a specialized assistant for the NEXPIRE surplus food rescue platform.

STRICT DOMAIN GUARDRAILS & SCOPE ENFORCEMENT:
1. You MUST ONLY answer questions strictly related to:
   - NEXPIRE surplus food management, flash sales, dynamic discounts, and perishable stock.
   - Live products and batches currently available in the database (listed below).
   - NEXPIRE store locations and addresses.
   - The claiming process (3-minute hold reservation, claim links, pickup, in-store payments).
   - NGO / shelter subsidized bulk allocations and standing orders.
   - Food freshness, near-expiry safety guidelines (best-before vs. use-by dates).
2. OUT-OF-SCOPE REFUSAL:
   - If the user asks ANY question outside the scope of NEXPIRE (e.g., coding, general math, science, politics, general history, writing essays, recipes requiring unlisted ingredients, non-platform chit-chat, or general knowledge), you MUST POLITELY REFUSE.
   - Refusal response example:
     "I am NEXPIRE's specialized Food Rescue Assistant. I can only answer questions related to NEXPIRE surplus food deals, active inventory, store locations, claiming procedures, and food safety. Let me know if you would like to explore today's discounted grocery batches!"
   - For out-of-scope queries, set `"intent": "out_of_scope"`, `"product_ids": []`, and suggested food discovery quick replies.
3. GROUNDING IN DATABASE INVENTORY:
   - Only recommend products that exist in the ACTIVE INVENTORY list below.
   - In `"product_ids"`, include the exact integer IDs of products you recommend or discuss.
   - Do NOT invent or hallucinate products, prices, or store branches that are not in the context.

CURRENT ACTIVE INVENTORY IN DATABASE:
{inventory_context}

NEXPIRE STORE LOCATIONS:
{stores_context}

RESPONSE FORMAT:
You must ALWAYS respond with a VALID JSON object matching this schema exactly:
{{
  "reply": "Your markdown-formatted answer. Friendly, concise, helpful, and safety-conscious.",
  "intent": "greeting | search_category | browse_discounts | claim_guide | expiry_faq | payment_faq | out_of_scope",
  "product_ids": [integer IDs of products to display as cards, or empty array],
  "quick_replies": ["3-4 short relevant suggestion chips (e.g., 'Dairy deals 🥛', 'How to claim 🤝')"]
}}
"""


class LLMAssistantService:
    def __init__(self):
        self.api_key = os.environ.get("GROQ_API_KEY", "").strip()
        self.model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
        self._client = None

    def is_configured(self) -> bool:
        """Returns True if a valid Groq API key is present."""
        self.api_key = os.environ.get("GROQ_API_KEY", "").strip()
        return bool(self.api_key and self.api_key != "your_groq_api_key_here")

    def _get_client(self):
        if not self._client:
            from groq import Groq
            self.api_key = os.environ.get("GROQ_API_KEY", "").strip()
            self.model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
            self._client = Groq(api_key=self.api_key)
        return self._client

    def _build_database_context(self, db: Session, store_id: Optional[int] = None) -> tuple[str, str]:
        """Fetches live active batches and stores to ground the LLM in real data."""
        # Query active discounted batches
        query = db.query(Batch).filter(
            Batch.status.in_(["ACTIVE", "DISCOUNTED"]),
            Batch.quantity > 0,
            Batch.expiration_date >= date.today(),
        )
        if store_id:
            query = query.filter(Batch.store_id == store_id)

        batches = query.order_by(Batch.discount_percentage.desc()).limit(20).all()
        
        if batches:
            batch_lines = []
            for b in batches:
                batch_lines.append(
                    f"- ID {b.id}: {b.product_name} ({b.category}) | Current Price: ${b.current_price:.2f} "
                    f"(Original: ${b.original_selling_price:.2f}, Discount: {b.discount_percentage:.0f}%) | "
                    f"Qty: {b.quantity} | Expiry: {b.expiration_date} | Store ID: {b.store_id}"
                )
            inventory_str = "\n".join(batch_lines)
        else:
            inventory_str = "No active surplus inventory currently listed in the database."

        # Query stores
        stores = db.query(Store).limit(10).all()
        if stores:
            store_lines = [f"- Store {s.id}: {s.name} at {s.address or 'Local Store'}" for s in stores]
            stores_str = "\n".join(store_lines)
        else:
            stores_str = "- Default Store 1: NEXPIRE Central Hub"

        return inventory_str, stores_str

    def generate_chat_response(
        self,
        message: str,
        history: Optional[List[Any]] = None,
        store_id: Optional[int] = None,
        db: Optional[Session] = None,
    ) -> Optional[Dict[str, Any]]:
        """Invokes Groq LLM with strict scope guardrails and database context."""
        if not self.is_configured():
            return None

        try:
            client = self._get_client()

            # Retrieve real DB records for grounding
            inventory_context, stores_context = "", ""
            if db:
                inventory_context, stores_context = self._build_database_context(db, store_id)

            system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
                inventory_context=inventory_context,
                stores_context=stores_context,
            )

            # Build message payload
            messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]

            # Append past turns (up to 6)
            if history:
                for h in history[-6:]:
                    if hasattr(h, "role") and hasattr(h, "content"):
                        messages.append({"role": h.role, "content": h.content})
                    elif isinstance(h, dict):
                        messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})

            messages.append({"role": "user", "content": message})

            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.2,  # Low temperature for strict factual grounding & guardrails
                max_tokens=800,
            )

            content = response.choices[0].message.content
            data = json.loads(content)
            return {
                "reply": data.get("reply", "I can assist you with NEXPIRE surplus food deals and claims."),
                "intent": data.get("intent", "browse_discounts"),
                "product_ids": data.get("product_ids", []),
                "quick_replies": data.get("quick_replies", ["Show all discounts 🛒", "How do I claim? 🤝"]),
            }
        except Exception as exc:
            logger.warning(f"Groq LLM assistant invocation failed: {exc}. Falling back to rule engine.")
            return None


# Global singleton instance
_llm_service: Optional[LLMAssistantService] = None


def get_llm_assistant_service() -> LLMAssistantService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMAssistantService()
    return _llm_service
