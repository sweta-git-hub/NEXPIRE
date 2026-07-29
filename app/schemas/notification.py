from typing import Optional
from pydantic import BaseModel, Field


class SMSNotificationRequest(BaseModel):
    to_phone: str = Field(..., description="Target phone number in E.164 format (e.g. +1234567890)")
    message: str = Field(..., min_length=1, description="Message text body")


class WhatsAppNotificationRequest(BaseModel):
    to_phone: str = Field(..., description="Target phone number in E.164 format")
    message: str = Field(..., min_length=1, description="WhatsApp text body")


class FlashSaleAlertRequest(BaseModel):
    to_phone: str = Field(..., description="Recipient phone number")
    batch_id: int = Field(..., description="Database Batch ID")
    item_name: str = Field(..., description="Name of the food item")
    store_name: str = Field(..., description="Name of the store")
    original_price: float = Field(..., ge=0, description="Original retail price")
    discounted_price: float = Field(..., ge=0, description="Discounted price")
    discount_percentage: float = Field(..., ge=0, le=100, description="Percentage markdown")
    claim_url: Optional[str] = Field(None, description="One-click claim URL")
    channel: str = Field("sms", description="Delivery channel ('sms' or 'whatsapp')")


class BroadcastAlertRequest(BaseModel):
    batch_id: int = Field(..., description="Database Batch ID")
    item_name: str = Field(..., description="Name of the food item")
    store_name: str = Field(..., description="Name of the store")
    original_price: float = Field(..., ge=0)
    discounted_price: float = Field(..., ge=0)
    discount_percentage: float = Field(..., ge=0, le=100)
    claim_url: Optional[str] = None
    recipient_phones: list[str] = Field(..., min_length=1, description="List of target recipient phone numbers")
    channel: str = Field("sms", description="Delivery channel ('sms' or 'whatsapp')")


class NotificationResponse(BaseModel):
    status: str = Field(..., description="Status ('sent' or 'simulated')")
    message_sid: str = Field(..., description="Twilio message SID or simulated identifier")
    channel: str = Field(..., description="Delivery channel ('sms' or 'whatsapp')")
    recipient: str = Field(..., description="Target recipient number")
    mock_mode: bool = Field(..., description="True if operating without live Twilio credentials")


class BroadcastResponse(BaseModel):
    batch_id: int
    channel: str
    total_recipients: int
    dispatched_count: int
    results: list[NotificationResponse]
