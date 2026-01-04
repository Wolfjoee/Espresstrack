import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from database import add_txn, get_today, get_all

TOKEN = os.getenv("7576078077:AAFlueaUbUOsjaNp32erHld7x0un8hcJH3o")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Salary Tracker Bot\n"
        "/salary <amount>\n"
        "/spend <amount> <note>\n"
        "/save <amount>\n"
        "/today\n"
        "/total"
    )

async def salary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    add_txn("salary", int(context.args[0]))
    await update.message.reply_text("Salary credited")

async def spend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    add_txn("spend", int(context.args[0]), " ".join(context.args[1:]))
    await update.message.reply_text("Expense added")

async def save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    add_txn("save", int(context.args[0]))
    await update.message.reply_text("Savings added")

async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_today()
    s = {"salary":0,"spend":0,"save":0}
    for t,a in data: s[t]+=a
    await update.message.reply_text(str(s))

async def total(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_all()
    s = {"salary":0,"spend":0,"save":0}
    for t,a in data: s[t]+=a
    await update.message.reply_text(str(s))

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("salary", salary))
app.add_handler(CommandHandler("spend", spend))
app.add_handler(CommandHandler("save", save))
app.add_handler(CommandHandler("today", today))
app.add_handler(CommandHandler("total", total))
app.run_polling()
