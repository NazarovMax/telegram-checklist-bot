from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
from telegram.error import NetworkError
from dotenv import load_dotenv
import os
import json

# Загружаем переменные окружения (нужно только для локальной работы)
load_dotenv()

print("Скрипт запущен", flush=True)

# Получаем токен из переменной окружения
bot_token = os.getenv('BOT_TOKEN')
PORT = os.getenv("PORT", 10000)

# Проверяем наличие токена
if not bot_token:
    print("Ошибка: Токен не найден в .env файле или переменных окружения!", flush=True)
else:
    print(f"Токен успешно загружен: {bot_token}", flush=True)

# Инициализация токена
updater = Updater(bot_token, use_context=True)

data_file = 'data.json'

print("Бот начинает polling...", flush=True)

# Загрузка данных пользователей
def load_data():
    if os.path.exists(data_file):
        with open(data_file, 'r') as file:
            return json.load(file)
    return {}

# Сохранение данных пользователей
def save_data(data):
    with open(data_file, 'w') as file:
        json.dump(data, file, indent=4)

# Инициализация данных
data = load_data()

# Команда /start
def start(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    if user_id not in data:
        data[user_id] = {
            "name": update.message.from_user.first_name,
            "checklists": {}
        }
        save_data(data)
    menu_keyboard = [[
        KeyboardButton("📝 Создать чек-лист"),
        KeyboardButton("📋 Мои чек-листы")
    ], [KeyboardButton("✏️ Редактировать чек-лист")], [KeyboardButton("🗑 Удалить чек-лист")]]
    reply_markup = ReplyKeyboardMarkup(menu_keyboard, resize_keyboard=True)
    update.message.reply_text(
        f"Привет, {data[user_id]['name']}! Готов помочь с чек-листами. Выбери команду из меню ниже:",
        reply_markup=reply_markup)

# Показать чек-листы пользователя
def show_checklists(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    checklists = data.get(user_id, {}).get('checklists', {})
    if checklists:
        keyboard = [[InlineKeyboardButton(name, callback_data=f'start_{name}')] for name in checklists]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("Вот твои чек-листы:", reply_markup=reply_markup)
    else:
        update.message.reply_text("У тебя пока нет чек-листов. Нажми \"📝 Создать чек-лист\", чтобы создать.")

# Удаление чек-листа
def delete_checklist(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    checklists = data.get(user_id, {}).get('checklists', {})
    
    if checklists:
        keyboard = [[InlineKeyboardButton(name, callback_data=f'delete_{name}')] for name in checklists]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("Выбери чек-лист для удаления:", reply_markup=reply_markup)
    else:
        update.message.reply_text("У тебя пока нет чек-листов. Нажми \"📝 Создать чек-лист\", чтобы создать.")


# Редактирование чек-листа
def edit_checklist(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    checklists = data.get(user_id, {}).get('checklists', {})
    
    if checklists:
        keyboard = [[InlineKeyboardButton(name, callback_data=f'edit_{name}')] for name in checklists]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("Выбери чек-лист для редактирования:", reply_markup=reply_markup)
    else:
        update.message.reply_text("У тебя пока нет чек-листов. Нажми \"📝 Создать чек-лист\", чтобы создать.")


# Создание нового чек-листа
def create_checklist(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    update.message.reply_text("Как назовем чек-лист?")
    context.user_data['creating_checklist'] = True
    
def button(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    data = query.data  # Данные из callback_data
    
    if data.startswith('start_'):
        checklist_name = data.split('_', 1)[1]
        query.edit_message_text(f"Ты выбрал чек-лист: {checklist_name}")
        
    elif data.startswith('edit_'):
        checklist_name = data.split('_', 1)[1]
        query.edit_message_text(f"Редактирование чек-листа: {checklist_name}")
        
    elif data.startswith('delete_'):
        checklist_name = data.split('_', 1)[1]
        query.edit_message_text(f"Чек-лист '{checklist_name}' удалён.")
        
def toggle_task(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = str(query.from_user.id)
    
    # Получаем название чек-листа из данных пользователя
    checklist_name = context.user_data.get('current_checklist')

    def edit_task(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    user_id = str(query.from_user.id)
    checklist_name = context.user_data.get('current_checklist')

    if not checklist_name or checklist_name not in data.get(user_id, {}).get('checklists', {}):
        query.edit_message_text("Ошибка: чек-лист не найден.")
        return

    if query.data.startswith('delete_'):
        task_index = int(query.data.split('_')[1])
        if 0 <= task_index < len(data[user_id]['checklists'][checklist_name]):
            del data[user_id]['checklists'][checklist_name][task_index]
            save_data(data)
            query.edit_message_text(f"Задача удалена из чек-листа '{checklist_name}'.")
        else:
            query.edit_message_text("Ошибка: неверный индекс задачи.")
    elif query.data == 'add_task':
        context.user_data['adding_task'] = True
        query.edit_message_text(f"Добавь новую задачу для чек-листа '{checklist_name}'.")
    elif query.data == 'finish_edit':
        query.edit_message_text(f"Редактирование чек-листа '{checklist_name}' завершено.")

    
    # Проверка на существование чек-листа
    if not checklist_name or checklist_name not in data.get(user_id, {}).get('checklists', {}):
        query.edit_message_text("Ошибка: чек-лист не найден.")
        return
    
    # Извлечение индекса задачи из callback_data
    task_index = int(query.data.split('_')[1])
    checklist = data[user_id]['checklists'][checklist_name]
    
    # Переключение статуса выполнения задачи
    if 0 <= task_index < len(checklist):
        checklist[task_index]['done'] = not checklist[task_index]['done']
        save_data(data)
        query.edit_message_text(f"Задача '{checklist[task_index]['task']}' обновлена!")
    else:
        query.edit_message_text("Ошибка: задача не найдена.")
        
def finish_checklist(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    user_id = str(query.from_user.id)
    checklist_name = context.user_data.get('current_checklist')
    
    if not checklist_name or checklist_name not in data.get(user_id, {}).get('checklists', {}):
        query.edit_message_text("Ошибка: чек-лист не найден.")
        return

    tasks = data[user_id]['checklists'][checklist_name]
    result = f"✅ Чек-лист '{checklist_name}' завершён!\n\n"
    
    for task in tasks:
        status = "✅" if task['done'] else "❌"
        result += f"{status} {task['task']}\n"
    
    query.edit_message_text(result)


# Основная функция запуска бота
def main():
    dp = updater.dispatcher

    # Удаление Webhook перед запуском polling
    updater.bot.delete_webhook(drop_pending_updates=True)

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.regex("^📝 Создать чек-лист$"), create_checklist))
    dp.add_handler(MessageHandler(Filters.regex("^📋 Мои чек-листы$"), show_checklists))
    dp.add_handler(MessageHandler(Filters.regex("^✏️ Редактировать чек-лист$"), edit_checklist))
    dp.add_handler(MessageHandler(Filters.regex("^🗑 Удалить чек-лист$"), delete_checklist))
    dp.add_handler(CallbackQueryHandler(button, pattern=r'start_.*|edit_.*|delete_.*'))
    dp.add_handler(CallbackQueryHandler(toggle_task, pattern=r'toggle_.*'))
    dp.add_handler(CallbackQueryHandler(finish_checklist, pattern=r'finish'))
    dp.add_handler(CallbackQueryHandler(edit_task, pattern=r'delete_.*|add_task|finish_edit'))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    print("Попытка запуска бота...")
    try:
        updater.start_polling()
        print("Бот запущен и подключён к Telegram API.")
    except NetworkError as e:
        print(f"Ошибка сети: {e}")
    except Exception as e:
        print(f"Произошла ошибка: {e}")

    print("Polling завершён.", flush=True)

    updater.idle()

if __name__ == '__main__':
    main()
