import os
import sys
import time
import random
import requests
from urllib.parse import quote

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHANNEL_ID = os.environ["TELEGRAM_CHANNEL_ID"]
REVIEW_CHAT_ID = os.environ.get("TELEGRAM_REVIEW_CHAT_ID", "").strip()
TARGET = REVIEW_CHAT_ID if REVIEW_CHAT_ID else CHANNEL_ID
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
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

FORMATS = [
    ("порада", "Дай одну конкретну практичну пораду на тему «{topic}» і поясни механізм: що саме відбувається в психіці й чому це працює."),
    ("міф і правда", "Візьми один поширений міф на тему «{topic}». Спершу назви міф, потім поясни, як насправді і чому."),
    ("вправа", "Опиши просту вправу на 2-3 хвилини на тему «{topic}»: покроково що робити і який ефект вона дає."),
    ("питання дня", "Напиши живий вступ на 3-4 речення на тему «{topic}» і заверши глибоким рефлексивним питанням до читача."),
    ("історія", "Розкажи коротку правдоподібну життєву історію на тему «{topic}» з конкретним психологічним висновком."),
    ("розбір", "Розбери одну типову життєву ситуацію на тему «{topic}»: що відбувається всередині людини і що конкретно з цим робити."),
]

IMAGE_STYLES = [
    "minimalist line art illustration, single accent color on cream background",
    "soft watercolor illustration, gentle muted tones",
    "warm cozy flat illustration, editorial style",
    "atmospheric photography, soft natural light, shallow depth of field",
    "abstract paper-cut collage, calm earthy palette",
    "dreamy gouache painting, soft pastel palette",
]


def ask_gemini(prompt, temperature=0.85, timeout=120):
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temperature},
    }
    last = None
    for _ in range(3):
        try:
            r = requests.post(GEMINI_URL, params={"key": GEMINI_API_KEY}, json=body, timeout=timeout)
            r.raise_for_status()
            data = r.json()
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            last = e
            time.sleep(6)
    raise last


def generate_post(topic, fmt_instruction):
    prompt = (
        "Ти — досвідчений практикуючий психолог, ведеш особистий телеграм-канал. "
        "Пишеш живою, природною розмовною українською, як до доброго знайомого. "
        + fmt_instruction.format(topic=topic) + " "
        "\n\nЯКІСТЬ (головне):\n"
        "- Одна чітка думка, розкрита по суті. Жодної води й банальностей.\n"
        "- Поясни конкретний психологічний механізм простими словами.\n"
        "- Додай 1 живий конкретний приклад або мікросценарій (без вигаданих імен знаменитостей).\n"
        "- Дай конкретну дію, яку можна зробити сьогодні.\n"
        "- УСІ речення завершені, природні, без кальок і суржику.\n\n"
        "СТИЛЬ:\n"
        "- Тепло, на «ти», без повчального тону. Бездоганна українська граматика.\n\n"
        "ЗАБОРОНЕНО (ознаки штучного тексту):\n"
        "- кліше «У сучасному світі», «У нашому стрімкому житті», «Памʼятай: ти не один», "
        "«Важливо памʼятати», «Кожен з нас»;\n"
        "- пафос, гасла, штучний оптимізм, абстракції без змісту, обірвані речення.\n\n"
        "Обсяг 500-900 символів. Почни з живого, не банального заголовка. "
        "Додай 2-3 доречні хештеги в кінці. Без markdown-розмітки, звичайний текст, емодзі помірно. "
        "Поверни ЛИШЕ повністю готовий текст поста, без пояснень."
    )
    return ask_gemini(prompt)


def generate_poll(topic):
    raw = ask_gemini(
        f"Створи опитування для каналу з психології на тему «{topic}». "
        "Перший рядок — питання (до 90 символів), далі 3-4 рядки варіантів (до 90 символів). "
        "Жива українська, бездоганна граматика, без кліше. Без нумерації, хештегів, пояснень.",
        temperature=0.7,
    )
    lines = [l.strip(" -•\t\"'") for l in raw.splitlines() if l.strip()]
    question = lines[0][:300]
    options = [l[:100] for l in lines[1:5]]
    if len(options) < 2:
        raise ValueError("замало варіантів")
    return question, options


def make_image_prompt(topic):
    style = random.choice(IMAGE_STYLES)
    try:
        scene = ask_gemini(
            "Опиши ОДНУ коротку англійською візуальну сцену (макс 14 слів), що символічно "
            f"передає психологічну тему: «{topic}». Конкретна метафора, без тексту, без облич крупним планом. "
            "Поверни лише англійський опис сцени.",
            temperature=1.0, timeout=60,
        ).replace("\n", " ").strip()
    except Exception:
        scene = "a calm symbolic scene about inner balance"
    return f"{scene}, {style}, no text, high quality"


def get_image(image_prompt):
    url = IMAGE_API + quote(image_prompt)
    r = requests.get(
        url,
        params={"width": 1024, "height": 1024, "nologo": "true",
                "model": "flux", "seed": random.randint(1, 999999), "enhance": "true"},
        timeout=180,
    )
    r.raise_for_status()
    return r.content


def send_photo(image_bytes, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    files = {"photo": ("post.jpg", image_bytes, "image/jpeg")}
    data = {"chat_id": TARGET, "caption": caption[:1024]}
    r = requests.post(url, data=data, files=files, timeout=60)
    r.raise_for_status()
    return r.json()


def send_text(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    r = requests.post(url, json={"chat_id": TARGET, "text": text, "disable_web_page_preview": True}, timeout=30)
    r.raise_for_status()
    return r.json()


def send_poll(question, options):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPoll"
    payload = {"chat_id": TARGET, "question": question,
               "options": [{"text": o} for o in options], "is_anonymous": True}
    r = requests.post(url, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()


def main():
    print("Режим:", "ЧЕРНЕТКА в особисті" if REVIEW_CHAT_ID else "одразу в канал")
    topic = random.choice(TOPICS)

    if random.random() < 0.2:
        try:
            q, opts = generate_poll(topic)
            send_poll(q, opts)
            print("Опитування:", q)
            return
        except Exception as e:
            print("Опитування не вдалося:", e, file=sys.stderr)

    fmt_name, fmt_instr = random.choice(FORMATS)
    print("Тема:", topic, "| Формат:", fmt_name)
    post = generate_post(topic, fmt_instr)
    print("Пост:\n", post)
    try:
        image = get_image(make_image_prompt(topic))
        send_photo(image, post)
        print("Надіслано з картинкою.")
    except Exception as e:
        print("Без картинки:", e, file=sys.stderr)
        send_text(post)
        print("Надіслано текстом.")


if __name__ == "__main__":
    main()
