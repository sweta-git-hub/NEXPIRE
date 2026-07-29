import logging
from typing import List, Dict, Any
from app.celery_app import celery_app
from app.services.notification import get_notification_service

logger = logging.getLogger("nexpire.tasks.dispatch")


@celery_app.task(name="app.tasks.dispatch.dispatch_flash_sale_notifications")
def dispatch_flash_sale_notifications(
    batch_details: Dict[str, Any],
    recipient_phones: List[str],
    channel: str = "sms",
) -> Dict[str, Any]:
    """
    Celery background task for asynchronous bulk alert dispatch off the main HTTP thread.
    """
    logger.info(f"Starting background notification dispatch for batch {batch_details.get('batch_id')} to {len(recipient_phones)} recipients.")
    service = get_notification_service()

    dispatched = 0
    results = []

    for phone in recipient_phones:
        res = service.send_flash_sale_alert(
            to_phone=phone,
            item_name=batch_details.get("item_name", "Perishable Item"),
            store_name=batch_details.get("store_name", "NEXPIRE Store"),
            original_price=batch_details.get("original_price", 10.0),
            discounted_price=batch_details.get("discounted_price", 5.0),
            discount_percentage=batch_details.get("discount_percentage", 50.0),
            claim_url=batch_details.get("claim_url"),
            channel=channel,
        )
        if res.get("status") in ("sent", "simulated"):
            dispatched += 1
        results.append(res)

    logger.info(f"Notification dispatch completed: {dispatched}/{len(recipient_phones)} delivered.")

    return {
        "batch_id": batch_details.get("batch_id"),
        "total": len(recipient_phones),
        "dispatched": dispatched,
        "results": results,
    }
