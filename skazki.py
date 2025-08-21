import requests
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater, CommandHandler, CallbackContext,
    MessageHandler, Filters, CallbackQueryHandler
)
import os
from dotenv import load_dotenv
from enum import Enum, auto
import tempfile

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# Состояния диалога
class ConversationState(Enum):
    START = auto()
    AGE = auto()
    NAME = auto()
    FAMILY = auto()
    PETS = auto()
    INTERESTS = auto()
    SITUATION = auto()
    REQUEST = auto()
    VOICE_SELECTION = auto()


class FairyTaleBot:
    def __init__(self):
        self.user_data = {}
        self.api_key = os.getenv("YANDEX_API_KEY")
        self.folder_id = os.getenv("YANDEX_FOLDER_ID")
        self.speech_api_key = os.getenv("YANDEX_SPEECH_API_KEY")

    def start(self, update: Update, context: CallbackContext) -> None:
        """Обработчик команды /start"""
        self.user_data[update.effective_chat.id] = {
            'state': ConversationState.START,
            'answers': {}
        }

        keyboard = [
            [InlineKeyboardButton("Начать создание сказки", callback_data='start_creation')]
        ]

        update.message.reply_text(
            "📖 Добро пожаловать в СказкоБот!\n\n"
            "Я помогу создать персонализированную сказку для вашего ребёнка.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    def start_creation(self, update: Update, context: CallbackContext) -> None:
        """Начало создания сказки"""
        query = update.callback_query
        query.answer()

        chat_id = query.message.chat_id
        self.user_data[chat_id]['state'] = ConversationState.AGE

        query.edit_message_text(
            "👶 Сколько лет вашему ребёнку? (От 2 до 10 лет)",
            reply_markup=self._age_keyboard()
        )

    def _age_keyboard(self):
        """Клавиатура для выбора возраста"""
        ages = [str(i) for i in range(2, 11)]
        buttons = [InlineKeyboardButton(age, callback_data=f"age_{age}") for age in ages]
        keyboard = [buttons[i:i + 3] for i in range(0, len(buttons), 3)]
        return InlineKeyboardMarkup(keyboard)

    def process_age(self, update: Update, context: CallbackContext) -> None:
        """Обработка выбора возраста"""
        query = update.callback_query
        query.answer()

        chat_id = query.message.chat_id
        age = query.data.split('_')[1]
        self.user_data[chat_id]['answers']['age'] = age
        self.user_data[chat_id]['state'] = ConversationState.NAME

        query.edit_message_text(
            f"Отлично, будем создавать сказку для {age}-летнего ребёнка.\n\n"
            "📛 Как зовут вашего ребёнка? (Напишите имя)",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Пропустить", callback_data="skip_name")]])
        )

    def process_name(self, update: Update, context: CallbackContext) -> None:
        """Обработка имени ребёнка"""
        chat_id = update.effective_chat.id

        if update.callback_query and update.callback_query.data == "skip_name":
            self.user_data[chat_id]['answers']['name'] = ""
            update.callback_query.answer()
            update.callback_query.edit_message_text(
                "Хорошо, сказка будет без имени.\n\n"
                "👨‍👩‍👧‍👦 Напишите, кто есть в вашей семье (родители, братья/сёстры).",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Пропустить", callback_data="skip_family")]])
            )
        else:
            name = update.message.text
            self.user_data[chat_id]['answers']['name'] = name
            update.message.reply_text(
                f"Прекрасное имя - {name}!\n\n"
                "👨‍👩‍👧‍👦 Напишите, кто есть в вашей семье (родители, братья/сёстры).",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Пропустить", callback_data="skip_family")]])
            )

        self.user_data[chat_id]['state'] = ConversationState.FAMILY

    def process_family(self, update: Update, context: CallbackContext) -> None:
        """Обработка информации о семье"""
        chat_id = update.effective_chat.id

        if update.callback_query and update.callback_query.data == "skip_family":
            self.user_data[chat_id]['answers']['family'] = ""
            update.callback_query.answer()
            update.callback_query.edit_message_text(
                "Хорошо, пропускаем информацию о семье.\n\n"
                "🐶 Есть ли у вашего ребёнка питомцы? Опишите их.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Пропустить", callback_data="skip_pets")]])
            )
        else:
            text = update.message.text if hasattr(update, 'message') else ""
            self.user_data[chat_id]['answers']['family'] = text
            update.message.reply_text(
                "🐶 Есть ли у вашего ребёнка питомцы? Опишите их.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Пропустить", callback_data="skip_pets")]])
            )

        self.user_data[chat_id]['state'] = ConversationState.PETS

    def process_pets(self, update: Update, context: CallbackContext) -> None:
        """Обработка информации о питомцах"""
        chat_id = update.effective_chat.id

        if update.callback_query and update.callback_query.data == "skip_pets":
            self.user_data[chat_id]['answers']['pets'] = ""
            update.callback_query.answer()
            update.callback_query.edit_message_text(
                "Хорошо, пропускаем информацию о питомцах.\n\n"
                "🎨 Какие увлечения у вашего ребёнка? (игрушки, герои, занятия)",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Пропустить", callback_data="skip_interests")]])
            )
        else:
            text = update.message.text if hasattr(update, 'message') else ""
            self.user_data[chat_id]['answers']['pets'] = text
            update.message.reply_text(
                "🎨 Какие увлечения у вашего ребёнка? (игрушки, герои, занятия)",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Пропустить", callback_data="skip_interests")]])
            )

        self.user_data[chat_id]['state'] = ConversationState.INTERESTS

    def process_interests(self, update: Update, context: CallbackContext) -> None:
        """Обработка информации об интересах"""
        chat_id = update.effective_chat.id

        if update.callback_query and update.callback_query.data == "skip_interests":
            self.user_data[chat_id]['answers']['interests'] = ""
            update.callback_query.answer()
            update.callback_query.edit_message_text(
                "Хорошо, пропускаем информацию об интересах.\n\n"
                "🛑 Какая ситуация или проблема у ребёнка?",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Пропустить", callback_data="skip_situation")]])
            )
        else:
            text = update.message.text if hasattr(update, 'message') else ""
            self.user_data[chat_id]['answers']['interests'] = text
            update.message.reply_text(
                "🛑 Какая ситуация или проблема у ребёнка?",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Пропустить", callback_data="skip_situation")]])
            )

        self.user_data[chat_id]['state'] = ConversationState.SITUATION

    def process_situation(self, update: Update, context: CallbackContext) -> None:
        """Обработка информации о ситуации"""
        chat_id = update.effective_chat.id

        if update.callback_query and update.callback_query.data == "skip_situation":
            self.user_data[chat_id]['answers']['situation'] = ""
            update.callback_query.answer()
            update.callback_query.edit_message_text(
                "Хорошо, пропускаем информацию о ситуации.\n\n"
                "📝 Какой должен быть сюжет или посыл сказки?",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Пропустить", callback_data="skip_request")]])
            )
        else:
            text = update.message.text if hasattr(update, 'message') else ""
            self.user_data[chat_id]['answers']['situation'] = text
            update.message.reply_text(
                "📝 Какой должен быть сюжет или посыл сказки?",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Пропустить", callback_data="skip_request")]])
            )

        self.user_data[chat_id]['state'] = ConversationState.REQUEST

    def process_request(self, update: Update, context: CallbackContext) -> None:
        """Обработка запроса на сказку"""
        chat_id = update.effective_chat.id

        if update.callback_query and update.callback_query.data == "skip_request":
            self.user_data[chat_id]['answers']['request'] = ""
            update.callback_query.answer()
        else:
            text = update.message.text if hasattr(update, 'message') else ""
            self.user_data[chat_id]['answers']['request'] = text

        # Генерация сказки
        context.bot.send_chat_action(chat_id=chat_id, action="typing")
        fairy_tale = self._generate_fairy_tale(self._generate_prompt(self.user_data[chat_id]['answers']))

        # Сохраняем сказку
        self.user_data[chat_id]['fairy_tale'] = fairy_tale
        self.user_data[chat_id]['state'] = ConversationState.VOICE_SELECTION

        # Отправляем сказку
        if hasattr(update, 'message'):
            update.message.reply_text(fairy_tale)
        else:
            update.callback_query.message.reply_text(fairy_tale)

        # Кнопки выбора голоса
        keyboard = [
            [InlineKeyboardButton("🔊 Мужской голос", callback_data='voice_male'),
             InlineKeyboardButton("🔊 Женский голос", callback_data='voice_female')],
            [InlineKeyboardButton("🔊 Мультяшный голос", callback_data='voice_cartoon'),
             InlineKeyboardButton("❌ Без озвучки", callback_data='voice_none')]
        ]

        if hasattr(update, 'message'):
            update.message.reply_text(
                "Выберите вариант озвучки сказки:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            update.callback_query.message.reply_text(
                "Выберите вариант озвучки сказки:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

    def _generate_prompt(self, answers: dict) -> str:
        """Генерация промпта для ИИ"""
        prompt = "Напиши детскую сказку со следующими параметрами:\n"
        prompt += f"- Возраст ребёнка: {answers.get('age', 'не указан')} лет\n"

        if answers.get('name'):
            prompt += f"- Главный герой: {answers['name']}\n"
        if answers.get('family'):
            prompt += f"- Члены семьи: {answers['family']}\n"
        if answers.get('pets'):
            prompt += f"- Питомцы: {answers['pets']}\n"
        if answers.get('interests'):
            prompt += f"- Интересы: {answers['interests']}\n"
        if answers.get('situation'):
            prompt += f"- Проблемная ситуация: {answers['situation']}\n"
        if answers.get('request'):
            prompt += f"- Желаемый посыл: {answers['request']}\n"

        prompt += (
            "\nТребования к сказке:\n"
            "1. Простой язык по возрасту\n"
            "2. Включи указанные персонажи\n"
            "3. Ненавязчивый посыл\n"
            "4. Увлекательный сюжет\n"
            "5. Длина 500-700 слов\n"
            "6. Диалоги и описания\n"
            "7. Мораль в конце\n"
            "Формат:\nНазвание\n\nТекст...\n\nМораль: ..."
        )
        return prompt

    def _generate_fairy_tale(self, prompt: str) -> str:
        """Генерация сказки через YandexGPT"""
        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json",
            "x-folder-id": self.folder_id
        }

        payload = {
            "modelUri": f"gpt://{self.folder_id}/yandexgpt-lite",
            "completionOptions": {
                "stream": False,
                "temperature": 0.7,
                "maxTokens": 2000
            },
            "messages": [
                {
                    "role": "system",
                    "text": "Ты профессиональный детский писатель"
                },
                {
                    "role": "user",
                    "text": prompt
                }
            ]
        }

        try:
            response = requests.post(
                "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()["result"]["alternatives"][0]["message"]["text"]
        except Exception as e:
            logger.error(f"Ошибка генерации сказки: {str(e)}")
            return "Извините, не удалось создать сказку. Пожалуйста, попробуйте позже."

    def process_voice_selection(self, update: Update, context: CallbackContext) -> None:
        """Обработка выбора голоса"""
        query = update.callback_query
        query.answer()

        chat_id = query.message.chat_id
        voice_type = query.data.split('_')[1]
        fairy_tale = self.user_data[chat_id]['fairy_tale']

        if voice_type == 'none':
            context.bot.send_message(
                chat_id=chat_id,
                text="Вы выбрали не озвучивать сказку.\n\nЧтобы создать новую, отправьте /start"
            )
            return

        # Создаем временный файл
        with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as temp_file:
            audio_file = temp_file.name

        # Озвучиваем
        processing_msg = context.bot.send_message(
            chat_id=chat_id,
            text="🔊 Озвучиваем сказку... Пожалуйста, подождите."
        )

        try:
            if self._generate_voice(fairy_tale, voice_type, audio_file):
                with open(audio_file, 'rb') as audio:
                    context.bot.send_audio(
                        chat_id=chat_id,
                        audio=audio,
                        caption="Ваша озвученная сказка!",
                        title="Сказка",
                        timeout=30
                    )
            else:
                context.bot.send_message(
                    chat_id=chat_id,
                    text="Не удалось озвучить сказку. Вы можете прочитать её выше."
                )
        except Exception as e:
            logger.error(f"Ошибка озвучки: {str(e)}")
            context.bot.send_message(
                chat_id=chat_id,
                text="Произошла ошибка при озвучке."
            )
        finally:
            # Удаляем временные файлы и сообщения
            if os.path.exists(audio_file):
                os.remove(audio_file)
            context.bot.delete_message(
                chat_id=chat_id,
                message_id=processing_msg.message_id
            )

            context.bot.send_message(
                chat_id=chat_id,
                text="Чтобы создать новую сказку, отправьте /start"
            )

    def _generate_voice(self, text: str, voice_type: str, output_file: str) -> bool:
        """Генерация аудио через SpeechKit"""
        if not self.speech_api_key:
            logger.error("Не задан API ключ SpeechKit")
            return False

        voice = {
            'male': 'filipp',
            'female': 'alena',
            'cartoon': 'zahar'
        }.get(voice_type, 'filipp')

        headers = {
            "Authorization": f"Api-Key {self.speech_api_key}",
        }

        data = {
            "text": text[:5000],  # Ограничение API
            "lang": "ru-RU",
            "voice": voice,
            "speed": "1.0",
            "format": "oggopus",
            "emotion": "good"
        }

        try:
            response = requests.post(
                "https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize",
                headers=headers,
                data=data,
                stream=True,
                timeout=30
            )
            response.raise_for_status()

            with open(output_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        except Exception as e:
            logger.error(f"Ошибка SpeechKit: {str(e)}")
            return False

    def handle_message(self, update: Update, context: CallbackContext) -> None:
        """Обработка текстовых сообщений"""
        chat_id = update.effective_chat.id

        if chat_id not in self.user_data:
            update.message.reply_text("Пожалуйста, начните с команды /start")
            return

        state = self.user_data[chat_id]['state']

        if state == ConversationState.NAME:
            self.process_name(update, context)
        elif state == ConversationState.FAMILY:
            self.process_family(update, context)
        elif state == ConversationState.PETS:
            self.process_pets(update, context)
        elif state == ConversationState.INTERESTS:
            self.process_interests(update, context)
        elif state == ConversationState.SITUATION:
            self.process_situation(update, context)
        elif state == ConversationState.REQUEST:
            self.process_request(update, context)
        else:
            update.message.reply_text(
                "Пожалуйста, следуйте инструкциям или начните заново с /start"
            )


def main():
    """Запуск бота"""
    required_vars = [
        "YANDEX_API_KEY",
        "YANDEX_FOLDER_ID",
        "YANDEX_SPEECH_API_KEY",
        "TELEGRAM_BOT_TOKEN"
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Отсутствуют переменные: {', '.join(missing_vars)}")
        print(f"❌ ОШИБКА: Не заданы: {', '.join(missing_vars)}")
        return

    bot = FairyTaleBot()
    updater = Updater(os.getenv("TELEGRAM_BOT_TOKEN"))
    dispatcher = updater.dispatcher

    # Обработчики команд
    dispatcher.add_handler(CommandHandler("start", bot.start))

    # Обработчики callback-запросов
    dispatcher.add_handler(CallbackQueryHandler(bot.start_creation, pattern='^start_creation$'))
    dispatcher.add_handler(CallbackQueryHandler(bot.process_age, pattern='^age_'))
    dispatcher.add_handler(CallbackQueryHandler(bot.process_name, pattern='^skip_name$'))
    dispatcher.add_handler(CallbackQueryHandler(bot.process_family, pattern='^skip_family$'))
    dispatcher.add_handler(CallbackQueryHandler(bot.process_pets, pattern='^skip_pets$'))
    dispatcher.add_handler(CallbackQueryHandler(bot.process_interests, pattern='^skip_interests$'))
    dispatcher.add_handler(CallbackQueryHandler(bot.process_situation, pattern='^skip_situation$'))
    dispatcher.add_handler(CallbackQueryHandler(bot.process_request, pattern='^skip_request$'))
    dispatcher.add_handler(CallbackQueryHandler(bot.process_voice_selection, pattern='^voice_'))

    # Обработчик текстовых сообщений
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, bot.handle_message))

    updater.start_polling()
    logger.info("Бот запущен")
    print("🤖 Бот запущен!")
    updater.idle()


if __name__ == '__main__':
    main()