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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user

    started_users.add(user.id)

    username_text = f"@{user.username}" if user.username else "yo‘q"
    profile_link = f"tg://user?id={user.id}"
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # kanalga yuboriladi
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
        print(f"Kanalga yuborishda xatolik: {e}")

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


async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    contact = update.message.contact

    if not contact:
        await update.message.reply_text(
            "Telefon tugmasini bosib yuboring."
        )
        return PHONE

    if contact.user_id != update.effective_user.id:
        await update.message.reply_text(
            "O‘zingizning telefon raqamingizni yuboring."
        )
        return PHONE

    user_id = update.effective_user.id

    users_data[user_id] = {
        "telegram_id": user_id,
        "phone": contact.phone_number,
    }

    await update.message.reply_text(
        "Ismingizni yozing:",
        reply_markup=ReplyKeyboardRemove(),
    )
    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    name = update.message.text.strip()

    users_data[user_id]["name"] = name

    await update.message.reply_text("Yoshingiz?")
    return AGE


async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id

    if not update.message.text.isdigit():
        await update.message.reply_text("Yoshni raqam bilan yozing")
        return AGE

    users_data[user_id]["age"] = update.message.text

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

    users_data[user_id]["gender"] = update.message.text

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

    users_data[user_id]["looking_for"] = update.message.text

    await update.message.reply_text(
        "Qaysi shahardansiz?",
        reply_markup=ReplyKeyboardRemove(),
    )
    return CITY


async def get_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id

    users_data[user_id]["city"] = update.message.text

    await update.message.reply_text(
        "O‘zingiz haqingizda yozing:"
    )
    return BIO


async def get_bio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id

    users_data[user_id]["bio"] = update.message.text

    await update.message.reply_text(
        "Profil rasmingizni yuboring:"
    )
    return PHOTO


async def get_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id

    photo_id = update.message.photo[-1].file_id

    users_data[user_id]["photo"] = photo_id

    profile = users_data[user_id]

    text = (
        "✅ Yangi profil\n\n"
        f"📱 {profile['phone']}\n"
        f"👤 {profile['name']}\n"
        f"🎂 {profile['age']}\n"
        f"🚻 {profile['gender']}\n"
        f"🔎 {profile['looking_for']}\n"
        f"🌆 {profile['city']}\n"
        f"📝 {profile['bio']}\n"
        f"🆔 {profile['telegram_id']}"
    )

    # foydalanuvchiga
    await update.message.reply_photo(
        photo=photo_id,
        caption="Profil saqlandi ✅"
    )

    # kanalga
    await context.bot.send_photo(
        chat_id=CHANNEL_ID,
        photo=photo_id,
        caption=text
    )

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Bekor qilindi",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


def main():
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PHONE: [MessageHandler(filters.CONTACT, get_phone)],
            NAME: [MessageHandler(filters.TEXT, get_name)],
            AGE: [MessageHandler(filters.TEXT, get_age)],
            GENDER: [MessageHandler(filters.TEXT, get_gender)],
            LOOKING_FOR: [MessageHandler(filters.TEXT, get_looking_for)],
            CITY: [MessageHandler(filters.TEXT, get_city)],
            BIO: [MessageHandler(filters.TEXT, get_bio)],
            PHOTO: [MessageHandler(filters.PHOTO, get_photo)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)

    print("Bot ishladi")
    app.run_polling()


if __name__ == "__main__":
    main()
