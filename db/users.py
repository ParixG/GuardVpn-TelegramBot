from typing import Optional

from db.client import get_client


async def upsert_user(telegram_id: int, username: Optional[str], first_name: str) -> dict:
    client = get_client()
    existing = await get_user(telegram_id)
    if existing:
        return existing
    result = (
        client.table("users")
        .insert(
            {
                "telegram_id": telegram_id,
                "username": username,
                "first_name": first_name,
            }
        )
        .execute()
    )
    return result.data[0]


async def get_user(telegram_id: int) -> Optional[dict]:
    client = get_client()
    result = client.table("users").select("*").eq("telegram_id", telegram_id).execute()
    return result.data[0] if result.data else None


async def deduct_wallet(telegram_id: int, amount: float) -> bool:
    client = get_client()
    result = client.rpc(
        "deduct_wallet", {"p_tid": telegram_id, "p_amount": amount}
    ).execute()
    return bool(result.data)


async def add_wallet(telegram_id: int, amount: float) -> None:
    client = get_client()
    client.rpc("add_wallet", {"p_tid": telegram_id, "p_amount": amount}).execute()
