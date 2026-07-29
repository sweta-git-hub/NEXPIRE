import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app
from app.services.notification import TwilioNotificationService, get_notification_service
from app.tasks.dispatch import dispatch_flash_sale_notifications


def make_mock_service() -> TwilioNotificationService:
    """Return a TwilioNotificationService pinned to mock_mode=True."""
    svc = TwilioNotificationService.__new__(TwilioNotificationService)
    svc.account_sid = "ACtest"
    svc.auth_token = "token"
    svc.sms_from = "+10000000000"
    svc.whatsapp_from = "whatsapp:+10000000000"
    svc.mock_mode = True
    svc.client = None
    return svc


@pytest.fixture(autouse=True)
def override_notification_service():
    mock_svc = make_mock_service()
    app.dependency_overrides[get_notification_service] = lambda: mock_svc
    yield mock_svc
    app.dependency_overrides.clear()


client = TestClient(app)


# ---------------------------------------------------------------------------
# Unit tests — TwilioNotificationService in mock mode
# ---------------------------------------------------------------------------

def test_notification_service_mock_mode():
    """Test that a mock-mode service returns simulated results."""
    service = make_mock_service()
    assert service.mock_mode is True

    sms_res = service.send_sms("+15551234567", "Test SMS")
    assert sms_res["status"] == "simulated"
    assert sms_res["mock_mode"] is True
    assert sms_res["message_sid"].startswith("SIM_SMS_")

    wa_res = service.send_whatsapp("+15551234567", "Test WhatsApp")
    assert wa_res["status"] == "simulated"
    assert wa_res["mock_mode"] is True
    assert wa_res["message_sid"].startswith("SIM_WA_")


def test_flash_sale_message_format():
    """Unit-test the message formatting helper directly."""
    service = make_mock_service()
    msg = service.format_flash_sale_message(
        item_name="Organic Milk 1L",
        store_name="Metro Fresh",
        original_price=3.99,
        discounted_price=1.99,
        discount_percentage=50.0,
        claim_url="http://localhost:3000/claim/1",
    )
    assert "Metro Fresh" in msg
    assert "Organic Milk 1L" in msg
    assert "50%" in msg
    assert "1.99" in msg
    assert "http://localhost:3000/claim/1" in msg


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------

def test_send_sms_endpoint():
    """Test POST /api/v1/notifications/send-sms."""
    payload = {
        "to_phone": "+15551234567",
        "message": "NEXPIRE Flash Alert: Organic Milk 50% OFF!"
    }
    response = client.post("/api/v1/notifications/send-sms", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "simulated"
    assert data["channel"] == "sms"
    assert data["recipient"] == "+15551234567"
    assert data["mock_mode"] is True


def test_send_whatsapp_endpoint():
    """Test POST /api/v1/notifications/send-whatsapp."""
    payload = {
        "to_phone": "+15559876543",
        "message": "NEXPIRE WhatsApp Flash Alert: Fresh Apples $1.99!"
    }
    response = client.post("/api/v1/notifications/send-whatsapp", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "simulated"
    assert data["channel"] == "whatsapp"
    assert "whatsapp:+15559876543" in data["recipient"]


def test_send_flash_sale_alert_endpoint():
    """Test POST /api/v1/notifications/send-flash-sale."""
    payload = {
        "to_phone": "+15551112222",
        "batch_id": 42,
        "item_name": "Organic Strawberries 1lb",
        "store_name": "Metro Fresh Market",
        "original_price": 5.99,
        "discounted_price": 2.99,
        "discount_percentage": 50.0,
        "claim_url": "http://localhost:3000/claim/42",
        "channel": "sms"
    }
    response = client.post("/api/v1/notifications/send-flash-sale", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "simulated"
    assert data["recipient"] == "+15551112222"


def test_broadcast_flash_sale_endpoint():
    """Test POST /api/v1/notifications/broadcast-flash-sale."""
    payload = {
        "batch_id": 101,
        "item_name": "Artisan Sourdough Bread",
        "store_name": "Downtown Bakery",
        "original_price": 6.50,
        "discounted_price": 2.00,
        "discount_percentage": 69.2,
        "claim_url": "http://localhost:3000/claim/101",
        "recipient_phones": ["+15550000001", "+15550000002", "+15550000003"],
        "channel": "sms"
    }
    response = client.post("/api/v1/notifications/broadcast-flash-sale", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["batch_id"] == 101
    assert data["total_recipients"] == 3
    assert data["dispatched_count"] == 3
    assert len(data["results"]) == 3


# ---------------------------------------------------------------------------
# Inbound webhook tests (no mocking needed — pure TwiML logic)
# ---------------------------------------------------------------------------

def test_twilio_inbound_webhook_yes_reply():
    """Test POST /api/v1/notifications/twilio-webhook handling 'YES' claim keyword."""
    form_data = {
        "From": "+15551234567",
        "Body": "YES",
        "MessageSid": "SM1234567890"
    }
    response = client.post("/api/v1/notifications/twilio-webhook", data=form_data)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/xml")
    assert "<Response>" in response.text
    assert "Your item reservation is being placed" in response.text


def test_twilio_inbound_webhook_help_reply():
    """Test POST /api/v1/notifications/twilio-webhook handling 'HELP' keyword."""
    form_data = {
        "From": "+15551234567",
        "Body": "HELP",
        "MessageSid": "SM0000000"
    }
    response = client.post("/api/v1/notifications/twilio-webhook", data=form_data)
    assert response.status_code == 200
    assert "NEXPIRE Help:" in response.text


def test_twilio_inbound_webhook_unknown_body():
    """Test POST /api/v1/notifications/twilio-webhook with unknown keyword."""
    form_data = {
        "From": "+15551234567",
        "Body": "HELLO",
        "MessageSid": "SM9999999"
    }
    response = client.post("/api/v1/notifications/twilio-webhook", data=form_data)
    assert response.status_code == 200
    assert "<Response>" in response.text


# ---------------------------------------------------------------------------
# Celery dispatch task test
# ---------------------------------------------------------------------------

def test_dispatch_celery_task():
    """Test Celery background dispatch task with mocked notification service."""
    mock_svc = make_mock_service()
    with patch("app.tasks.dispatch.get_notification_service", return_value=mock_svc):
        batch_details = {
            "batch_id": 99,
            "item_name": "Greek Yogurt",
            "store_name": "Central Market",
            "original_price": 4.00,
            "discounted_price": 1.50,
            "discount_percentage": 62.5,
            "claim_url": "http://localhost:3000/claim/99"
        }
        recipients = ["+15553334444", "+15555556666"]
        res = dispatch_flash_sale_notifications(batch_details, recipients, channel="sms")

    assert res["batch_id"] == 99
    assert res["total"] == 2
    assert res["dispatched"] == 2
    assert len(res["results"]) == 2
    assert all(r["mock_mode"] for r in res["results"])
