from typing import Optional

from db.client import get_client


async def create_request(
    user_telegram_id: int, amount: float, receipt_file_id: str
) -> dict:
    client = get_client()
    result = (
        client.table("topup_requests")
        .insert(
            {
                "user_telegram_id": user_telegram_id,
                "amount": amount,
                "receipt_file_id": receipt_file_id,
            }
        )
        .execute()
    )
    return result.data[0]


async def set_admin_messages(request_id: str, messages: list[dict]) -> None:
    client = get_client()
    client.table("topup_requests").update({"admin_messages": messages}).eq(
        "id", request_id
    ).execute()


async def get_request(request_id: str) -> Optional[dict]:
    client = get_client()
    result = (
        client.table("topup_requests").select("*").eq("id", request_id).execute()
    )
    return result.data[0] if result.data else None


async def decide(request_id: str, admin_id: int, approve: bool) -> Optional[dict]:
    """Atomically decide a pending request via the decide_topup RPC.

    Returns the request row if this call won the race, None if the
    request was already decided (repeat click or a second admin).
    """
    client = get_client()
    result = client.rpc(
        "decide_topup",
        {"p_request_id": request_id, "p_admin_id": admin_id, "p_approve": approve},
    ).execute()
    return result.data[0] if result.data else None
