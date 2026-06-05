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

SALE_MODE = False
CONSULT_CONTACT = "запис на консультацію — у дірект / в Instagram"

UMBRELLAS = [
    [
        "звідки береться ранкова тривога й що з нею робити",
        "як тривога проявляється в тілі (напруга, дихання, серце)",
        "тривожні думки-катастрофи і як їх ловити",
        "проста техніка заземлення за 2 хвилини",
        "тривога перед сном і як заспокоїтися ввечері",
        "коли тривога корисна, а коли заважає",
        "тривога й бажання все контролювати",
    ],
    [
        "як розпізнати, що твої межі порушують",
        "чому складно казати «ні» близьким",
        "різниця між турботою і контролем у стосунках",
        "як говорити про потреби, щоб почули",
        "емоційне виснаження від спілкування",
        "коли варто віддалитися від людини",
        "як відновити довіру після сварки",
    ],
    [
        "звідки беруться сумніви в собі",
        "як внутрішній голос формує самооцінку",
        "порівняння себе з іншими і чому воно ранить",
        "як підтримати себе у момент невдачі",
        "залежність самооцінки від чужої думки",
        "маленькі дії, що зміцнюють впевненість",
        "різниця між самооцінкою і самоцінністю",
    ],
    [
        "перші ознаки вигорання, які легко пропустити",
        "чому відпочинок не завжди відновлює",
        "вигорання й втрата сенсу в роботі",
        "як відновлювати ресурс щодня потроху",
        "межі між роботою й життям",
        "коли вигорання потребує допомоги фахівця",
        "як говорити «досить» без провини",
    ],
    [
        "чому ми не вміємо називати свої емоції",
        "що насправді ховається за злістю",
        "як проживати смуток, а не тікати від нього",
        "емоції, які ми соромимося відчувати",
        "як емоції впливають на рішення",
        "техніка паузи між емоцією і реакцією",
        "чому пригнічені емоції повертаються",
    ],
    [
        "як звучить твій внутрішній критик",
        "звідки він узявся й чий це насправді голос",
        "різниця між критикою і вимогливістю до себе",
        "як відповідати критику без боротьби",
        "самоспівчуття замість самобичування",
        "як критик заважає починати нове",
        "маленькі фрази самопідтримки на щодень",
    ],
]

FUNNEL = ["залучення"] * 5 + ["довіра"] * 3 + ["звʼязок"] * 2

STAGE_INSTRUCTIONS = {
    "залучення": ("Тип: ЗАЛУЧЕННЯ. Корисне й цікаве на тему «{theme}» — практична порада, "
                  "розвінчання міфу або вправа. Наприкінці мʼякий заклик зберегти або спробувати сьогодні."),
    "довіра": ("Тип: ДОВІРА. Розкрий тему «{theme}» глибше: поясни психологічний механізм простими "
               "словами, розбери типову ситуацію — що всередині людини і що з цим робити."),
    "звʼязок": ("Тип: ЗВʼЯЗОК. Навколо теми «{theme}» живий короткий текст із рефлексивним питанням "
                "або запрошенням поділитися думкою в коментарях."),
}

IMAGE_STYLES = [
    "minimalist line art illustration, single accent color on cream background",
    "soft watercolor illustration, gentle muted tones",
    "warm cozy flat illustration, editorial style",
    "atmospheric photography, soft natural light, shallow depth of field",
    "abstract paper-cut collage, calm earthy palette",
    "dreamy gouache painting, soft pastel palette",
]

ACCURACY = (
    "\n\nТОЧНІСТЬ І НАУКОВІСТЬ (обовʼязково):\n"
    "- Спирайся лише на усталені, перевірені психологічні знання. Жодних вигаданих фактів.\n"
    "- НЕ вигадуй конкретних цифр, відсотків, назв досліджень, імен учених, цитат. "
    "Не знаєш точно — формулюй загально й коректно.\n"
    "- Не став діагнозів, не давай небезпечних порад; складні стани — мʼяко до фахівця.\n"
    "- Перед відповіддю подумки перевір: чи правда, чи коректно, чи не вводить в оману. Сумнівне — прибери.\n"
)

ANTISHABLON = (
    "\n\nЗАБОРОНЕНО (ознаки ШІ): звороти «Вона думала… а виявилось…», «Це не про…, це про…», "
    "«Уявіть собі…», «У світі, де…», «У сучасному світі», «І ось тут починається найцікавіше», "
    "«Спойлер:», «Памʼятай: ти не один», «Кожен з нас»; драматичні обриви через крапку; пафос, гасла, "
    "коучингова риторика; стиль, що впізнається як ChatGPT.\n"
    "ЗАМІСТЬ ШАБЛОНІВ: конкретні живі приклади й мікросценки, як говорить жива людина.\n"
)

HOOK = ("\nГАЧОК: перший рядок має чіпляти за 1 секунду — несподіване спостереження, питання або "
        "конкретна сцена. НЕ починай з визначення поняття.\n")

ENGAGE = ("\nЗАЛУЧЕННЯ: наприкінці природний мікрозаклик до дії — поставити питання в коментарі, "
          "зберегти, поділитися думкою. Без тиску.\n")


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


def maybe_consult_line():
    return ("Якщо тема відгукнулась і потрібна підтримка — " + CONSULT_CONTACT + ". ") if SALE_MODE else ""


def generate_video(theme):
    """ГОЛОВНЕ: відео-ідея з готовим розмовним текстом під камеру + фейслес-варіант."""
    prompt = (
        "Ти — Тетяна Вінар, психологиня, канал «Психологічно чесно». Тема: «" + theme + "». "
        "Зроби ідею короткого ВЕРТИКАЛЬНОГО відео (Reels 9:16, 20-45 сек) — це ГОЛОВНИЙ контент дня."
        + ACCURACY + HOOK +
        "\nДай у такому форматі (звичайний текст, без markdown):\n"
        "🎬 ІДЕЯ: (коротка назва)\n"
        "🪝 Гачок (перші 3 секунди, що сказати/показати):\n\n"
        "🗣 ВАРІАНТ А — ГОВОРИТИ В КАМЕРУ\n"
        "Готовий розмовний монолог, який можна просто зачитати/переказати (живою усною мовою, "
        "короткі фрази, як говорять люди, 20-40 секунд звучання). Дай ПОВНИЙ текст, готовий до зйомки.\n\n"
        "🙈 ВАРІАНТ Б — ФЕЙСЛЕС (без обличчя)\n"
        "Ті самі думки як озвучка за кадром АБО текст на екран по кадрах. Дай кадри + повний текст/субтитри.\n\n"
        "🎵 Музика (настрій, з бібліотеки Instagram/Facebook):\n"
        "📲 Підпис до публікації (1-2 живі речення + 2-3 хештеги + мікрозаклик коментувати):"
        + ANTISHABLON + "\nЖива людська українська, тепло й конкретно."
    )
    return ask_gemini(prompt, temperature=0.85)


def generate_post(theme, stage):
    instr = STAGE_INSTRUCTIONS[stage].format(theme=theme)
    prompt = (
        "Ти — Тетяна Вінар, психологиня, канал «Психологічно чесно». Пишеш живою розмовною "
        "українською, тепло, на «ти». Це КОРОТКА підтримка до відео дня.\n\n"
        + instr + " " + maybe_consult_line() +
        "\nКОРОТКО: одна думка по суті, живий приклад, конкретна дія. Завершені речення."
        + ACCURACY + HOOK + ENGAGE + ANTISHABLON +
        "\nВАЖЛИВО: саме цей конкретний кут, не загальні слова. Обсяг 350-600 символів. "
        "2-3 хештеги. Без markdown, емодзі помірно. Поверни ЛИШЕ текст поста."
    )
    return ask_gemini(prompt)


def generate_test(theme):
    prompt = (
        "Психологиня. Короткий тест-самоперевірка на тему «" + theme + "», на логіці реальних "
        "опитувальників." + ACCURACY +
        "\nФОРМАТ (без markdown):\n🧠 ТЕСТ: (назва)\n\nІнструкція: бали 0-3 за питання.\n\n"
        "1.\n2.\n3.\n4.\n5.\n\nПорахуй бали 👇\n\nРЕЗУЛЬТАТ:\n0-5 —\n6-10 —\n11-15 — (за потреби до фахівця)\n\n"
        "Наприкінці: «Це тест для самоспостереження, а не медичний діагноз.»" + ANTISHABLON +
        "\nПоверни ЛИШЕ тест."
    )
    return ask_gemini(prompt, temperature=0.7)


def generate_choice(theme):
    prompt = (
        "Психологиня. Вправа «обери образ» на тему «" + theme + "»." + ACCURACY +
        "\nФОРМАТ (без markdown):\n🃏 ОБЕРИ ОБРАЗ\n\n(вступ 1-2 речення)\n\n1️⃣\n2️⃣\n3️⃣\n4️⃣\n\n"
        "Обрав(ла)? 👇\n\n1️⃣ —\n2️⃣ —\n3️⃣ —\n4️⃣ —\n\n"
        "Наприкінці: «Це не передбачення, а привід поміркувати про себе.»\nБез езотерики." + ANTISHABLON +
        "\nПоверни ЛИШЕ вправу."
    )
    return ask_gemini(prompt, temperature=0.85)


def generate_poll(theme):
    raw = ask_gemini(
        f"Опитування для каналу психології на тему «{theme}». Рядок 1 — питання (до 90 симв.), "
        "далі 3-4 варіанти. Без кліше, нумерації, хештегів." + ACCURACY, temperature=0.7,
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
            "Опиши ОДНУ коротку англійською сцену (макс 14 слів), що символічно передає тему: "
            f"«{theme}». Метафора, без тексту, без облич. Поверни лише англійський опис.",
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


def current_subtopic():
    day = int(time.time() // 86400)
    return UMBRELLAS[(day // 7) % len(UMBRELLAS)][day % 7]


def pick_theme_and_stage():
    day = int(time.time() // 86400)
    return current_subtopic(), FUNNEL[day % len(FUNNEL)]


def send_support_content(theme, stage):
    """Коротка підтримка до відео: інколи тест/образ/опитування, інакше короткий пост."""
    if stage == "залучення":
        roll = random.random()
        if roll < 0.2:
            try:
                q, opts = generate_poll(theme)
                send_poll(q, opts)
                return
            except Exception as e:
                print("Опитування не вдалося:", e, file=sys.stderr)
        elif roll < 0.4:
            t = generate_test(theme)
            try:
                send_photo(get_image(make_image_prompt(theme)), t)
            except Exception:
                send_text(t)
            return
        elif roll < 0.6:
            c = generate_choice(theme)
            try:
                send_photo(get_image(make_choice_image_prompt()), c)
            except Exception:
                send_text(c)
            return
    post = generate_post(theme, stage)
    try:
        send_photo(get_image(make_image_prompt(theme)), post)
    except Exception:
        send_text(post)


def main():
    print(">>> MAIN ПОЧАВСЯ", flush=True)
    print("Режим:", "ЧЕРНЕТКА в особисті" if REVIEW_CHAT_ID else "одразу в канал", flush=True)
    theme, stage = pick_theme_and_stage()
    print("Кут:", theme, "| Стадія:", stage, flush=True)

    # ВІДЕО — ГОЛОВНЕ, першим
    try:
        idea = generate_video(theme)
        send_text("🎥 ВІДЕО ДНЯ (головне) — тема: " + theme + "\n\n" + idea)
        print(">>> Надіслано відео.", flush=True)
    except Exception as e:
        print(">>> Відео не вдалося:", e, file=sys.stderr, flush=True)

    # Пост — коротка підтримка
    time.sleep(2)
    send_support_content(theme, stage)
    print(">>> Надіслано підтримку.", flush=True)


if __name__ == "__main__":
    main()
