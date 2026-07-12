from typing import Optional

from db.client import get_client


async def insert_transaction(
    user_telegram_id: int, amount: float, type: str, note: Optional[str] = None
) -> dict:
    client = get_client()
    result = (
        client.table("transactions")
        .insert(
            {
                "user_telegram_id": user_telegram_id,
                "amount": amount,
                "type": type,
                "note": note,
            }
        )
        .execute()
    )
    return result.data[0]
