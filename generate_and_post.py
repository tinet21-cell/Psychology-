import os
import sys
import datetime
import requests

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHANNEL_ID = os.environ["TELEGRAM_CHANNEL_ID"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

TOPICS = [
    "емоційний інтелект і робота з емоціями",
    "тривога та способи її знизити",
    "здорові межі в стосунках",
    "самооцінка і прийняття себе",
    "як справлятися зі стресом",
    "когнітивні викривлення мислення",
    "прокрастинація та мотивація",
    "вигорання і відновлення ресурсу",
    "ефективна комунікація і конфлікти",
    "формування корисних звичок",
    "усвідомленість у щоденному житті",
    "емпатія та стосунки з близькими",
    "перфекціонізм і страх помилок",
    "психологічна стійкість",
    "робота з внутрішнім критиком",
]


def pick_topic():
    return TOPICS[datetime.date.today().toordinal() % len(TOPICS)]


def generate_post(topic):
    prompt = (
        "Ти редактор україномовного телеграм-каналу з психології. "
        f"Напиши короткий теплий пост на тему: «{topic}». "
        "Українською, 120-200 слів, із заголовком, 2-3 абзацами і порадою чи питанням у кінці. "
        "Підтримуючий тон, без складних термінів. Це науково-популярний контент, не діагностика. "
        "Додай 3-4 хештеги. Без Markdown-розмітки, звичайний текст, емодзі дозволені. "
        "Поверни лише текст поста."
    )
    resp = requests.post(
        GEMINI_URL,
        params={"key": GEMINI_API_KEY},
        json={"contents": [{"parts": [{"text": prompt}]}]},
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()


def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    resp = requests.post(
        url,
        json={"chat_id": CHANNEL_ID, "text": text, "disable_web_page_preview": True},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def main():
    topic = pick_topic()
    print("Тема дня:", topic)
    post = generate_post(topic)
    print("Пост:\n", post)
    result = send_to_telegram(post)
    print("Опубліковано. message_id:", result["result"]["message_id"])


if __name__ == "__main__":
    main()
