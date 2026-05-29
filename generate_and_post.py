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

FORMATS = [
    ("порада", "Дай одну конкретну практичну пораду на тему «{topic}» і коротко поясни, чому це працює."),
    ("міф і правда", "Розвінчай поширений міф на тему «{topic}»: спочатку міф, потім як насправді."),
    ("вправа", "Запропонуй просту вправу на 2-3 хвилини на тему «{topic}», покроково що робити."),
    ("питання дня", "Постав читачам тепле рефлексивне питання на тему «{topic}», яке хочеться обговорити в коментарях. Додай 2-3 речення вступу."),
    ("історія", "Розкажи коротку життєву історію або метафору на тему «{topic}» з мʼяким висновком."),
    ("чек-лист", "Зроби короткий чек-лист на 4-5 пунктів на тему «{topic}», кожен пункт з нового рядка."),
]


def ask_text(prompt, timeout=120):
    body = {"model": "openai", "messages": [{"role": "user", "content": prompt}]}
    last = None
    for _ in range(3):
        try:
            r = requests.post(TEXT_API, json=body, timeout=timeout)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            last = e
            time.sleep(5)
    raise last


def proofread(text):
    try:
        fixed = ask_text(
            "Виправ у цьому тексті всі граматичні, відмінкові й пунктуаційні помилки "
            "українською мовою. Збережи зміст, тон, емодзі, хештеги і структуру без змін. "
            "Не додавай нічого від себе. Поверни ЛИШЕ виправлений текст:\n\n" + text,
            timeout=90,
        )
        return fixed.strip()
    except Exception:
        return text


def generate_post(topic, fmt_instruction):
    prompt = (
        "Ти — практикуючий психолог, який веде теплий особистий телеграм-канал. "
        "Пишеш живою розмовною українською, як до доброго знайомого. "
        + fmt_instruction.format(topic=topic) + " "
        "\n\nСТИЛЬ (дуже важливо):\n"
        "- Пиши по-людськи, з емоцією, ніби ділишся власним спостереженням.\n"
        "- Короткі живі речення, природний ритм.\n"
        "- Звертайся на «ти», тепло й без повчального тону.\n"
        "- Конкретика й образи замість абстракцій.\n"
        "- Бездоганна українська граматика й правильні відмінки.\n\n"
        "СУВОРО ЗАБОРОНЕНО (ознаки штучного тексту):\n"
        "- кліше: «У сучасному світі», «У нашому стрімкому житті», «Памʼятай: ти не один», "
        "«Важливо памʼятати», «Кожен з нас», «Не варто забувати»;\n"
        "- пафос, мотиваційні гасла, штучний оптимізм, знаки оклику через слово;\n"
        "- канцелярит і складні терміни; сухі переліки без живої думки;\n"
        "- однакові шаблонні зачини й кінцівки.\n\n"
        "Обсяг до 800 символів. Почни з живого, не банального заголовка. "
        "Додай 2-3 доречні хештеги в кінці. Без markdown-розмітки, звичайний текст, емодзі — помірно. "
        "Поверни ЛИШЕ готовий текст поста, без пояснень."
    )
    return proofread(ask_text(prompt))


def generate_poll(topic):
    raw = ask_text(
        f"Створи опитування для каналу з психології на тему «{topic}». "
        "Поверни РІВНО у форматі: перший рядок — питання (до 90 символів), "
        "далі 3-4 рядки — варіанти відповіді (кожен до 90 символів, з нового рядка). "
        "Жива розмовна українська, бездоганна граматика й відмінки, без кліше. "
        "Без нумерації, без хештегів, без пояснень."
    )
    lines = [l.strip(" -•\t\"'") for l in raw.splitlines() if l.strip()]
    question = lines[0][:300]
    options = [l[:100] for l in lines[1:5]]
    if len(options) < 2:
        raise ValueError("замало варіантів")
    return question, options


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


def send_poll(question, options):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPoll"
    payload = {
        "chat_id": CHANNEL_ID,
        "question": question,
        "options": [{"text": o} for o in options],
        "is_anonymous": True,
    }
    r = requests.post(url, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()


def main():
    day = datetime.date.today().toordinal()
    topic = TOPICS[day % len(TOPICS)]

    if day % 5 == 0:
        try:
            q, opts = generate_poll(topic)
            send_poll(q, opts)
            print("Опубліковано опитування:", q)
            return
        except Exception as e:
            print("Опитування не вдалося, роблю звичайний пост:", e, file=sys.stderr)

    fmt_name, fmt_instr = FORMATS[day % len(FORMATS)]
    print("Тема:", topic, "| Формат:", fmt_name)
    post = generate_post(topic, fmt_instr)
    print("Пост:\n", post)
    try:
        img_prompt = make_image_prompt(topic)
        image = get_image(img_prompt)
        send_photo(image, post)
        print("Опубліковано з картинкою.")
    except Exception as e:
        print("Без картинки, шлю текстом:", e, file=sys.stderr)
        send_text(post)
        print("Опубліковано текстом.")


if __name__ == "__main__":
    main()
