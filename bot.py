import os
from datetime import datetime

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

likes_data = {}      # {user_id: set(target_user_ids)}
viewed_data = {}     # {user_id: set(viewed_user_ids)}
matches_data = set() # {(small_id, big_id)}

main_menu = ReplyKeyboardMarkup(
    [
        ["👤 Profil", "🌐 Profillar"],
    ],
    resize_keyboard=True
)

profile_menu = ReplyKeyboardMarkup(
    [
        ["✏️ Tahrirlash"],
        ["⬅️ Qaytish"],
    ],
    resize_keyboard=True
)

browse_menu = ReplyKeyboardMarkup(
    [
        ["❤️ Like", "⏭ Skip"],
        ["⬅️ Qaytish"],
    ],
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
        "Assalomu alaykum.\n\n"
        "Ro‘yxatdan o‘tish uchun telefon raqamingizni yuboring:",
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
        await update.message.reply_text("Ismingizni to‘g‘ri kiriting:")
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

    await update.message.reply_text(
        "Jinsingiz:",
        reply_markup=keyboard,
    )
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

    await update.message.reply_text(
        "Kim bilan tanishmoqchisiz?",
        reply_markup=keyboard,
    )
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

        users_data[user_id]["city"] = f"Lokatsiya: {lat}, {lon}"
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

    await update.message.reply_text(
        "O‘zingiz haqingizda yozing:",
        reply_markup=skip_keyboard,
    )
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

    caption_text = (
        "✅ Yangi profil\n\n"
        f"📱 Telefon: {profile.get('phone', 'yo‘q')}\n"
        f"👤 Ism: {profile.get('name', 'yo‘q')}\n"
        f"🎂 Yosh: {profile.get('age', 'yo‘q')}\n"
        f"🚻 Jins: {profile.get('gender', 'yo‘q')}\n"
        f"🔎 Qidiryapti: {profile.get('looking_for', 'yo‘q')}\n"
        f"🌆 Shahar: {profile.get('city', 'yo‘q')}\n"
        f"📝 Bio: {profile.get('bio', 'yo‘q')}\n"
        f"🆔 ID: {profile.get('telegram_id', 'yo‘q')}"
    )

    await update.message.reply_photo(
        photo=photo_id,
        caption="Profil saqlandi ✅",
        reply_markup=main_menu
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
        await update.message.reply_text(f"Kanalga yuborishda xatolik: {e}")

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

    text = (
        "👤 Sizning profilingiz\n\n"
        f"📱 Telefon: {profile.get('phone', 'yo‘q')}\n"
        f"👤 Ism: {profile.get('name', 'yo‘q')}\n"
        f"🎂 Yosh: {profile.get('age', 'yo‘q')}\n"
        f"🚻 Jins: {profile.get('gender', 'yo‘q')}\n"
        f"🔎 Qidiryapti: {profile.get('looking_for', 'yo‘q')}\n"
        f"🌆 Shahar: {profile.get('city', 'yo‘q')}\n"
        f"📝 Bio: {profile.get('bio', 'yo‘q')}"
    )

    await update.message.reply_photo(
        photo=profile["photo"],
        caption=text,
        reply_markup=profile_menu
    )


async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_main_menu(update)


async def show_next_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in users_data or not is_profile_complete(user_id):
        await update.message.reply_text(
            "Avval profilingizni to‘liq yarating. /start bosing.",
            reply_markup=main_menu
        )
        return

    viewed = viewed_data.setdefault(user_id, set())
    likes_data.setdefault(user_id, set())

    current_user_gender_pref = users_data[user_id].get("looking_for")

    candidate_id = None
    for other_id in users_data.keys():
        if other_id == user_id:
            continue
        if not is_profile_complete(other_id):
            continue
        if other_id in viewed:
            continue
        if not fits_preference(user_id, other_id):
            continue

        # agar xohlasangiz, nomzodning ham sizga mosligini tekshirish uchun
        other_pref = users_data[other_id].get("looking_for")
        your_gender = users_data[user_id].get("gender")
        if other_pref != "🔄 Farqi yo‘q" and other_pref != your_gender:
            continue

        candidate_id = other_id
        break

    if candidate_id is None:
        await update.message.reply_text(
            "Hozircha yangi profillar yo‘q 🙂",
            reply_markup=main_menu
        )
        return

    context.user_data["current_profile_id"] = candidate_id

    profile = users_data[candidate_id]
    text = (
        "🌐 Profil\n\n"
        f"👤 Ism: {profile.get('name', 'yo‘q')}\n"
        f"🎂 Yosh: {profile.get('age', 'yo‘q')}\n"
        f"🚻 Jins: {profile.get('gender', 'yo‘q')}\n"
        f"🌆 Shahar: {profile.get('city', 'yo‘q')}\n"
        f"📝 Bio: {profile.get('bio', 'yo‘q')}"
    )

    await update.message.reply_photo(
        photo=profile["photo"],
        caption=text,
        reply_markup=browse_menu
    )


async def browse_profiles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_next_profile(update, context)


async def like_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    target_id = context.user_data.get("current_profile_id")

    if not target_id:
        await update.message.reply_text(
            "Avval profil oching.",
            reply_markup=main_menu
        )
        return

    likes_data.setdefault(user_id, set()).add(target_id)
    viewed_data.setdefault(user_id, set()).add(target_id)

    # o‘zaro like bo‘lsa match
    if user_id in likes_data.get(target_id, set()):
        pair = get_match_pair(user_id, target_id)

        if pair not in matches_data:
            matches_data.add(pair)

            target_profile = users_data.get(target_id, {})
            user_profile = users_data.get(user_id, {})

            try:
                await update.message.reply_text(
                    f"🎉 Sizda match bo‘ldi!\n\n"
                    f"👤 {target_profile.get('name', 'Foydalanuvchi')}",
                    reply_markup=main_menu
                )
            except Exception:
                pass

            try:
                await context.bot.send_message(
                    chat_id=target_id,
                    text=(
                        f"🎉 Sizda match bo‘ldi!\n\n"
                        f"👤 {user_profile.get('name', 'Foydalanuvchi')}"
                    ),
                )
            except Exception as e:
                print(f"Match xabarini yuborishda xatolik: {e}")

            try:
                await context.bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=(
                        "💖 Yangi match!\n\n"
                        f"{user_profile.get('name', 'User')} ❤️ "
                        f"{target_profile.get('name', 'User')}"
                    )
                )
            except Exception as e:
                print(f"Matchni kanalga yuborishda xatolik: {e}")
        else:
            await update.message.reply_text("Bu profilga like bosildi ✅", reply_markup=main_menu)
    else:
        await update.message.reply_text("Like yuborildi ❤️", reply_markup=main_menu)

    context.user_data.pop("current_profile_id", None)
    await show_next_profile(update, context)


async def skip_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    target_id = context.user_data.get("current_profile_id")

    if not target_id:
        await update.message.reply_text(
            "Avval profil oching.",
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
    app.add_handler(MessageHandler(filters.Regex("^🌐 Profillar$"), browse_profiles))
    app.add_handler(MessageHandler(filters.Regex("^❤️ Like$"), like_profile))
    app.add_handler(MessageHandler(filters.Regex("^⏭ Skip$"), skip_profile))

    print("Bot ishladi")
    app.run_polling()


if __name__ == "__main__":
    main()
