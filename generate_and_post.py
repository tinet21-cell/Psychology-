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
CHANNEL_LINK = "https://t.me/vinartati"

NICHE = (
    "АВДИТОРІЯ КАНАЛУ (тримай в голові, НЕ вставляй буквально): "
    "люди з тривогою або суміжними станами — ті хто постійно турбується, "
    "не може зупинитись, контролює все навколо, важко спить, виснажені але не відпочивають. "
    "Часто не знають що це тривога — вважають що просто такий характер або слабкість. "
    "ЗВЕРТАННЯ гендерно нейтральне — на «ти», уникай «вона»/«він».\n"
)

UMBRELLAS = [
    [
        "як тривога говорить через тіло поки ми не чуємо слів",
        "серце б'ється — і вже не знаєш це страх чи небезпека",
        "чому м'язи напружені навіть коли нічого не відбувається",
        "тривога і дихання: чому так важко зробити повний вдих",
        "тіло як перший сигнал тривоги якого ми не чуємо",
        "фізична втома від тривоги — виснажився але нічого не робив",
        "маленька тілесна практика яка справді знижує тривогу за 2 хвилини",
    ],
    [
        "як тривога змінює те як ми спілкуємось із близькими",
        "коли через тривогу починаєш контролювати партнера",
        "чому тривожна людина часто обирає емоційно недоступних",
        "конфлікт як розрядка — чому сварки іноді приносять полегшення",
        "тривога і ревнощі — звідки страх втратити",
        "як сказати близькому що тобі тривожно і бути почутим",
        "самотність у стосунках як форма тривоги",
    ],
    [
        "чому тривога і потреба все контролювати — це одне",
        "ілюзія контролю: що насправді ми намагаємось приборкати",
        "перфекціонізм як спроба убезпечити себе від тривоги",
        "що відбувається коли відпускаєш контроль — і чому це страшно",
        "контрольні списки і ритуали — коли порядок стає залежністю",
        "різниця між здоровою відповідальністю і тривожним контролем",
        "перший крок до того щоб жити з невизначеністю",
    ],
    [
        "як тривога руйнує впевненість у собі зсередини",
        "синдром самозванця — це тривога яка говорить твоїм голосом",
        "порівняння себе з іншими як тривожна петля",
        "чому тривожні люди часто надто самокритичні",
        "як хронічна тривога змінює ставлення до власних рішень",
        "самоцінність яка не залежить від результату — як це взагалі можливо",
        "маленький крок до більшої довіри собі",
    ],
    [
        "чому тривога активується саме ввечері і вночі",
        "думки по колу перед сном — що за цим стоїть",
        "страх не заснути як окрема форма тривоги",
        "нічна катастрофізація — коли все здається безнадійним о третій ночі",
        "тіло не може спати бо мозок не відпускає",
        "ранкова тривога: чому прокидаєшся вже стиснутим",
        "проста вечірня практика щоб знизити тривогу перед сном",
    ],
    [
        "тривога на роботі — як вона виглядає і чому її не помічають",
        "прокрастинація як симптом тривоги а не лінощів",
        "страх помилки який паралізує більше ніж сама помилка",
        "коли перфекціонізм зупиняє а не допомагає",
        "тривога перед важливою розмовою або презентацією",
        "синдром вигорання і тривога — що спільного",
        "як тривога змушує брати більше ніж можеш",
    ],
    [
        "чому тривожній людині так складно казати «ні»",
        "страх конфлікту як причина розмитих меж",
        "як тривога змушує погоджуватись — і потім шкодувати",
        "вина після відмови: звідки вона і що з нею робити",
        "коли межі є але їх постійно порушують",
        "тривога і надмірне пояснення своїх рішень іншим",
        "маленький крок: одна межа яку можна встановити сьогодні",
    ],
    [
        "страх близькості — як тривога заважає відкритись",
        "чому тривожні люди тримають людей на відстані",
        "коли хочеш близькості але боїшся бути відкинутим",
        "тривога і прив'язаність — як це формується і як впливає",
        "ревнощі і власницькість як тривожна реакція",
        "як говорити про свою тривогу партнеру",
        "безпечні стосунки як ресурс проти тривоги",
    ],
]

FUNNEL = ["залучення"] * 5 + ["довіра"] * 3 + ["звʼязок"] * 2

STAGE_INSTRUCTIONS = {
    "залучення": (
        "Тип: ЗАЛУЧЕННЯ. На тему «{theme}» дай корисне й впізнаване — практичну пораду, "
        "розвінчання поширеного myth про тривогу, або просту вправу. "
        "Щоб хотілось зберегти й переслати. Наприкінці мʼякий заклик спробувати сьогодні."
    ),
    "довіра": (
        "Тип: ДОВІРА. Веди СТРОГО за формулою: "
        "1) конкретний прояв «{theme}» у побуті — жива сцена; "
        "2) чому так — механізм тривоги простими словами; "
        "3) що з цим робити — один конкретний крок; "
        "4) інсайт-висновок одним реченням. "
        "Не пропускай кроки."
    ),
    "звʼязок": (
        "Тип: ЗВʼЯЗОК. Навколо теми «{theme}» живий короткий текст із рефлексивним питанням "
        "або запрошенням поділитися в коментарях. Тепло, без повчань."
    ),
}

STORY_FORMATS = {
    "підслухана розмова": (
        "Формат ПІДСЛУХАНА РОЗМОВА. Подай думку про «{theme}» через чужий випадковий діалог "
        "(черга, транспорт, кафе) — спостереження збоку, без повчань."
    ),
    "відкритий фінал": (
        "Формат ВІДКРИТИЙ ФІНАЛ. Поміркуй над «{theme}» як над питанням без однозначної відповіді. "
        "Чесно — що відповідь неоднозначна, поділись роздумом."
    ),
    "хибна перемога": (
        "Формат ХИБНА ПЕРЕМОГА. Розкрий «{theme}» через ідею: людина досягає бажаного й розуміє "
        "що справа була не в цьому. Про тривогу і справжні потреби."
    ),
    "виправданий опонент": (
        "Формат ВИПРАВДАНИЙ ОПОНЕНТ. Розкрий «{theme}» через ідею: те що дратувало або критика "
        "з якою не погоджувались — згодом виявилась слушною."
    ),
    "паралельна структура": (
        "Формат ПАРАЛЕЛЬНА СТРУКТУРА. Теза про «{theme}», потім РІВНО три приклади в однаковій "
        "граматичній формі через тире, наприкінці — коротка формула-висновок. Ритмічно."
    ),
    "список впізнавання": (
        "Формат СПИСОК ВПІЗНАВАННЯ. Дай 5-7 побутових ситуацій навколо «{theme}» де читач впізнає "
        "себе хоч в одній (напр. «хотів відпочити, а замість цього…»). Чим конкретніше — тим краще."
    ),
    "розбір фрази": (
        "Формат РОЗБІР ФРАЗИ. Візьми типову фразу яку чують тривожні люди навколо «{theme}» "
        "(напр. «та розслабся вже», «ти придумуєш», «все буде добре»). "
        "Покажи що насправді стоїть за цією фразою."
    ),
    "до і після": (
        "Формат ДО І ПІСЛЯ. Покажи узагальнений образ людини «до» (як виглядає тривога в «{theme}») "
        "і «після» (коли щось змінилось). Конкретні деталі дня, без видавання за реальний випадок."
    ),
}

INSIGHT_TOPICS = [
    "момент коли зрозуміла що моя тривога захищає мене від чогось",
    "коли помітила що намагаюсь контролювати те чого не можна",
    "перша думка після того як щось іде не за планом",
    "що насправді стоїть за страхом помилитись",
    "коли тривога говорить чужим голосом а не моїм",
    "маленька ситуація яка показала мені щось велике про себе",
    "момент коли вирішила довіряти собі попри невизначеність",
]

IMAGE_STYLES = [
    "minimalist line art illustration, single accent color on cream background",
    "soft watercolor illustration, gentle muted tones",
    "warm cozy flat illustration, editorial style",
    "atmospheric photography, soft natural light, shallow depth of field",
    "abstract paper-cut collage, calm earthy palette",
    "dreamy gouache painting, soft pastel palette",
]

ACCURACY = (
    "\n\nТОЧНІСТЬ (обовʼязково): лише усталені перевірені психологічні знання. "
    "Жодних вигаданих фактів, цифр, назв досліджень, цитат. "
    "Не знаєш точно — формулюй загально. Не став діагнозів. "
    "Складні стани — мʼяко до фахівця. Сумнівне — прибери.\n"
)

ANTISHABLON = (
    "\n\nЗАБОРОНЕНО (забороняй САМУ КОНСТРУКЦІЮ):\n"
    "- «Це не X, а Y» у будь-якому вигляді;\n"
    "- «Це не чарівна пігулка»;\n"
    "- «Памʼятай», «Не забувай» на початку речення;\n"
    "- загальні поради без конкретики: «дбай про себе», «знайди час», «розслабся»;\n"
    "- звернення-вступи: «Привіт», «Друзі», «Доброго дня», «Знайоме відчуття коли»;\n"
    "- «Уявіть собі», «У сучасному світі», «Спойлер», «Кожен з нас»;\n"
    "- драматичні обриви через крапку; пафос, гасла, коучинг; стиль ChatGPT.\n"
    "ЗАМІСТЬ ШАБЛОНІВ: конкретні живі приклади і мікросценки.\n"
)

HOOK = (
    "\nГАЧОК: перший рядок зупиняє за секунду — конкретна сцена, питання або спостереження "
    "де тривожна людина впізнає себе. НЕ починай з визначення поняття або вступу.\n"
)

ENGAGE = (
    "\nЗАЛУЧЕННЯ: наприкінці — конкретна пропозиція зі схемою «якщо впізнав(ла) себе — "
    "напиши слово [конкретне слово] у коментарі, і я надішлю [конкретну вправу/розбір]». "
    "ЗАБОРОНЕНО: «поділись у коментарях» без конкретного слова-пароля.\n"
)


def clean_markdown(text):
    for token in ("**", "__", "##", "# "):
        text = text.replace(token, "")
    return text.strip()


def ask_gemini(prompt, temperature=0.85, timeout=120):
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": temperature}}
    last = None
    for _ in range(3):
        try:
            r = requests.post(GEMINI_URL, params={"key": GEMINI_API_KEY},
                              json=body, timeout=timeout)
            r.raise_for_status()
            text = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
            return clean_markdown(text)
        except Exception as e:
            last = e
            time.sleep(6)
    raise last


def maybe_consult_line():
    return ("Якщо тема відгукнулась і потрібна підтримка — " + CONSULT_CONTACT + ". ") if SALE_MODE else ""


def generate_card_of_day(theme):
    prompt = (
        NICHE +
        "Ти — Тетяна Вінар, психологиня, канал «Психологічно чесно». "
        "Створи КАРТУ ДНЯ на тему «" + theme + "».\n\n"
        "Карта дня — короткий психологічний «знімок» для зупинки в середині дня. "
        "Не порада. Не пояснення. Одна думка або питання яке веде всередину.\n\n"
        "ФОРМАТ (звичайний текст, без markdown):\n"
        "🃏 КАРТА ДНЯ\n\n"
        "[Коротка назва — 3-5 слів, як заголовок карти]\n\n"
        "[Одна думка або спостереження — 2-3 речення. Не повчання. "
        "Жива, точна, як слово людини якій довіряєш.]\n\n"
        "Питання дня:\n"
        "[Одне рефлексивне питання — конкретне, не загальне]\n\n"
        "#карта_дня #психологія #тривога"
        + ACCURACY + ANTISHABLON +
        "\nЖива людська українська. Без пафосу. Поверни ЛИШЕ готову карту."
    )
    return ask_gemini(prompt, temperature=0.9)


def generate_post(theme, stage):
    instr = STAGE_INSTRUCTIONS[stage].format(theme=theme)
    prompt = (
        NICHE +
        "Ти — Тетяна Вінар, психологиня, канал «Психологічно чесно». "
        "Жива розмовна українська, тепло, на «ти».\n\n"
        + instr + " " + maybe_consult_line() +
        "\nКОРОТКО: одна думка, живий приклад, конкретна дія."
        + ACCURACY + HOOK + ENGAGE + ANTISHABLON +
        "\nВАЖЛИВО: саме цей конкретний кут. 350-600 символів. 2-3 хештеги. "
        "Без markdown, емодзі помірно. Поверни ЛИШЕ текст поста."
    )
    return ask_gemini(prompt)


def generate_story_content(theme, stage):
    prompt = (
        NICHE +
        "Ти — Тетяна Вінар, психологиня. Створи контент для Instagram Stories "
        "на тему «" + theme + "».\n\n"
        "Сторі — дуже короткий формат. Текст максимально лаконічний і чіпляючий.\n\n"
        "Дай 3 варіанти сторі (різні формати):\n\n"
        "СТОРІ 1 — Питання для опитування:\n"
        "[Одне коротке питання + 2 варіанти відповіді]\n\n"
        "СТОРІ 2 — Цитата або думка (текст на фото або кольоровий фон):\n"
        "[1-2 рядки які будуть накладені на зображення]\n\n"
        "СТОРІ 3 — Заклик перейти в пост або канал:\n"
        "[Короткий текст + що людина знайде якщо перейде в канал " + CHANNEL_LINK + "]\n\n"
        + ANTISHABLON +
        "\nЖива людська українська, без пафосу. Поверни лише готовий контент."
    )
    return ask_gemini(prompt, temperature=0.85)


def generate_story(theme):
    name = random.choice(list(STORY_FORMATS))
    instr = STORY_FORMATS[name].format(theme=theme)
    prompt = (
        NICHE + "Ти — Тетяна Вінар, психологиня. Жива розмовна українська, тепло.\n\n"
        + instr + "\n"
        + ACCURACY + HOOK + ENGAGE + ANTISHABLON +
        "\n400-700 символів. 2-3 хештеги. Без markdown. Поверни ЛИШЕ текст поста."
    )
    return name, ask_gemini(prompt)


def generate_carousel(theme):
    prompt = (
        NICHE +
        "Ти — Тетяна Вінар, психологиня. Зроби КАРУСЕЛЬ для Instagram на тему «"
        + theme + "» (6 слайдів), мінімум тексту на слайді."
        + ACCURACY + HOOK +
        "\nФормат (без markdown):\n"
        "СЛАЙД 1 (обкладинка-гачок): сильний короткий заголовок (питання/парадокс/факт).\n"
        "СЛАЙД 2: підзаголовок + 1-2 рядки.\n"
        "СЛАЙД 3: аспект + 1-2 рядки.\n"
        "СЛАЙД 4: аспект + 1-2 рядки.\n"
        "СЛАЙД 5: головна думка/висновок.\n"
        "СЛАЙД 6 (CTA): зберегти, написати в коментарі, "
        "«Більше — у телеграм-каналі: " + CHANNEL_LINK + "».\n\n"
        "📲 ПІДПИС ПІД INSTAGRAM: перші 2 рядки — гачок, далі розкриття, "
        "заклик коментувати + 3-4 хештеги.\n"
        "📘 ПІДПИС ПІД FACEBOOK: тепліший тон, без хештегів або 1. "
        "Починається ІНШИМ гачком ніж Instagram."
        + ANTISHABLON + "\nЖива людська українська."
    )
    return ask_gemini(prompt)


def insight_scaffold():
    topic = random.choice(INSIGHT_TOPICS)
    return (
        "💡 ІНСАЙТ ДНЯ (наповни своїм — публікуй лише якщо відгукнеться)\n\n"
        f"Тема-кут: {topic}\n\n"
        "Каркас:\n"
        "— Гачок: почни з конкретної дрібниці чи сцени, не зі вступу.\n"
        "— Інсайт: який несподіваний висновок ти з цього винесла.\n"
        "— Чому так: механізм тривоги простими словами.\n"
        "— Питання до читача наприкінці.\n\n"
        "Реальний випадок АБО загальне спостереження — наскільки комфортно. "
        "Особисте відкривай скільки сама хочеш."
    )


def generate_test(theme):
    prompt = (
        NICHE + "Психологиня. Короткий тест-самоперевірка на тему «" + theme
        + "», на логіці реальних опитувальників тривоги."
        + ACCURACY +
        "\nФОРМАТ (без markdown):\n"
        "🧠 ТЕСТ: (назва)\n\n"
        "Інструкція: бали 0-3 за питання.\n\n"
        "1.\n2.\n3.\n4.\n5.\n\n"
        "Порахуй бали 👇\n\n"
        "РЕЗУЛЬТАТ:\n"
        "0-5 —\n6-10 —\n11-15 — (за потреби мʼяко до фахівця)\n\n"
        "Наприкінці: «Це тест для самоспостереження, а не медичний діагноз.»"
        + ANTISHABLON +
        "\nПоверни ЛИШЕ тест."
    )
    return ask_gemini(prompt, temperature=0.7)


def generate_choice(theme):
    prompt = (
        NICHE + "Психологиня. Вправа «обери образ» на тему «" + theme + "»."
        + ACCURACY +
        "\nФОРМАТ (без markdown):\n"
        "🃏 ОБЕРИ ОБРАЗ\n\n(вступ 1-2 речення)\n\n"
        "1️⃣\n2️⃣\n3️⃣\n4️⃣\n\n"
        "Обрав(ла)? 👇\n\n"
        "1️⃣ —\n2️⃣ —\n3️⃣ —\n4️⃣ —\n\n"
        "Наприкінці: «Це не передбачення, а привід поміркувати про себе.»\n"
        "Без езотерики." + ANTISHABLON +
        "\nПоверни ЛИШЕ вправу."
    )
    return ask_gemini(prompt, temperature=0.85)


def generate_poll(theme):
    raw = ask_gemini(
        NICHE + f"Опитування для психологічного каналу на тему «{theme}». "
        "Рядок 1 — питання (до 90 симв.), далі 3-4 варіанти. "
        "Без кліше, нумерації, хештегів." + ACCURACY,
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
            "Опиши ОДНУ коротку англійською сцену (макс 14 слів), що символічно передає "
            f"психологічну тему тривоги: «{theme}». Метафора, без тексту, без облич. "
            "Поверни лише англійський опис.",
            temperature=1.0, timeout=60,
        ).replace("\n", " ").strip()
    except Exception:
        scene = "a calm symbolic scene about anxiety and inner stillness"
    return f"{scene}, {style}, no text, high quality"


def make_choice_image_prompt():
    return (
        "four symbolic cards in a row, minimalist illustration, "
        "calm muted palette, soft watercolor, no text, high quality"
    )


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
    day = int(time.time() // 86400)

    # Карусель раз на 5 днів
    if day % 5 == 1:
        try:
            carousel = generate_carousel(theme)
            send_text(
                "🎠 КАРУСЕЛЬ ДЛЯ INSTAGRAM/FB — тема: " + theme +
                "\n(оформи в Canva → постни в Instagram і Facebook)\n\n" + carousel
            )
            print(">>> Надіслано карусель.", flush=True)
        except Exception as e:
            print(">>> Карусель не вдалася:", e, file=sys.stderr)
        return

    # Інсайт-каркас раз на 5 днів
    if day % 5 == 0:
        send_text(insight_scaffold())
        print(">>> Надіслано інсайт-каркас.", flush=True)
        return

    # Сторі-контент раз на 5 днів
    if day % 5 == 3:
        try:
            story_content = generate_story_content(theme, stage)
            send_text(
                "📱 СТОРІ ДЛЯ INSTAGRAM — тема: " + theme +
                "\n(3 варіанти сторі під одну тему)\n\n" + story_content
            )
            print(">>> Надіслано сторі-контент.", flush=True)
        except Exception as e:
            print(">>> Сторі не вдалися:", e, file=sys.stderr)
        return

    # Сюжетний формат раз на 5 днів
    if day % 5 == 2:
        name, story = generate_story(theme)
        print("Сюжетний формат:", name, flush=True)
        try:
            send_photo(get_image(make_image_prompt(theme)), story)
        except Exception:
            send_text(story)
        return

    # Залучення: тест / образ / опитування / пост
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

    # Звичайний пост
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

    # КАРТА ДНЯ — завжди першою
    try:
        card = generate_card_of_day(theme)
        send_text(card)
        print(">>> Надіслано карту дня.", flush=True)
    except Exception as e:
        print(">>> Карта дня не вдалася:", e, file=sys.stderr, flush=True)

    time.sleep(2)

    # Підтримуючий контент
    send_support_content(theme, stage)
    print(">>> Готово.", flush=True)


if __name__ == "__main__":
    main()
