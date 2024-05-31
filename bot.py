from telegram import Update, ParseMode, ChatPermissions
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from datetime import datetime, timedelta
import random

# Замените 'YOUR_BOT_TOKEN' на токен вашего бота
BOT_TOKEN = '7479142796:AAFTsC-4vu6oGF5V8oWzfKRxJC7ZDBLgGzg'
CENSORED_WORDS = ['пидар', 'сука', 'гандон', 'шлюха', 'ебать', 'чмо', 'хуй', 'пизда', 'ебаный', 'пиздюк', 'хуйло', 'уебан', 'уебок', 'ушлепок', 'шалава', 'мразь', 'долбаебы', 'уебки', 'уебаны', 'мразота', 'даун']  # Добавьте русские слова, которые нужно цензурировать
CAPTCHA_QUESTIONS = {
    'Сколько будет 2 + 2?': '4',
    'Сколько будет 3 + 5?': '8',
    'Сколько будет 6 - 1?': '5'
}

# Словарь для хранения предупреждений пользователей
user_warnings = {}

# Словарь для хранения задач капчи для новых пользователей
captcha_users = {}

# Время блокировки в минутах
BAN_DURATION = 30

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Привет! Я бот модерации.')

def censor_message(text):
    for word in CENSORED_WORDS:
        text = text.replace(word, '*' * len(word))
    return text

def warn_user(user_id):
    if user_id in user_warnings:
        user_warnings[user_id]['count'] += 1
    else:
        user_warnings[user_id] = {'count': 1, 'last_warning': datetime.now()}
    return user_warnings[user_id]['count']

def new_user_captcha(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    question, answer = random.choice(list(CAPTCHA_QUESTIONS.items()))
    captcha_users[user_id] = answer
    context.bot.send_message(chat_id=chat_id, text=f'Добро пожаловать, {update.message.from_user.first_name}! Докажи что ты настоящий "ДЕЛОВАР", а не бот: {question}')

def check_message(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    text = update.message.text

    # Проверка на капчу
    if user_id in captcha_users:
        if text == captcha_users[user_id]:
            del captcha_users[user_id]
            context.bot.send_message(chat_id=chat_id, text='Спасибо за подтверждение, теперь можешь "деловарить.')
        else:
            context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)
        return

    # Удаление ссылок, тегов и упоминаний
    if 'http' in text or '@' in text or '#' in text:
        context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)
        return

    # Проверка на цензуру
    censored_text = censor_message(text)
    if censored_text != text:
        # Отправить предупреждение пользователю
        warning_count = warn_user(user_id)
        context.bot.send_message(chat_id=chat_id, text=f'{update.message.from_user.first_name}, это предупреждение #{warning_count}. Соблюдай правила чата и не оскорбляй участников, иначел после 3-х предупреждений БАН на 30 минут.')
        
        # Если 3 предупреждения, блокировать пользователя
        if warning_count >= 3:
            context.bot.restrict_chat_member(chat_id=chat_id, user_id=user_id, permissions=ChatPermissions(can_send_messages=False), until_date=datetime.now() + timedelta(minutes=BAN_DURATION))
            context.bot.send_message(chat_id=chat_id, text=f'{update.message.from_user.first_name} был заблокирован на 30 минут за неоднократное нарушение правил чата и оскорбительное поведение.')

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.status_update.new_chat_members, new_user_captcha))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, check_message))
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
