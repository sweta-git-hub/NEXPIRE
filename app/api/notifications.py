import logging
from typing import Optional
from fastapi import APIRouter, Depends, Form, Response, HTTPException, status

from app.schemas.notification import (
    SMSNotificationRequest,
    WhatsAppNotificationRequest,
    FlashSaleAlertRequest,
    BroadcastAlertRequest,
    NotificationResponse,
    BroadcastResponse,
)
from app.services.notification import (
    TwilioNotificationService,
    get_notification_service,
)

logger = logging.getLogger("nexpire.api.notifications")

router = APIRouter(prefix="/api/v1/notifications", tags=["Notifications"])


@router.post("/send-sms", response_model=NotificationResponse)
def send_sms_notification(
    req: SMSNotificationRequest,
    service: TwilioNotificationService = Depends(get_notification_service),
):
    """Dispatch a direct SMS notification."""
    result = service.send_sms(req.to_phone, req.message)
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("error", "SMS dispatch failed"))
    return NotificationResponse(**result)


@router.post("/send-whatsapp", response_model=NotificationResponse)
def send_whatsapp_notification(
    req: WhatsAppNotificationRequest,
    service: TwilioNotificationService = Depends(get_notification_service),
):
    """Dispatch a direct WhatsApp notification."""
    result = service.send_whatsapp(req.to_phone, req.message)
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("error", "WhatsApp dispatch failed"))
    return NotificationResponse(**result)


@router.post("/send-flash-sale", response_model=NotificationResponse)
def send_flash_sale_alert(
    req: FlashSaleAlertRequest,
    service: TwilioNotificationService = Depends(get_notification_service),
):
    """Send a single flash sale markdown alert to a customer via SMS or WhatsApp."""
    result = service.send_flash_sale_alert(
        to_phone=req.to_phone,
        item_name=req.item_name,
        store_name=req.store_name,
        original_price=req.original_price,
        discounted_price=req.discounted_price,
        discount_percentage=req.discount_percentage,
        claim_url=req.claim_url,
        channel=req.channel,
    )
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("error", "Flash sale alert failed"))
    return NotificationResponse(**result)


@router.post("/broadcast-flash-sale", response_model=BroadcastResponse)
def broadcast_flash_sale(
    req: BroadcastAlertRequest,
    service: TwilioNotificationService = Depends(get_notification_service),
):
    """Broadcast a flash sale alert to multiple recipient phone numbers."""
    results = []
    dispatched = 0
    for phone in req.recipient_phones:
        res = service.send_flash_sale_alert(
            to_phone=phone,
            item_name=req.item_name,
            store_name=req.store_name,
            original_price=req.original_price,
            discounted_price=req.discounted_price,
            discount_percentage=req.discount_percentage,
            claim_url=req.claim_url,
            channel=req.channel,
        )
        if res.get("status") in ("sent", "simulated"):
            dispatched += 1
        results.append(NotificationResponse(**res))

    return BroadcastResponse(
        batch_id=req.batch_id,
        channel=req.channel,
        total_recipients=len(req.recipient_phones),
        dispatched_count=dispatched,
        results=results,
    )


@router.post("/twilio-webhook")
def twilio_inbound_webhook(
    From: Optional[str] = Form(None),
    Body: Optional[str] = Form(None),
    MessageSid: Optional[str] = Form(None),
):
    """
    Inbound Twilio SMS/WhatsApp Webhook handler.
    Receives inbound messages (e.g. replying "YES" or "CLAIM") and responds with TwiML XML.
    """
    body_text = (Body or "").strip().upper()
    sender_phone = From or "Unknown"

    logger.info(f"Inbound webhook received from {sender_phone} with Body: '{body_text}' (SID: {MessageSid})")

    if "YES" in body_text or "CLAIM" in body_text:
        reply_message = (
            "🎉 Thank you! Your item reservation is being placed. "
            "Please check your message link or tap here to finalize checkout: http://localhost:3000/claim/latest"
        )
    elif "HELP" in body_text:
        reply_message = "NEXPIRE Help: Reply 'YES' to claim the latest flash sale alert or visit http://localhost:3000"
    else:
        reply_message = "Thank you for contacting NEXPIRE! Reply 'YES' to claim active flash sale discounts."

    twiml_response = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<Response>\n'
        f'    <Message>{reply_message}</Message>\n'
        '</Response>'
    )

    return Response(content=twiml_response, media_type="application/xml")
