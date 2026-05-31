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


def generate_test(topic):
    prompt = (
        "Ти — психолог. Склади короткий тест для самоперевірки на тему «" + topic + "» "
        "для телеграм-каналу. Тест має спиратися на логіку реальних психологічних опитувальників "
        "(на кшталт шкал самооцінки стану), бути коректним і обережним.\n\n"
        "ФОРМАТ (звичайний текст, без markdown):\n"
        "🧠 ТЕСТ: (коротка назва)\n\n"
        "Інструкція: за кожне питання порахуй бали від 0 до 3 (0 — ніколи, 1 — інколи, 2 — часто, 3 — майже завжди).\n\n"
        "1. (питання)\n"
        "2. (питання)\n"
        "3. (питання)\n"
        "4. (питання)\n"
        "5. (питання)\n\n"
        "Підрахуй свої бали 👇\n\n"
        "РЕЗУЛЬТАТ:\n"
        "0-5 балів — (коротка інтерпретація + мʼяка порада)\n"
        "6-10 балів — (інтерпретація + порада)\n"
        "11-15 балів — (інтерпретація + порада, за потреби мʼяко порадь звернутись до фахівця)\n\n"
        "ВАЖЛИВО наприкінці додай рядок: «Це тест для самоспостереження, а не медичний діагноз.»\n\n"
        "Жива природна українська, тепло, на «ти», без кліше. Поверни ЛИШЕ готовий тест."
    )
    return ask_gemini(prompt, temperature=0.7)


def generate_choice(topic):
    prompt = (
        "Ти — психолог. Зроби рефлексивну вправу формату «обери образ» на тему «" + topic + "» "
        "для телеграм-каналу.\n\n"
        "ФОРМАТ (звичайний текст, без markdown):\n"
        "🃏 ОБЕРИ ОБРАЗ\n\n"
        "(1-2 речення вступу: розслабся й обери образ, що відгукується найбільше)\n\n"
        "1️⃣ (короткий опис образу)\n"
        "2️⃣ (короткий опис образу)\n"
        "3️⃣ (короткий опис образу)\n"
        "4️⃣ (короткий опис образу)\n\n"
        "Обрав(ла)? Дивись, що це може означати 👇\n\n"
        "1️⃣ — (психологічна інтерпретація: що твій вибір говорить про стан/потребу, повʼязану з темою)\n"
        "2️⃣ — (інтерпретація)\n"
        "3️⃣ — (інтерпретація)\n"
        "4️⃣ — (інтерпретація)\n\n"
        "ВАЖЛИВО наприкінці додай рядок: «Це не передбачення, а привід поміркувати про себе.»\n\n"
        "Образи прості й візуальні (предмети, природа, сцени). Інтерпретації теплі, підтримливі, "
        "психологічно змістовні, без езотерики й містики. Жива українська, на «ти», без кліше. "
        "Поверни ЛИШЕ готову вправу."
    )
    return ask_gemini(prompt, temperature=0.85)


def generate_video_idea(topic):
    prompt = (
        "Ти — контент-менеджер психологічного телеграм-каналу. Тема: «" + topic + "». "
        "Запропонуй ідею для короткого ВЕРТИКАЛЬНОГО відео (Reels/TikTok/Shorts), формат 9:16, "
        "15-40 секунд, ФЕЙСЛЕС (без обличчя — кадри рук, природи, предметів, текст на екрані). "
        "Гачок у перші 3 секунди.\n\n"
        "Дай ДВА варіанти втілення однієї ідеї (звичайний текст, без markdown):\n\n"
        "🎬 ІДЕЯ: (коротка назва)\n\n"
        "━━━━━━━━━━━━━━\n"
        "🤖 ВАРІАНТ 1 — ПРОМТ ДЛЯ AI-ВІДЕО\n"
        "Готовий детальний промт англійською для генератора відео (Veo/Sora). "
        "Обовʼязково вкажи: vertical 9:16 aspect ratio, атмосферна сцена БЕЗ людей або лише руки/деталі, "
        "рух камери, освітлення, настрій. Дай одним абзацом, готовий до копіювання.\n"
        "Текст на екран (українською): які фрази й коли показати.\n\n"
        "━━━━━━━━━━━━━━\n"
        "📱 ВАРІАНТ 2 — ПЛАН ЗЙОМКИ ТЕЛЕФОНОМ (фейслес)\n"
        "Прості кадри без обличчя, які легко зняти самій. Формат:\n"
        "⏱ Хронометраж\n"
        "📐 Телефон ВЕРТИКАЛЬНО (9:16)\n"
        "Кадри:\n"
        "1. (що показати в кадрі — напр. руки, чашка, вікно — + текст на екрані)\n"
        "2. ...\n"
        "3. ...\n"
        "📝 Повний текст субтитрів по черзі (бо відео без голосу — текст головний)\n\n"
        "━━━━━━━━━━━━━━\n"
        "🎵 Музика: (настрій + нагадай брати з бібліотеки Facebook/Instagram)\n"
        "📲 Підпис до публікації: (1-2 речення + 3-4 хештеги)\n\n"
        "Жива українська, тепло, психологічно змістовно, практично."
    )
    return ask_gemini(prompt, temperature=0.85)


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


def make_choice_image_prompt():
    return ("four symbolic cards in a row, minimalist tarot-like illustration, "
            "calm muted palette, soft watercolor, no text, high quality")


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


def split_text(text, limit=4000):
    text = text.strip()
    if len(text) <= limit:
        return [text]
    parts = []
    while len(text) > limit:
        chunk = text[:limit]
        cut = chunk.rfind("\n\n")
        if cut < limit * 0.5:
            cut = chunk.rfind("\n")
        if cut < limit * 0.5:
            cut = chunk.rfind(". ")
            if cut != -1:
                cut += 1
        if cut < limit * 0.5:
            cut = limit
        parts.append(text[:cut].strip())
        text = text[cut:].strip()
    if text:
        parts.append(text)
    return parts


def send_photo(image_bytes, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    if len(caption) <= 1024:
        files = {"photo": ("post.jpg", image_bytes, "image/jpeg")}
        data = {"chat_id": TARGET, "caption": caption}
        r = requests.post(url, data=data, files=files, timeout=60)
        r.raise_for_status()
        return r.json()
    files = {"photo": ("post.jpg", image_bytes, "image/jpeg")}
    data = {"chat_id": TARGET}
    r = requests.post(url, data=data, files=files, timeout=60)
    r.raise_for_status()
    send_text(caption)
    return r.json()


def send_text(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    last = None
    for part in split_text(text, 4000):
        r = requests.post(url, json={"chat_id": TARGET, "text": part,
                                     "disable_web_page_preview": True}, timeout=30)
        r.raise_for_status()
        last = r.json()
    return last


def send_poll(question, options):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPoll"
    payload = {"chat_id": TARGET, "question": question,
               "options": [{"text": o} for o in options], "is_anonymous": True}
    r = requests.post(url, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()


def send_main_content():
    """Щоденний основний контент: пост / опитування / тест / обери-образ."""
    topic = random.choice(TOPICS)
    roll = random.random()

    if roll < 0.12:
        try:
            q, opts = generate_poll(topic)
            send_poll(q, opts)
            print("Опитування:", q)
            return
        except Exception as e:
            print("Опитування не вдалося:", e, file=sys.stderr)

    elif roll < 0.24:
        print("Режим: ТЕСТ | Тема:", topic)
        test = generate_test(topic)
        try:
            send_photo(get_image(make_image_prompt(topic)), test)
            print("Надіслано тест з картинкою.")
        except Exception as e:
            print("Без картинки:", e, file=sys.stderr)
            send_text(test)
        return

    elif roll < 0.36:
        print("Режим: ОБЕРИ ОБРАЗ | Тема:", topic)
        choice = generate_choice(topic)
        try:
            send_photo(get_image(make_choice_image_prompt()), choice)
            print("Надіслано обери-образ з картинкою.")
        except Exception as e:
            print("Без картинки:", e, file=sys.stderr)
            send_text(choice)
        return

    fmt_name, fmt_instr = random.choice(FORMATS)
    print("Тема:", topic, "| Формат:", fmt_name)
    post = generate_post(topic, fmt_instr)
    print("Пост:\n", post)
    try:
        send_photo(get_image(make_image_prompt(topic)), post)
        print("Надіслано пост з картинкою.")
    except Exception as e:
        print("Без картинки:", e, file=sys.stderr)
        send_text(post)


def send_daily_video():
    """Щоденна фейслес відео-ідея окремим повідомленням."""
    topic = random.choice(TOPICS)
    print("Відео-ідея | Тема:", topic)
    try:
        idea = generate_video_idea(topic)
        send_text("💡 ВІДЕО-ІДЕЯ ДНЯ (фейслес, вертикальне)\n\n" + idea)
        print("Надіслано відео-ідею.")
    except Exception as e:
        print("Відео-ідея не вдалася:", e, file=sys.stderr)


def main():
    print("Режим:", "ЧЕРНЕТКА в особисті" if REVIEW_CHAT_ID else "одразу в канал")
    send_main_content()
    time.sleep(2)
    send_daily_video()


if __name__ == "__main__":
    main()
