import os
import sys
import time
import random
import requests
from urllib.parse import quote

print(">>> СКРИПТ СТАРТУВАВ", flush=True)

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHANNEL_ID = os.environ["TELEGRAM_CHANNEL_ID"]
REVIEW_CHAT_ID = os.environ.get("TELEGRAM_REVIEW_CHAT_ID", "").strip()
TARGET = REVIEW_CHAT_ID if REVIEW_CHAT_ID else CHANNEL_ID
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

print(">>> СЕКРЕТИ ПРОЧИТАНО", flush=True)

GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
IMAGE_API = "https://image.pollinations.ai/prompt/"

# >>> ПЕРЕМИКАЧ ПРОДАЖУ <<<
# Поки консультацій нема — False (режим росту й довіри).
# Коли зʼявляться консультації — постав True, і бот почне додавати мʼякі запрошення.
SALE_MODE = False
CONSULT_CONTACT = "запис на консультацію — у дірект / в Instagram"  # заміниш, коли буде актуально

# Тематичні тижні-парасольки (тримається ~7 днів)
UMBRELLAS = [
    "тривога та внутрішній неспокій",
    "стосунки й здорові межі",
    "самооцінка і ставлення до себе",
    "вигорання та відновлення ресурсу",
    "емоції та вміння їх розуміти",
    "внутрішній критик і самопідтримка",
]

# Воронка без продажу: 50% залучення, 30% довіра, 20% звʼязок з аудиторією
FUNNEL = (
    ["залучення"] * 5 +
    ["довіра"] * 3 +
    ["звʼязок"] * 2
)

STAGE_INSTRUCTIONS = {
    "залучення": (
        "Тип: ЗАЛУЧЕННЯ. Дай корисне й цікаве на тему «{theme}» — практичну пораду, "
        "розвінчання міфу або просту вправу. Щоб хотілось зберегти й переслати. "
        "Наприкінці мʼякий заклик зберегти пост або спробувати сьогодні."
    ),
    "довіра": (
        "Тип: ДОВІРА/ЕКСПЕРТНІСТЬ. Розкрий тему «{theme}» глибше: поясни конкретний психологічний "
        "механізм простими словами, розбери типову ситуацію — що відбувається всередині людини "
        "і що з цим робити. Покажи фахову компетентність без зверхності."
    ),
    "звʼязок": (
        "Тип: ЗВʼЯЗОК З АУДИТОРІЄЮ. Навколо теми «{theme}» напиши живий короткий текст і заверши "
        "рефлексивним питанням або запрошенням поділитися думкою в коментарях. "
        "Мета — щира взаємодія, а не повчання."
    ),
}

IMAGE_STYLES = [
    "minimalist line art illustration, single accent color on cream background",
    "soft watercolor illustration, gentle muted tones",
    "warm cozy flat illustration, editorial style",
    "atmospheric photography, soft natural light, shallow depth of field",
    "abstract paper-cut collage, calm earthy palette",
    "dreamy gouache painting, soft pastel palette",
]


def ask_gemini(prompt, temperature=0.85, timeout=120):
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": temperature}}
    last = None
    for _ in range(3):
        try:
            r = requests.post(GEMINI_URL, params={"key": GEMINI_API_KEY}, json=body, timeout=timeout)
            r.raise_for_status()
            return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            last = e
            time.sleep(6)
    raise last


ANTISHABLON = (
    "\n\nСУВОРО ЗАБОРОНЕНО (ознаки штучного тексту):\n"
    "- звороти-шаблони: «Вона думала… а виявилось…», «Це не про…, це про…», «Уявіть собі…», "
    "«Дозвольте розповісти…», «У світі, де…», «У сучасному світі», «У нашому стрімкому житті», "
    "«І ось тут починається найцікавіше», «Спойлер:», «Памʼятай: ти не один», «Важливо памʼятати», "
    "«Кожен з нас»;\n"
    "- драматичні обриви короткими реченнями через крапку для ефекту;\n"
    "- пафос, гасла, штучний оптимізм, коучингова риторика, абстракції без змісту;\n"
    "- будь-який стиль, що впізнається як ChatGPT.\n"
    "ЗАМІСТЬ ШАБЛОНІВ: пиши конкретними живими прикладами й мікросценками, як говорить жива людина.\n"
)


def maybe_consult_line():
    if SALE_MODE:
        return ("Якщо тема відгукнулась і потрібна підтримка — " + CONSULT_CONTACT + ". ")
    return ""


def generate_post(theme, stage):
    instr = STAGE_INSTRUCTIONS[stage].format(theme=theme)
    prompt = (
        "Ти — Тетяна Вінар, практикуюча психологиня, ведеш особистий телеграм-канал «Психологічно чесно». "
        "Пишеш живою, природною розмовною українською, тепло, на «ти», як до доброго знайомого.\n\n"
        + instr + " " + maybe_consult_line() +
        "\n\nЯКІСТЬ: одна чітка думка по суті, без води; конкретний механізм простими словами; "
        "живий приклад або мікросценарій (без вигаданих знаменитостей); конкретна дія на сьогодні; "
        "усі речення завершені, бездоганна граматика."
        + ANTISHABLON +
        "\nОбсяг 500-900 символів. Живий нешаблонний перший рядок. 2-3 органічні хештеги. "
        "Без markdown, звичайний текст, емодзі помірно. Поверни ЛИШЕ готовий текст поста."
    )
    return ask_gemini(prompt)


def generate_test(theme):
    prompt = (
        "Ти — психологиня. Склади короткий тест для самоперевірки на тему «" + theme + "» для каналу. "
        "Спирайся на логіку реальних психологічних опитувальників, будь коректною й обережною.\n\n"
        "ФОРМАТ (звичайний текст, без markdown):\n"
        "🧠 ТЕСТ: (коротка назва)\n\n"
        "Інструкція: за кожне питання порахуй бали 0-3 (0 — ніколи, 3 — майже завжди).\n\n"
        "1. (питання)\n2. (питання)\n3. (питання)\n4. (питання)\n5. (питання)\n\n"
        "Порахуй бали 👇\n\n"
        "РЕЗУЛЬТАТ:\n0-5 — (інтерпретація + мʼяка порада)\n6-10 — (інтерпретація + порада)\n"
        "11-15 — (інтерпретація + порада, за потреби мʼяко порадь звернутись до фахівця)\n\n"
        "Наприкінці додай рядок: «Це тест для самоспостереження, а не медичний діагноз.»\n"
        + ANTISHABLON +
        "\nЖива українська, тепло, на «ти». Поверни ЛИШЕ готовий тест."
    )
    return ask_gemini(prompt, temperature=0.7)


def generate_choice(theme):
    prompt = (
        "Ти — психологиня. Зроби рефлексивну вправу «обери образ» на тему «" + theme + "» для каналу.\n\n"
        "ФОРМАТ (звичайний текст, без markdown):\n"
        "🃏 ОБЕРИ ОБРАЗ\n\n(1-2 речення вступу: розслабся й обери образ, що відгукується)\n\n"
        "1️⃣ (образ)\n2️⃣ (образ)\n3️⃣ (образ)\n4️⃣ (образ)\n\n"
        "Обрав(ла)? Дивись, що це може означати 👇\n\n"
        "1️⃣ — (інтерпретація: що вибір говорить про стан/потребу, повʼязану з темою)\n"
        "2️⃣ — (інтерпретація)\n3️⃣ — (інтерпретація)\n4️⃣ — (інтерпретація)\n\n"
        "Наприкінці додай рядок: «Це не передбачення, а привід поміркувати про себе.»\n"
        "Образи прості й візуальні, інтерпретації теплі й змістовні, без езотерики."
        + ANTISHABLON +
        "\nПоверни ЛИШЕ готову вправу."
    )
    return ask_gemini(prompt, temperature=0.85)


def generate_video_idea(theme):
    prompt = (
        "Ти ведеш психологічний канал. Тема тижня: «" + theme + "». "
        "Запропонуй ідею короткого ВЕРТИКАЛЬНОГО фейслес-відео (Reels, 9:16, 15-40 сек) — "
        "без обличчя, кадри рук/природи/предметів, текст на екрані. Гачок у перші 3 секунди.\n\n"
        "Формат (звичайний текст, без markdown):\n"
        "🎬 ІДЕЯ: (назва)\n🎞 Кадри: (що показати)\n"
        "📝 Текст на екран по кадрах: (живі короткі фрази — БЕЗ шаблонів)\n"
        "🎵 Музика: (настрій + з бібліотеки Instagram/Facebook)\n"
        "📲 Підпис: (1-2 живі речення + 2-3 хештеги)\n"
        + ANTISHABLON +
        "\nЖива людська українська, тепло й конкретно."
    )
    return ask_gemini(prompt, temperature=0.85)


def generate_poll(theme):
    raw = ask_gemini(
        f"Створи опитування для каналу з психології на тему «{theme}». "
        "Перший рядок — питання (до 90 символів), далі 3-4 рядки варіантів (до 90 символів). "
        "Жива українська, без кліше. Без нумерації, хештегів, пояснень.",
        temperature=0.7,
    )
    lines = [l.strip(" -•\t\"'") for l in raw.splitlines() if l.strip()]
    question = lines[0][:300]
    options = [l[:100] for l in lines[1:5]]
    if len(options) < 2:
        raise ValueError("замало варіантів")
    return question, options


def make_image_prompt(theme):
    style = random.choice(IMAGE_STYLES)
    try:
        scene = ask_gemini(
            "Опиши ОДНУ коротку англійською візуальну сцену (макс 14 слів), що символічно "
            f"передає психологічну тему: «{theme}». Конкретна метафора, без тексту, без облич крупним планом. "
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
    r = requests.get(url, params={"width": 1024, "height": 1024, "nologo": "true",
                                  "model": "flux", "seed": random.randint(1, 999999),
                                  "enhance": "true"}, timeout=180)
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


def pick_theme_and_stage():
    day = int(time.time() // 86400)
    umbrella = UMBRELLAS[(day // 7) % len(UMBRELLAS)]
    stage = FUNNEL[day % len(FUNNEL)]
    return umbrella, stage


def send_main_content(theme, stage):
    """На стадії 'залучення' інколи замість поста — тест/образ/опитування (це теж залучення)."""
    if stage == "залучення":
        roll = random.random()
        if roll < 0.2:
            try:
                q, opts = generate_poll(theme)
                send_poll(q, opts)
                print("Опитування:", q, flush=True)
                return
            except Exception as e:
                print("Опитування не вдалося:", e, file=sys.stderr)
        elif roll < 0.4:
            print("ТЕСТ", flush=True)
            test = generate_test(theme)
            try:
                send_photo(get_image(make_image_prompt(theme)), test)
            except Exception as e:
                print("Без картинки:", e, file=sys.stderr)
                send_text(test)
            return
        elif roll < 0.6:
            print("ОБЕРИ ОБРАЗ", flush=True)
            choice = generate_choice(theme)
            try:
                send_photo(get_image(make_choice_image_prompt()), choice)
            except Exception as e:
                print("Без картинки:", e, file=sys.stderr)
                send_text(choice)
            return

    post = generate_post(theme, stage)
    print("Пост:\n", post, flush=True)
    try:
        send_photo(get_image(make_image_prompt(theme)), post)
        print(">>> Надіслано пост.", flush=True)
    except Exception as e:
        print(">>> Без картинки:", e, file=sys.stderr, flush=True)
        send_text(post)


def main():
    print(">>> MAIN ПОЧАВСЯ", flush=True)
    print("Режим:", "ЧЕРНЕТКА в особисті" if REVIEW_CHAT_ID else "одразу в канал", flush=True)
    theme, stage = pick_theme_and_stage()
    print("Парасолька:", theme, "| Стадія:", stage, flush=True)

    send_main_content(theme, stage)

    # Окремо — фейслес відео-ідея дня
    time.sleep(2)
    try:
        idea = generate_video_idea(theme)
        send_text("💡 ВІДЕО-ІДЕЯ ДНЯ (фейслес, вертикальне)\n\n" + idea)
        print(">>> Надіслано відео-ідею.", flush=True)
    except Exception as e:
        print(">>> Відео-ідея не вдалася:", e, file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()
