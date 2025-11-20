import os
import json
import asyncio
from instagrapi import Client
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

BOT_TOKEN = "8543073241:AAE3_E5zMkoF-jz0tbRMjduNhnQ1tus6kH0"

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

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
@dp.message(commands=["start"]) # FIX: Corrected decorator for aiogram v3
async def start(msg: types.Message):
    await msg.answer(
        "🤖 **Instagram Multi-Tool Bot**\n"
        "Send login as:\n`username|password`\n\n"
        "Bot will save your IG session securely."
    )


# ---------------- LOGIN ----------------
@dp.message(lambda m: "|" in m.text) # FIX: Corrected decorator for aiogram v3
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
@dp.message(commands=["menu"]) # FIX: Corrected decorator for aiogram v3
async def menu(msg: types.Message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("📌 My Profile Info"))
    kb.add(KeyboardButton("➕ Follow User"), KeyboardButton("➖ Unfollow User"))
    kb.add(KeyboardButton("📤 Post Upload"), KeyboardButton("🖼 Change Profile Pic"))
    kb.add(KeyboardButton("📄 Change Bio"), KeyboardButton("📋 Unfollow From List"))
    await msg.answer("Choose an action 👇", reply_markup=kb)


# ---------------- PROFILE INFO ----------------
@dp.message(lambda m: m.text == "📌 My Profile Info") # FIX: Corrected decorator for aiogram v3
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
@dp.message(lambda m: m.text == "➕ Follow User") # FIX: Corrected decorator for aiogram v3
async def ask_follow(msg: types.Message):
    await msg.answer("Send IG username to follow:")

@dp.message(lambda m: m.reply_to_message and "follow" in m.reply_to_message.text.lower()) # FIX: Corrected decorator for aiogram v3
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
@dp.message(lambda m: m.text == "➖ Unfollow User") # FIX: Corrected decorator for aiogram v3
async def ask_unfollow(msg: types.Message):
    await msg.answer("Send IG username to unfollow:")

@dp.message(lambda m: m.reply_to_message and "unfollow" in m.reply_to_message.text.lower()) # FIX: Corrected decorator for aiogram v3
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
@dp.message(lambda m: m.text == "📋 Unfollow From List") # FIX: Corrected decorator for aiogram v3
async def ask_list(msg: types.Message):
    await msg.answer("Send list of usernames (one per line):")

@dp.message(lambda m: m.text and "\n" in m.text) # FIX: Corrected decorator for aiogram v3 (added m.text check for safety)
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
@dp.message(lambda m: m.text == "📄 Change Bio") # FIX: Corrected decorator for aiogram v3
async def ask_bio(msg: types.Message):
    await msg.answer("Send new bio:")

@dp.message(lambda m: m.reply_to_message and "bio" in m.reply_to_message.text.lower()) # FIX: Corrected decorator for aiogram v3
async def change_bio(msg: types.Message):
    cl = get_client(msg.from_user.id)
    if not cl: return await msg.answer("Not logged in.")
    try:
        cl.account_edit(biography=msg.text)
        await msg.answer("✅ Bio updated.")
    except:
        await msg.answer("⚠️ Error updating bio.")


# ---------------- CHANGE PROFILE PIC ----------------
@dp.message(lambda m: m.text == "🖼 Change Profile Pic") # FIX: Corrected decorator for aiogram v3
async def ask_pic(msg: types.Message):
    await msg.answer("Send new profile picture:")

@dp.message(lambda m: m.content_type == types.ContentType.PHOTO and m.reply_to_message and "profile picture" in m.reply_to_message.text.lower())
async def upload_pic(msg: types.Message):
    cl = get_client(msg.from_user.id)
    if not cl: return await msg.answer("Not logged in.")

    file_path = f"pfp_{msg.from_user.id}.jpg"
    
    # Get the file ID of the largest photo
    file_id = msg.photo[-1].file_id
    
    # Download the photo using the bot instance
    await bot.download(
        file_id, 
        destination=file_path
    )

    try:
        cl.account_change_profile_picture(file_path)
        await msg.answer("✅ Profile picture updated!")
    except Exception as e:
        await msg.answer(f"⚠️ Failed to update picture: {e}")
    finally:
        os.remove(file_path) # Clean up the downloaded file


# ---------------- POST UPLOAD ----------------
@dp.message(lambda m: m.text == "📤 Post Upload") # FIX: Corrected decorator for aiogram v3
async def ask_post(msg: types.Message):
    await msg.answer("Send photo to upload:")

# NOTE: This handler uses a reply-based check to differentiate from the profile picture upload
@dp.message(lambda m: m.content_type == types.ContentType.PHOTO and m.reply_to_message and "photo to upload" in m.reply_to_message.text.lower())
async def post_upload(msg: types.Message):
    cl = get_client(msg.from_user.id)
    if not cl: return await msg.answer("Not logged in.")

    file_path = f"post_{msg.from_user.id}.jpg"
    
    # Get the file ID of the largest photo
    file_id = msg.photo[-1].file_id

    # Download the photo using the bot instance (v3 method)
    await bot.download(
        file_id, 
        destination=file_path
    )

    try:
        cl.photo_upload(file_path, caption="Uploaded via bot 🤖")
        await msg.answer("📤 Post uploaded!")
    except Exception as e:
        await msg.answer("⚠️ Error: " + str(e))
    finally:
        os.remove(file_path) # Clean up the downloaded file


# ---------------- START BOT ----------------
async def main():
    print("Bot starting...")
    # Use the Dispatcher's start_polling method with the Bot instance
    await dp.start_polling(bot) 

if __name__ == "__main__":
    asyncio.run(main())
