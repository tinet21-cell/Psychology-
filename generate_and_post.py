import os
import sys
import time
import datetime
import requests
from urllib.parse import quote

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHANNEL_ID = os.environ["TELEGRAM_CHANNEL_ID"]

TEXT_API = "https://text.pollinations.ai/openai"
IMAGE_API = "https://image.pollinations.ai/prompt/"

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


def ask_text(prompt, timeout=120):
    body = {
        "model": "openai",
        "messages": [{"role": "user", "content": prompt}],
    }
    last = None
    for _ in range(3):
        try:
            r = requests.post(TEXT_API, json=body, timeout=timeout)
            r.raise_for_status()
            data = r.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            last = e
            time.sleep(5)
    raise last


def generate_post(topic):
    prompt = (
        "Ти редактор україномовного телеграм-каналу з психології. "
        f"Напиши короткий теплий пост на тему: «{topic}». "
        "Українською, 80-130 слів, не більше 800 символів. "
        "Заголовок, 2 абзаци, у кінці порада або питання. "
        "Підтримуючий тон, без складних термінів, науково-популярно, не діагностика. "
        "Додай 3 хештеги. Без markdown-розмітки, звичайний текст, емодзі дозволені. "
        "Поверни ЛИШЕ готовий текст поста, без жодних пояснень чи міркувань."
    )
    return ask_text(prompt)


def make_image_prompt(topic):
    try:
        p = ask_text(
            "Translate this psychology theme into a short English prompt (max 12 words) "
            "for a calm minimalist abstract illustration, soft pastel colors. "
            f"Theme: {topic}. Return only the prompt, nothing else.",
            timeout=60,
        )
        return p.replace("\n", " ").strip()
    except Exception:
        return "calm minimalist abstract psychology illustration, soft pastel colors"


def get_image(image_prompt):
    url = IMAGE_API + quote(image_prompt)
    r = requests.get(
        url,
        params={"width": 1024, "height": 1024, "nologo": "true", "model": "flux"},
        timeout=180,
    )
    r.raise_for_status()
    return r.content


def send_photo(image_bytes, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    files = {"photo": ("post.jpg", image_bytes, "image/jpeg")}
    data = {"chat_id": CHANNEL_ID, "caption": caption[:1024]}
    r = requests.post(url, data=data, files=files, timeout=60)
    r.raise_for_status()
    return r.json()


def send_text(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    r = requests.post(
        url,
        json={"chat_id": CHANNEL_ID, "text": text, "disable_web_page_preview": True},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def main():
    topic = pick_topic()
    print("Тема:", topic)
    post = generate_post(topic)
    print("Пост:\n", post)
    try:
        img_prompt = make_image_prompt(topic)
        print("Image prompt:", img_prompt)
        image = get_image(img_prompt)
        send_photo(image, post)
        print("Опубліковано з картинкою.")
    except Exception as e:
        print("Без картинки, шлю текстом:", e, file=sys.stderr)
        send_text(post)
        print("Опубліковано текстом.")


if __name__ == "__main__":
    main()
