import re
import json
from pathlib import Path
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    MessageHandler,
    CallbackQueryHandler,
    CommandHandler,
    filters,
    ContextTypes
)
MAIN_MENU = 0

class ContentForwarder:
    def __init__(self, group_chat_id: int):
        self.GROUP_CHAT_ID = group_chat_id
        self.CONTENT_DB_FILE = "content_db.json"
        self.FAVORITES_FILE = "favorites.json"
        self.content_db = self.load_content_db()
        self.favorites = self.load_favorites()
        
        # Добавляем клавиатуру меню
        self.main_menu_keyboard = [["Фильмы", "Сериалы"], ["Книги"]]

        # Добавляем команды для группового использования
        self.group_commands_keyboard = [
            ["/add_film", "/add_series"],
            ["/add_book", "/cancel_add"]
        ]

    def create_group_commands_keyboard(self):
        """Создает клавиатуру с командами для группы"""
        return ReplyKeyboardMarkup(self.group_commands_keyboard, resize_keyboard=True)
    
    def _is_favorite(self, user_id: str, content_type: str, content_name: str) -> bool:
        """Проверяет, есть ли контент в избранном"""
        return (user_id in self.favorites 
                and content_type in self.favorites[user_id] 
                and content_name in self.favorites[user_id][content_type])

    def _create_fav_button(self, user_id: str, content_type: str, content_name: str) -> InlineKeyboardButton:
        """Создает кнопку избранного с актуальным состоянием"""
        is_fav = self._is_favorite(user_id, content_type, content_name)
        return InlineKeyboardButton(
            text="❤️ Убрать из избранного" if is_fav else "❤️ В избранное",
            callback_data=f"unfav_{content_type}_{content_name}" if is_fav else f"fav_{content_type}_{content_name}"
        )

    async def start_group_adding(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик начала добавления в группе"""
        if update.message.chat.id != self.GROUP_CHAT_ID:
            return

        await update.message.reply_text(
            "Выберите тип контента для добавления:",
            reply_markup=self.create_group_commands_keyboard(),
            disable_web_page_preview=True
        )

    async def handle_group_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик групповых команд добавления"""
        if update.message.chat.id != self.GROUP_CHAT_ID:
            return

        command = update.message.text
        if command == "/add_film":
            await self.start_content_adding(update, context, "films")
        elif command == "/add_series":
            await self.start_content_adding(update, context, "series")
        elif command == "/add_book":
            await self.start_content_adding(update, context, "books")
        elif command == "/cancel_add":
            if 'adding_content' in context.user_data:
                del context.user_data['adding_content']
            await update.message.reply_text(
                "Добавление отменено",
                reply_markup=self.create_group_commands_keyboard(),
                disable_web_page_preview=True
            )

    def create_keyboard(self, keyboard):
        """Создает клавиатуру для меню"""
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    def load_content_db(self):
        """Загружает базу данных контента из файла"""
        try:
            if Path(self.CONTENT_DB_FILE).exists():
                with open(self.CONTENT_DB_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Ошибка при загрузке базы данных: {e}")
        
        return {"films": {}, "series": {}, "books": {}}

    def load_favorites(self):
        """Загружает избранное из файла"""
        try:
            if Path(self.FAVORITES_FILE).exists():
                with open(self.FAVORITES_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Ошибка при загрузке избранного: {e}")
        
        return {}

    def save_content_db(self):
        """Сохраняет базу данных контента в файл"""
        try:
            with open(self.CONTENT_DB_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.content_db, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка при сохранении базы данных: {e}")

    def save_favorites(self):
        """Сохраняет избранное в файл"""
        try:
            with open(self.FAVORITES_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.favorites, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка при сохранении избранного: {e}")

    def parse_content(self, content_type: str, text: str) -> dict:
        """Парсинг метаданных из текста сообщения"""
        metadata = {
            "title": "Без названия",
            "description": "Нет описания",
            "link": "Нет ссылки"
        }

        # Общие поля для всех типов контента
        common_fields = {
            "year": "Не указан",
            "rating": "Не указан",
            "country": "Не указан",
            "language": "Не указан",
            "genre": "Не указан",
            "age": "Не указан"
        }

        # Специфичные поля для каждого типа
        type_specific = {
            "films": {
                "duration": "Не указана"
            },
            "series": {
                "season": "1",
                "episode": "1",
                "duration": "Не указана"
            },
            "books": {
                "series": "Нет",
                "publisher": "Не указано",
                "pages": "Не указано"
            }
        }

        metadata.update(common_fields)
        if content_type in type_specific:
            metadata.update(type_specific[content_type])

        lines = [line.strip() for line in text.split('\n') if line.strip()]

        if lines:
            first_line = lines[0].replace("#фильм", "").replace("#сериал", "").replace("#книга", "").strip()
            if first_line:
                lines[0] = first_line
            else:
                lines = lines[1:] if len(lines) > 1 else lines

        for line in lines:
            if line.startswith("Название:"):
                metadata["title"] = line.replace("Название:", "").strip()
            elif line.startswith("Год:"):
                metadata["year"] = line.replace("Год:", "").strip()
            elif line.startswith("Рейтинг:"):
                metadata["rating"] = line.replace("Рейтинг:", "").strip()
            elif line.startswith("Страна:"):
                metadata["country"] = line.replace("Страна:", "").strip()
            elif line.startswith("Язык:"):
                metadata["language"] = line.replace("Язык:", "").strip()
            elif line.startswith("Жанр:"):
                metadata["genre"] = line.replace("Жанр:", "").strip()
            elif line.startswith("Возраст:"):
                metadata["age"] = line.replace("Возраст:", "").strip()
            elif line.startswith("Описание:"):
                metadata["description"] = line.replace("Описание:", "").strip()
            elif line.startswith("Длительность:") and content_type in ["films", "series"]:
                metadata["duration"] = line.replace("Длительность:", "").strip()
            elif line.startswith("Ссылка:") or line.startswith("https://") or line.startswith("http://"):
                metadata["link"] = line.replace("Ссылка:", "").strip()
            elif line.startswith("Сезон:") and content_type == "series":
                metadata["season"] = line.replace("Сезон:", "").strip()
            elif line.startswith("Серия:") and content_type == "series":
                metadata["episode"] = line.replace("Серия:", "").strip()
            elif line.startswith("Серия:") and content_type == "books":
                metadata["series"] = line.replace("Серия:", "").strip()
            elif line.startswith("Издательство:") and content_type == "books":
                metadata["publisher"] = line.replace("Издательство:", "").strip()
            elif line.startswith("Страниц:") and content_type == "books":
                metadata["pages"] = line.replace("Страниц:", "").strip()
            elif not metadata["title"] or metadata["title"] == "Без названия":
                metadata["title"] = line

        return metadata

    async def handle_group_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик сообщений в группе"""
        if update.message.chat.id != self.GROUP_CHAT_ID:
            return

        content_type = None
        if update.message.caption:
            caption = update.message.caption.lower()
            if "#фильм" in caption:
                content_type = "films"
            elif "#сериал" in caption:
                content_type = "series"
            elif "#книга" in caption:
                content_type = "books"

        if not content_type:
            return

        file = update.message.video or update.message.document or update.message.photo
        if not file:
            return

        # Для фото берем последнее (самое высокое качество)
        if update.message.photo:
            file = update.message.photo[-1]

        metadata = self.parse_content(content_type, update.message.caption)
        metadata["title"] = metadata.get("title") or (file.file_name if hasattr(file, 'file_name') else f"Без названия ({file.file_id[:6]})")

        self.content_db[content_type][metadata["title"]] = {
            "file_id": file.file_id,
            "is_video": bool(update.message.video),
            "is_document": bool(update.message.document),
            "is_photo": bool(update.message.photo),
            "message_id": update.message.message_id,
            "metadata": metadata
        }
        
        self.save_content_db()

    async def start_content_adding(self, update: Update, context: ContextTypes.DEFAULT_TYPE, content_type: str):
        """Начинает красивый процесс пошагового добавления контента"""
        content_icons = {
            "films": "🎬",
            "series": "📺", 
            "books": "📚"
        }

        context.user_data['adding_content'] = {
            'type': content_type,
            'step': 0,
            'metadata': {
                "title": "Не указано",
                "description": "Не указано",
                "link": "Нет ссылки",
                "year": "Не указано",
                "rating": "Не указано",
                "country": "Не указано",
                "language": "Не указано",
                "genre": "Не указано",
                "age": "Не указано"
            }
        }

        # Добавляем специфичные поля
        if content_type == "films":
            context.user_data['adding_content']['metadata']['duration'] = "Не указано"
        elif content_type == "series":
            context.user_data['adding_content']['metadata'].update({
                'season': "1",
                'episode': "1",
                'duration': "Не указано"
            })
        elif content_type == "books":
            context.user_data['adding_content']['metadata'].update({
                'series': "Нет",
                'publisher': "Не указано",
                'pages': "Не указано"
            })

        # Красивое приветственное сообщение
        await update.message.reply_text(
            f"""{content_icons[content_type]} <b>Добавление нового {'фильма' if content_type == 'films' else 'сериала' if content_type == 'series' else 'книги'}</b>

            Давайте заполним информацию шаг за шагом. 
            Можете пропустить любой пункт, отправив "-".""",
            parse_mode='HTML',
            reply_markup=ReplyKeyboardRemove(),
            disable_web_page_preview=True
        )
    
        await self.ask_for_next_field(update, context)

    async def ask_for_next_field(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Красиво запрашивает следующее поле"""
        content_type = context.user_data['adding_content']['type']
        step = context.user_data['adding_content']['step']
        metadata = context.user_data['adding_content']['metadata']

        # Поля с эмодзи и описаниями
        fields_order = [
            ('title', "📝 <b>Название:</b>\n(Например: <i>Крепкий орешек</i>)"),
            ('year', "📅 <b>Год выпуска:</b>\n(Например: <i>1988</i>)"),
            ('rating', "⭐ <b>Рейтинг:</b>\n(Например: <i>8.2/10</i> или <i>95%</i>)"),
            ('country', "🌍 <b>Страна:</b>\n(Например: <i>США</i>)"),
            ('language', "🗣 <b>Язык:</b>\n(Например: <i>Русский</i>)"),
            ('genre', "🎭 <b>Жанр:</b>\n(Например: <i>Боевик, Триллер</i>)"),
            ('age', "🔞 <b>Возрастное ограничение:</b>\n(Например: <i>16+</i>)"),
            ('description', "📖 <b>Описание</b>\n(Краткое описание сюжета)")
        ]

        # Специфичные поля для каждого типа
        if content_type == "films":
            fields_order.append(('duration', "⏱ <b>Длительность:</b>\n(В минутах, например: <i>132</i>)"))
        elif content_type == "series":
            fields_order.extend([
                ('season', "📡 <b>Сезон:</b>\n(Номер сезона, например: <i>1</i>)"),
                ('episode', "🎥 <b>Серия:</b>\n(Номер серии, например: <i>5</i>)"),
                ('duration', "⏱ <b>Длительность серии:</b>\n(В минутах, например: <i>45</i>)")
            ])
        elif content_type == "books":
            fields_order.extend([
                ('series', "🔗 <b>Серия книг:</b>\n(Название серии или <i>Нет</i>)"),
                ('publisher', "🏢 <b>Издательство:</b>\n(Например: <i>АСТ</i>)"),
                ('pages', "📄 <b>Количество страниц:</b>\n(Например: <i>320</i>)")
            ])

        if step < len(fields_order):
            field, prompt = fields_order[step]
            context.user_data['adding_content']['current_field'] = field

            # Отправляем красивое сообщение с подсказкой
            await update.message.reply_text(
                prompt,
                parse_mode='HTML'
            )
        else:
            # Все основные поля заполнены, запрашиваем ссылку
            if 'link' not in context.user_data['adding_content']['metadata'] or context.user_data['adding_content']['metadata']['link'] == "Нет ссылки":
                context.user_data['adding_content']['current_field'] = 'link'
                await update.message.reply_text(
                    "🔗 <b>Ссылка на контент:</b>\n(URL или \"-\" чтобы пропустить)",
                    parse_mode='HTML'
                )
            else:
                # Ссылка получена, запрашиваем файл
                summary = self._generate_content_summary(metadata, content_type)
                await update.message.reply_text(
                    f"""✅ <b>Информация сохранена!</b>

    {summary}

    Теперь отправьте файл (видео, документ или фото):""",
                    parse_mode='HTML',
                    disable_web_page_preview=True
                )
                context.user_data['adding_content']['step'] = 'awaiting_file'

    def _generate_content_summary(self, metadata: dict, content_type: str) -> str:
        """Генерирует резюме введенных данных без дублирования названий полей"""
        content_type_name = {
            "films": "Название фильма",
            "series": "Название сериала", 
            "books": "Название книги"
        }[content_type]

        summary = [f"\n📋 <b>{content_type_name}:</b> <i>{metadata['title']}</i>"]

        # Поля с эмодзи (без дублирования названий)
        fields = [
            ('year', '📅 Год:'),
            ('rating', '⭐ Рейтинг:'),
            ('country', '🌍 Страна:'),
            ('language', '🗣 Язык:'),
            ('genre', '🎭 Жанр:'),
            ('age', '🔞 Возраст:'),
            ('duration', '⏱ Длительность:'),
            ('description', '📖 Описание')
        ]

        # Специфичные поля для сериалов
        if content_type == "series":
            fields.insert(6, ('season', '📡 Сезон:'))
            fields.insert(7, ('episode', '🎥 Серия:'))
        # Специфичные поля для книг
        elif content_type == "books":
            fields.extend([
                ('series', '🔗 Серия:'),
                ('publisher', '🏢 Издательство:'),
                ('pages', '📄 Страниц:')
            ])
            fields.remove(('duration', '⏱'))  # Удаляем длительность для книг

        # Формируем строки
        for field, emoji in fields:
            value = metadata.get(field)
            if value and value != "Не указано":
                summary.append(f"{emoji} <i>{value}</i>")

        # Добавляем ссылку в конец, если она есть
        if metadata.get('link') and metadata['link'] != "Нет ссылки":
            summary.append(f"\n🔗 <b>Ссылка:</b> <i>{metadata['link']}</i>")

        return "\n".join(summary)
    
    async def handle_content_field(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает введенное значение поля с красивым подтверждением"""
        if 'adding_content' not in context.user_data:
            return

        current_field = context.user_data['adding_content']['current_field']
        value = update.message.text.strip()

        # Обработка пропуска поля
        if value == "-":
            value = "Нет ссылки" if current_field == "link" else "Не указано"

        # Сохраняем значение
        context.user_data['adding_content']['metadata'][current_field] = value

        # Подтверждение ввода
        field_names = {
            'title': "Название",
            'year': "Год",
            'rating': "Рейтинг",
            'country': "Страна",
            'language': "Язык",
            'genre': "Жанр",
            'age': "Возрастное ограничение",
            'description': "Описание",
            'duration': "Длительность",
            'season': "Сезон",
            'episode': "Серия",
            'series': "Серия книг",
            'publisher': "Издательство",
            'pages': "Количество страниц",
            'link': "Ссылка"  # Добавлено новое поле
        }

        await update.message.reply_text(
            f"✅ <b>{field_names[current_field]}:</b> <i>{value}</i>",
            parse_mode='HTML',
            disable_web_page_preview=True
        )

        # Увеличиваем шаг
        context.user_data['adding_content']['step'] += 1

        # Запрашиваем следующее поле
        await self.ask_for_next_field(update, context)

    async def handle_content_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает файл, отправленный после заполнения метаданных."""
        if ('adding_content' not in context.user_data or 
            context.user_data['adding_content'].get('step') != 'awaiting_file'):
            return  # Не в режиме ожидания файла

        content_type = context.user_data['adding_content']['type']
        metadata = context.user_data['adding_content']['metadata']

        file = None
        if update.message.video:
            file = update.message.video
        elif update.message.document:
            file = update.message.document
        elif update.message.photo:
            file = update.message.photo[-1]  # Берем фото с самым высоким разрешением

        if not file:
            await update.message.reply_text("❌ Пожалуйста, отправьте файл (видео, документ или фото).")
            return

        # Сохраняем в базу данных
        self.content_db[content_type][metadata["title"]] = {
            "file_id": file.file_id,
            "is_video": bool(update.message.video),
            "is_document": bool(update.message.document),
            "is_photo": bool(update.message.photo),
            "message_id": update.message.message_id,
            "metadata": metadata
        }
        self.save_content_db()

        # Отправляем подтверждение
        await update.message.reply_text(
            f"✅ Файл успешно добавлен в базу! Название: {metadata['title']}",
            reply_markup=self.create_keyboard(self.main_menu_keyboard),
            disable_web_page_preview=True
        )

        # Очищаем состояние
        del context.user_data['adding_content']

    async def send_content(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отправка информации о контенте пользователю с интерактивным избранным"""
        query = update.callback_query
        await query.answer()

        try:
            parts = query.data.split("_", 2)
            action = parts[0]
            content_type = parts[1]
            user_id = str(query.from_user.id)

            # Обработка кнопки "Назад к списку"
            if action == "list":
                await self.show_content_list(query, content_type, 0)
                return

            # Остальная логика для других действий
            content_name = parts[2]

            # Обработка добавления/удаления из избранного
            if action in ["fav", "unfav"]:
                # Инициализируем избранное пользователя если нужно
                if user_id not in self.favorites:
                    self.favorites[user_id] = {}
                if content_type not in self.favorites[user_id]:
                    self.favorites[user_id][content_type] = []

                if action == "fav":
                    if content_name not in self.favorites[user_id][content_type]:
                        self.favorites[user_id][content_type].append(content_name)
                        self.save_favorites()
                        await query.answer("✅ Добавлено в избранное")
                    else:
                        await query.answer("⚠️ Уже в избранном")
                else:  # unfav
                    if content_name in self.favorites[user_id][content_type]:
                        self.favorites[user_id][content_type].remove(content_name)
                        self.save_favorites()
                        await query.answer("❌ Удалено из избранного")

                # Обновляем сообщение с новой кнопкой
                return await self._update_content_message(
                    query, content_type, content_name, user_id
                )

            # Остальная логика отображения контента
            content_data = self.content_db[content_type].get(content_name)
            if not content_data:
                await query.edit_message_text("❌ Контент не найден")
                return

            meta = content_data["metadata"]
            caption = self._generate_content_caption(content_type, content_name, meta)

            # Создаем клавиатуру с актуальной кнопкой избранного
            keyboard = self._create_content_keyboard(
                content_type, content_name, user_id
            )

            await query.edit_message_text(
                caption,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML',
                disable_web_page_preview=True
            )

        except Exception as e:
            await query.edit_message_text(f"❌ Ошибка: {str(e)}")

    def _generate_content_caption(self, content_type, content_name, meta):
        """Генерирует описание контента"""
        caption = f"📚 <b>{content_name}</b>\n\n" if content_type == "books" else f"🎬 <b>{content_name}</b>\n\n"

        # Добавляем поля в зависимости от типа контента
        if content_type == "books":
            caption += f"📅 <b>Год выпуска:</b> {meta.get('year', '?')}\n"
            caption += f"🎭 <b>Жанр:</b> {meta.get('genre', '?')}\n"
            caption += f"⭐ <b>Рейтинг:</b> {meta.get('rating', '?')}\n"
            caption += f"🌍 <b>Страна:</b> {meta.get('country', '?')}\n"
            caption += f"🗣 <b>Язык:</b> {meta.get('language', '?')}\n"
            caption += f"📚 <b>Серия:</b> {meta.get('series', 'Нет')}\n"
            caption += f"🏢 <b>Издательство:</b> {meta.get('publisher', 'Не указано')}\n"
            caption += f"🔞 <b>Возраст:</b> {meta.get('age', 'Не указан')}\n"
            caption += f"📖 <b>Страниц:</b> {meta.get('pages', 'Не указано')}\n"
        elif content_type == "films":
            caption += f"📅 <b>Год выпуска:</b> {meta.get('year', '?')}\n"
            caption += f"⭐ <b>Рейтинг:</b> {meta.get('rating', '?')}\n"
            caption += f"🌍 <b>Страна:</b> {meta.get('country', '?')}\n"
            caption += f"🗣 <b>Язык:</b> {meta.get('language', '?')}\n"
            caption += f"🎭 <b>Жанр:</b> {meta.get('genre', '?')}\n"
            caption += f"⏱ <b>Длительность:</b> {meta.get('duration', 'Не указана')}\n"
        elif content_type == "series":
            caption += f"📅 <b>Год выпуска:</b> {meta.get('year', '?')}\n"
            caption += f"⭐ <b>Рейтинг:</b> {meta.get('rating', '?')}\n"
            caption += f"🌍 <b>Страна:</b> {meta.get('country', '?')}\n"
            caption += f"🗣 <b>Язык:</b> {meta.get('language', '?')}\n"
            caption += f"🎭 <b>Жанр:</b> {meta.get('genre', '?')}\n"
            caption += f"📺 <b>Сезон:</b> {meta.get('season', '1')}\n"
            caption += f"🎥 <b>Серия:</b> {meta.get('episode', '1')}\n"
            caption += f"⏱ <b>Длительность:</b> {meta.get('duration', 'Не указана')}\n"

        caption += f"\n📝 <b>Описание</b>\n{meta.get('description', 'Нет описания')}"

        if meta.get('link'):
            caption += f"\n\n🔗 <b>Ссылка:</b> {meta['link']}"

        return caption

    def _create_content_keyboard(self, content_type, content_name, user_id):
        """Создает клавиатуру для сообщения с контентом"""
        is_favorite = (user_id in self.favorites and 
                      content_type in self.favorites[user_id] and 
                      content_name in self.favorites[user_id][content_type])

        fav_button = (
            InlineKeyboardButton(
                "❤️ Убрать из избранного", 
                callback_data=f"unfav_{content_type}_{content_name}"
            ) if is_favorite else
            InlineKeyboardButton(
                "❤️ В избранное", 
                callback_data=f"fav_{content_type}_{content_name}"
            )
        )

        return [
            [InlineKeyboardButton("📩 Получить", callback_data=f"get_{content_type}_{content_name}")],
            [fav_button],
            [InlineKeyboardButton("🔙 Назад к списку", callback_data=f"list_{content_type}")]
        ]

    async def _update_content_message(self, query, content_type, content_name, user_id):
        """Обновляет сообщение с контентом после изменения избранного"""
        content_data = self.content_db[content_type].get(content_name)
        if not content_data:
            await query.edit_message_text("❌ Контент не найден")
            return

        meta = content_data["metadata"]
        caption = self._generate_content_caption(content_type, content_name, meta)
        keyboard = self._create_content_keyboard(content_type, content_name, user_id)

        await query.edit_message_text(
            caption,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML',
            disable_web_page_preview=True
        )

    async def show_content_list(self, query, content_type: str, page: int):
        """Показывает список контента определенного типа"""
        content_type_name = {
            "films": "Фильмы",
            "series": "Сериалы",
            "books": "Книги"
        }.get(content_type, "Контент")

        items = list(self.content_db[content_type].keys())

        if not items:
            await query.edit_message_text(f"❌ Нет {content_type_name.lower()} в базе")
            return

        # Создаем клавиатуру с элементами
        keyboard = []
        for item in items:
            keyboard.append([InlineKeyboardButton(item, callback_data=f"view_{content_type}_{item}")])

        # Добавляем кнопку "Назад" в главное меню
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")])

        await query.edit_message_text(
            f"📋 <b>{content_type_name}:</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )

    async def get_content(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отправка медиафайла пользователю"""
        query = update.callback_query
        await query.answer()

        try:
            _, content_type, content_name = query.data.split("_", 2)
            content_data = self.content_db[content_type].get(content_name)
            user_id = str(query.from_user.id)

            if not content_data:
                await query.edit_message_text("❌ Контент не найден")
                return

            # Отправляем файл
            await context.bot.send_chat_action(query.message.chat_id, "upload_video")
            file_id = content_data["file_id"]

            try:
                await context.bot.send_video(
                    chat_id=query.message.chat_id,
                    video=file_id,
                    supports_streaming=True,
                    caption=f"{'🎬' if content_type == 'films' else '📺'} {content_name}",
                    read_timeout=60,
                    write_timeout=60
                )
            except Exception:
                await context.bot.send_document(
                    chat_id=query.message.chat_id,
                    document=file_id,
                    caption=f"{'🎬' if content_type == 'films' else '📺'} {content_name}",
                    read_timeout=60,
                    write_timeout=60
                )

            # Обновляем оригинальное сообщение
            current_text = query.message.text
            new_text = f"✅ {content_name} отправлен"

            if current_text != new_text:
                await query.edit_message_text(
                    new_text
                )

        except Exception as e:
            await query.edit_message_text(f"❌ Ошибка: {str(e)}")

    async def show_favorites(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показывает избранное пользователя"""
        user_id = str(update.message.from_user.id)
        
        if user_id not in self.favorites or not any(self.favorites[user_id].values()):
            await update.message.reply_text("У вас пока нет избранного.")
            return
        
        favorites_text = "📌 <b>Ваше избранное:</b>\n\n"
        
        for content_type, items in self.favorites[user_id].items():
            if not items:
                continue
                
            favorites_text += f"<b>{content_type.capitalize()}:</b>\n"
            for i, item in enumerate(items, 1):
                favorites_text += f"{i}. {item}\n"
            favorites_text += "\n"
        
        await update.message.reply_text(favorites_text, parse_mode='HTML', disable_web_page_preview=True)

    async def back_to_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Возвращает в главное меню"""
        query = update.callback_query
        await query.answer()

        await query.edit_message_text(
            "Выберите тип контента:",
            reply_markup=ReplyKeyboardMarkup(self.main_menu_keyboard, resize_keyboard=True)
        )
    
    async def handle_group_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обрабатывает текстовые сообщения в группе при добавлении контента"""
        if 'adding_content' in context.user_data:
            # Если идет процесс добавления контента
            if context.user_data['adding_content']['step'] == 'awaiting_file':
                # Пропускаем, так как ожидаем файл
                return

            # Обрабатываем поле контента
            await self.handle_content_field(update, context)
        else:
            # Проверяем, не является ли сообщение командой добавления контента
            text = update.message.text.lower()
            if "#фильм" in text or "#сериал" in text or "#книга" in text:
                await self.handle_group_message(update, context)

    def register_handlers(self, application):
        """Регистрация обработчиков"""
        # Обработчики для групповых команд
        application.add_handler(CommandHandler(
            "start_add",
            self.start_group_adding,
            filters.Chat(self.GROUP_CHAT_ID)
        ))

        application.add_handler(MessageHandler(
            filters.Chat(self.GROUP_CHAT_ID) & 
            filters.Regex("^(/add_film|/add_series|/add_book|/cancel_add)$"),
            self.handle_group_command
        ))
        
        # Обработчики для callback-запросов
        application.add_handler(CallbackQueryHandler(
            self.send_content,
            pattern="^(list|view|fav)_"
        ))
        application.add_handler(CallbackQueryHandler(
            self.get_content,
            pattern="^get_"
        ))
        
        # Обработчик для команды избранного
        application.add_handler(CommandHandler(
            "favorites",
            self.show_favorites
        ))

        # Обработчик для медиа-сообщений в группе
        application.add_handler(MessageHandler(
            filters.Chat(self.GROUP_CHAT_ID) & 
            (filters.VIDEO | filters.Document.ALL | filters.PHOTO),
            self.handle_content_file
        ))

        application.add_handler(CallbackQueryHandler(
            self.send_content,
            pattern="^(list|view|fav|unfav)_"
        ))

        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.Chat(self.GROUP_CHAT_ID),
            self.handle_group_text_message
        ))

        application.add_handler(CallbackQueryHandler(
            self.back_to_main_menu,
            pattern="^back_to_main$"
        ))