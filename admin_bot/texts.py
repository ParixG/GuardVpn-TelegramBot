"""All admin-facing texts and button labels for the VpnPluser admin panel."""

# ---------- Reply-keyboard button labels ----------
BTN_ADD_USER = "➕ افزودن کاربر"
BTN_CHECK_USER = "🔍 جستجوی کاربر"
BTN_USER_MANAGER = "👥 مدیریت کاربران"
BTN_ADD_BALANCE = "💰 شارژ کیف پول"
BTN_PLAN_MANAGER = "📦 مدیریت پلن‌ها"
BTN_CANCEL = "❌ انصراف"

# ---------- Inline button labels ----------
BTN_APPROVE = "✅ تایید"
BTN_REJECT = "❌ رد"
BTN_SKIP = "⏭ رد کردن"
BTN_CONFIRM = "✅ تایید"
BTN_CANCEL_INLINE = "❌ انصراف"

# ---------- General ----------
WELCOME = (
    "🛡 پنل مدیریت VpnPluser\n\n"
    "به پنل مدیریت خوش آمدید. از منوی زیر گزینه مورد نظر را انتخاب کنید 👇"
)
OPERATION_CANCELED = "❌ عملیات لغو شد."
BACK_TO_MENU = "🏠 منوی اصلی"
INVALID_NUMBER = "⚠️ لطفا یک عدد معتبر وارد کنید."

# ---------- Add user ----------
ASK_TID = "🆔 آیدی عددی تلگرام کاربر را وارد کنید:"
ASK_GUARD_USERNAME = "👤 نام کاربری دلخواه Guard را وارد کنید یا دکمه «⏭ رد کردن» را بزنید:"
NO_PLANS = "⚠️ پلنی موجود نیست."
CHOOSE_PLAN = "📋 یک پلن انتخاب کنید:"
PLAN_NOT_FOUND = "⚠️ پلن یافت نشد."
CONFIRM_ADD_USER = (
    "🧾 خلاصه درخواست\n"
    "━━━━━━━━━━━━━━━\n"
    "🆔 آیدی: {telegram_id}\n"
    "👤 پیشوند نام کاربری: {username_prefix}\n"
    "{plan_line}\n"
    "━━━━━━━━━━━━━━━\n\n"
    "آیا افزودن کاربر را تایید می‌کنید؟"
)
GUARD_CREATE_FAILED = "⚠️ خطا در ایجاد اشتراک در پنل Guard."
ADD_USER_SUCCESS = "✅ کاربر با موفقیت اضافه شد.\n\n🔗 لینک اشتراک:\n{link}"
USER_NOTIFY_FAILED = "⚠️ توجه: ارسال پیام به کاربر ممکن نبود (شاید ربات کاربر را استارت نکرده)."

# ---------- Add balance ----------
AB_ASK_TID = "🆔 آیدی عددی تلگرام کاربر را وارد کنید:"
AB_USER_NOT_FOUND = "⚠️ کاربری با این آیدی یافت نشد. آیدی دیگری وارد کنید یا «❌ انصراف» را بزنید."
AB_ASK_AMOUNT = "💰 مبلغ شارژ را به تومان وارد کنید:"
AB_INVALID_AMOUNT = "⚠️ مبلغ نامعتبر است. یک عدد مثبت وارد کنید."
AB_CONFIRM = (
    "🧾 تایید شارژ کیف پول\n"
    "━━━━━━━━━━━━━━━\n"
    "👤 کاربر: {name} (@{username})\n"
    "🆔 آیدی: {telegram_id}\n"
    "💰 مبلغ: {amount}\n"
    "━━━━━━━━━━━━━━━\n\n"
    "آیا تایید می‌کنید؟"
)
AB_SUCCESS = "✅ کیف پول کاربر با موفقیت شارژ شد."

# ---------- Check user ----------
CU_ASK_QUERY = "🔍 نام کاربری Guard یا آیدی عددی تلگرام کاربر را وارد کنید:"
CU_NO_SUBSCRIPTIONS = "📭 اشتراکی برای این کاربر یافت نشد."
CU_GUARD_NOT_FOUND = "⚠️ اشتراک «{guard_username}» در پنل Guard یافت نشد."

# ---------- User manager ----------
UM_NO_USERS = "📭 کاربری یافت نشد."
UM_PAGE = "📄 صفحه {page}"
UM_ENABLED = "✅ اشتراک {guard_username} فعال شد."
UM_DISABLED = "⛔ اشتراک {guard_username} غیرفعال شد."
UM_DELETED = "🗑 اشتراک {guard_username} حذف شد."
UM_ENABLE_FAILED = "⚠️ خطا در فعال‌سازی {guard_username}"
UM_DISABLE_FAILED = "⚠️ خطا در غیرفعال‌سازی {guard_username}"
UM_DELETE_FAILED = "⚠️ خطا در حذف {guard_username}"
BTN_UM_ENABLE = "✅ فعال"
BTN_UM_DISABLE = "⛔ غیرفعال"
BTN_UM_DELETE = "🗑 حذف"
BTN_UM_PREV = "« قبلی"
BTN_UM_NEXT = "بعدی »"

# ---------- Plan manager ----------
BTN_PM_ADD = "➕ افزودن پلن"
BTN_PM_EDIT_NAME = "✏️ نام"
BTN_PM_EDIT_DATA = "📊 حجم"
BTN_PM_EDIT_DAYS = "⏳ مدت"
BTN_PM_EDIT_PRICE = "💰 قیمت"
BTN_PM_EDIT_SERVICES = "🔗 سرویس‌ها"
BTN_PM_DELETE = "🗑 حذف پلن"
BTN_PM_BACK = "« بازگشت"
BTN_PM_CLOSE = "❌ بستن"

PM_MENU = (
    "📦 مدیریت پلن‌ها\n\n"
    "یک پلن را برای مشاهده و ویرایش انتخاب کنید یا پلن جدید بسازید 👇"
)
PM_NO_PLANS = "📭 هنوز پلنی ثبت نشده است. با «➕ افزودن پلن» اولین پلن را بسازید."
PM_PLAN_DETAIL = (
    "📦 پلن #{id}\n"
    "━━━━━━━━━━━━━━━\n"
    "💎 نام: {name}\n"
    "📊 حجم: {data_limit_gb} گیگ\n"
    "⏳ مدت: {duration_days} روز\n"
    "💰 قیمت: {price}\n"
    "🔗 سرویس‌های Guard: {service_ids}\n"
    "━━━━━━━━━━━━━━━"
)
PM_ASK_NAME = "💎 نام پلن را وارد کنید:"
PM_ASK_DATA = "📊 حجم پلن را به گیگابایت وارد کنید (مثلا 50):"
PM_ASK_DAYS = "⏳ مدت پلن را به روز وارد کنید (مثلا 30):"
PM_ASK_PRICE = "💰 قیمت پلن را به تومان وارد کنید (مثلا 150000):"
PM_ASK_SERVICES = "🔗 شناسه سرویس‌های Guard را با کاما جدا کنید (مثلا: 1,2):"
BTN_PM_SVC_DONE = "✅ ثبت انتخاب"
PM_CHOOSE_SERVICES = (
    "🔗 سرویس‌های Guard این پلن را انتخاب کنید.\n"
    "با لمس هر سرویس، انتخاب یا لغو می‌شود. در پایان «✅ ثبت انتخاب» را بزنید:"
)
PM_SERVICES_FETCH_FAILED = (
    "⚠️ دریافت لیست سرویس‌ها از پنل Guard ممکن نبود.\n"
    "شناسه سرویس‌ها را دستی و جداشده با کاما وارد کنید (مثلا: 1,2):"
)
PM_SVC_NEED_ONE = "⚠️ حداقل یک سرویس انتخاب کنید."
PM_INVALID_NAME = "⚠️ نام نمی‌تواند خالی باشد."
PM_INVALID_GB = "⚠️ حجم نامعتبر است. یک عدد مثبت وارد کنید (مثلا 50 یا 1.5)."
PM_INVALID_SERVICES = (
    "⚠️ فرمت نامعتبر است. شناسه‌ها را به صورت عددی و جداشده با کاما وارد کنید (مثلا: 1,2)."
)
PM_ADD_CONFIRM = "🧾 پیش‌نمایش پلن جدید\n\n{detail}\n\nآیا ساخت این پلن را تایید می‌کنید؟"
PM_CREATED = "✅ پلن جدید با موفقیت ساخته شد."
PM_ASK_NEW_VALUE = "✏️ مقدار جدید برای «{field}» را وارد کنید:"
PM_FIELD_NAME = "نام"
PM_FIELD_DATA = "حجم (گیگ)"
PM_FIELD_DAYS = "مدت (روز)"
PM_FIELD_PRICE = "قیمت (تومان)"
PM_FIELD_SERVICES = "شناسه سرویس‌ها"
PM_UPDATED = "✅ پلن با موفقیت به‌روزرسانی شد."
PM_DELETE_CONFIRM = "⚠️ آیا از حذف پلن «{name}» مطمئن هستید؟ این عمل قابل بازگشت نیست."
PM_DELETED = "🗑 پلن «{name}» حذف شد."
PM_DELETE_HAS_SUBS = (
    "⚠️ این پلن قابل حذف نیست چون اشتراک‌هایی به آن متصل هستند."
)
PM_ERROR = "⚠️ خطا در انجام عملیات. دوباره تلاش کنید."

# ---------- Top-up review ----------
TOPUP_CAPTION = (
    "💳 درخواست افزایش موجودی جدید\n"
    "━━━━━━━━━━━━━━━\n"
    "👤 کاربر: {name} (@{username})\n"
    "🆔 آیدی: {telegram_id}\n"
    "💰 مبلغ: {amount}\n"
    "🗓 زمان: {created_at}\n"
    "🔖 شناسه: {request_id}\n"
    "━━━━━━━━━━━━━━━"
)
TOPUP_ALREADY_DECIDED = "⚠️ این درخواست قبلا رسیدگی شده است."
TOPUP_APPROVED_SUFFIX = "\n\n✅ تایید شد توسط {admin}"
TOPUP_REJECTED_SUFFIX = "\n\n❌ رد شد توسط {admin}"
