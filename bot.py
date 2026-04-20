import os
from datetime import datetime
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
CHANNEL_ID = -1003937370541

PHONE, NAME, AGE, GENDER, LOOKING_FOR, CITY, BIO, PHOTO = range(8)

users_data = {}
started_users = set()
likes_data = {}       # {user_id: set(target_ids)}
viewed_data = {}      # {user_id: set(viewed_ids)}
matches_data = set()  # {(small_id, big_id)}

geolocator = Nominatim(user_agent="friend_match_uz_bot")

# Qisqartirishlar
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
    "Toshkent": "Toshkent",
    "Xorazm Region": "Xorazm",
    "Samarqand Region": "Samarqand",
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
    [["❤️ Like", "➡️ Keyingisi"], ["⬅️ Qaytish"]],
    resize_keyboard=True
)


def is_profile_complete(user_id: int) -> bool:
    profile = users_data.get(user_id, {})
    required = ["phone", "name", "age", "gender", "looking_for", "city", "bio", "photo"]
    return all(k in profile for k in required)


def get_match_pair(user1: int, user2: int):
    return tuple(sorted((user1, user2)))


def fits_preference(viewer_id: int, candidate_id: int) -> bool:
    viewer = users_data.get(viewer_id, {})
    candidate = users_data.get(candidate_id, {})

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


async def send_main_menu(update: Update):
    await update.message.reply_text("Asosiy menyu", reply_markup=main_menu)


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

    users_data[user_id] = {
        "telegram_id": user_id,
        "telegram_username": update.effective_user.username,
        "phone": contact.phone_number,
        "location": None,
    }

    await update.message.reply_text(
        "Ismingizni yozing:",
        reply_markup=ReplyKeyboardRemove(),
    )
    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    name = update.message.text.strip()

    if len(name) < 2:
        await update.message.reply_text("Ismingizni to‘g‘ri kiriting.")
        return NAME

    users_data[user_id]["name"] = name
    await update.message.reply_text("Yoshingiz?")
    return AGE


async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    age_text = update.message.text.strip()

    if not age_text.isdigit():
        await update.message.reply_text("Yoshni raqam bilan yozing.")
        return AGE

    age = int(age_text)

    if age < 18 or age > 100:
        await update.message.reply_text("18 dan 100 gacha yosh kiriting.")
        return AGE

    users_data[user_id]["age"] = age

    keyboard = ReplyKeyboardMarkup(
        [["👨 Erkak", "👩 Ayol"]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    await update.message.reply_text("Jinsingiz:", reply_markup=keyboard)
    return GENDER


async def get_gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if text not in ["👨 Erkak", "👩 Ayol"]:
        await update.message.reply_text("Tugmalardan birini tanlang.")
        return GENDER

    users_data[user_id]["gender"] = text

    keyboard = ReplyKeyboardMarkup(
        [["👨 Erkak", "👩 Ayol"], ["🔄 Farqi yo‘q"]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    await update.message.reply_text("Kim bilan tanishmoqchisiz?", reply_markup=keyboard)
    return LOOKING_FOR


async def get_looking_for(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if text not in ["👨 Erkak", "👩 Ayol", "🔄 Farqi yo‘q"]:
        await update.message.reply_text("Tugmalardan birini tanlang.")
        return LOOKING_FOR

    users_data[user_id]["looking_for"] = text

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
    user_id = update.effective_user.id

    if update.message.location:
        lat = update.message.location.latitude
        lon = update.message.location.longitude

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
                if not full_location:
                    full_location = "Noma’lum"
            else:
                full_location = "Noma’lum"

        except Exception as e:
            print(f"Lokatsiyadan shahar aniqlashda xatolik: {e}")
            full_location = "Noma’lum"

        users_data[user_id]["city"] = full_location
        users_data[user_id]["location"] = (lat, lon)

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

        users_data[user_id]["city"] = text
        users_data[user_id]["location"] = None

    skip_keyboard = ReplyKeyboardMarkup(
        [["⏭ O‘tkazib yuborish"]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    await update.message.reply_text("O‘zingiz haqingizda yozing:", reply_markup=skip_keyboard)
    return BIO


async def get_bio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if text == "⏭ O‘tkazib yuborish":
        users_data[user_id]["bio"] = "yo‘q"
    else:
        users_data[user_id]["bio"] = text

    await update.message.reply_text(
        "Profil rasmingizni yuboring:",
        reply_markup=ReplyKeyboardRemove(),
    )
    return PHOTO


async def get_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id

    if not update.message.photo:
        await update.message.reply_text("Iltimos, rasm yuboring.")
        return PHOTO

    photo_id = update.message.photo[-1].file_id
    users_data[user_id]["photo"] = photo_id

    profile = users_data[user_id]

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

        if profile.get("location"):
            lat, lon = profile["location"]
            await context.bot.send_location(
                chat_id=CHANNEL_ID,
                latitude=lat,
                longitude=lon
            )

    except Exception as e:
        print(f"Kanalga yuborishda xatolik: {e}")

    return ConversationHandler.END


async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in users_data or not is_profile_complete(user_id):
        await update.message.reply_text(
            "Sizda hali to‘liq profil yo‘q. /start bosing.",
            reply_markup=main_menu
        )
        return

    profile = users_data[user_id]

    await update.message.reply_photo(
        photo=profile["photo"],
        caption=build_profile_caption(profile, "👤 Sizning profilingiz"),
        reply_markup=profile_menu
    )


async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_main_menu(update)


def find_next_candidate(user_id: int):
    viewed = viewed_data.setdefault(user_id, set())

    candidates = []
    for other_id in users_data.keys():
        if other_id == user_id:
            continue
        if not is_profile_complete(other_id):
            continue
        if not fits_preference(user_id, other_id):
            continue

        other_pref = users_data[other_id].get("looking_for")
        your_gender = users_data[user_id].get("gender")
        if other_pref != "🔄 Farqi yo‘q" and other_pref != your_gender:
            continue

        candidates.append(other_id)

    if not candidates:
        return None

    for candidate_id in candidates:
        if candidate_id not in viewed:
            return candidate_id

    viewed.clear()
    return candidates[0] if candidates else None


async def show_next_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in users_data or not is_profile_complete(user_id):
        await update.message.reply_text(
            "Avval profilingizni to‘liq yarating. /start bosing.",
            reply_markup=main_menu
        )
        return

    likes_data.setdefault(user_id, set())
    viewed_data.setdefault(user_id, set())

    candidate_id = find_next_candidate(user_id)

    if candidate_id is None:
        await update.message.reply_text(
            "Hozircha profillar yo‘q 🙂",
            reply_markup=main_menu
        )
        return

    context.user_data["current_profile_id"] = candidate_id

    profile = users_data[candidate_id]
    await update.message.reply_photo(
        photo=profile["photo"],
        caption=build_profile_caption(profile, "🌐 Profil"),
        reply_markup=browse_menu
    )


async def browse_profiles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_next_profile(update, context)


async def like_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    target_id = context.user_data.get("current_profile_id")

    if not target_id:
        await update.message.reply_text(
            "Avval 🚀 Boshlash ni bosing.",
            reply_markup=main_menu
        )
        return

    likes_data.setdefault(user_id, set()).add(target_id)
    viewed_data.setdefault(user_id, set()).add(target_id)

    my_profile = users_data.get(user_id, {})
    target_profile = users_data.get(target_id, {})

    my_name = my_profile.get("name", "Foydalanuvchi")
    target_name = target_profile.get("name", "Foydalanuvchi")

    # Like haqida xabar target userga
    try:
        await context.bot.send_message(
            chat_id=target_id,
            text=(
                f"❤️ Sizni kimdir yoqtirdi!\n\n"
                f"👤 Ism: {my_name}\n"
                f"Botga kirib 🚀 Boshlash ni bosing."
            ),
        )
    except Exception as e:
        print(f"Like xabarini yuborishda xatolik: {e}")

    matched_now = False

    if user_id in likes_data.get(target_id, set()):
        pair = get_match_pair(user_id, target_id)

        if pair not in matches_data:
            matches_data.add(pair)
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

    if not matched_now:
        await update.message.reply_text("Like yuborildi ❤️")

    context.user_data.pop("current_profile_id", None)
    await show_next_profile(update, context)


async def next_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    target_id = context.user_data.get("current_profile_id")

    if not target_id:
        await update.message.reply_text(
            "Avval 🚀 Boshlash ni bosing.",
            reply_markup=main_menu
        )
        return

    viewed_data.setdefault(user_id, set()).add(target_id)
    context.user_data.pop("current_profile_id", None)

    await show_next_profile(update, context)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Bekor qilindi.",
        reply_markup=main_menu,
    )
    return ConversationHandler.END


def main():
    if not TOKEN:
        raise ValueError("TOKEN topilmadi. Railway Variables ga TOKEN qo‘shing.")

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
    app.add_handler(MessageHandler(filters.Regex("^➡️ Keyingisi$"), next_profile))

    print("Bot ishladi")
    app.run_polling()


if __name__ == "__main__":
    main()
