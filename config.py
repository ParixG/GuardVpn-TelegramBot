from dotenv import load_dotenv
import os

load_dotenv()   # no-op on Linux when vars are already in environment via EnvironmentFile

USER_BOT_TOKEN  = os.environ["USER_BOT_TOKEN"]
ADMIN_BOT_TOKEN = os.environ["ADMIN_BOT_TOKEN"]
ADMIN_IDS       = list(map(int, os.environ["ADMIN_IDS"].split(",")))
GUARD_URL       = os.environ["GUARD_URL"]
GUARD_API_KEY   = os.environ["GUARD_API_KEY"]
SUPABASE_URL    = os.environ["SUPABASE_URL"]
SUPABASE_KEY    = os.environ["SUPABASE_KEY"]

# Card-to-card top-up info shown to users
CARD_NUMBER     = os.environ["CARD_NUMBER"]
CARD_HOLDER     = os.environ["CARD_HOLDER"]
