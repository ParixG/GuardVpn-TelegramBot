def bytes_to_gb(value: int) -> float:
    return round(value / (1024**3), 2)


def format_price(price_toman: int) -> str:
    return f"{price_toman:,} تومان"


def format_plan_line(plan: dict) -> str:
    return (
        f"💎 {plan['name']}\n"
        f"💰 قیمت: {format_price(plan['price_toman'])}\n"
        f"📊 حجم: {plan['data_limit_gb']} گیگ | ⏳ مدت: {plan['duration_days']} روز"
    )


def format_subscription(sub) -> str:
    status = "فعال ✅" if getattr(sub, "enabled", False) and getattr(sub, "is_active", False) else "غیرفعال ❌"
    used = bytes_to_gb(getattr(sub, "current_usage", 0))
    limit = bytes_to_gb(getattr(sub, "limit_usage", 0))
    return (
        "📡 وضعیت اشتراک\n"
        "━━━━━━━━━━━━━━━\n"
        f"🔘 وضعیت: {status}\n"
        f"👤 نام کاربری: {sub.username}\n"
        f"📊 حجم مصرفی: {used} از {limit} گیگ\n"
        f"🔗 لینک اشتراک:\n{sub.link}"
    )


def format_wallet(balance: float) -> str:
    return (
        "👛 کیف پول شما\n"
        "━━━━━━━━━━━━━━━\n"
        f"💰 موجودی: {balance:,.0f} تومان"
    )
