import os
import asyncio
from google import genai
from google.genai import types
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

# Токены из переменных окружения
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Инициализация Gemini
client = genai.Client(api_key=GEMINI_API_KEY)

# История чатов для каждого пользователя
chat_histories = {}

SYSTEM_PROMPT = """Ты полезный ИИ-ассистент. Отвечай на русском языке, 
если пользователь пишет по-русски. Будь дружелюбным и помогай с любыми вопросами."""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я ИИ-ассистент на базе Gemini. Спрашивай что угодно! 🤖\n"
        "Команды:\n/start — начать\n/clear — очистить историю чата"
    )


async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_histories[user_id] = []
    await update.message.reply_text("История чата очищена! 🗑️")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text

    # Инициализируем историю если нет
    if user_id not in chat_histories:
        chat_histories[user_id] = []

    # Показываем что бот печатает
    await update.message.chat.send_action("typing")

    try:
        # Добавляем сообщение пользователя в историю
        chat_histories[user_id].append(
            types.Content(role="user", parts=[types.Part(text=user_message)])
        )

        # Запрос к Gemini с историей
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=chat_histories[user_id],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                max_output_tokens=2048,
                temperature=0.7,
            )
        )

        bot_reply = response.text

        # Добавляем ответ в историю
        chat_histories[user_id].append(
            types.Content(role="model", parts=[types.Part(text=bot_reply)])
        )

        # Ограничиваем историю последними 20 сообщениями
        if len(chat_histories[user_id]) > 20:
            chat_histories[user_id] = chat_histories[user_id][-20:]

        await update.message.reply_text(bot_reply)

    except Exception as e:
        await update.message.reply_text(f"Ошибка: {str(e)}")


def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Бот запущен!")
    app.run_polling()


if __name__ == "__main__":
    main()
