import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import time, json, os

TOKEN = os.getenv("BOT_TOKEN")
DATA_FILE = "data.json"
SPAM_DELAY = 10
TEMP_LINK_TIME = 600  # 10 دقیقه

# ---------- load / save ----------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {
            "users": {},
            "last_links": {},
            "temp_links": {},
            "total": 0
        }
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

data = load_data()
user_last_time = {}

# ---------- texts ----------
TEXT = {
    "fa": {
        "welcome": "👋 سلام!\n🤖 ربات تبدیل فایل به لینک\n👇 از منو استفاده کن",
        "send_file": "📎 فایل رو ارسال کن",
        "no_link": "❌ هنوز لینکی نداری",
        "expired": "⛔ لینک منقضی شده",
        "settings": "⚙️ تنظیمات",
        "language": "🌍 زبان تغییر کرد",
        "stats": "📊 آمار شما:\n📁 فایل‌ها: {count}\n📈 کل: {total}"
    },
    "en": {
        "welcome": "👋 Hi!\n🤖 File to Link Bot\n👇 Use menu below",
        "send_file": "📎 Send your file",
        "no_link": "❌ No link yet",
        "expired": "⛔ Link expired",
        "settings": "⚙️ Settings",
        "language": "🌍 Language changed",
        "stats": "📊 Your stats:\n📁 Files: {count}\n📈 Total: {total}"
    }
}

# ---------- keyboard ----------
def keyboard(lang):
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("📁 ارسال فایل"), KeyboardButton("🔗 لینک موقت من")],
            [KeyboardButton("📊 آمار من"), KeyboardButton("🌍 تغییر زبان")]
        ],
        resize_keyboard=True
    )

# ---------- helpers ----------
def get_lang(uid):
    return data["users"].get(uid, {}).get("lang", "fa")

# ---------- start ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.message.from_user.id)
    if uid not in data["users"]:
        data["users"][uid] = {"count": 0, "lang": "fa"}
        save_data()

    lang = get_lang(uid)
    await update.message.reply_text(TEXT[lang]["welcome"], reply_markup=keyboard(lang))

# ---------- text ----------
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.message.from_user.id)
    text = update.message.text
    lang = get_lang(uid)

    if text == "📁 ارسال فایل":
        await update.message.reply_text(TEXT[lang]["send_file"], reply_markup=keyboard(lang))

    elif text == "📊 آمار من":
        await update.message.reply_text(
            TEXT[lang]["stats"].format(
                count=data["users"][uid]["count"],
                total=data["total"]
            ),
            reply_markup=keyboard(lang)
        )

    elif text == "🌍 تغییر زبان":
        data["users"][uid]["lang"] = "en" if lang == "fa" else "fa"
        save_data()
        lang = get_lang(uid)
        await update.message.reply_text(TEXT[lang]["language"], reply_markup=keyboard(lang))

    elif text == "🔗 لینک موقت من":
        info = data["temp_links"].get(uid)
        if not info:
            await update.message.reply_text(TEXT[lang]["no_link"], reply_markup=keyboard(lang))
            return

        if time.time() > info["expire"]:
            await update.message.reply_text(TEXT[lang]["expired"], reply_markup=keyboard(lang))
            return

        await update.message.reply_text(info["link"], reply_markup=keyboard(lang))

# ---------- file ----------
async def file_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.message.from_user.id)
    now = time.time()
    lang = get_lang(uid)

    if now - user_last_time.get(uid, 0) < SPAM_DELAY:
        return

    user_last_time[uid] = now

    file = update.message.effective_attachment
    telegram_file = await file.get_file()

    data["users"][uid]["count"] += 1
    data["total"] += 1

    data["temp_links"][uid] = {
        "link": telegram_file.file_path,
        "expire": now + TEMP_LINK_TIME
    }

    save_data()

    await update.message.reply_text(
        f"🔗 لینک موقت (10 دقیقه):\n{telegram_file.file_path}",
        reply_markup=keyboard(lang)
    )

# ---------- run ----------
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
app.add_handler(MessageHandler(filters.ATTACHMENT, file_handler))

print("🤖 Bot running...")
app.run_polling()
