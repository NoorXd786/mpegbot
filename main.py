
from pyrogram import Client, filters
from pyrogram.types import Message
import os
import subprocess
import uuid
import logging

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

app = Client("mp4_to_mpeg2_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

def convert_mp4_to_mpeg2(input_path: str, output_path: str) -> bool:
    try:
        command = [
            "ffmpeg",
            "-i", input_path,
            "-c:v", "mpeg2video",
            "-q:v", "2",
            "-c:a", "mp2",
            "-f", "mpegts",
            output_path
        ]
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg failed: {e.stderr.decode()}")
        return False

def is_owner(message: Message) -> bool:
    return message.from_user and message.from_user.id == OWNER_ID

@app.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    if not is_owner(message):
        return await message.reply("❌ You are not authorized to use this bot.")
    await message.reply("👋 Welcome! Send an MP4 video or document to convert it to MPEG-2 format.\nUse /help for more info.")

@app.on_message(filters.command("help"))
async def help_command(client: Client, message: Message):
    if not is_owner(message):
        return await message.reply("❌ You are not authorized to use this bot.")
    await message.reply(
        "📖 *Bot Command List:*\n"
        "/start - Welcome message\n"
        "/help - Show this help message\n\n"
        "🎥 Just send an `.mp4` file (video or document) and I’ll convert it to MPEG-2 format."
    )

@app.on_message(filters.video | (filters.document & filters.regex(r'\.mp4$')))
async def handle_video(client: Client, message: Message):
    if not is_owner(message):
        return await message.reply("❌ You are not authorized to use this bot.")

    try:
        status_msg = await message.reply("⏳ Downloading your MP4 file...")
        temp_input = f"temp_{uuid.uuid4()}.mp4"
        temp_output = f"output_{uuid.uuid4()}.mpg"

        await message.download(file_name=temp_input)

        if not os.path.exists(temp_input):
            await status_msg.edit("❌ Failed to download the MP4 file.")
            return

        await status_msg.edit("🔄 Converting to MPEG-2...")
        success = convert_mp4_to_mpeg2(temp_input, temp_output)

        if not success:
            await status_msg.edit("❌ Conversion failed. Check logs.")
            return

        await status_msg.edit("📤 Uploading your MPEG-2 file...")
        await message.reply_document(
            temp_output,
            caption="✅ Your MPEG-2 file is ready!",
            thumb="https://placehold.co/300x200?text=MPEG2"
        )

    except Exception as e:
        await status_msg.edit(f"❌ Error: {str(e)}")
    finally:
        for f in [temp_input, temp_output]:
            if os.path.exists(f):
                os.remove(f)

if __name__ == "__main__":
    logger.info("Starting MP4 to MPEG-2 Converter Bot...")
    app.run()
