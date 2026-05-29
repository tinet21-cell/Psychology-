import os
import sys
import time
import datetime
import requests
from urllib.parse import quote

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHANNEL_ID = os.environ["TELEGRAM_CHANNEL_ID"]
REVIEW_CHAT_ID = os.environ.get("TELEGRAM_REVIEW_CHAT_ID", "").strip()

# Якщо заданий REVIEW_CHAT_ID — пост іде тобі в особисті на перевірку.
# Якщо прибрати цей секрет — бот публікуватиме одразу в канал.
TARGET = REVIEW_CHAT_ID if REVIEW_CHAT_ID else CHANNEL_ID

PREFERRED_MODEL = "claude"  # можна змінити на "openai", "mistral"

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

FORMATS = [
    ("порада", "Дай одну конкретну практичну пораду на тему «{topic}» і поясни механізм: чому це працює на рівні психіки."),
    ("міф і правда", "Розвінчай поширений міф на тему «{topic}»: спочатку міф, потім що насправді і чому."),
    ("вправа", "Запропонуй просту вправу на 2-3 хвилини на тему «{topic}», покроково, з поясненням ефекту."),
    ("питання дня", "Постав читачам глибоке рефлексивне питання на тему «{topic}» з живим вступом на 2-3 речення."),
    ("історія", "Розкажи коротку правдоподібну життєву історію на тему «{topic}» з конкретним висновком."),
    ("розбір", "Розбери одну типову ситуацію на тему «{topic}»: що відбувається всередині людини і що з цим робити."),
]


def ask_text(prompt, timeout=120):
    last = None
    for model in (PREFERRED_MODEL, "openai"):
        body = {"model": model, "messages": [{"role": "user", "content": prompt}]}
        for _ in range(2):
            try:
                r = requests.post(TEXT_API, json=body, timeout=timeout)
                r.raise_for_status()
                return r.json()["choices"][0]["message"]["content"].strip()
            except Exception as e:
                last = e
                time.sleep(4)
    raise last


def proofread(text):
    try:
        return ask_text(
            "Виправ усі граматичні, відмінкові й пунктуаційні помилки українською. "
            "Збережи зміст, тон, емодзі, хештеги і структуру. Нічого не додавай. "
            "Поверни ЛИШЕ виправлений текст:\n\n" + text,
            timeout=90,
        ).strip()
    except Exception:
        return text


def generate_post(topic, fmt_instruction):
    prompt = (
        "Ти — досвідчений практикуючий психолог, який веде особистий телеграм-канал. "
        "Пишеш живою розмовною українською, як до доброго знайомого. "
        + fmt_instruction.format(topic=topic) + " "
        "\n\nГОЛОВНЕ — ГЛИБИНА І КОРИСТЬ:\n"
        "- Одна чітка думка, а не загальні слова. Розкрий її по суті.\n"
        "- Поясни конкретний механізм (що відбувається з емоціями/мисленням і чому).\n"
        "- Додай 1 живий конкретний приклад або мікросценарій із реального життя.\n"
        "- Дай конкретну дію, яку можна зробити вже сьогодні.\n"
        "- Жодної «води», банальностей і пустих узагальнень.\n\n"
        "СТИЛЬ:\n"
        "- По-людськи, з емоцією, ніби ділишся власним спостереженням. Звертайся на «ти».\n"
        "- Короткі живі речення, природний ритм. Бездоганна граматика.\n\n"
        "СУВОРО ЗАБОРОНЕНО (ознаки штучного тексту):\n"
        "- кліше: «У сучасному світі», «У нашому стрімкому житті», «Памʼятай: ти не один», "
        "«Важливо памʼятати», «Кожен з нас», «Не варто забувати»;\n"
        "- пафос, гасла, штучний оптимізм, абстрактні фрази без змісту, знаки оклику через слово.\n\n"
        "Обсяг 400-900 символів. Почни з живого, не банального заголовка. "
        "Додай 2-3 доречні хештеги в кінці. Без markdown, звичайний текст, емодзі помірно. "
        "Поверни ЛИШЕ готовий текст поста, без пояснень."
    )
    return proofread(ask_text(prompt))


def generate_poll(topic):
    raw = ask_text(
        f"Створи опитування для каналу з психології на тему «{topic}». "
        "Перший рядок — питання (до 90 символів), далі 3-4 рядки варіантів (до 90 символів кожен). "
        "Жива українська, бездоганна граматика, без кліше. Без нумерації, хештегів і пояснень."
    )
    lines = [l.strip(" -•\t\"'") for l in raw.splitlines() if l.strip()]
    question = lines[0][:300]
    options = [l[:100] for l in lines[1:5]]
    if len(options) < 2:
        raise ValueError("замало варіантів")
    return question, options


def make_image_prompt(topic):
    try:
        return ask_text(
            "Translate this psychology theme into a short English prompt (max 12 words) "
            "for a calm minimalist abstract illustration, soft pastel colors. "
            f"Theme: {topic}. Return only the prompt.",
            timeout=60,
        ).replace("\n", " ").strip()
    except Exception:
        return "calm minimalist abstract psychology illustration, soft pastel colors"


def get_image(image_prompt):
    url = IMAGE_API + quote(image_prompt)
    r = requests.get(url, params={"width": 1024, "height": 1024, "nologo": "true", "model": "flux"}, timeout=180)
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
    mode = "ЧЕРНЕТКА в особисті" if REVIEW_CHAT_ID else "одразу в канал"
    print("Режим:", mode)
    day = datetime.date.today().toordinal()
    topic = TOPICS[day % len(TOPICS)]

    if day % 5 == 0:
        try:
            q, opts = generate_poll(topic)
            send_poll(q, opts)
            print("Опитування:", q)
            return
        except Exception as e:
            print("Опитування не вдалося:", e, file=sys.stderr)

    fmt_name, fmt_instr = FORMATS[day % len(FORMATS)]
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
