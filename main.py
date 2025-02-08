from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
from dotenv import load_dotenv
import os
import json

# Загружаем переменные окружения
load_dotenv()

# Инициализация токена
updater = Updater(os.getenv("BOT_TOKEN"), use_context=True)

data_file = 'data.json'

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
        data[user_id] = {"name": update.message.from_user.first_name, "checklists": {}}
        save_data(data)
    menu_keyboard = [[KeyboardButton("/create_checklist"), KeyboardButton("/my_checklists")], [KeyboardButton("/edit_checklist")]]
    reply_markup = ReplyKeyboardMarkup(menu_keyboard, resize_keyboard=True)
    update.message.reply_text(f"Привет, {data[user_id]['name']}! Готов помочь с чек-листами. Выбери команду из меню ниже:", reply_markup=reply_markup)

# Создание нового чек-листа
def create_checklist(update: Update, context: CallbackContext):
    context.user_data['creating'] = True
    update.message.reply_text("Как назовем чек-лист?")

# Редактирование чек-листа
def edit_checklist(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    checklists = data[user_id]['checklists']
    if checklists:
        keyboard = [[InlineKeyboardButton(name, callback_data=f'edit_{name}')] for name in checklists]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("Выбери чек-лист для редактирования:", reply_markup=reply_markup)
    else:
        update.message.reply_text("У тебя пока нет чек-листов. Напиши /create_checklist, чтобы создать.")

# Обработка сообщений пользователя
def handle_message(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    if context.user_data.get('creating'):
        checklist_name = update.message.text
        data[user_id]['checklists'][checklist_name] = []
        context.user_data['current_checklist'] = checklist_name
        context.user_data['creating'] = False
        context.user_data['adding_tasks'] = True
        save_data(data)
        update.message.reply_text(f"Добавим задачи в чек-лист '{checklist_name}'. Напиши первую задачу или '/done', чтобы закончить.")
    elif context.user_data.get('adding_tasks'):
        if update.message.text == '/done':
            context.user_data['adding_tasks'] = False
            save_data(data)
            update.message.reply_text(f"Чек-лист '{context.user_data['current_checklist']}' сохранен! Напиши /my_checklists, чтобы посмотреть.")
        else:
            task = update.message.text
            checklist_name = context.user_data['current_checklist']
            data[user_id]['checklists'][checklist_name].append({'task': task, 'done': False})
            save_data(data)
            update.message.reply_text(f"Добавлено: {task}. Добавь ещё или напиши /done.")

# Показать чек-листы пользователя
def show_checklists(update: Update, context: CallbackContext):
    user_id = str(update.message.from_user.id)
    checklists = data[user_id]['checklists']
    if checklists:
        keyboard = [[InlineKeyboardButton(name, callback_data=f'start_{name}')] for name in checklists]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("Вот твои чек-листы:", reply_markup=reply_markup)
    else:
        update.message.reply_text("У тебя пока нет чек-листов. Напиши /create_checklist, чтобы создать.")

# Начать выполнение чек-листа
def button(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = str(query.from_user.id)
    if query.data.startswith('edit_'):
        checklist_name = query.data.split('_', 1)[1]
        context.user_data['editing'] = True
        context.user_data['current_checklist'] = checklist_name
        update_edit_menu(query, user_id, checklist_name)
    else:
        checklist_name = query.data.split('_', 1)[1]
        context.user_data['current_checklist'] = checklist_name
        show_tasks(query, user_id, checklist_name)

# Показать задачи чек-листа
def show_tasks(query, user_id, checklist_name):
    tasks = data[user_id]['checklists'][checklist_name]
    keyboard = []
    text = f"Чек-лист: {checklist_name}\n\n"
    for idx, task in enumerate(tasks):
        status = '✅' if task['done'] else '⬜'
        text += f"{status} {task['task']}\n"
        keyboard.append([InlineKeyboardButton(f"{status} {task['task']}", callback_data=f'toggle_{idx}')])
    keyboard.append([InlineKeyboardButton("Вышел", callback_data='finish')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text, reply_markup=reply_markup)

# Обновить меню редактирования чек-листа
def update_edit_menu(query, user_id, checklist_name):
    tasks = data[user_id]['checklists'][checklist_name]
    keyboard = []
    text = f"Редактирование чек-листа: {checklist_name}\n\n"
    for idx, task in enumerate(tasks):
        text += f"{task['task']}\n"
        keyboard.append([InlineKeyboardButton(f"Удалить: {task['task']}", callback_data=f'delete_{idx}')])
    keyboard.append([InlineKeyboardButton("Добавить задачу", callback_data='add_task')])
    keyboard.append([InlineKeyboardButton("Готово", callback_data='finish_edit')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text, reply_markup=reply_markup)

# Редактирование задач чек-листа
def edit_task(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = str(query.from_user.id)
    checklist_name = context.user_data['current_checklist']

    if query.data.startswith('delete_'):
        idx = int(query.data.split('_')[1])
        del data[user_id]['checklists'][checklist_name][idx]
        save_data(data)
        update_edit_menu(query, user_id, checklist_name)

    elif query.data == 'add_task':
        context.user_data['adding_tasks'] = True
        query.edit_message_text(f"Напиши новую задачу для чек-листа '{checklist_name}'.")

    elif query.data == 'finish_edit':
        context.user_data['editing'] = False
        query.edit_message_text(f"Редактирование чек-листа '{checklist_name}' завершено.")

# Отметка выполнения задач
def toggle_task(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = str(query.from_user.id)
    idx = int(query.data.split('_')[1])
    checklist_name = context.user_data['current_checklist']
    data[user_id]['checklists'][checklist_name][idx]['done'] = not data[user_id]['checklists'][checklist_name][idx]['done']
    save_data(data)
    show_tasks(query, user_id, checklist_name)

# Завершение чек-листа
def finish_checklist(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = str(query.from_user.id)
    checklist_name = context.user_data['current_checklist']
    tasks = data[user_id]['checklists'][checklist_name]
    text = "Все задачи выполнены:\n\n"
    for task in tasks:
        status = '✅' if task['done'] else '❌'
        text += f"{status} {task['task']}\n"
    query.edit_message_text(text)

# Основная функция запуска бота
def main():
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("create_checklist", create_checklist))
    dp.add_handler(CommandHandler("my_checklists", show_checklists))
    dp.add_handler(CommandHandler("edit_checklist", edit_checklist))
    dp.add_handler(CallbackQueryHandler(button, pattern=r'start_.*|edit_.*'))
    dp.add_handler(CallbackQueryHandler(toggle_task, pattern=r'toggle_.*'))
    dp.add_handler(CallbackQueryHandler(finish_checklist, pattern=r'finish'))
    dp.add_handler(CallbackQueryHandler(edit_task, pattern=r'delete_.*|add_task|finish_edit'))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
