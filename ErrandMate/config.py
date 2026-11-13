import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.environ.get("ERRANDMATE_DB_PATH", os.path.join(BASE_DIR, "ErrandMate.db"))

APP_NAME = "ErrandMate"
WINDOW_TITLE = "ErrandMate - Errand Running Platform"
WINDOW_SIZE = "1180x760"
WINDOW_MIN_SIZE = (1020, 660)

# Modern light interface with deep indigo surfaces and clean accent colours
BG_DARK   = "#0F172A"   # slate/indigo header
BG_CARD   = "#1E293B"   # header hover / dark cards
BG_MAIN   = "#F8FAFC"   # app background
BG_SOFT   = "#EEF2FF"   # soft highlighted surface
WHITE     = "#FFFFFF"
MUTED     = "#F1F5F9"
LIGHT_BDR = "#E2E8F0"

ORANGE    = "#6366F1"   # primary indigo
ORANGE2   = "#4F46E5"   # primary hover
GREEN     = "#10B981"
RED_CLR   = "#EF4444"
BLUE      = "#0EA5E9"
PURPLE    = "#8B5CF6"
YELLOW    = "#F59E0B"

DARK_TXT  = "#0F172A"
GRAY_TXT  = "#64748B"
SOFT_TXT  = "#94A3B8"

FONT_FAMILY = "Segoe UI"
FONT_BODY = (FONT_FAMILY, 10)
FONT_BODY_BOLD = (FONT_FAMILY, 10, "bold")
FONT_SMALL = (FONT_FAMILY, 9)
FONT_TITLE = (FONT_FAMILY, 22, "bold")
FONT_SUBTITLE = (FONT_FAMILY, 12)
FONT_H2 = (FONT_FAMILY, 16, "bold")

TASK_STATUS_LABELS = {
    "open": "Open",
    "accepted": "Accepted",
    "in_progress": "In Progress",
    "awaiting_confirmation": "Awaiting Confirmation",
    "completed": "Completed",
    "cancelled": "Cancelled",
}

TASK_STATUS_COLORS = {
    "open": ORANGE,
    "accepted": BLUE,
    "in_progress": YELLOW,
    "awaiting_confirmation": PURPLE,
    "completed": GREEN,
    "cancelled": RED_CLR,
}

task_categories = [
    "Grocery Shopping",
    "Delivery / Courier",
    "House Cleaning",
    "Pet Care",
    "Gardening",
    "Pharmacy Pickup",
    "Cooking / Meal Prep",
    "Moving Help",
    "Tech Support",
    "Car Wash",
    "Laundry",
    "Other",
]
