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

TOKEN = "TOKENINGIZNI_BU_YERGA"

# Bosqichlar
PHONE, NAME, AGE, GENDER, LOOKING_FOR, CITY, BIO, PHOTO = range(8)

# Oddiy vaqtinchalik saqlash
# Keyin xohlasangiz SQLite ga o'tkazamiz
users_data = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    phone_keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton("📱 Telefon raqam yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    await update.message.reply_text(
        "Assalomu alaykum.\n\n"
        "Ro‘yxatdan o‘tish uchun avval telefon raqamingizni yuboring:",
        reply_markup=phone_keyboard,
    )
    return PHONE


async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    contact = update.message.contact

    if not contact:
        await update.message.reply_text(
            "Iltimos, tugma orqali telefon raqamingizni yuboring."
        )
        return PHONE

    user_id = update.effective_user.id

    users_data[user_id] = {
        "telegram_id": user_id,
        "phone": contact.phone_number,
    }

    await update.message.reply_text(
        "Rahmat.\n\nEndi ismingizni yozing:",
        reply_markup=ReplyKeyboardRemove(),
    )
    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    name = update.message.text.strip()

    if len(name) < 2:
        await update.message.reply_text("Ism juda qisqa. Qayta yozing:")
        return NAME

    users_data[user_id]["name"] = name

    await update.message.reply_text("Yoshingiz nechida?")
    return AGE


async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    age_text = update.message.text.strip()

    if not age_text.isdigit():
        await update.message.reply_text("Yoshni faqat raqam bilan yozing. Masalan: 22")
        return AGE

    age = int(age_text)

    if age < 18 or age > 100:
        await update.message.reply_text("Iltimos, 18 dan 100 gacha bo‘lgan yosh kiriting.")
        return AGE

    users_data[user_id]["age"] = age

    gender_keyboard = ReplyKeyboardMarkup(
        [["👨 Erkak", "👩 Ayol"]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    await update.message.reply_text(
        "Jinsingizni tanlang:",
        reply_markup=gender_keyboard,
    )
    return GENDER


async def get_gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    gender = update.message.text.strip()

    if gender not in ["👨 Erkak", "👩 Ayol"]:
        await update.message.reply_text("Tugmalardan birini tanlang.")
        return GENDER

    users_data[user_id]["gender"] = gender

    looking_keyboard = ReplyKeyboardMarkup(
        [["👨 Erkak", "👩 Ayol", "🔄 Farqi yo‘q"]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    await update.message.reply_text(
        "Kim bilan tanishmoqchisiz?",
        reply_markup=looking_keyboard,
    )
    return LOOKING_FOR


async def get_looking_for(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    looking_for = update.message.text.strip()

    if looking_for not in ["👨 Erkak", "👩 Ayol", "🔄 Farqi yo‘q"]:
        await update.message.reply_text("Tugmalardan birini tanlang.")
        return LOOKING_FOR

    users_data[user_id]["looking_for"] = looking_for

    await update.message.reply_text(
        "Qaysi shahardansiz?",
        reply_markup=ReplyKeyboardRemove(),
    )
    return CITY


async def get_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    city = update.message.text.strip()

    if len(city) < 2:
        await update.message.reply_text("Shahar nomini to‘g‘ri kiriting:")
        return CITY

    users_data[user_id]["city"] = city

    await update.message.reply_text(
        "O‘zingiz haqingizda qisqacha yozing:\n"
        "Masalan: sportni yaxshi ko‘raman, sayr qilish yoqadi."
    )
    return BIO


async def get_bio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    bio = update.message.text.strip()

    if len(bio) < 5:
        await update.message.reply_text("Bio juda qisqa. Biroz to‘liqroq yozing:")
        return BIO

    users_data[user_id]["bio"] = bio

    await update.message.reply_text("Endi profil uchun rasm yuboring:")
    return PHOTO


async def get_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id

    if not update.message.photo:
        await update.message.reply_text("Iltimos, rasm yuboring.")
        return PHOTO

    # Eng kattaroq rasm file_id sini olamiz
    photo_file_id = update.message.photo[-1].file_id
    users_data[user_id]["photo"] = photo_file_id

    profile = users_data[user_id]

    summary_text = (
        "✅ Profil tayyor!\n\n"
        f"📱 Telefon: {profile['phone']}\n"
        f"👤 Ism: {profile['name']}\n"
        f"🎂 Yosh: {profile['age']}\n"
        f"🚻 Jins: {profile['gender']}\n"
        f"🔎 Qidiryapti: {profile['looking_for']}\n"
        f"🌍 Shahar: {profile['city']}\n"
        f"📝 Bio: {profile['bio']}"
    )

    main_menu = ReplyKeyboardMarkup(
        [
            ["❤️ Odamlarni ko‘rish"],
            ["✏️ Profilni tahrirlash"],
        ],
        resize_keyboard=True,
    )

    await update.message.reply_photo(
        photo=photo_file_id,
        caption=summary_text,
        reply_markup=main_menu,
    )

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Ro‘yxatdan o‘tish bekor qilindi.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


async def text_after_registration(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    text = update.message.text.strip()

    if text == "❤️ Odamlarni ko‘rish":
        await update.message.reply_text(
            "Bu keyingi bosqich bo‘ladi. Hozircha profil yaratish qismi tayyor."
        )
    elif text == "✏️ Profilni tahrirlash":
        await update.message.reply_text(
            "Profilni qayta to‘ldirish uchun /start bosing."
        )
    else:
        await update.message.reply_text("Davom etish uchun /start bosing.")


def main() -> None:
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PHONE: [MessageHandler(filters.CONTACT, get_phone)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
            GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_gender)],
            LOOKING_FOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_looking_for)],
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_city)],
            BIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_bio)],
            PHOTO: [MessageHandler(filters.PHOTO, get_photo)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_after_registration))

    print("Bot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()
