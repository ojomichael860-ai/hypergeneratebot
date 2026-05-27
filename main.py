import os
import asyncio
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, filters, ContextTypes, ConversationHandler
)

# --- Web Server for Render Health Checks ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Hyper Content Engine Deployment Active!")

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()

def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    print(f"Health check server running on port {port}")
    server.serve_forever()

# --- Conversation State Machines ---
LANG, COUNTRY, CHANNEL, PACKAGE, TOPIC, PROOF = range(6)

# --- Multilingual Localization Data Dictionaries ---
LOCALIZATION = {
    "en": {
        "welcome": "🚀 **Welcome to Hyper Generate Bot!**\n\nChoose your preferred communication language:",
        "country": "🌍 Please enter your **Country** so we can optimize regional communication workflows:",
        "channel": "📣 Excellent! Now, please paste and send your **Telegram Channel Link** or username (e.g., https://t.me/SabaPoolGB) where you want the bot to post content:",
        "packages": "📦 **Choose Your Content Generation Package:**\n\n"
                    "🔹 **1. BASIC PACKAGE**\n"
                    "• 3 targeted posts per day\n"
                    "• Duration: 5 Days\n"
                    "• Cost: **$35 USDT**\n\n"
                    "🔸 **2. STANDARD PACKAGE**\n"
                    "• 5 targeted posts per day\n"
                    "• Duration: 7 Days\n"
                    "• Cost: **$50 USDT**\n\n"
                    "👑 **3. PREMIUM PACKAGE**\n"
                    "• 10 targeted posts per day\n"
                    "• Duration: 10 Days\n"
                    "• Cost: **$80 USDT**",
        "invoice": "💳 **USDT TRC-20 Payment Invoice**\n\n"
                   "Please transfer exactly **${price} USDT** to the following official company address:\n\n"
                   "`TPekazrggAXQKveX6jyPEx3b8HPT247Hg8`\n\n"
                   "⚠️ *Important:* After sending the funds, wait **10 minutes** for blockchain confirmations, then upload a clear **screenshot of your transaction receipt** to activate your bot service configuration.",
        "topic": "📝 **Payment logged for validation!**\n\nNow, please send the **Topic/Niche** you want your channel content to focus on (e.g., Forex Trading, Fitness Tips, Football Pools, Web3 Updates):",
        "complete": "✅ **Configuration Complete!**\n\nOur system admins will verify your receipt snapshot within 10 minutes. Once confirmed, your automated scheduling sequence will begin posting directly to your channel!"
    },
    "es": {
        "welcome": "🚀 **¡Bienvenido a Hyper Generate Bot!**\n\nSeleccione su idioma de comunicación preferido:",
        "country": "🌍 Por favor, introduzca su **País** para optimizar el soporte regional:",
        "channel": "📣 ¡Excelente! Ahora, pegue y envíe el **Enlace o usuario de su canal de Telegram**:",
        "packages": "📦 **Elija su paquete de generación de contenido:**\n\n"
                    "🔹 **1. PAQUETE BÁSICO**\n• 3 publicaciones por día\n• Duración: 5 Días\n• Costo: **$35 USDT**\n\n"
                    "🔸 **2. PAQUETE ESTÁNDAR**\n• 5 publicaciones por día\n• Duración: 7 Días\n• Costo: **$50 USDT**\n\n"
                    "👑 **3. PAQUETE PREMIUM**\n• 10 publicaciones por día\n• Duración: 10 Días\n• Costo: **$80 USDT**",
        "invoice": "💳 **Factura de Pago USDT TRC-20**\n\nPor favor envíe exactamente **${price} USDT** a la siguiente dirección:\n\n`TPekazrggAXQKveX6jyPEx3b8HPT247Hg8`\n\n⚠️ *Importante:* Espere **10 minutos** y suba una **captura de pantalla de su comprobante**.",
        "topic": "📝 **¡Pago enviado para validación!**\n\nAhora, envíe el **Tema o Nicho** del contenido de su canal:",
        "complete": "✅ **¡Configuración completa!**\n\nVerificaremos su captura en 10 minutos para activar las publicaciones automáticas."
    }
}

# --- Mock AI Content Generator Fallback ---
def generate_ai_content(topic: str) -> str:
    """Simulates an ultra-fast generation payload safe for free-tier memory loops."""
    return f"🔥 **Latest Updates on {topic.title()}** 🔥\n\nHere is your high-quality scheduled insight block regarding {topic}. Staying consistent is the true secret to organic community channel development in 2026! 📈✨"

# --- Bot Flow State Machine Logic ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry pipeline: Requests Language setup preference options."""
    keyboard = [
        [InlineKeyboardButton("🇺🇸 English", callback_data="lang_en")],
        [InlineKeyboardButton("🇪🇸 Español", callback_data="lang_es")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(LOCALIZATION["en"]["welcome"], reply_markup=reply_markup, parse_mode="Markdown")
    return LANG

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    selected_lang = query.data.split("_")[1]
    context.user_data["lang"] = selected_lang
    
    await query.message.edit_text(LOCALIZATION[selected_lang]["country"], parse_mode="Markdown")
    return COUNTRY

async def capture_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "en")
    context.user_data["country"] = update.message.text
    
    await update.message.reply_text(LOCALIZATION[lang]["channel"], parse_mode="Markdown")
    return CHANNEL

async def capture_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "en")
    context.user_data["channel_link"] = update.message.text
    
    keyboard = [
        [InlineKeyboardButton("Basic ($35)", callback_data="pkg_35")],
        [InlineKeyboardButton("Standard ($50)", callback_data="pkg_50")],
        [InlineKeyboardButton("Premium ($80)", callback_data="pkg_80")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(LOCALIZATION[lang]["packages"], reply_markup=reply_markup, parse_mode="Markdown")
    return PACKAGE

async def process_package_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    price = query.data.split("_")[1]
    context.user_data["selected_price"] = price
    lang = context.user_data.get("lang", "en")
    
    invoice_text = LOCALIZATION[lang]["invoice"].format(price=price)
    await query.message.edit_text(invoice_text, parse_mode="Markdown")
    return PROOF

async def capture_payment_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "en")
    
    # Check if the user actually sent a screenshot photo array
    if not update.message.photo:
        await update.message.reply_text("⚠️ Please upload a valid image screenshot receipt to proceed.")
        return PROOF

    # Capture the image file identification parameters
    photo_file_id = update.message.photo[-1].file_id
    context.user_data["receipt_image_id"] = photo_file_id
    
    await update.message.reply_text(LOCALIZATION[lang]["topic"], parse_mode="Markdown")
    return TOPIC

async def finalize_configuration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "en")
    topic = update.message.text
    context.user_data["content_topic"] = topic
    
    await update.message.reply_text(LOCALIZATION[lang]["complete"], parse_mode="Markdown")
    
    # OPTIONAL DEV LOOP: Send a copy of the diagnostic payload metadata to the server owner log stream
    print(f"--- NEW ORDER CONFIGURATION LOG ---")
    print(f"Channel Link: {context.user_data.get('channel_link')}")
    print(f"Country Profile: {context.user_data.get('country')}")
    print(f"Tier Cost Selection: ${context.user_data.get('selected_price')} USDT")
    print(f"Niche/Topic Target: {topic}")
    print(f"------------------------------------")
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Process setup cancelled.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def main():
    TOKEN = os.environ.get("TELEGRAM_TOKEN")
    if not TOKEN:
        raise ValueError("Missing TELEGRAM_TOKEN parameter environment variable target rule.")

    # Deploy port binding background framework structures for Render hosting
    threading.Thread(target=run_health_server, daemon=True).start()

    app = Application.builder().token(TOKEN).build()
    
    # Construct complete multi-state dialog configuration mapping logic trees
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANG: [CallbackQueryHandler(set_language, pattern="^lang_")],
            COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, capture_country)],
            CHANNEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, capture_channel)],
            PACKAGE: [CallbackQueryHandler(process_package_selection, pattern="^pkg_")],
            PROOF: [MessageHandler(filters.PHOTO, capture_payment_screenshot)],
            TOPIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, finalize_configuration)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    
    app.add_handler(conv_handler)
    print("Hyper Content dynamic bot framework actively polling...")
    
    async with app:
        await app.initialize()
        await app.start()
        await app.updater.start_polling()
        while True:
            await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
