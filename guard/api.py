import time

from guardcoreapi import GuardCoreApi
from guardcoreapi.core import RequestCore
from guardcoreapi.types import SubscriptionResponse

import config


def make_guard_username(telegram_id: int, plan_id: int) -> str:
    return f"tg{telegram_id}p{plan_id}t{int(time.time()) % 100000}"


def _headers() -> dict:
    return RequestCore.generate_headers(config.GUARD_API_KEY)


async def create_subscription(
    username: str, data_limit_gb: float, duration_days: int, service_ids: list[int]
) -> SubscriptionResponse:
    # The panel requires limit_expire as a future unix timestamp, and returns
    # a 500 if optional fields are sent as null — send only required fields.
    payload = {
        "username": username,
        "limit_usage": int(data_limit_gb * 1024**3),
        "limit_expire": int(time.time()) + duration_days * 86400,
        "service_ids": service_ids,
    }
    result = await RequestCore.post(
        "/api/subscriptions",
        headers=_headers(),
        json=[payload],
        response_model=SubscriptionResponse,
        use_list=True,
        base_url=config.GUARD_URL,
    )
    return result[0]


async def get_services() -> list[dict]:
    # Raw dicts instead of ServiceResponse: the pip library's models lag behind
    # the live panel and reject rows with new/missing fields.
    return await RequestCore.get(
        "/api/services",
        headers=_headers(),
        base_url=config.GUARD_URL,
    )


async def get_subscription(username: str) -> SubscriptionResponse:
    return await GuardCoreApi.get_subscription(
        username=username,
        api_key=config.GUARD_API_KEY,
        base_url=config.GUARD_URL,
    )


async def enable_subscription(username: str) -> dict:
    return await RequestCore.post(
        "/api/subscriptions/enable",
        headers=_headers(),
        json={"usernames": [username]},
        base_url=config.GUARD_URL,
    )


async def disable_subscription(username: str) -> dict:
    return await RequestCore.post(
        "/api/subscriptions/disable",
        headers=_headers(),
        json={"usernames": [username]},
        base_url=config.GUARD_URL,
    )


async def delete_subscription(username: str) -> dict:
    return await RequestCore.fetch(
        "/api/subscriptions",
        method="DELETE",
        headers=_headers(),
        json={"usernames": [username]},
        base_url=config.GUARD_URL,
    )
