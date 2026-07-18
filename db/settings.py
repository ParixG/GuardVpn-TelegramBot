from typing import Optional

from db.client import get_client


async def get_test_settings() -> Optional[dict]:
    client = get_client()
    result = client.table("test_settings").select("*").eq("id", True).execute()
    return result.data[0] if result.data else None


async def update_test_settings(fields: dict) -> Optional[dict]:
    client = get_client()
    result = client.table("test_settings").update(fields).eq("id", True).execute()
    return result.data[0] if result.data else None
