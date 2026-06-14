import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

import gemini_parser
import sheets
from config import TELEGRAM_TOKEN

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *Bot Absensi Siap!*\n\n"
        "Kirim pesan seperti contoh:\n"
        "• `Budi hadir 15 Maret 2024`\n"
        "• `EMP003 ❌ 20-01-2024`\n"
        "• `siti tidak masuk 15 jan 2024`\n"
        "• `Budi ✅ 15 january 2024`",
        parse_mode="Markdown",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Cara penggunaan:\n\n"
        "1. Kirim pesan dengan nama/kode pegawai + tanggal + status hadir/tidak\n"
        "2. Bot akan otomatis memahami format apapun\n"
        "3. Gunakan ✅ atau ❌ atau kata 'hadir'/'tidak hadir'/'masuk'/'alfa' dll\n\n"
        "Contoh:\n"
        "- \"Budi Santoso hadir 15-03-2024\"\n"
        "- \"EMP005 alfa 20 maret 2024\"\n"
        "- \"siti ✅ 15 january\"\n"
        "- \"Dewi Lestari tidak masuk 01-01-2024\""
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text.strip()

    if not message:
        return

    try:
        parsed = gemini_parser.parse_attendance_message(message)

        if not parsed.get("tanggal") or not parsed.get("status"):
            await update.message.reply_text(
                "❌ Tidak bisa memahami pesan. Pastikan menyertakan "
                "nama/kode pegawai, tanggal, dan status hadir/tidak hadir.\n"
                "Contoh: `Budi hadir 15 Maret 2024`",
                parse_mode="Markdown",
            )
            return

        result = sheets.update_attendance(**parsed)
        await update.message.reply_text(result["message"])

    except ValueError as e:
        logger.error(f"Parse error: {e}")
        await update.message.reply_text(f"❌ Gagal memahami pesan: {e}")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Terjadi error: {str(e)}")


def main():
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN tidak ditemukan di .env")
        return

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot started polling...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
