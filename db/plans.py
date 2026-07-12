from typing import Optional

from db.client import get_client


async def get_plans() -> list[dict]:
    client = get_client()
    result = client.table("plans").select("*").order("price_toman").execute()
    return result.data


async def get_plan(plan_id: int) -> Optional[dict]:
    client = get_client()
    result = client.table("plans").select("*").eq("id", plan_id).execute()
    return result.data[0] if result.data else None


async def create_plan(
    name: str,
    data_limit_gb: float,
    duration_days: int,
    price_toman: int,
    guard_service_ids: list[int],
) -> dict:
    client = get_client()
    result = (
        client.table("plans")
        .insert(
            {
                "name": name,
                "data_limit_gb": data_limit_gb,
                "duration_days": duration_days,
                "price_toman": price_toman,
                "guard_service_ids": guard_service_ids,
            }
        )
        .execute()
    )
    return result.data[0]


async def update_plan(plan_id: int, fields: dict) -> Optional[dict]:
    client = get_client()
    result = client.table("plans").update(fields).eq("id", plan_id).execute()
    return result.data[0] if result.data else None


async def delete_plan(plan_id: int) -> None:
    client = get_client()
    client.table("plans").delete().eq("id", plan_id).execute()
