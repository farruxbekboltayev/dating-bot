import os
from datetime import datetime
from typing import Optional, Tuple, List

import psycopg
from geopy.geocoders import Nominatim
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    KeyboardButton,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
CHANNEL_ID = -1003937370541

PHONE, NAME, AGE, GENDER, LOOKING_FOR, CITY, BIO, PHOTO = range(8)

geolocator = Nominatim(user_agent="friend_match_uz_bot")

state_map = {
    "Illinois": "IL",
    "California": "CA",
    "New York": "NY",
    "Texas": "TX",
    "Florida": "FL",
    "Pennsylvania": "PA",
    "Ohio": "OH",
    "Michigan": "MI",
    "New Jersey": "NJ",
    "Virginia": "VA",
    "Washington": "WA",
    "Arizona": "AZ",
    "Georgia": "GA",
    "North Carolina": "NC",
    "South Carolina": "SC",
    "Massachusetts": "MA",
    "Maryland": "MD",
    "Missouri": "MO",
    "Indiana": "IN",
    "Colorado": "CO",
    "Nevada": "NV",
    "Utah": "UT",
    "Oregon": "OR",
    "Minnesota": "MN",
    "Wisconsin": "WI",
    "Tashkent": "Toshkent",
    "Xorazm Region": "Xorazm",
    "Samarkand Region": "Samarqand",
    "Bukhara Region": "Buxoro",
    "Andijan Region": "Andijon",
    "Namangan Region": "Namangan",
    "Fergana Region": "Farg‘ona",
    "Kashkadarya Region": "Qashqadaryo",
    "Surxondaryo Region": "Surxondaryo",
    "Jizzakh Region": "Jizzax",
    "Sirdaryo Region": "Sirdaryo",
    "Navoiy Region": "Navoiy",
    "Republic of Karakalpakstan": "Qoraqalpog‘iston",
}

country_map = {
    "United States": "USA",
    "Uzbekistan": "UZ",
    "Russia": "RU",
    "Kazakhstan": "KZ",
    "Turkey": "TR",
}

main_menu = ReplyKeyboardMarkup(
    [["👤 Profil", "🚀 Boshlash"]],
    resize_keyboard=True
)

profile_menu = ReplyKeyboardMarkup(
    [["✏️ Tahrirlash"], ["⬅️ Qaytish"]],
    resize_keyboard=True
)

browse_menu = ReplyKeyboardMarkup(
    [["❤️ Like", "➡️ O‘tkazib yuborish"], ["⬅️ Qaytish"]],
    resize_keyboard=True
)


def get_conn():
    return psycopg.connect(DATABASE_URL)


def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    telegram_id BIGINT PRIMARY KEY,
                    telegram_username TEXT,
                    phone TEXT,
                    name TEXT,
                    age INT,
                    gender TEXT,
                    looking_for TEXT,
                    city TEXT,
                    bio TEXT,
                    photo TEXT,
                    lat DOUBLE PRECISION,
                    lon DOUBLE PRECISION,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS likes (
                    from_user BIGINT,
                    to_user BIGINT,
                    created_at TIMESTAMP DEFAULT NOW(),
                    PRIMARY KEY (from_user, to_user)
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS matches (
                    user1 BIGINT,
                    user2 BIGINT,
                    created_at TIMESTAMP DEFAULT NOW(),
                    PRIMARY KEY (user1, user2)
                )
            """)


def save_user(profile: dict):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO users (
                    telegram_id, telegram_username, phone, name, age,
                    gender, looking_for, city, bio, photo, lat, lon
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (telegram_id)
                DO UPDATE SET
                    telegram_username = EXCLUDED.telegram_username,
                    phone = EXCLUDED.phone,
                    name = EXCLUDED.name,
                    age = EXCLUDED.age,
                    gender = EXCLUDED.gender,
                    looking_for = EXCLUDED.looking_for,
                    city = EXCLUDED.city,
                    bio = EXCLUDED.bio,
                    photo = EXCLUDED.photo,
                    lat = EXCLUDED.lat,
                    lon = EXCLUDED.lon
            """, (
                profile["telegram_id"],
                profile.get("telegram_username"),
                profile.get("phone"),
                profile.get("name"),
                profile.get("age"),
                profile.get("gender"),
                profile.get("looking_for"),
                profile.get("city"),
                profile.get("bio"),
                profile.get("photo"),
                profile.get("lat"),
                profile.get("lon"),
            ))


def get_user(user_id: int) -> Optional[dict]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT telegram_id, telegram_username, phone, name, age,
                       gender, looking_for, city, bio, photo, lat, lon
                FROM users
                WHERE telegram_id = %s
            """, (user_id,))
            row = cur.fetchone()

    if not row:
        return None

    return {
        "telegram_id": row[0],
        "telegram_username": row[1],
        "phone": row[2],
        "name": row[3],
        "age": row[4],
        "gender": row[5],
        "looking_for": row[6],
        "city": row[7],
        "bio": row[8],
        "photo": row[9],
        "lat": row[10],
        "lon": row[11],
    }


def is_profile_complete(user_id: int) -> bool:
    profile = get_user(user_id)
    if not profile:
        return False

    required = ["phone", "name", "age", "gender", "looking_for", "city", "bio", "photo"]
    return all(profile.get(k) not in (None, "") for k in required)


def save_like(from_user: int, to_user: int):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO likes (from_user, to_user)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
            """, (from_user, to_user))


def has_like(from_user: int, to_user: int) -> bool:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 1
                FROM likes
                WHERE from_user = %s AND to_user = %s
                LIMIT 1
            """, (from_user, to_user))
            return cur.fetchone() is not None


def save_match(user1: int, user2: int):
    a, b = sorted((user1, user2))
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO matches (user1, user2)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
            """, (a, b))


def match_exists(user1: int, user2: int) -> bool:
    a, b = sorted((user1, user2))
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 1
                FROM matches
                WHERE user1 = %s AND user2 = %s
                LIMIT 1
            """, (a, b))
            return cur.fetchone() is not None


def get_all_candidate_ids() -> List[int]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT telegram_id
                FROM users
                WHERE phone IS NOT NULL
                  AND name IS NOT NULL
                  AND age IS NOT NULL
                  AND gender IS NOT NULL
                  AND looking_for IS NOT NULL
                  AND city IS NOT NULL
                  AND bio IS NOT NULL
                  AND photo IS NOT NULL
                ORDER BY created_at DESC
            """)
            return [row[0] for row in cur.fetchall()]


def fits_preference(viewer_id: int, candidate_id: int) -> bool:
    viewer = get_user(viewer_id)
    candidate = get_user(candidate_id)

    if not viewer or not candidate:
        return False

    viewer_pref = viewer.get("looking_for")
    candidate_gender = candidate.get("gender")

    if viewer_pref == "🔄 Farqi yo‘q":
        return True

    return viewer_pref == candidate_gender


def get_contact_text(profile: dict) -> str:
    username = profile.get("telegram_username")
    tg_id = profile.get("telegram_id")

    if username:
        return f"@{username}"
    if tg_id:
        return f"tg://user?id={tg_id}"
    return "username yo‘q"


def build_profile_caption(profile: dict, title: str = "👤 Profil") -> str:
    return (
        f"{title}\n\n"
        f"👤 Ism: {profile.get('name', 'yo‘q')}\n"
        f"🎂 Yosh: {profile.get('age', 'yo‘q')}\n"
        f"🚻 Jins: {profile.get('gender', 'yo‘q')}\n"
        f"🔎 Qidiryapti: {profile.get('looking_for', 'yo‘q')}\n"
        f"🌆 Shahar: {profile.get('city', 'yo‘q')}\n"
        f"📝 Bio: {profile.get('bio', 'yo‘q')}"
    )


async def send_profile_to_user(
    chat_id: int,
    candidate_id: int,
    context: ContextTypes.DEFAULT_TYPE,
    title: str = "🌐 Profil",
):
    profile = get_user(candidate_id)
    if not profile or not profile.get("photo"):
        return

    caption = build_profile_caption(profile, title)

    await context.bot.send_photo(
        chat_id=chat_id,
        photo=profile["photo"],
        caption=caption,
        reply_markup=browse_menu
    )


async def send_main_menu(update: Update):
    await update.message.reply_text("Asosiy menyu", reply_markup=main_menu)


def build_short_location(lat: float, lon: float) -> str:
    try:
        location = geolocator.reverse((lat, lon), language="en", exactly_one=True)

        if location and "address" in location.raw:
            address = location.raw["address"]

            city = (
                address.get("city")
                or address.get("town")
                or address.get("village")
                or address.get("county")
                or ""
            )

            state = address.get("state", "") or address.get("region", "")
            country = address.get("country", "")

            state = state_map.get(state, state)
            country = country_map.get(country, country)

            full_location = ", ".join(
                part for part in [city, state, country] if part
            )
            return full_location or "Noma’lum"

        return "Noma’lum"
    except Exception as e:
        print(f"Lokatsiyadan shahar aniqlashda xatolik: {e}")
        return "Noma’lum"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    started_users.add(user.id)

    username_text = f"@{user.username}" if user.username else "yo‘q"
    profile_link = f"tg://user?id={user.id}"
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=(
                "🆕 Yangi foydalanuvchi /start bosdi\n\n"
                f"👤 Ismi: {user.first_name}\n"
                f"🆔 ID: {user.id}\n"
                f"📛 Username: {username_text}\n"
                f"⏰ Vaqt: {current_time}\n"
                f"🔗 Profil: {profile_link}\n"
                f"👥 Foydalanuvchi soni: {len(started_users)}"
            ),
        )
    except Exception as e:
        print(f"Start xabarini kanalga yuborishda xatolik: {e}")

    phone_keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton("📱 Telefon raqam yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    await update.message.reply_text(
        "Assalomu alaykum.\n\nRo‘yxatdan o‘tish uchun telefon raqamingizni yuboring:",
        reply_markup=phone_keyboard,
    )
    return PHONE


async def edit_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    phone_keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton("📱 Telefon raqam yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    await update.message.reply_text(
        "Profilni qayta to‘ldirish uchun telefon raqamingizni yuboring:",
        reply_markup=phone_keyboard,
    )
    return PHONE


async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    contact = update.message.contact

    if not contact:
        await update.message.reply_text("Telefon tugmasini bosib yuboring.")
        return PHONE

    if contact.user_id != update.effective_user.id:
        await update.message.reply_text("O‘zingizning telefon raqamingizni yuboring.")
        return PHONE

    user_id = update.effective_user.id

    context.user_data["profile"] = {
        "telegram_id": user_id,
        "telegram_username": update.effective_user.username,
        "phone": contact.phone_number,
        "lat": None,
        "lon": None,
    }

    await update.message.reply_text(
        "Ismingizni yozing:",
        reply_markup=ReplyKeyboardRemove(),
    )
    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    profile = context.user_data["profile"]
    name = update.message.text.strip()

    if len(name) < 2:
        await update.message.reply_text("Ismingizni to‘g‘ri kiriting.")
        return NAME

    profile["name"] = name
    await update.message.reply_text("Yoshingiz?")
    return AGE


async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    profile = context.user_data["profile"]
    age_text = update.message.text.strip()

    if not age_text.isdigit():
        await update.message.reply_text("Yoshni raqam bilan yozing.")
        return AGE

    age = int(age_text)

    if age < 18 or age > 100:
        await update.message.reply_text("18 dan 100 gacha yosh kiriting.")
        return AGE

    profile["age"] = age

    keyboard = ReplyKeyboardMarkup(
        [["👨 Erkak", "👩 Ayol"]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    await update.message.reply_text("Jinsingiz:", reply_markup=keyboard)
    return GENDER


async def get_gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    profile = context.user_data["profile"]
    text = update.message.text.strip()

    if text not in ["👨 Erkak", "👩 Ayol"]:
        await update.message.reply_text("Tugmalardan birini tanlang.")
        return GENDER

    profile["gender"] = text

    keyboard = ReplyKeyboardMarkup(
        [["👨 Erkak", "👩 Ayol"], ["🔄 Farqi yo‘q"]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    await update.message.reply_text("Kim bilan tanishmoqchisiz?", reply_markup=keyboard)
    return LOOKING_FOR


async def get_looking_for(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    profile = context.user_data["profile"]
    text = update.message.text.strip()

    if text not in ["👨 Erkak", "👩 Ayol", "🔄 Farqi yo‘q"]:
        await update.message.reply_text("Tugmalardan birini tanlang.")
        return LOOKING_FOR

    profile["looking_for"] = text

    location_keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton("📍 Lokatsiyani yuborish", request_location=True)],
            ["✍️ Qo‘lda yozish"],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    await update.message.reply_text(
        "Qaysi shahardansiz?\nLokatsiya yuborishingiz yoki qo‘lda yozishingiz mumkin.",
        reply_markup=location_keyboard,
    )
    return CITY


async def get_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    profile = context.user_data["profile"]

    if update.message.location:
        lat = update.message.location.latitude
        lon = update.message.location.longitude

        profile["lat"] = lat
        profile["lon"] = lon
        profile["city"] = build_short_location(lat, lon)

    else:
        text = update.message.text.strip()

        if text == "✍️ Qo‘lda yozish":
            await update.message.reply_text(
                "Shahar nomini yozing:",
                reply_markup=ReplyKeyboardRemove(),
            )
            return CITY

        if len(text) < 2:
            await update.message.reply_text("Shahar nomini to‘g‘ri kiriting.")
            return CITY

        profile["city"] = text
        profile["lat"] = None
        profile["lon"] = None

    skip_keyboard = ReplyKeyboardMarkup(
        [["⏭ O‘tkazib yuborish"]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    await update.message.reply_text("O‘zingiz haqingizda yozing:", reply_markup=skip_keyboard)
    return BIO


async def get_bio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    profile = context.user_data["profile"]
    text = update.message.text.strip()

    profile["bio"] = "yo‘q" if text == "⏭ O‘tkazib yuborish" else text

    await update.message.reply_text(
        "Profil rasmingizni yuboring:",
        reply_markup=ReplyKeyboardRemove(),
    )
    return PHOTO


async def get_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    profile = context.user_data["profile"]

    if not update.message.photo:
        await update.message.reply_text("Iltimos, rasm yuboring.")
        return PHOTO

    photo_id = update.message.photo[-1].file_id
    profile["photo"] = photo_id

    save_user(profile)

    await update.message.reply_photo(
        photo=photo_id,
        caption="Profil saqlandi ✅",
        reply_markup=main_menu
    )

    username_line = (
        f"📛 Username: @{profile.get('telegram_username')}\n"
        if profile.get("telegram_username")
        else ""
    )

    caption_text = (
        "✅ Yangi profil\n\n"
        f"📱 Telefon: {profile.get('phone', 'yo‘q')}\n"
        f"👤 Ism: {profile.get('name', 'yo‘q')}\n"
        f"🎂 Yosh: {profile.get('age', 'yo‘q')}\n"
        f"🚻 Jins: {profile.get('gender', 'yo‘q')}\n"
        f"🔎 Qidiryapti: {profile.get('looking_for', 'yo‘q')}\n"
        f"🌆 Shahar: {profile.get('city', 'yo‘q')}\n"
        f"📝 Bio: {profile.get('bio', 'yo‘q')}\n"
        f"{username_line}"
        f"🆔 ID: {profile.get('telegram_id', 'yo‘q')}"
    )

    try:
        await context.bot.send_photo(
            chat_id=CHANNEL_ID,
            photo=photo_id,
            caption=caption_text
        )

        if profile.get("lat") is not None and profile.get("lon") is not None:
            await context.bot.send_location(
                chat_id=CHANNEL_ID,
                latitude=profile["lat"],
                longitude=profile["lon"]
            )

    except Exception as e:
        print(f"Kanalga yuborishda xatolik: {e}")

    context.user_data.pop("profile", None)
    return ConversationHandler.END


async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_profile_complete(user_id):
        await update.message.reply_text(
            "Sizda hali to‘liq profil yo‘q. /start bosing.",
            reply_markup=main_menu
        )
        return

    profile = get_user(user_id)

    await update.message.reply_photo(
        photo=profile["photo"],
        caption=build_profile_caption(profile, "👤 Sizning profilingiz"),
        reply_markup=profile_menu
    )


async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_main_menu(update)


def find_next_candidate(user_id: int, viewed_ids: set):
    candidates = []
    for other_id in get_all_candidate_ids():
        if other_id == user_id:
            continue
        if not fits_preference(user_id, other_id):
            continue

        other_profile = get_user(other_id)
        your_profile = get_user(user_id)

        other_pref = other_profile.get("looking_for")
        your_gender = your_profile.get("gender")
        if other_pref != "🔄 Farqi yo‘q" and other_pref != your_gender:
            continue

        candidates.append(other_id)

    if not candidates:
        return None

    for candidate_id in candidates:
        if candidate_id not in viewed_ids:
            return candidate_id

    viewed_ids.clear()
    return candidates[0] if candidates else None


async def show_next_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_profile_complete(user_id):
        await update.message.reply_text(
            "Avval profilingizni to‘liq yarating. /start bosing.",
            reply_markup=main_menu
        )
        return

    viewed_ids = set(context.user_data.get("viewed_ids", []))
    candidate_id = find_next_candidate(user_id, viewed_ids)

    context.user_data["viewed_ids"] = list(viewed_ids)

    if candidate_id is None:
        await update.message.reply_text(
            "Hozircha profillar yo‘q 🙂",
            reply_markup=main_menu
        )
        return

    context.user_data["current_profile_id"] = candidate_id

    await send_profile_to_user(
        chat_id=user_id,
        candidate_id=candidate_id,
        context=context,
        title="🌐 Profil"
    )


async def browse_profiles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_next_profile(update, context)


async def like_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    target_id = context.user_data.get("current_profile_id")
    if not target_id:
        target_id = pending_like_views.get(user_id)

    if not target_id:
        await update.message.reply_text(
            "Avval 🚀 Boshlash ni bosing.",
            reply_markup=main_menu
        )
        return

    save_like(user_id, target_id)

    viewed_ids = set(context.user_data.get("viewed_ids", []))
    viewed_ids.add(target_id)
    context.user_data["viewed_ids"] = list(viewed_ids)

    my_profile = get_user(user_id)
    target_profile = get_user(target_id)

    my_name = my_profile.get("name", "Foydalanuvchi")
    target_name = target_profile.get("name", "Foydalanuvchi")

    matched_now = False

    if not has_like(target_id, user_id):
        try:
            pending_like_views[target_id] = user_id

            await context.bot.send_message(
                chat_id=target_id,
                text=(
                    f"❤️ Sizni kimdir yoqtirdi!\n\n"
                    f"👤 {my_name} sizga like bosdi.\n"
                    f"Quyida uning profilini ko‘rishingiz mumkin:"
                ),
            )

            await send_profile_to_user(
                chat_id=target_id,
                candidate_id=user_id,
                context=context,
                title="❤️ Sizni yoqtirgan profil"
            )

        except Exception as e:
            print(f"Like xabarini yuborishda xatolik: {e}")

    if has_like(target_id, user_id):
        if not match_exists(user_id, target_id):
            save_match(user_id, target_id)
            matched_now = True

            your_contact = get_contact_text(my_profile)
            target_contact = get_contact_text(target_profile)

            await update.message.reply_text(
                "🎉 Match bo‘ldi!\n\n"
                f"👤 {target_name} ham sizni yoqtirdi.\n"
                f"Aloqa: {target_contact}",
                reply_markup=main_menu
            )

            try:
                await context.bot.send_message(
                    chat_id=target_id,
                    text=(
                        "🎉 Match bo‘ldi!\n\n"
                        f"👤 {my_name} ham sizni yoqtirdi.\n"
                        f"Aloqa: {your_contact}"
                    ),
                )
            except Exception as e:
                print(f"Match xabarini yuborishda xatolik: {e}")

            try:
                await context.bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=f"💖 Yangi match!\n\n{my_name} ❤️ {target_name}"
                )
            except Exception as e:
                print(f"Matchni kanalga yuborishda xatolik: {e}")

            if pending_like_views.get(user_id) == target_id:
                pending_like_views.pop(user_id, None)
            if pending_like_views.get(target_id) == user_id:
                pending_like_views.pop(target_id, None)

    if not matched_now:
        await update.message.reply_text("Like yuborildi ❤️")

    context.user_data.pop("current_profile_id", None)
    await show_next_profile(update, context)


async def next_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    target_id = context.user_data.get("current_profile_id")
    if not target_id:
        target_id = pending_like_views.get(user_id)

    if not target_id:
        await update.message.reply_text(
            "Avval 🚀 Boshlash ni bosing.",
            reply_markup=main_menu
        )
        return

    viewed_ids = set(context.user_data.get("viewed_ids", []))
    viewed_ids.add(target_id)
    context.user_data["viewed_ids"] = list(viewed_ids)

    context.user_data.pop("current_profile_id", None)

    if pending_like_views.get(user_id) == target_id:
        pending_like_views.pop(user_id, None)

    await show_next_profile(update, context)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Bekor qilindi.",
        reply_markup=main_menu,
    )
    context.user_data.pop("profile", None)
    return ConversationHandler.END


def main():
    if not TOKEN:
        raise ValueError("TOKEN topilmadi. Railway Variables ga TOKEN qo‘shing.")
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL topilmadi.")

    init_db()

    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(filters.Regex("^✏️ Tahrirlash$"), edit_profile),
        ],
        states={
            PHONE: [MessageHandler(filters.CONTACT, get_phone)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
            GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_gender)],
            LOOKING_FOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_looking_for)],
            CITY: [
                MessageHandler(filters.LOCATION, get_city),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_city),
            ],
            BIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_bio)],
            PHOTO: [MessageHandler(filters.PHOTO, get_photo)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.Regex("^👤 Profil$"), show_profile))
    app.add_handler(MessageHandler(filters.Regex("^⬅️ Qaytish$"), back_to_main))
    app.add_handler(MessageHandler(filters.Regex("^🚀 Boshlash$"), browse_profiles))
    app.add_handler(MessageHandler(filters.Regex("^❤️ Like$"), like_profile))
    app.add_handler(MessageHandler(filters.Regex("^➡️ O‘tkazib yuborish$"), next_profile))

    print("Bot ishladi")
    app.run_polling()


if __name__ == "__main__":
    main()
