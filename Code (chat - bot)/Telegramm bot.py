from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from datetime import datetime
import json
import os

# Определяем состояния для ConversationHandler
(
    MAIN_MENU, FILMS_MENU, SERIES_MENU, BOOKS_MENU,
    VIEW_NOTES, ADD_NOTE, EDIT_NOTE_CHOOSE, EDIT_NOTE, DELETE_NOTE
) = range(9)

# Токен бота
TOKEN = "7462511961:AAG2LwhbWPX3GHP-wLHmMHnohu81l9_fWoQ"
application = Application.builder().token(TOKEN).build()

# Файл для хранения заметок
NOTES_FILE = "notes.json"

# Загрузка заметок из файла
def load_notes():
    if os.path.exists(NOTES_FILE):
        with open(NOTES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# Сохранение заметок в файл
def save_notes(notes):
    with open(NOTES_FILE, 'w', encoding='utf-8') as f:
        json.dump(notes, f, ensure_ascii=False, indent=2)

# Текст сообщений
WELCOME_TEXT = """
Привет! 👋 Я твой помощник в мире развлечений. 
Я могу помочь тебе с фильмами, сериалами и книгами. 
Выбери категорию ниже и начнем! 🎬📺📚
"""

# Клавиатуры
main_menu_keyboard = [["Фильмы", "Сериалы"], ["Книги"]]

films_menu_keyboard = [
    ["Список фильмов", "Рекомендации"],
    ["Фильтр", "Избранное"],
    ["Заметки", "Назад"]
]

series_menu_keyboard = [
    ["Список сериалов", "Рекомендации"],
    ["Фильтр", "Избранное"],
    ["Заметки", "Назад"]
]

books_menu_keyboard = [
    ["Список книг", "Рекомендации"],
    ["Фильтр", "Избранное"],
    ["Заметки", "Назад"]
]

notes_menu_keyboard = [
    ["Просмотреть заметки", "Добавить заметку"],
    ["Редактировать заметку", "Удалить заметку"],
    ["Назад"]
]

def create_keyboard(keyboard):
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        WELCOME_TEXT,
        reply_markup=create_keyboard(main_menu_keyboard)
    )
    return MAIN_MENU

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if text == "Фильмы":
        await update.message.reply_text(
            "Выберите действие с фильмами",
            reply_markup=create_keyboard(films_menu_keyboard)
        )
        return FILMS_MENU
    elif text == "Сериалы":
        await update.message.reply_text(
            "Выберите действие с сериалами",
            reply_markup=create_keyboard(series_menu_keyboard)
        )
        return SERIES_MENU
    elif text == "Книги":
        await update.message.reply_text(
            "Выберите действие с книгами",
            reply_markup=create_keyboard(books_menu_keyboard)
        )
        return BOOKS_MENU
    else:
        await update.message.reply_text(
            "Пожалуйста, используйте кнопки для навигации.",
            reply_markup=create_keyboard(main_menu_keyboard))
        return MAIN_MENU

async def films_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if text == "Назад":
        await update.message.reply_text(
            "Главное меню",
            reply_markup=create_keyboard(main_menu_keyboard))
        return MAIN_MENU
    elif text == "Заметки":
        context.user_data['category'] = 'films'
        await update.message.reply_text(
            "Управление заметками о фильмах",
            reply_markup=create_keyboard(notes_menu_keyboard))
        return VIEW_NOTES
    else:
        await update.message.reply_text(
            f"Вы выбрали - {text}. Этот функционал еще в разработке.",
            reply_markup=create_keyboard(films_menu_keyboard))
        return FILMS_MENU

async def series_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if text == "Назад":
        await update.message.reply_text(
            "Главное меню",
            reply_markup=create_keyboard(main_menu_keyboard))
        return MAIN_MENU
    elif text == "Заметки":
        context.user_data['category'] = 'series'
        await update.message.reply_text(
            "Управление заметками о сериалах",
            reply_markup=create_keyboard(notes_menu_keyboard))
        return VIEW_NOTES
    else:
        await update.message.reply_text(
            f"Вы выбрали - {text}. Этот функционал еще в разработке.",
            reply_markup=create_keyboard(series_menu_keyboard))
        return SERIES_MENU

async def books_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if text == "Назад":
        await update.message.reply_text(
            "Главное меню",
            reply_markup=create_keyboard(main_menu_keyboard))
        return MAIN_MENU
    elif text == "Заметки":
        context.user_data['category'] = 'books'
        await update.message.reply_text(
            "Управление заметками о книгах",
            reply_markup=create_keyboard(notes_menu_keyboard))
        return VIEW_NOTES
    else:
        await update.message.reply_text(
            f"Вы выбрали - {text}. Этот функционал еще в разработке.",
            reply_markup=create_keyboard(books_menu_keyboard))
        return BOOKS_MENU

async def view_notes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    user_id = str(update.message.from_user.id)
    category = context.user_data.get('category', '')
    
    if text == "Назад":
        if category == 'films':
            await update.message.reply_text(
                "Меню фильмов",
                reply_markup=create_keyboard(films_menu_keyboard))
            return FILMS_MENU
        elif category == 'series':
            await update.message.reply_text(
                "Меню сериалов",
                reply_markup=create_keyboard(series_menu_keyboard))
            return SERIES_MENU
        elif category == 'books':
            await update.message.reply_text(
                "Меню книг",
                reply_markup=create_keyboard(books_menu_keyboard))
            return BOOKS_MENU
    
    notes = load_notes()
    user_notes = notes.get(user_id, {}).get(category, {})
    
    if text == "Просмотреть заметки":
        if not user_notes:
            await update.message.reply_text(
                "У вас пока нет заметок в этой категории.",
                reply_markup=create_keyboard(notes_menu_keyboard))
        else:
            notes_list = "\n".join(
                f"{i+1}. {note['text']} ({note['date']})"
                for i, note in enumerate(user_notes.values()))
            await update.message.reply_text(
                f"Ваши заметки:\n{notes_list}",
                reply_markup=create_keyboard(notes_menu_keyboard))
        return VIEW_NOTES
    
    elif text == "Добавить заметку":
        await update.message.reply_text(
            "Напишите текст новой заметки",
            reply_markup=ReplyKeyboardRemove())
        return ADD_NOTE
    
    elif text == "Редактировать заметку":
        if not user_notes:
            await update.message.reply_text(
                "Нет заметок для редактирования.",
                reply_markup=create_keyboard(notes_menu_keyboard))
            return VIEW_NOTES
        
        notes_list = "\n".join(
            f"{i+1}. {note['text']}"
            for i, note in enumerate(user_notes.values()))
        context.user_data['notes'] = user_notes
        await update.message.reply_text(
            f"Выберите заметку для редактирования:\n{notes_list}\n\nОтправьте номер заметки:",
            reply_markup=ReplyKeyboardRemove())
        return EDIT_NOTE_CHOOSE
    
    elif text == "Удалить заметку":
        if not user_notes:
            await update.message.reply_text(
                "Нет заметок для удаления.",
                reply_markup=create_keyboard(notes_menu_keyboard))
            return VIEW_NOTES
        
        notes_list = "\n".join(
            f"{i+1}. {note['text']}"
            for i, note in enumerate(user_notes.values()))
        context.user_data['notes'] = user_notes
        await update.message.reply_text(
            f"Выберите заметку для удаления:\n{notes_list}\n\nОтправьте номер заметки:",
            reply_markup=ReplyKeyboardRemove())
        return DELETE_NOTE
    
    else:
        await update.message.reply_text(
            "Пожалуйста, используйте кнопки для навигации.",
            reply_markup=create_keyboard(notes_menu_keyboard))
        return VIEW_NOTES

async def add_note(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = str(update.message.from_user.id)
    category = context.user_data.get('category', '')
    note_text = update.message.text
    current_date = datetime.now().strftime("%d.%m.%Y %H:%M")
    
    notes = load_notes()
    if user_id not in notes:
        notes[user_id] = {}
    if category not in notes[user_id]:
        notes[user_id][category] = {}
    
    note_id = str(len(notes[user_id][category]) + 1)  # Сначала +1, потом преобразование в строку
    
    notes[user_id][category][note_id] = {
        'text': note_text,
        'date': current_date
    }
    
    save_notes(notes)
    
    await update.message.reply_text(
        f"Заметка добавлена!\nДата: {current_date}",
        reply_markup=create_keyboard(notes_menu_keyboard))
    return VIEW_NOTES

async def edit_note_choose(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        note_num = int(update.message.text) - 1
        user_notes = context.user_data['notes']
        note_ids = list(user_notes.keys())
        
        if 0 <= note_num < len(note_ids):
            note_id = note_ids[note_num]
            context.user_data['edit_note_id'] = note_id
            await update.message.reply_text(
                f"Текущий текст заметки:\n{user_notes[note_id]['text']}\n\nВведите новый текст:",
                reply_markup=ReplyKeyboardRemove())
            return EDIT_NOTE
        else:
            await update.message.reply_text(
                "Неверный номер заметки. Попробуйте еще раз",
                reply_markup=ReplyKeyboardRemove())
            return EDIT_NOTE_CHOOSE
    except ValueError:
        await update.message.reply_text(
            "Пожалуйста, введите номер заметки",
            reply_markup=ReplyKeyboardRemove())
        return EDIT_NOTE_CHOOSE

async def edit_note(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = str(update.message.from_user.id)
    category = context.user_data.get('category', '')
    note_id = context.user_data.get('edit_note_id')
    new_text = update.message.text
    
    notes = load_notes()
    if user_id in notes and category in notes[user_id] and note_id in notes[user_id][category]:
        notes[user_id][category][note_id]['text'] = new_text
        notes[user_id][category][note_id]['date'] = datetime.now().strftime("%d.%m.%Y %H:%M")
        save_notes(notes)
        
        await update.message.reply_text(
            "Заметка успешно обновлена!",
            reply_markup=create_keyboard(notes_menu_keyboard))
    else:
        await update.message.reply_text(
            "Ошибка при редактировании заметки.",
            reply_markup=create_keyboard(notes_menu_keyboard))
    
    return VIEW_NOTES

async def delete_note(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        note_num = int(update.message.text) - 1
        user_id = str(update.message.from_user.id)
        category = context.user_data.get('category', '')
        user_notes = context.user_data['notes']
        note_ids = list(user_notes.keys())
        
        if 0 <= note_num < len(note_ids):
            note_id = note_ids[note_num]
            
            notes = load_notes()
            if user_id in notes and category in notes[user_id] and note_id in notes[user_id][category]:
                del notes[user_id][category][note_id]
                save_notes(notes)
                
                await update.message.reply_text(
                    "Заметка успешно удалена!",
                    reply_markup=create_keyboard(notes_menu_keyboard))
            else:
                await update.message.reply_text(
                    "Ошибка при удалении заметки.",
                    reply_markup=create_keyboard(notes_menu_keyboard))
        else:
            await update.message.reply_text(
                "Неверный номер заметки.",
                reply_markup=create_keyboard(notes_menu_keyboard))
    except ValueError:
        await update.message.reply_text(
            "Пожалуйста, введите номер заметки:",
            reply_markup=create_keyboard(notes_menu_keyboard))
    
    return VIEW_NOTES

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "До свидания! Нажмите /start, чтобы начать заново.",
        reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main() -> None:
    # Создаем ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MAIN_MENU: [
                MessageHandler(filters.Regex("^(Фильмы|Сериалы|Книги)$"), main_menu)
            ],
            FILMS_MENU: [
                MessageHandler(filters.Regex("^(Список фильмов|Рекомендации|Фильтр|Избранное|Заметки|Назад)$"), films_menu)
            ],
            SERIES_MENU: [
                MessageHandler(filters.Regex("^(Список сериалов|Рекомендации|Фильтр|Избранное|Заметки|Назад)$"), series_menu)
            ],
            BOOKS_MENU: [
                MessageHandler(filters.Regex("^(Список книг|Рекомендации|Фильтр|Избранное|Заметки|Назад)$"), books_menu)
            ],
            VIEW_NOTES: [
                MessageHandler(filters.Regex("^(Просмотреть заметки|Добавить заметку|Редактировать заметку|Удалить заметку|Назад)$"), view_notes)
            ],
            ADD_NOTE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_note)
            ],
            EDIT_NOTE_CHOOSE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_note_choose)
            ],
            EDIT_NOTE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_note)
            ],
            DELETE_NOTE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, delete_note)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)

    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    main()
