import pytest
from app.api.assistant import _detect_intent, _build_response, ChatMessage, ChatRequest
from app.models.batch import Batch
from datetime import date

def test_detect_intent():
    intent, cat = _detect_intent("hello there!")
    assert intent == "greeting"
    assert cat is None

    intent, cat = _detect_intent("show me some discounts")
    assert intent == "browse_discounts"
    assert cat is None

    intent, cat = _detect_intent("do you have dairy or milk products?")
    assert intent == "search_category"
    assert cat == "Dairy"

    intent, cat = _detect_intent("how do I claim an item?")
    assert intent == "claim_guide"
    assert cat is None

    intent, cat = _detect_intent("is near-expiry food safe to eat?")
    assert intent == "expiry_faq"
    assert cat is None

    intent, cat = _detect_intent("what payments do you accept?")
    assert intent == "payment_faq"
    assert cat is None

    intent, cat = _detect_intent("help me")
    assert intent == "help"
    assert cat is None


def test_build_response():
    # Empty products
    res = _build_response("greeting", None, [], "hi")
    assert "NEXPIRE" in res.reply
    assert len(res.products) == 0

    # Greeting with a batch
    mock_batch = Batch(
        id=999,
        store_id=1,
        sku="TEST-SKU",
        product_name="Test Milk",
        category="Dairy",
        quantity=5,
        cost_price=10.0,
        original_selling_price=20.0,
        current_price=15.0,
        expiration_date=date.today(),
        discount_percentage=25.0,
        status="DISCOUNTED"
    )

    res = _build_response("greeting", None, [mock_batch], "hi")
    assert "1 deals" in res.reply
    assert len(res.products) == 1
    assert res.products[0].product_name == "Test Milk"
    assert res.products[0].discount_percentage == 25.0


def test_llm_chat_in_scope_and_guardrails(client, db_session, monkeypatch):
    """Test LLM assistant behavior with mocked Groq for in-scope deals and out-of-scope refusals."""
    from unittest.mock import MagicMock, patch
    from app.services.llm_assistant import get_llm_assistant_service
    from app.models.store import Store

    # Create test store & batch
    store = Store(name="Test Mart", address="123 Main St", location_lat=12.9, location_lng=77.5)
    db_session.add(store)
    db_session.commit()
    db_session.refresh(store)

    batch = Batch(
        store_id=store.id,
        sku="LLM-MILK",
        product_name="Organic Whole Milk",
        category="Dairy",
        quantity=10,
        cost_price=2.0,
        original_selling_price=4.0,
        current_price=2.5,
        discount_percentage=37.5,
        expiration_date=date.today(),
        status="DISCOUNTED",
    )
    db_session.add(batch)
    db_session.commit()
    db_session.refresh(batch)

    # 1. Test In-Scope Query with Mocked LLM
    mock_llm = get_llm_assistant_service()
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test_key_12345")
    mock_llm.api_key = "gsk_test_key_12345"

    with patch.object(
        mock_llm,
        "generate_chat_response",
        return_value={
            "reply": "We have Organic Whole Milk at 38% off today!",
            "intent": "search_category",
            "product_ids": [batch.id],
            "quick_replies": ["Dairy deals 🥛", "How to claim 🤝"],
        },
    ):
        res = client.post("/api/v1/assistant/chat", json={"message": "Do you have any milk on sale?"})
        assert res.status_code == 200
        data = res.json()
        assert "Organic Whole Milk" in data["reply"]
        assert len(data["products"]) == 1
        assert data["products"][0]["id"] == batch.id
        assert data["intent"] == "search_category"

    # 2. Test Out-of-Scope Query (Guardrail Enforcement)
    with patch.object(
        mock_llm,
        "generate_chat_response",
        return_value={
            "reply": "I am NEXPIRE's specialized Food Rescue Assistant. I can only answer questions related to NEXPIRE surplus food deals, active inventory, store locations, claiming procedures, and food safety.",
            "intent": "out_of_scope",
            "product_ids": [],
            "quick_replies": ["Show all discounts 🛒", "Dairy deals 🥛"],
        },
    ):
        res = client.post("/api/v1/assistant/chat", json={"message": "Write a python script to solve a quadratic equation"})
        assert res.status_code == 200
        data = res.json()
        assert "Food Rescue Assistant" in data["reply"]
        assert len(data["products"]) == 0
        assert data["intent"] == "out_of_scope"

