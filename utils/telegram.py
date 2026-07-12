import re

_PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


def normalize_digits(text: str) -> str:
    """Convert Persian/Arabic digits to ASCII and strip separators."""
    return text.strip().translate(_PERSIAN_DIGITS).replace(",", "").replace("٬", "")


def btn_regex(label: str) -> str:
    """Exact-match regex for a reply-keyboard button label.

    Labels contain emojis and other regex metacharacters, so they must be
    escaped; using the same constant for the keyboard and the filter keeps
    them in sync by construction.
    """
    return f"^{re.escape(label)}$"
