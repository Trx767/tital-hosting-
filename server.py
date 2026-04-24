import os
import subprocess
import logging
import threading
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# --- ⚙️ CONFIGURATION ---
TOKEN = '8640771765:AAHq8W2oT-LgcWQTHahu8TmO0S8XNuiTL3A'
ADMIN_IDS = [8338131451]
running_processes = {}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- 🌐 RENDER KEEP-ALIVE SERVER ---
def keep_alive():
    port = int(os.environ.get("PORT", 8080))
    with TCPServer(("", port), SimpleHTTPRequestHandler) as httpd:
        print(f"📡 Web Server Active on Port {port}")
        httpd.serve_forever()

threading.Thread(target=keep_alive, daemon=True).start()

# --- ⌨️ BOTTOM MENU ---
def get_main_menu():
    kb = [
        [KeyboardButton("📊 My Bots Status"), KeyboardButton("📂 My Files")],
        [KeyboardButton("🗑 Delete/Stop Bot"), KeyboardButton("📡 Server Health")]
    ]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 <b>TITAN RENDER HOSTING IS LIVE</b>\n\nစာရိုက်ဘေးက Icon ကိုနှိပ်ပြီး Menu သုံးပါ။\nဖိုင် (.py / .js) ပို့ပြီး Hosting တင်နိုင်ပါပြီ။",
        parse_mode='HTML', reply_markup=get_main_menu()
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    if text == "📊 My Bots Status":
        if user_id not in running_processes or not running_processes[user_id]:
            await update.message.reply_text("ℹ️ Run ထားသော Bot မရှိပါ။")
        else:
            msg = "📊 <b>Active Bots:</b>\n"
            for n, p in running_processes[user_id].items():
                s = "🟢 Online" if p.poll() is None else "🔴 Stopped"
                msg += f"• {n} - {s}\n"
            await update.message.reply_text(msg, parse_mode='HTML')
    
    elif text == "📂 My Files":
        ud = f"user_{user_id}"
        if os.path.exists(ud) and os.listdir(ud):
            files = "\n".join([f"• <code>{f}</code>" for f in os.listdir(ud)])
            await update.message.reply_text(f"📂 <b>Your Files:</b>\n{files}", parse_mode='HTML')
        else:
            await update.message.reply_text("📂 ဖိုင်မရှိသေးပါ။")

    elif text == "🗑 Delete/Stop Bot":
        ud = f"user_{user_id}"
        if not os.path.exists(ud) or not os.listdir(ud):
            await update.message.reply_text("❌ ဖျက်စရာဖိုင် မရှိပါ။")
            return
        kb = [[InlineKeyboardButton(f"❌ Delete: {f}", callback_data=f"del_{f}")] for f in os.listdir(ud)]
        await update.message.reply_text("ဖျက်လိုသောဖိုင် ရွေးပါ:", reply_markup=InlineKeyboardMarkup(kb))

async def handle_docs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    doc = update.message.document
    fn = doc.file_name
    ext = os.path.splitext(fn)[1].lower()
    if ext in ['.py', '.js']:
        ud = f"user_{user_id}"
        if not os.path.exists(ud): os.makedirs(ud)
        path = os.path.join(ud, fn)
        file = await context.bot.get_file(doc.file_id)
        await file.download_to_drive(path)
        if user_id not in running_processes: running_processes[user_id] = {}
        if fn in running_processes[user_id]: running_processes[user_id][fn].terminate()
        cmd = ['python', path] if ext == '.py' else ['node', path]
        running_processes[user_id][fn] = subprocess.Popen(cmd)
        await update.message.reply_text(f"✅ <b>Deployed:</b> {fn}", parse_mode='HTML')

async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = q.from_user.id
    fn = q.data.replace("del_", "")
    await q.answer()
    if uid in running_processes and fn in running_processes[uid]:
        running_processes[uid][fn].terminate()
        del running_processes[uid][fn]
    try: os.remove(f"user_{uid}/{fn}")
    except: pass
    await q.edit_message_text(f"✅ <code>{fn}</code> deleted.", parse_mode='HTML')

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_docs))
    app.add_handler(CallbackQueryHandler(callback))
    app.run_polling()

if __name__ == '__main__':
    main()
              
