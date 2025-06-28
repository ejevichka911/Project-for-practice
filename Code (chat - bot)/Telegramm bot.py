from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler
)
from datetime import datetime
import json
import os
from content_forwarder import ContentForwarder

# Обновляем список состояний
(
    MAIN_MENU, FILMS_MENU, SERIES_MENU, BOOKS_MENU,
    VIEW_NOTES, ADD_NOTE, EDIT_NOTE_CHOOSE, EDIT_NOTE, DELETE_NOTE,
    FILTER_MENU, FILTER_SELECTION, SERIES_FILTER_MENU, SERIES_FILTER_SELECTION,
    BOOKS_FILTER_MENU, BOOKS_FILTER_SELECTION,
    VIEW_CONTENT_LIST, VIEW_CONTENT_DETAILS, VIEW_FAVORITES, DELETE_FAVORITE
) = range(19)

# Токен бота
TOKEN = "..."
application = Application.builder().token(TOKEN).build()

#Группа в тг
GROUP_CHAT_ID = -1002634234444

# Файл для хранения заметок
NOTES_FILE = "notes.json"

# Пример данных для фильтрации
GENRES = ["Комедия", "Драма", "Боевик", "Фантастика", "Ужасы", "Мультфильм"]
COUNTRIES = ["Россия", "США", "Франция", "Корея", "Великобритания"]
LANGUAGES = ["Русский", "Английский", "Французский", "Корейский"]
RATINGS = ["Высокий (8+)", "Средний (5-7)", "Низкий (до 5)"]
YEARS = ["2020-2023", "2010-2019", "2000-2009", "1990-1999"]
AGES = ["0+", "6+", "12+", "16+", "18+"]

# Добавляем параметры для фильтрации книг
BOOK_GENRES = ["Фантастика", "Фэнтези", "Детектив", "Роман", "Ужасы", "Научная литература"]
BOOK_COUNTRIES = COUNTRIES  # Используем те же страны, что и для фильмов
BOOK_LANGUAGES = LANGUAGES  # Используем те же языки, что и для фильмов
BOOK_RATINGS = RATINGS  # Используем те же рейтинги, что и для фильмов
BOOK_YEARS = YEARS  # Используем те же годы, что и для фильмов
BOOK_AGES = AGES  # Используем те же возрастные ограничения
BOOK_SERIES = ["Да", "Нет"]
BOOK_PUBLISHERS = ["Эксмо", "АСТ", "Питер", "Манн, Иванов и Фербер", "Дрофа"]

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

HELP_TEXT = """
📌 Доступные команды
/start - Начать работу с ботом
/help - Показать это сообщение

🎬 Основные функции
- Поиск фильмов, сериалов и книг
- Фильтрация по различным параметрам
- Добавление в избранное
- Создание заметок о просмотренном/прочитанном

📌 Управление
Используйте кнопки меню для навигации. 
Для возврата в предыдущее меню нажмите "Назад".
"""

# Клавиатуры
main_menu_keyboard = [["Старт", "Помощь"], ["Фильмы", "Сериалы"], ["Книги"]]

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

# Обновляем функцию show_filter_options для разных категорий
async def show_filter_options(update: Update, context: ContextTypes.DEFAULT_TYPE, category: str = 'films'):
    if category == 'films':
        keyboard = [
            [InlineKeyboardButton("По жанру", callback_data='filter_genre')],
            [InlineKeyboardButton("По стране", callback_data='filter_country')],
            [InlineKeyboardButton("По языку", callback_data='filter_language')],
            [InlineKeyboardButton("По рейтингу", callback_data='filter_rating')],
            [InlineKeyboardButton("По году", callback_data='filter_year')],
            [InlineKeyboardButton("По возрасту", callback_data='filter_age')],
            [InlineKeyboardButton("Применить фильтры", callback_data='apply_filters')],
            [InlineKeyboardButton("Сбросить фильтры", callback_data='reset_filters')],
            [InlineKeyboardButton("Назад", callback_data='back_to_films')]
        ]
    elif category == 'series':
        keyboard = [
            [InlineKeyboardButton("По жанру", callback_data='series_filter_genre')],
            [InlineKeyboardButton("По стране", callback_data='series_filter_country')],
            [InlineKeyboardButton("По языку", callback_data='series_filter_language')],
            [InlineKeyboardButton("По рейтингу", callback_data='series_filter_rating')],
            [InlineKeyboardButton("По году", callback_data='series_filter_year')],
            [InlineKeyboardButton("По возрасту", callback_data='series_filter_age')],
            [InlineKeyboardButton("Применить фильтры", callback_data='series_apply_filters')],
            [InlineKeyboardButton("Сбросить фильтры", callback_data='series_reset_filters')],
            [InlineKeyboardButton("Назад", callback_data='back_to_series')]
        ]
    elif category == 'books':
        keyboard = [
            [InlineKeyboardButton("По жанру", callback_data='books_filter_genre')],
            [InlineKeyboardButton("По стране", callback_data='books_filter_country')],
            [InlineKeyboardButton("По языку", callback_data='books_filter_language')],
            [InlineKeyboardButton("По рейтингу", callback_data='books_filter_rating')],
            [InlineKeyboardButton("По году", callback_data='books_filter_year')],
            [InlineKeyboardButton("По возрасту", callback_data='books_filter_age')],
            [InlineKeyboardButton("По серии", callback_data='books_filter_series')],
            [InlineKeyboardButton("По издательству", callback_data='books_filter_publisher')],
            [InlineKeyboardButton("Применить фильтры", callback_data='books_apply_filters')],
            [InlineKeyboardButton("Сбросить фильтры", callback_data='books_reset_filters')],
            [InlineKeyboardButton("Назад", callback_data='back_to_books')]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Формируем текст с текущими фильтрами
    filters = context.user_data.get('filters', {})
    filter_text = "Текущие фильтры:\n" if filters else "Фильтры не выбраны\n"
    for key, value in filters.items():
        filter_text += f"- {key}: {value}\n"
    
    # Определяем, откуда пришел запрос - из сообщения или callback
    if update.callback_query:
        await update.callback_query.edit_message_text(
            f"{filter_text}\nВыберите параметр для фильтрации:",
            reply_markup=reply_markup)
    else:
        await update.message.reply_text(
            f"{filter_text}\nВыберите параметр для фильтрации:",
            reply_markup=reply_markup)

async def handle_filter_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    data = query.data
    filters = context.user_data.get('filters', {})
    
    if data == 'apply_filters':
        if not filters:
            await query.edit_message_text(
                "Вы не выбрали ни одного фильтра!",
                reply_markup=None)
            await show_filter_options(update, context)
            return FILTER_MENU
        
        # Здесь должна быть ваша логика фильтрации
        filtered_movies = apply_filters(filters)
        
        if not filtered_movies:
            await query.edit_message_text(
                "По вашим критериям ничего не найдено.",
                reply_markup=None)
        else:
            movies_list = "\n".join(f"{i+1}. {movie['title']} ({movie['year']})" 
                          for i, movie in enumerate(filtered_movies[:10]))
            await query.edit_message_text(
                f"Найдено фильмов: {len(filtered_movies)}\n\n{movies_list}",
                reply_markup=None)
        
        await query.message.reply_text(
            "Меню фильмов",
            reply_markup=create_keyboard(films_menu_keyboard))
        return FILMS_MENU
    
    elif data == 'reset_filters':
        context.user_data['filters'] = {}
        await query.edit_message_text(
            "Все фильтры сброшены!",
            reply_markup=None)
        await show_filter_options(update, context)
        return FILTER_MENU
    
    elif data == 'back_to_films':
        await query.edit_message_text(
            "Меню фильмов",
            reply_markup=None)
        await query.message.reply_text(
            "Меню фильмов",
            reply_markup=create_keyboard(films_menu_keyboard))
        return FILMS_MENU
    
    elif data == 'back_to_filters':
        await show_filter_options(update, context)
        return FILTER_MENU
    
    else:
        # Показываем варианты для выбранного фильтра
        filter_type = data.split('_')[1]
        context.user_data['current_filter'] = filter_type
        
        if filter_type == 'genre':
            options = GENRES
        elif filter_type == 'country':
            options = COUNTRIES
        elif filter_type == 'language':
            options = LANGUAGES
        elif filter_type == 'rating':
            options = RATINGS
        elif filter_type == 'year':
            options = YEARS
        elif filter_type == 'age':
            options = AGES
        
        keyboard = [[InlineKeyboardButton(opt, callback_data=f'option_{opt}')] for opt in options]
        keyboard.append([InlineKeyboardButton("Назад", callback_data='back_to_filters')])
        
        await query.edit_message_text(
            f"Выберите {filter_type}:",
            reply_markup=InlineKeyboardMarkup(keyboard))
        return FILTER_SELECTION

async def handle_filter_option(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data == 'back_to_filters':
        await show_filter_options(update, context)
        return FILTER_MENU
    
    selected_option = data.split('_', 1)[1]
    filter_type = context.user_data['current_filter']
    context.user_data.setdefault('filters', {})[filter_type] = selected_option
    
    await query.edit_message_text(
        f"Выбран {filter_type}: {selected_option}",
        reply_markup=None)
    await show_filter_options(update, context)
    return FILTER_MENU

# Добавляем обработчики для фильтрации сериалов
async def handle_series_filter_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    data = query.data
    filters = context.user_data.get('filters', {})
    
    if data == 'series_apply_filters':
        if not filters:
            await query.edit_message_text(
                "Вы не выбрали ни одного фильтра!",
                reply_markup=None)
            await show_filter_options(update, context, 'series')
            return SERIES_FILTER_MENU
        
        filtered_series = apply_series_filters(filters)
        
        if not filtered_series:
            await query.edit_message_text(
                "По вашим критериям ничего не найдено.",
                reply_markup=None)
        else:
            series_list = "\n".join(f"{i+1}. {series['title']} ({series['year']})" 
                          for i, series in enumerate(filtered_series[:10]))
            await query.edit_message_text(
                f"Найдено сериалов: {len(filtered_series)}\n\n{series_list}",
                reply_markup=None)
        
        await query.message.reply_text(
            "Меню сериалов",
            reply_markup=create_keyboard(series_menu_keyboard))
        return SERIES_MENU
    
    elif data == 'series_reset_filters':
        context.user_data['filters'] = {}
        await query.edit_message_text(
            "Все фильтры сброшены!",
            reply_markup=None)
        await show_filter_options(update, context, 'series')
        return SERIES_FILTER_MENU
    
    elif data == 'back_to_series':
        await query.edit_message_text(
            "Меню сериалов",
            reply_markup=None)
        await query.message.reply_text(
            "Меню сериалов",
            reply_markup=create_keyboard(series_menu_keyboard))
        return SERIES_MENU
    
    elif data == 'back_to_filters':
        await show_filter_options(update, context, 'series')
        return SERIES_FILTER_MENU
    
    else:
        filter_type = data.split('_')[2]
        context.user_data['current_filter'] = filter_type
        
        if filter_type == 'genre':
            options = GENRES
        elif filter_type == 'country':
            options = COUNTRIES
        elif filter_type == 'language':
            options = LANGUAGES
        elif filter_type == 'rating':
            options = RATINGS
        elif filter_type == 'year':
            options = YEARS
        elif filter_type == 'age':
            options = AGES
        
        keyboard = [[InlineKeyboardButton(opt, callback_data=f'series_option_{opt}')] for opt in options]
        keyboard.append([InlineKeyboardButton("Назад", callback_data='back_to_filters')])
        
        await query.edit_message_text(
            f"Выберите {filter_type}:",
            reply_markup=InlineKeyboardMarkup(keyboard))
        return SERIES_FILTER_SELECTION

async def handle_series_filter_option(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data == 'back_to_filters':
        await show_filter_options(update, context, 'series')
        return SERIES_FILTER_MENU
    
    selected_option = data.split('_', 2)[2]
    filter_type = context.user_data['current_filter']
    context.user_data.setdefault('filters', {})[filter_type] = selected_option
    
    await query.edit_message_text(
        f"Выбран {filter_type}: {selected_option}",
        reply_markup=None)
    await show_filter_options(update, context, 'series')
    return SERIES_FILTER_MENU

# Добавляем обработчики для фильтрации книг
async def handle_books_filter_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    data = query.data
    filters = context.user_data.get('filters', {})
    
    if data == 'books_apply_filters':
        if not filters:
            await query.edit_message_text(
                "Вы не выбрали ни одного фильтра!",
                reply_markup=None)
            await show_filter_options(update, context, 'books')
            return BOOKS_FILTER_MENU
        
        filtered_books = apply_books_filters(filters)
        
        if not filtered_books:
            await query.edit_message_text(
                "По вашим критериям ничего не найдено.",
                reply_markup=None)
        else:
            books_list = "\n".join(f"{i+1}. {book['title']} ({book['author']}, {book['year']})" 
                          for i, book in enumerate(filtered_books[:10]))
            await query.edit_message_text(
                f"Найдено книг: {len(filtered_books)}\n\n{books_list}",
                reply_markup=None)
        
        await query.message.reply_text(
            "Меню книг",
            reply_markup=create_keyboard(books_menu_keyboard))
        return BOOKS_MENU
    
    elif data == 'books_reset_filters':
        context.user_data['filters'] = {}
        await query.edit_message_text(
            "Все фильтры сброшены!",
            reply_markup=None)
        await show_filter_options(update, context, 'books')
        return BOOKS_FILTER_MENU
    
    elif data == 'back_to_books':
        await query.edit_message_text(
            "Меню книг",
            reply_markup=None)
        await query.message.reply_text(
            "Меню книг",
            reply_markup=create_keyboard(books_menu_keyboard))
        return BOOKS_MENU
    
    elif data == 'back_to_filters':
        await show_filter_options(update, context, 'books')
        return BOOKS_FILTER_MENU
    
    else:
        filter_type = data.split('_')[2]
        context.user_data['current_filter'] = filter_type
        
        if filter_type == 'genre':
            options = BOOK_GENRES
        elif filter_type == 'country':
            options = BOOK_COUNTRIES
        elif filter_type == 'language':
            options = BOOK_LANGUAGES
        elif filter_type == 'rating':
            options = BOOK_RATINGS
        elif filter_type == 'year':
            options = BOOK_YEARS
        elif filter_type == 'age':
            options = BOOK_AGES
        elif filter_type == 'series':
            options = BOOK_SERIES
        elif filter_type == 'publisher':
            options = BOOK_PUBLISHERS
        
        keyboard = [[InlineKeyboardButton(opt, callback_data=f'books_option_{opt}')] for opt in options]
        keyboard.append([InlineKeyboardButton("Назад", callback_data='back_to_filters')])
        
        await query.edit_message_text(
            f"Выберите {filter_type}:",
            reply_markup=InlineKeyboardMarkup(keyboard))
        return BOOKS_FILTER_SELECTION

async def handle_books_filter_option(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data == 'back_to_filters':
        await show_filter_options(update, context, 'books')
        return BOOKS_FILTER_MENU
    
    selected_option = data.split('_', 2)[2]
    filter_type = context.user_data['current_filter']
    context.user_data.setdefault('filters', {})[filter_type] = selected_option
    
    await query.edit_message_text(
        f"Выбран {filter_type}: {selected_option}",
        reply_markup=None)
    await show_filter_options(update, context, 'books')
    return BOOKS_FILTER_MENU

# Добавим обработчики для избранного
async def show_favorites(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Показывает список избранного пользователя"""
    forwarder = context.bot_data.get('forwarder')
    if not forwarder:
        await update.message.reply_text("Ошибка: модуль пересылки не инициализирован")
        return
    
    user_id = str(update.message.from_user.id if update.message else update.callback_query.from_user.id)
    favorites = forwarder.favorites.get(user_id, {})
    
    if not any(favorites.values()):
        if update.message:
            await update.message.reply_text(
                "У вас пока нет избранного.",
                reply_markup=create_keyboard(films_menu_keyboard if context.user_data.get('current_category') == 'films' 
                                          else series_menu_keyboard if context.user_data.get('current_category') == 'series'
                                          else books_menu_keyboard)
            )
        else:
            await update.callback_query.edit_message_text(
                "У вас пока нет избранного.",
                reply_markup=None
            )
            await update.callback_query.message.reply_text(
                "Меню",
                reply_markup=create_keyboard(films_menu_keyboard if context.user_data.get('current_category') == 'films' 
                                          else series_menu_keyboard if context.user_data.get('current_category') == 'series'
                                          else books_menu_keyboard)
            )
        return FILMS_MENU if context.user_data.get('current_category') == 'films' else SERIES_MENU if context.user_data.get('current_category') == 'series' else BOOKS_MENU
    
    keyboard = []
    for content_type, items in favorites.items():
        if not items:
            continue
            
        for item in items:
            # Проверяем, существует ли контент в базе
            if item in forwarder.content_db.get(content_type, {}):
                keyboard.append([InlineKeyboardButton(
                    f"{'🎬' if content_type == 'films' else '📺' if content_type == 'series' else '📚'} {item}",
                    callback_data=f"view_{content_type}_{item}"
                )])
    
    if not keyboard:
        if update.message:
            await update.message.reply_text(
                "У вас пока нет избранного.",
                reply_markup=create_keyboard(films_menu_keyboard if context.user_data.get('current_category') == 'films' 
                                          else series_menu_keyboard if context.user_data.get('current_category') == 'series'
                                          else books_menu_keyboard)
            )
        else:
            await update.callback_query.edit_message_text(
                "У вас пока нет избранного.",
                reply_markup=None
            )
            await update.callback_query.message.reply_text(
                "Меню",
                reply_markup=create_keyboard(films_menu_keyboard if context.user_data.get('current_category') == 'films' 
                                          else series_menu_keyboard if context.user_data.get('current_category') == 'series'
                                          else books_menu_keyboard)
            )
        return FILMS_MENU if context.user_data.get('current_category') == 'films' else SERIES_MENU if context.user_data.get('current_category') == 'series' else BOOKS_MENU
    
    keyboard.append([InlineKeyboardButton("🗑 Удалить из избранного", callback_data="delete_favorites")])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_from_favorites")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(
            "📌 Ваше избранное:",
            reply_markup=reply_markup
        )
    else:
        await update.callback_query.edit_message_text(
            "📌 Ваше избранное:",
            reply_markup=reply_markup
        )
    return VIEW_FAVORITES

async def handle_favorites_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает callback'и из меню избранного"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "back_from_favorites":
        await query.edit_message_text("Меню")
        current_category = context.user_data.get('current_category', 'films')
        if current_category == 'films':
            await query.message.reply_text(
                "Меню фильмов",
                reply_markup=create_keyboard(films_menu_keyboard))
            return FILMS_MENU
        elif current_category == 'series':
            await query.message.reply_text(
                "Меню сериалов",
                reply_markup=create_keyboard(series_menu_keyboard))
            return SERIES_MENU
        else:
            await query.message.reply_text(
                "Меню книг",
                reply_markup=create_keyboard(books_menu_keyboard))
            return BOOKS_MENU
    
    elif data == "delete_favorites":
        forwarder = context.bot_data.get('forwarder')
        user_id = str(query.from_user.id)
        favorites = forwarder.favorites.get(user_id, {})
        
        keyboard = []
        for content_type, items in favorites.items():
            if not items:
                continue
                
            for item in items:
                if item in forwarder.content_db.get(content_type, {}):
                    keyboard.append([InlineKeyboardButton(
                        f"❌ {item}",
                        callback_data=f"remove_{content_type}_{item}"
                    )])
        
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_favorites")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "Выберите что удалить из избранного:",
            reply_markup=reply_markup
        )
        return DELETE_FAVORITE
    
    elif data.startswith("remove_"):
        _, content_type, content_name = data.split("_", 2)
        forwarder = context.bot_data.get('forwarder')
        user_id = str(query.from_user.id)
        
        if user_id in forwarder.favorites and content_type in forwarder.favorites[user_id]:
            if content_name in forwarder.favorites[user_id][content_type]:
                forwarder.favorites[user_id][content_type].remove(content_name)
                forwarder.save_favorites()
                
                # Получаем текущее сообщение и его клавиатуру
                message = query.message
                reply_markup = message.reply_markup
                
                # Обновляем клавиатуру, удаляя кнопку с удаленным элементом
                new_keyboard = []
                for row in reply_markup.inline_keyboard:
                    # Пропускаем строку с кнопкой, соответствующей удаленному элементу
                    if not (len(row) == 1 and row[0].callback_data == f"remove_{content_type}_{content_name}"):
                        new_keyboard.append(row)
                
                # Если после удаления не осталось элементов, показываем сообщение
                if not any(forwarder.favorites[user_id].values()):
                    await query.edit_message_text(
                        "Ваше избранное теперь пусто",
                        reply_markup=None
                    )
                    current_category = context.user_data.get('current_category', 'films')
                    if current_category == 'films':
                        await query.message.reply_text(
                            "Меню фильмов",
                            reply_markup=create_keyboard(films_menu_keyboard))
                        return FILMS_MENU
                    elif current_category == 'series':
                        await query.message.reply_text(
                            "Меню сериалов",
                            reply_markup=create_keyboard(series_menu_keyboard))
                        return SERIES_MENU
                    else:
                        await query.message.reply_text(
                            "Меню книг",
                            reply_markup=create_keyboard(books_menu_keyboard))
                        return BOOKS_MENU
                else:
                    # Обновляем сообщение с новой клавиатурой
                    await query.edit_message_text(
                        "✅ Удалено! Выберите что еще удалить:",
                        reply_markup=InlineKeyboardMarkup(new_keyboard)
                    )
                return DELETE_FAVORITE
    
    elif data == "back_to_favorites":
        return await show_favorites(update, context)
    
    elif data.startswith("view_"):
        return await handle_content_list_callback(update, context)
    
    return VIEW_FAVORITES

# Добавьте новые обработчики для работы с контентом
async def show_content_list(update: Update, context: ContextTypes.DEFAULT_TYPE, content_type: str):
    """Показывает список доступного контента"""
    forwarder = context.bot_data.get('forwarder')
    if not forwarder:
        await update.message.reply_text("Ошибка: модуль пересылки не инициализирован")
        return
    
    content_db = forwarder.content_db.get(content_type, {})
    if not content_db:
        await update.message.reply_text(f"В базе пока нет {content_type}.")
        return
    
    # Создаем клавиатуру с кнопками для каждого элемента контента
    keyboard = []
    items_per_page = 5
    page = int(context.args[0]) if context.args and context.args[0].isdigit() else 0
    
    items = list(content_db.items())
    total_pages = (len(items) + items_per_page - 1) // items_per_page
    
    for item in items[page*items_per_page : (page+1)*items_per_page]:
        title = item[0]
        metadata = item[1]['metadata']
        year = metadata.get('year', '')
        button_text = f"{title} ({year})" if year else title
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"view_{content_type}_{title}")])
    
    # Добавляем кнопки навигации
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"list_{content_type}_{page-1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("Вперед ➡️", callback_data=f"list_{content_type}_{page+1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.append([InlineKeyboardButton("Назад в меню", callback_data=f"back_to_{content_type}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"Доступные {content_type} (страница {page+1}/{total_pages}):",
        reply_markup=reply_markup
    )
    return VIEW_CONTENT_LIST

async def films_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик для списка фильмов"""
    return await show_content_list(update, context, "films")

async def series_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик для списка сериалов"""
    return await show_content_list(update, context, "series")

async def books_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик для списка книг"""
    return await show_content_list(update, context, "books")

async def handle_content_list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик callback'ов для списка контента"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data.startswith("view_"):
        # Пользователь хочет посмотреть детали контента
        _, content_type, content_name = data.split("_", 2)
        forwarder = context.bot_data.get('forwarder')
        content_data = forwarder.content_db[content_type].get(content_name)
        
        if not content_data:
            await query.edit_message_text("❌ Контент не найден")
            return VIEW_CONTENT_LIST
        
        meta = content_data["metadata"]
        caption = f"{content_name}\n"
        
        if content_type == "films":
            caption += f"Год: {meta.get('year', '?')}\nЖанр: {meta.get('genre', '?')}\nСтрана: {meta.get('country', '?')}"
        elif content_type == "series":
            caption += f"Сезон: {meta.get('season', '1')}\nСерия: {meta.get('episode', '1')}\nГод: {meta.get('year', '?')}\nЖанр: {meta.get('genre', '?')}"
        elif content_type == "books":
            caption += f"Автор: {meta.get('author', '?')}\nГод: {meta.get('year', '?')}\nЖанр: {meta.get('genre', '?')}"
        
        # Добавляем кнопку для отправки контента
        keyboard = [
            [InlineKeyboardButton("📩 Получить", callback_data=f"send_{content_type}_{content_name}")],
            [InlineKeyboardButton("🔙 Назад к списку", callback_data=f"list_{content_type}_0")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            caption,
            reply_markup=reply_markup
        )
        return VIEW_CONTENT_DETAILS
    
    elif data.startswith("list_"):
        # Пользователь хочет перейти на другую страницу
        _, content_type, page = data.split("_")
        page = int(page)
        
        forwarder = context.bot_data.get('forwarder')
        content_db = forwarder.content_db.get(content_type, {})
        items_per_page = 5
        total_pages = (len(content_db) + items_per_page - 1) // items_per_page
        
        keyboard = []
        items = list(content_db.items())
        
        for item in items[page*items_per_page : (page+1)*items_per_page]:
            title = item[0]
            metadata = item[1]['metadata']
            year = metadata.get('year', '')
            button_text = f"{title} ({year})" if year else title
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"view_{content_type}_{title}")])
        
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"list_{content_type}_{page-1}"))
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton("Вперед ➡️", callback_data=f"list_{content_type}_{page+1}"))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        keyboard.append([InlineKeyboardButton("Назад в меню", callback_data=f"back_to_{content_type}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"Доступные {content_type} (страница {page+1}/{total_pages}):",
            reply_markup=reply_markup
        )
        return VIEW_CONTENT_LIST
    
    elif data.startswith("back_to_"):
        # Пользователь хочет вернуться в меню
        content_type = data.split("_")[2]
        
        if content_type == "films":
            await query.edit_message_text(
                "Меню фильмов",
                reply_markup=None)
            await query.message.reply_text(
                "Выберите действие с фильмами",
                reply_markup=create_keyboard(films_menu_keyboard))
            return FILMS_MENU
        elif content_type == "series":
            await query.edit_message_text(
                "Меню сериалов",
                reply_markup=None)
            await query.message.reply_text(
                "Выберите действие с сериалами",
                reply_markup=create_keyboard(series_menu_keyboard))
            return SERIES_MENU
        elif content_type == "books":
            await query.edit_message_text(
                "Меню книг",
                reply_markup=None)
            await query.message.reply_text(
                "Выберите действие с книгами",
                reply_markup=create_keyboard(books_menu_keyboard))
            return BOOKS_MENU
    
    return VIEW_CONTENT_LIST


def apply_filters(filters):
    """Ваша функция для фильтрации фильмов"""
    # Здесь должна быть ваша реализация фильтрации
    # Возвращаем список отфильтрованных фильмов
    return []

def apply_series_filters(filters):
    """Функция для фильтрации сериалов"""
    # Здесь должна быть ваша реализация фильтрации
    return []

def apply_books_filters(filters):
    """Функция для фильтрации книг"""
    # Здесь должна быть ваша реализация фильтрации
    return []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Очищаем предыдущее состояние
    context.user_data.clear()

    await update.message.reply_text(
        WELCOME_TEXT,
        reply_markup=create_keyboard(main_menu_keyboard)
    )
    return MAIN_MENU

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if text == "Старт":
        # Вызываем ту же логику, что и для команды /start
        return await start(update, context)
    elif text == "Помощь":
        # Вызываем логику команды /help
        await help_command(update, context)
        return MAIN_MENU
    elif text == "Фильмы":
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

# Обновите обработчики для меню фильмов/сериалов/книг
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
    elif text == "Фильтр":
        context.user_data['filters'] = {}
        context.user_data['current_category'] = 'films'
        await show_filter_options(update, context, 'films')
        return FILTER_MENU
    elif text == "Список фильмов":
        return await films_list(update, context)
    elif text == "Избранное":
        context.user_data['current_category'] = 'films'
        return await show_favorites(update, context)
    else:
        await update.message.reply_text(
            f"Вы выбрали - {text}. Этот функционал еще в разработке.",
            reply_markup=create_keyboard(films_menu_keyboard))
        return FILMS_MENU

# Обновите обработчики для меню фильмов/сериалов/книг
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
    elif text == "Фильтр":
        context.user_data['filters'] = {}
        context.user_data['current_category'] = 'series'
        await show_filter_options(update, context, 'series')
        return SERIES_FILTER_MENU
    elif text == "Список сериалов":
        return await series_list(update, context)
    elif text == "Избранное":
        context.user_data['current_category'] = 'series'
        return await show_favorites(update, context)
    else:
        await update.message.reply_text(
            f"Вы выбрали - {text}. Этот функционал еще в разработке.",
            reply_markup=create_keyboard(series_menu_keyboard))
        return SERIES_MENU

# Обновите обработчики для меню фильмов/сериалов/книг
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
    elif text == "Фильтр":
        context.user_data['filters'] = {}
        context.user_data['current_category'] = 'books'
        await show_filter_options(update, context, 'books')
        return BOOKS_FILTER_MENU
    elif text == "Список книг":
        return await books_list(update, context)
    elif text == "Избранное":
        context.user_data['current_category'] = 'books'
        return await show_favorites(update, context)
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
    
    note_id = str(len(notes[user_id][category]) + 1)
    
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

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет сообщение со списком команд"""
    await update.message.reply_text(HELP_TEXT)

# Обновите функцию main()
def main() -> None:
    # Создаем ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MAIN_MENU: [
                MessageHandler(filters.Regex("^(Старт|Помощь|Фильмы|Сериалы|Книги)$"), main_menu)
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
            FILTER_MENU: [
                CallbackQueryHandler(handle_filter_selection)
            ],
            FILTER_SELECTION: [
                CallbackQueryHandler(handle_filter_option)
            ],
            SERIES_FILTER_MENU: [
                CallbackQueryHandler(handle_series_filter_selection)
            ],
            SERIES_FILTER_SELECTION: [
                CallbackQueryHandler(handle_series_filter_option)
            ],
            BOOKS_FILTER_MENU: [
                CallbackQueryHandler(handle_books_filter_selection)
            ],
            BOOKS_FILTER_SELECTION: [
                CallbackQueryHandler(handle_books_filter_option)
            ],
            VIEW_CONTENT_LIST: [
                CallbackQueryHandler(handle_content_list_callback)
            ],
            VIEW_CONTENT_DETAILS: [
                CallbackQueryHandler(handle_content_list_callback)  # Можно использовать тот же обработчик
            ],
            VIEW_FAVORITES: [
                CallbackQueryHandler(handle_favorites_callback)
            ],
            DELETE_FAVORITE: [
                CallbackQueryHandler(handle_favorites_callback)
            ],
        },
        fallbacks=[
            CommandHandler('start', start), 
            CommandHandler('cancel', cancel)
        ],
        allow_reentry=True
    )
    # Создаем экземпляр ContentForwarder и сохраняем
    forwarder = ContentForwarder(GROUP_CHAT_ID)
    application.bot_data['forwarder'] = forwarder

    # Регистрируем обработчики
    forwarder.register_handlers(application)
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("help", help_command))

    application.run_polling()

if __name__ == '__main__':
    main()
