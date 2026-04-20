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

geolocator = Nominatim(user_agent="friend_match_uz_bot")

main_menu = ReplyKeyboardMarkup(
    [["👤 Profil"]],
    resize_keyboard=True
)

profile_menu = ReplyKeyboardMarkup(
    [
        ["✏️ Tahrirlash"],
        ["⬅️ Qaytish"],
    ],
    resize_keyboard=True
)


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

        try:
            location = geolocator.reverse((lat, lon), language="en", exactly_one=True)

            if location and "address" in location.raw:
                address = location.raw["address"]
                city = (
                    address.get("city")
                    or address.get("town")
                    or address.get("village")
                    or address.get("county")
                    or address.get("state")
                    or "Noma’lum"
                )
            else:
                city = "Noma’lum"

        except Exception as e:
            print(f"Lokatsiyadan shahar aniqlashda xatolik: {e}")
            city = "Noma’lum"

        users_data[user_id]["city"] = city
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

    if user_id not in users_data:
        await update.message.reply_text(
            "Sizda hali profil yo‘q. /start bosing.",
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

    if "photo" in profile:
        await update.message.reply_photo(
            photo=profile["photo"],
            caption=text,
            reply_markup=profile_menu
        )
    else:
        await update.message.reply_text(
            text,
            reply_markup=profile_menu
        )


async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Asosiy menyu",
        reply_markup=main_menu
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Bekor qilindi.",
        reply_markup=ReplyKeyboardRemove(),
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

    print("Bot ishladi")
    app.run_polling()


if __name__ == "__main__":
    main()
