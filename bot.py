import telebot
from telebot import types
from config import BOT_TOKEN, TIMEZONE, DAILY_REPORT_TIME
from database import Database
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
from datetime import datetime

bot = telebot.TeleBot(BOT_TOKEN)
db = Database()

# User states for conversation flow
user_states = {}

# Main Menu Keyboard
def main_menu_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        types.InlineKeyboardButton("💰 Add Credit", callback_data="add_credit"),
        types.InlineKeyboardButton("💸 Add Debit", callback_data="add_debit"),
        types.InlineKeyboardButton("📊 Balance", callback_data="balance"),
        types.InlineKeyboardButton("📋 Last 30 Days", callback_data="statement"),
        types.InlineKeyboardButton("🤝 Borrow Money", callback_data="borrow"),
        types.InlineKeyboardButton("💵 Lend Money", callback_data="lend"),
        types.InlineKeyboardButton("📥 Pending Borrows", callback_data="pending_borrows"),
        types.InlineKeyboardButton("📤 Pending Lends", callback_data="pending_lends"),
    ]
    markup.add(*buttons)
    return markup

# Start command
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    db.get_user_data(user_id)
    
    welcome_text = f"""
👋 *Welcome to Salary Tracker Bot!*

Hi {message.from_user.first_name}! I'll help you track your finances.

*Features:*
💰 Track income (credits)
💸 Track expenses (debits)
📊 Check your balance & savings
📋 View last 30 days statement
🤝 Manage borrowed money
💵 Manage lent money
⏰ Daily reports at 8:00 AM

Use the buttons below to get started!
"""
    
    bot.send_message(
        message.chat.id,
        welcome_text,
        parse_mode='Markdown',
        reply_markup=main_menu_keyboard()
    )

# Help command
@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
*📖 How to use the bot:*

1️⃣ *Add Credit* - Record income/salary received
2️⃣ *Add Debit* - Record expenses made
3️⃣ *Balance* - Check current balance and savings
4️⃣ *Last 30 Days* - View recent transactions
5️⃣ *Borrow Money* - Record money you borrowed
6️⃣ *Lend Money* - Record money you lent
7️⃣ *Pending Borrows* - Check unpaid borrowed amounts
8️⃣ *Pending Lends* - Check unreceived lent amounts

💡 Every day at 8:00 AM, you'll receive a summary of yesterday's finances!
"""
    
    bot.send_message(
        message.chat.id,
        help_text,
        parse_mode='Markdown',
        reply_markup=main_menu_keyboard()
    )

# Callback query handler
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    
    if call.data == "add_credit":
        user_states[user_id] = {'action': 'credit', 'step': 'amount'}
        bot.send_message(call.message.chat.id, "💰 Enter the credit amount:")
        
    elif call.data == "add_debit":
        user_states[user_id] = {'action': 'debit', 'step': 'amount'}
        bot.send_message(call.message.chat.id, "💸 Enter the debit amount:")
        
    elif call.data == "balance":
        show_balance(call.message.chat.id, user_id)
        
    elif call.data == "statement":
        show_statement(call.message.chat.id, user_id)
        
    elif call.data == "borrow":
        user_states[user_id] = {'action': 'borrow', 'step': 'amount'}
        bot.send_message(call.message.chat.id, "🤝 Enter the amount you borrowed:")
        
    elif call.data == "lend":
        user_states[user_id] = {'action': 'lend', 'step': 'amount'}
        bot.send_message(call.message.chat.id, "💵 Enter the amount you lent:")
        
    elif call.data == "pending_borrows":
        show_pending_borrows(call.message.chat.id, user_id)
        
    elif call.data == "pending_lends":
        show_pending_lends(call.message.chat.id, user_id)
        
    elif call.data.startswith("return_borrow_"):
        index = int(call.data.split("_")[2])
        db.mark_borrow_returned(user_id, index)
        bot.answer_callback_query(call.id, "✅ Marked as returned!")
        show_pending_borrows(call.message.chat.id, user_id)
        
    elif call.data.startswith("receive_lend_"):
        index = int(call.data.split("_")[2])
        db.mark_lend_received(user_id, index)
        bot.answer_callback_query(call.id, "✅ Marked as received!")
        show_pending_lends(call.message.chat.id, user_id)
        
    elif call.data == "main_menu":
        bot.send_message(
            call.message.chat.id,
            "📱 *Main Menu*",
            parse_mode='Markdown',
            reply_markup=main_menu_keyboard()
        )

# Message handler for user input
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    
    if user_id not in user_states:
        bot.send_message(
            message.chat.id,
            "Please use the menu buttons to interact with the bot.",
            reply_markup=main_menu_keyboard()
        )
        return
    
    state = user_states[user_id]
    action = state['action']
    step = state['step']
    
    if step == 'amount':
        try:
            amount = float(message.text)
            if amount <= 0:
                bot.send_message(message.chat.id, "❌ Amount must be positive. Try again:")
                return
            
            state['amount'] = amount
            
            if action in ['borrow', 'lend']:
                state['step'] = 'person'
                person_type = "from whom" if action == 'borrow' else "to whom"
                bot.send_message(message.chat.id, f"👤 Enter the person {person_type}:")
            else:
                state['step'] = 'description'
                bot.send_message(message.chat.id, "📝 Enter a description (or type 'skip'):")
                
        except ValueError:
            bot.send_message(message.chat.id, "❌ Invalid amount. Please enter a number:")
            
    elif step == 'person':
        state['person'] = message.text
        state['step'] = 'description'
        bot.send_message(message.chat.id, "📝 Enter a description (or type 'skip'):")
        
    elif step == 'description':
        description = message.text if message.text.lower() != 'skip' else ''
        amount = state['amount']
        
        if action == 'credit':
            db.add_credit(user_id, amount, description)
            bot.send_message(
                message.chat.id,
                f"✅ Credit added!\n💰 Amount: ${amount}\n📝 Description: {description or 'N/A'}",
                reply_markup=main_menu_keyboard()
            )
            
        elif action == 'debit':
            db.add_debit(user_id, amount, description)
            bot.send_message(
                message.chat.id,
                f"✅ Debit added!\n💸 Amount: ${amount}\n📝 Description: {description or 'N/A'}",
                reply_markup=main_menu_keyboard()
            )
            
        elif action == 'borrow':
            db.add_borrow(user_id, amount, state['person'], description)
            bot.send_message(
                message.chat.id,
                f"✅ Borrow recorded!\n🤝 Amount: ${amount}\n👤 From: {state['person']}\n📝 Description: {description or 'N/A'}",
                reply_markup=main_menu_keyboard()
            )
            
        elif action == 'lend':
            db.add_lend(user_id, amount, state['person'], description)
            bot.send_message(
                message.chat.id,
                f"✅ Lend recorded!\n💵 Amount: ${amount}\n👤 To: {state['person']}\n📝 Description: {description or 'N/A'}",
                reply_markup=main_menu_keyboard()
            )
        
        del user_states[user_id]

def show_balance(chat_id, user_id):
    balance = db.get_balance(user_id)
    user_data = db.get_user_data(user_id)
    
    total_credits = sum(t['amount'] for t in user_data['credits'])
    total_debits = sum(t['amount'] for t in user_data['debits'])
    
    pending_borrows = sum(b['amount'] for b in db.get_pending_borrows(user_id))
    pending_lends = sum(l['amount'] for l in db.get_pending_lends(user_id))
    
    balance_text = f"""
📊 *Your Financial Summary*

💰 *Total Income:* ${total_credits:.2f}
💸 *Total Expenses:* ${total_debits:.2f}
💵 *Current Balance:* ${balance:.2f}

🤝 *Pending Borrows:* ${pending_borrows:.2f}
📤 *Pending Lends:* ${pending_lends:.2f}

📅 *Date:* {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
    
    bot.send_message(
        chat_id,
        balance_text,
        parse_mode='Markdown',
        reply_markup=main_menu_keyboard()
    )

def show_statement(chat_id, user_id):
    transactions = db.get_last_30_days_transactions(user_id)
    
    if not transactions:
        bot.send_message(
            chat_id,
            "📋 No transactions in the last 30 days.",
            reply_markup=main_menu_keyboard()
        )
        return
    
    statement_text = "📋 *Last 30 Days Statement*\n\n"
    
    for trans in transactions[:20]:  # Show max 20 transactions
        trans_type = "💰 Credit" if trans['type'] == 'credit' else "💸 Debit"
        amount = trans['amount']
        desc = trans['description'] or 'N/A'
        date = datetime.strptime(trans['date'], '%Y-%m-%d %H:%M:%S').strftime('%d/%m %H:%M')
        
        statement_text += f"{trans_type}: ${amount:.2f}\n📝 {desc}\n📅 {date}\n\n"
    
    bot.send_message(
        chat_id,
        statement_text,
        parse_mode='Markdown',
        reply_markup=main_menu_keyboard()
    )

def show_pending_borrows(chat_id, user_id):
    borrows = db.get_pending_borrows(user_id)
    
    if not borrows:
        bot.send_message(
            chat_id,
            "✅ No pending borrows!",
            reply_markup=main_menu_keyboard()
        )
        return
    
    markup = types.InlineKeyboardMarkup()
    
    text = "🤝 *Pending Borrows:*\n\n"
    for i, borrow in enumerate(borrows):
        text += f"💰 ${borrow['amount']:.2f}\n👤 From: {borrow['from']}\n📅 {borrow['date'][:10]}\n\n"
        markup.add(types.InlineKeyboardButton(
            f"✅ Return ${borrow['amount']:.2f}",
            callback_data=f"return_borrow_{i}"
        ))
    
    markup.add(types.InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu"))
    
    bot.send_message(chat_id, text, parse_mode='Markdown', reply_markup=markup)

def show_pending_lends(chat_id, user_id):
    lends = db.get_pending_lends(user_id)
    
    if not lends:
        bot.send_message(
            chat_id,
            "✅ No pending lends!",
            reply_markup=main_menu_keyboard()
        )
        return
    
    markup = types.InlineKeyboardMarkup()
    
    text = "💵 *Pending Lends:*\n\n"
    for i, lend in enumerate(lends):
        text += f"💰 ${lend['amount']:.2f}\n👤 To: {lend['to']}\n📅 {lend['date'][:10]}\n\n"
        markup.add(types.InlineKeyboardButton(
            f"✅ Received ${lend['amount']:.2f}",
            callback_data=f"receive_lend_{i}"
        ))
    
    markup.add(types.InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu"))
    
    bot.send_message(chat_id, text, parse_mode='Markdown', reply_markup=markup)

# Daily notification function
def send_daily_report():
    for user_id in db.data.keys():
        try:
            stats = db.get_yesterday_stats(user_id)
            
            report = f"""
☀️ *Good Morning!*

📊 *Yesterday's Summary:*

💰 Income: ${stats['income']:.2f}
💸 Expenses: ${stats['expense']:.2f}
💵 Savings: ${stats['savings']:.2f}

{'🎉 Great job saving!' if stats['savings'] > 0 else '⚠️ Watch your spending!'}
"""
            
            bot.send_message(
                int(user_id),
                report,
                parse_mode='Markdown',
                reply_markup=main_menu_keyboard()
            )
        except Exception as e:
            print(f"Error sending daily report to {user_id}: {e}")

# Schedule daily reports
scheduler = BackgroundScheduler(timezone=pytz.timezone(TIMEZONE))
hour, minute = DAILY_REPORT_TIME.split(':')
scheduler.add_job(
    send_daily_report,
    CronTrigger(hour=int(hour), minute=int(minute)),
    id='daily_report'
)
scheduler.start()

# Start bot
if __name__ == '__main__':
    print("Bot is running...")
    bot.infinity_polling()
