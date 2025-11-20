import os
import json
import asyncio # New import for aiogram v3 startup
from instagrapi import Client
from aiogram import Bot, Dispatcher, types # Removed 'executor' from this line
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

BOT_TOKEN = "8543073241:AAE3_E5zMkoF-jz0tbRMjduNhnQ1tus6kH0"

bot = Bot(BOT_TOKEN)
dp = Dispatcher() # Dispatcher is initialized without the bot instance in v3

DATA_FILE = "sessions.json"

# Load saved sessions
if os.path.exists(DATA_FILE):
    sessions = json.load(open(DATA_FILE))
else:
    sessions = {}

def save_sessions():
    json.dump(sessions, open(DATA_FILE, "w"), indent=4)

def get_client(user_id):
    cl = Client()
    if str(user_id) in sessions:
        try:
            cl.login_by_sessionid(sessions[str(user_id)])
            return cl
        except:
            return None
    return None


# ---------------- START ----------------
@dp.message.register(commands=["start"]) # Corrected decorator for v3
async def start(msg: types.Message):
    await msg.answer(
        "🤖 **Instagram Multi-Tool Bot**\n"
        "Send login as:\n`username|password`\n\n"
        "Bot will save your IG session securely."
    )


# ---------------- LOGIN ----------------
@dp.message.register(lambda m: "|" in m.text) # Corrected decorator for v3
async def login(msg: types.Message):
    user, pw = msg.text.split("|")
    user = user.strip()
    pw = pw.strip()

    cl = Client()

    try:
        cl.login(user, pw)
        sessionid = cl.sessionid
        sessions[str(msg.from_user.id)] = sessionid
        save_sessions()

        await msg.answer("✅ Logged in successfully!\nType /menu")
    except Exception as e:
        await msg.answer("❌ Login failed:\n" + str(e))


# ---------------- MENU ----------------
@dp.message.register(commands=["menu"]) # Corrected decorator for v3
async def menu(msg: types.Message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("📌 My Profile Info")) # Corrected ReplyKeyboardMarkup usage for v3
    kb.add(KeyboardButton("➕ Follow User"), KeyboardButton("➖ Unfollow User"))
    kb.add(KeyboardButton("📤 Post Upload"), KeyboardButton("🖼 Change Profile Pic"))
    kb.add(KeyboardButton("📄 Change Bio"), KeyboardButton("📋 Unfollow From List"))
    await msg.answer("Choose an action 👇", reply_markup=kb)


# ---------------- PROFILE INFO ----------------
@dp.message.register(lambda m: m.text == "📌 My Profile Info") # Corrected decorator for v3
async def profile(msg: types.Message):
    cl = get_client(msg.from_user.id)
    if not cl:
        return await msg.answer("❌ Not logged in.")

    me = cl.account_info()
    await msg.answer(
        f"👤 **Profile Info**\n\n"
        f"Username: {me.username}\n"
        f"Followers: {me.follower_count}\n"
        f"Following: {me.following_count}\n"
        f"Posts: {me.media_count}"
    )


# ---------------- FOLLOW USER ----------------
@dp.message.register(lambda m: m.text == "➕ Follow User") # Corrected decorator for v3
async def ask_follow(msg: types.Message):
    await msg.answer("Send IG username to follow:")

# NOTE: aiogram v3 handlers don't natively support checking m.reply_to_message in the decorator lambda as easily as v2.
# A more robust v3 approach would be using FSM or checking inside the handler.
# Keeping the original lambda logic here, but be aware this reply-based logic can be unreliable in v3.
@dp.message.register(lambda m: m.reply_to_message and "follow" in m.reply_to_message.text.lower()) # Corrected decorator for v3
async def do_follow(msg: types.Message):
    cl = get_client(msg.from_user.id)
    if not cl: return await msg.answer("Not logged in.")

    try:
        uid = cl.user_id_from_username(msg.text.strip())
        cl.user_follow(uid)
        await msg.answer("✅ Followed successfully!")
    except:
        await msg.answer("⚠️ Error following user.")


# ---------------- UNFOLLOW USER ----------------
@dp.message.register(lambda m: m.text == "➖ Unfollow User") # Corrected decorator for v3
async def ask_unfollow(msg: types.Message):
    await msg.answer("Send IG username to unfollow:")

@dp.message.register(lambda m: m.reply_to_message and "unfollow" in m.reply_to_message.text.lower()) # Corrected decorator for v3
async def do_unfollow(msg: types.Message):
    cl = get_client(msg.from_user.id)
    if not cl: return await msg.answer("Not logged in.")

    try:
        uid = cl.user_id_from_username(msg.text.strip())
        cl.user_unfollow(uid)
        await msg.answer("❌ Unfollowed successfully!")
    except:
        await msg.answer("⚠️ Error unfollowing user.")


# ---------------- UNFOLLOW FROM LIST ----------------
@dp.message.register(lambda m: m.text == "📋 Unfollow From List") # Corrected decorator for v3
async def ask_list(msg: types.Message):
    await msg.answer("Send list of usernames (one per line):")

@dp.message.register(lambda m: "\n" in m.text) # Corrected decorator for v3
async def unfollow_list(msg: types.Message):
    cl = get_client(msg.from_user.id)
    if not cl: return await msg.answer("Not logged in.")

    users = msg.text.split("\n")
    count = 0
    for u in users:
        u = u.strip()
        try:
            uid = cl.user_id_from_username(u)
            cl.user_unfollow(uid)
            count += 1
        except:
            pass

    await msg.answer(f"✅ Unfollowed {count} users.")


# ---------------- CHANGE BIO ----------------
@dp.message.register(lambda m: m.text == "📄 Change Bio") # Corrected decorator for v3
async def ask_bio(msg: types.Message):
    await msg.answer("Send new bio:")

@dp.message.register(lambda m: m.reply_to_message and "bio" in m.reply_to_message.text.lower()) # Corrected decorator for v3
async def change_bio(msg: types.Message):
    cl = get_client(msg.from_user.id)
    if not cl: return await msg.answer("Not logged in.")
    try:
        cl.account_edit(biography=msg.text)
        await msg.answer("✅ Bio updated.")
    except:
        await msg.answer("⚠️ Error updating bio.")


# ---------------- CHANGE PROFILE PIC ----------------
@dp.message.register(lambda m: m.text == "🖼 Change Profile Pic") # Corrected decorator for v3
async def ask_pic(msg: types.Message):
    await msg.answer("Send new profile picture:")

@dp.message.register(content_types=["photo"]) # Corrected decorator for v3
async def upload_pic(msg: types.Message):
    cl = get_client(msg.from_user.id)
    if not cl: return await msg.answer("Not logged in.")

    file_path = f"pfp_{msg.from_user.id}.jpg"
    # Download the photo using the bot instance
    await bot.download(
        msg.photo[-1], 
        destination=file_path
    )

    try:
        cl.account_change_profile_picture(file_path)
        await msg.answer("✅ Profile picture updated!")
    except:
        await msg.answer("⚠️ Failed to update picture.")


# ---------------- POST UPLOAD ----------------
@dp.message.register(lambda m: m.text == "📤 Post Upload") # Corrected decorator for v3
async def ask_post(msg: types.Message):
    await msg.answer("Send photo to upload:")

# NOTE: content_types=["photo"] will catch all photos, including replies.
# The original 'is_reply=False' logic is not directly transferable to a lambda in v3.
# This handler will fire for ANY photo, unless a reply handler is more specific.
@dp.message.register(content_types=["photo"]) # Corrected decorator for v3
async def post_upload(msg: types.Message):
    cl = get_client(msg.from_user.id)
    if not cl: return await msg.answer("Not logged in.")

    # A simple check to avoid conflict if the photo is a reply to something else,
    # though the decorator order typically handles this in v3.
    if msg.reply_to_message: 
        return # Skip if it's a photo being used as a reply

    file_path = f"post_{msg.from_user.id}.jpg"
    
    # Download the photo using the bot instance (v3 method)
    await bot.download(
        msg.photo[-1], 
        destination=file_path
    )

    try:
        cl.photo_upload(file_path, caption="Uploaded via bot 🤖")
        await msg.answer("📤 Post uploaded!")
    except Exception as e:
        await msg.answer("⚠️ Error: " + str(e))


# ---------------- START BOT ----------------
async def main(): # New asynchronous function for startup
    # Use the Dispatcher's start_polling method with the Bot instance
    await dp.start_polling(bot) 

if __name__ == "__main__":
    print("Bot starting...")
    # asyncio.run is the v3 method to start the bot
    asyncio.run(main())
