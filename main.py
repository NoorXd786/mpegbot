from pyrogram import Client, filters
from pyrogram.types import Message
import os
import subprocess
import tempfile
import logging

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OWNER_ID = int(os.getenv("OWNER_ID", 0))

# FFmpeg existence check
def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except Exception:
        logger.error("FFmpeg is not installed or not found in PATH.")
        exit("FFmpeg is required. Install it or add to PATH.")

check_ffmpeg()

app = Client("mp4_to_mpeg2_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Conversion function
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
        logger.error(f"FFmpeg failed: {e.stderr.decode(errors='ignore')}")
        return False

# Authorization
def is_owner(message: Message) -> bool:
    return message.from_user and message.from_user.id == OWNER_ID

# /start
@app.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    if not is_owner(message):
        return await message.reply("❌ You are not authorized to use this bot.")
    await message.reply("👋 Welcome! Send an MP4 video or document to convert it to MPEG-2 format.\nUse /help for more info.")

# /help
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

# Handle MP4 input
@app.on_message(filters.video | filters.document)
async def handle_video(client: Client, message: Message):
    if not is_owner(message):
        return await message.reply("❌ You are not authorized to use this bot.")

    file_name = message.video.file_name if message.video else message.document.file_name
    if not file_name or not file_name.lower().endswith(".mp4"):
        return await message.reply("❌ Please send a valid `.mp4` file.")

    status_msg = await message.reply("⏳ Downloading your MP4 file...")

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_input, \
             tempfile.NamedTemporaryFile(delete=False, suffix=".mpg") as temp_output:

            await message.download(file_name=temp_input.name)

            await status_msg.edit("🔄 Converting to MPEG-2...")
            success = convert_mp4_to_mpeg2(temp_input.name, temp_output.name)

            if not success:
                return await status_msg.edit("❌ Conversion failed. See logs.")

            await status_msg.edit("📤 Uploading your MPEG-2 file...")
            await client.send_chat_action(message.chat.id, "upload_document")

            await message.reply_document(
                document=temp_output.name,
                caption="✅ Your MPEG-2 file is ready!",
                file_name="converted.mpg"
            )

    except Exception as e:
        logger.exception("Unexpected error")
        await status_msg.edit(f"❌ Error: {str(e)}")
    finally:
        # Clean up files safely
        for f in [temp_input.name, temp_output.name]:
            if os.path.exists(f):
                os.remove(f)

# Entry point
if __name__ == "__main__":
    logger.info("🔁 Starting MP4 to MPEG-2 Converter Bot...")
    app.run()
