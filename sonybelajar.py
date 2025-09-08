import logging
import random
import json
import os
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from telegram.constants import ParseMode

TOKEN = "8465595263:AAEBZyLxwDxkJBqJHVwWACNPwBkaaC0An7A"

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    level=logging.INFO,
)

KUTIPAN = [
    "Jangan berhenti ketika lelah, berhentilah ketika selesai.",
    "Setiap langkah kecil membawa kamu lebih dekat ke tujuan besar.",
    "Gagal itu biasa, yang penting jangan berhenti mencoba.",
    "Waktu terbaik untuk memulai adalah sekarang.",
    "Fokus pada proses, hasil akan mengikuti."
]

DATA_NOTES = "catatan.json"
DATA_STICKERS = "stickers.json"

def now_str():
    return datetime.now().strftime("%d-%m-%Y %H:%M:%S")

def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ===== Start & Help =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("/motivasi"), KeyboardButton("/waktu")],
        [KeyboardButton("/lihatcatatan"), KeyboardButton("/sticker")],
        [KeyboardButton("/format"), KeyboardButton("/format_html")],
        [KeyboardButton("/help")]
    ]
    await update.message.reply_text(
        "Halo, ini sonybelajarBot. Pilih perintah di menu atau ketik manual.",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Perintah:\n"
        "/start Memulai bot\n"
        "/help Bantuan\n"
        "/motivasi Kutipan motivasi\n"
        "/waktu Waktu sekarang\n"
        "/catat <teks> Simpan catatan\n"
        "/lihatcatatan Lihat catatan\n"
        "/hapuscatatan <nomor> Hapus catatan\n"
        "/hapussemua Hapus semua catatan\n"
        "/sticker Kirim stiker motivasi\n"
        "/format Contoh format MarkdownV2\n"
        "/format_html Contoh format HTML"
    )

# ===== Motivasi & Waktu =====
async def motivasi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(KUTIPAN))

async def waktu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Waktu sekarang: {now_str()} WIB")

# ===== Catatan =====
async def catat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args).strip()
    if not text:
        await update.message.reply_text("Format: /catat <teks catatan>")
        return
    data = load_json(DATA_NOTES, {})
    key = str(update.effective_chat.id)
    data.setdefault(key, [])
    data[key].append({"t": now_str(), "text": text})
    save_json(DATA_NOTES, data)
    await update.message.reply_text("Catatan disimpan.")

async def lihatcatatan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_json(DATA_NOTES, {})
    key = str(update.effective_chat.id)
    notes = data.get(key, [])
    if not notes:
        await update.message.reply_text("Belum ada catatan.")
        return
    lines = []
    for i, n in enumerate(notes, start=1):
        lines.append(f"{i}. [{n['t']}] {n['text']}")
        if i >= 20:
            lines.append(f"... total {len(notes)} catatan")
            break
    await update.message.reply_text("\n".join(lines))

async def hapuscatatan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Format: /hapuscatatan <nomor>")
        return
    idx = int(context.args[0])
    data = load_json(DATA_NOTES, {})
    key = str(update.effective_chat.id)
    notes = data.get(key, [])
    if idx < 1 or idx > len(notes):
        await update.message.reply_text("Nomor tidak valid.")
        return
    removed = notes.pop(idx - 1)
    data[key] = notes
    save_json(DATA_NOTES, data)
    await update.message.reply_text(f"Catatan dihapus: {removed['text']}")

async def hapussemua(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_json(DATA_NOTES, {})
    key = str(update.effective_chat.id)
    count = len(data.get(key, []))
    data[key] = []
    save_json(DATA_NOTES, data)
    await update.message.reply_text(f"Semua catatan dihapus. Total {count}.")

# ===== Sticker + Inline Button =====
def sticker_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("Stiker Lagi 🔄", callback_data="sticker_again")]])

async def sticker_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store = load_json(DATA_STICKERS, {})
    key = str(update.effective_chat.id)
    items = store.get(key, [])
    if not items:
        await update.message.reply_text(
            "Belum ada stiker tersimpan. Kirimkan satu stiker ke bot dulu, lalu coba /sticker."
        )
        return
    file_id = random.choice(items)
    await update.message.reply_sticker(file_id, reply_markup=sticker_keyboard())

async def sticker_catcher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    st = update.message.sticker
    if not st:
        return
    store = load_json(DATA_STICKERS, {})
    key = str(update.effective_chat.id)
    store.setdefault(key, [])
    if st.file_id not in store[key]:
        store[key].append(st.file_id)
        save_json(DATA_STICKERS, store)
        await update.message.reply_text("Stiker disimpan. Coba /sticker untuk kirim ulang secara acak.")
    else:
        await update.message.reply_text("Stiker ini sudah ada. Coba /sticker.")

async def sticker_again_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    store = load_json(DATA_STICKERS, {})
    key = str(query.message.chat.id)
    items = store.get(key, [])
    if not items:
        await query.message.reply_text("Belum ada stiker tersimpan.")
        return
    file_id = random.choice(items)
    await context.bot.send_sticker(chat_id=query.message.chat.id, sticker=file_id, reply_markup=sticker_keyboard())

# ===== Format: MarkdownV2 & HTML =====
async def format_md(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # MarkdownV2 perlu escape karakter khusus: _ * [ ] ( ) ~ ` > # + - = | { } . !
    teks = (
        "*Contoh\\ Markdown*\n"
        "_Teks\\ miring_\n"
        "*Teks\\ tebal*\n"
        "`Kode\\ inline`\n"
        "\\- Item 1\n"
        "\\- Item 2\n"
        "[Kunjungi\\ Google](https://google.com)"
    )
    await update.message.reply_text(teks, parse_mode=ParseMode.MARKDOWN_V2)

async def format_html(update: Update, context: ContextTypes.DEFAULT_TYPE):
    teks = (
        "<b>Contoh HTML</b><br>"
        "<i>Teks miring</i><br>"
        "<b>Teks tebal</b><br>"
        "<code>Kode inline</code><br>"
        "• Item 1<br>"
        "• Item 2<br>"
        '<a href="https://google.com">Kunjungi Google</a>'
    )
    await update.message.reply_text(teks, parse_mode=ParseMode.HTML)

# ===== Fallback =====
async def fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Perintah tidak dikenali. Coba /help.")

def main():
    app = Application.builder().token(TOKEN).build()

    # Dasar
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("motivasi", motivasi))
    app.add_handler(CommandHandler("waktu", waktu))

    # Catatan
    app.add_handler(CommandHandler("catat", catat))
    app.add_handler(CommandHandler("lihatcatatan", lihatcatatan))
    app.add_handler(CommandHandler("hapuscatatan", hapuscatatan))
    app.add_handler(CommandHandler("hapussemua", hapussemua))

    # Sticker
    app.add_handler(CommandHandler("sticker", sticker_cmd))
    app.add_handler(MessageHandler(filters.Sticker.ALL, sticker_catcher))
    app.add_handler(CallbackQueryHandler(sticker_again_callback, pattern="^sticker_again$"))

    # Format
    app.add_handler(CommandHandler("format", format_md))
    app.add_handler(CommandHandler("format_html", format_html))

    # Fallback
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fallback))

    print("sonybelajarBot sudah berjalan...")
    app.run_polling()

if __name__ == "__main__":
    main()
