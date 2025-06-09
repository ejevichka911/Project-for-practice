from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# Определяем состояния для ConversationHandler
MAIN_MENU, FILMS_MENU = range(2)

# Токен бота 
application = Application.builder().token("TOKEN").build()

# Текст сообщений
WELCOME_TEXT = """
Привет! 👋 Я твой помощник в мире развлечений. 
Я могу помочь тебе с фильмами, сериалами и книгами. 
Выбери категорию ниже и начнем! 🎬📺📚
"""

# Клавиатура
main_menu_keyboard = [
    ["Фильмы", "Сериалы"],
    ["Книги"]
]

films_menu_keyboard = [
    ["Список фильмов", "Рекомендации"],
    ["Фильтр", "Избранное"],
    ["Заметки", "Назад"]
]

def create_keyboard(keyboard):
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

# Обработчики команд и сообщений
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
            "Выберите действие с фильмами:",
            reply_markup=create_keyboard(films_menu_keyboard)
        )
        return FILMS_MENU
    elif text in ["Сериалы", "Книги"]:
        await update.message.reply_text(
            f"Вы выбрали: {text}. Этот функционал еще в разработке.",
            reply_markup=create_keyboard(main_menu_keyboard)
        ) 
        return MAIN_MENU
    else:
        await update.message.reply_text(
            "Пожалуйста, используйте кнопки для навигации.",
            reply_markup=create_keyboard(main_menu_keyboard))
        return MAIN_MENU

async def films_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if text == "Назад":
        await update.message.reply_text(
            "Главное меню:",
            reply_markup=create_keyboard(main_menu_keyboard))
        return MAIN_MENU
    else:
        await update.message.reply_text(
            f"Вы выбрали: {text}. Этот функционал еще в разработке.",
            reply_markup=create_keyboard(films_menu_keyboard))
        return FILMS_MENU

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
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)

    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    main()
