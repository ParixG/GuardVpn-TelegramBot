from typing import Optional

from db.client import get_client

PAGE_SIZE = 5


async def insert(user_telegram_id: int, guard_username: str, plan_id: int) -> dict:
    client = get_client()
    result = (
        client.table("subscriptions")
        .insert(
            {
                "user_telegram_id": user_telegram_id,
                "guard_username": guard_username,
                "plan_id": plan_id,
            }
        )
        .execute()
    )
    return result.data[0]


async def get_user_subscriptions(user_telegram_id: int) -> list[dict]:
    client = get_client()
    result = (
        client.table("subscriptions")
        .select("*, plans(*)")
        .eq("user_telegram_id", user_telegram_id)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data


async def get_by_guard_username(guard_username: str) -> Optional[dict]:
    client = get_client()
    result = (
        client.table("subscriptions")
        .select("*, plans(*)")
        .eq("guard_username", guard_username)
        .execute()
    )
    return result.data[0] if result.data else None


async def get_all_paged(page: int) -> tuple[list[dict], int]:
    """Returns (rows, total_count) for the given 0-indexed page, joined with users."""
    client = get_client()
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE - 1
    result = (
        client.table("subscriptions")
        .select("*, users(*), plans(*)", count="exact")
        .order("created_at", desc=True)
        .range(start, end)
        .execute()
    )
    return result.data, result.count or 0


async def delete(guard_username: str) -> None:
    client = get_client()
    client.table("subscriptions").delete().eq("guard_username", guard_username).execute()
