import os
import asyncio
import threading
import json
import http.client
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
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
        self.wfile.write(b"HyperGenerateBot Engine is Live!")

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
LANG, COUNTRY, CHANNEL, PACKAGE, PAYMENT_HASH, PAYMENT_SCREENSHOT, TOPIC = range(7)

ALLOWED_COUNTRIES = [
    "United States", "Brazil", "Indonesia", "Russia", "Turkey", 
    "Philippines", "South Korea", "Cambodia", "Malaysia", "Portugal"
]

# Hardcoded Admin Handle Configuration
ADMIN_USERNAME = "@venusm121"

LOCALIZATION = {
    "en": {
        "welcome": "🚀 **Welcome to HyperGenerateBot!**\n\nChoose your preferred communication language below:",
        "country": "🌍 Please select or type your **Country** from our active optimization list:",
        "channel": "📣 Great! Now, please paste and send your **Telegram Channel Link or Username** (e.g., `https://t.me/YourChannel`):\n\n*(Note: Your channel will require approval from our administrator before posting begins.)*",
        "packages": "📦 **Select Your Content Automation Package Tier:**\n\n"
                    "🔹 **1. BASIC PACKAGE**\n"
                    "• 3 customized posts per day\n"
                    "• Duration: 5 Days\n"
                    "• Cost: **$35 USDT**\n\n"
                    "🔸 **2. STANDARD PACKAGE**\n"
                    "• 5 customized posts per day\n"
                    "• Duration: 7 Days\n"
                    "• Cost: **$50 USDT**\n\n"
                    "👑 **3. PREMIUM PACKAGE**\n"
                    "• 10 customized posts per day\n"
                    "• Duration: 10 Days\n"
                    "• Cost: **$80 USDT**",
        "hash_req": "💳 **USDT TRC-20 Invoice Address Connection**\n\n"
                    "Please transfer exactly **${price} USDT** to our company address:\n\n"
                    "`TPekazrggAXQKveX6jyPEx3b8HPT247Hg8`\n\n"
                    "👉 Copy and reply here with your **Transaction Hash Address (TxID)** to log this invoice:",
        "screenshot_req": "📸 **Hash received!**\n\nNow, upload the **Screenshot of your transaction receipt** for confirmation within 10 minutes:",
        "topic": "📝 **Verification details received!**\n\nNow, type and send the **Topic/Niche** you want your channel content to focus on:",
        "complete": f"✅ **Configuration Sent For Review!**\n\nOur administrator {ADMIN_USERNAME} is verifying your payment and channel permissions. You will be notified once approved! 🚀"
    },
    "es": {
        "welcome": "🚀 **¡Bienvenido a HyperGenerateBot!**\n\nSeleccione su idioma de comunicación de preferencia:",
        "country": "🌍 Por favor, seleccione o escriba su **País** de nuestra lista:",
        "channel": "📣 ¡Excelente! Ahora, pegue y envíe el **Enlace o usuario de su canal**:\n\n*(Nota: Su canal requerirá la aprobación del administrador antes de comenzar.)*",
        "packages": "📦 **Elija su paquete de generación de contenido:**\n\n"
                    "🔹 **1. PAQUETE BÁSICO**\n• 3 publicaciones por día\n• Duración: 5 Días\n• Costo: **$35 USDT**\n\n"
                    "🔸 **2. PAQUETE ESTÁNDAR**\n• 5 publicaciones por día\n• Duración: 7 Días\n• Costo: **$50 USDT**\n\n"
                    "👑 **3. PAQUETE PREMIUM**\n• 10 publicaciones por día\n• Duración: 10 Días\n• Costo: **$80 USDT**",
        "hash_req": "💳 **Factura de Pago USDT TRC-20**\n\nPor favor envíe exactamente **${price} USDT** a:\n\n`TPekazrggAXQKveX6jyPEx3b8HPT247Hg8`\n\n👉 Responda aquí con el **Hash de la Transacción (TxID)**:",
        "screenshot_req": "📸 **¡Hash recibido!**\n\nAhora suba una **captura de pantalla de su comprobante de pago** para confirmación dentro de 10 minutos:",
        "topic": "📝 **¡Datos de pago guardados!**\n\nAhora, envíe el **Tema o Nicho** del contenido para su canal:",
        "complete": f"✅ **¡Configuración enviada a revisión!**\n\nNuestro administrador {ADMIN_USERNAME} está verificando su pago y canal. ¡Se le notificará una vez aprobado! 🚀"
    }
}

# --- Conversational Workflow Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    
    country_buttons = [[country] for country in ALLOWED_COUNTRIES]
    reply_markup = ReplyKeyboardMarkup(country_buttons, one_time_keyboard=True, resize_keyboard=True)
    
    await query.message.delete()
    await query.message.chat.send_message(
        LOCALIZATION[selected_lang]["country"], 
        reply_markup=reply_markup, 
        parse_mode="Markdown"
    )
    return COUNTRY

async def capture_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "en")
    context.user_data["country"] = update.message.text
    
    await update.message.reply_text(
        LOCALIZATION[lang]["channel"], 
        reply_markup=ReplyKeyboardRemove(), 
        parse_mode="Markdown"
    )
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
    
    hash_text = LOCALIZATION[lang]["hash_req"].format(price=price)
    await query.message.edit_text(hash_text, parse_mode="Markdown")
    return PAYMENT_HASH

async def capture_hash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "en")
    context.user_data["tx_hash"] = update.message.text
    
    await update.message.reply_text(LOCALIZATION[lang]["screenshot_req"], parse_mode="Markdown")
    return PAYMENT_SCREENSHOT

async def capture_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "en")
    
    if not update.message.photo:
        await update.message.reply_text("⚠️ Please upload a clear photo screenshot of your receipt.")
        return PAYMENT_SCREENSHOT

    context.user_data["screenshot_id"] = update.message.photo[-1].file_id
    await update.message.reply_text(LOCALIZATION[lang]["topic"], parse_mode="Markdown")
    return TOPIC

async def finalize_configuration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "en")
    topic = update.message.text
    user_id = update.message.from_user.id
    
    context.user_data["content_topic"] = topic
    
    await update.message.reply_text(LOCALIZATION[lang]["complete"], parse_mode="Markdown")
    
    # Secure Console Log Output for Admin Tracking
    print(f"\n📢 [PENDING APPROVAL REQUEST SENT TO ADMIN LOGS]")
    print(f"User ID: {user_id}")
    print(f"Country: {context.user_data.get('country')}")
    print(f"Channel Link: {context.user_data.get('channel_link')}")
    print(f"Plan Price: ${context.user_data.get('selected_price')} USDT")
    print(f"TxID Hash: {context.user_data.get('tx_hash')}")
    print(f"Topic Target: {topic}\n")
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Onboarding sequence stopped.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def main():
    TOKEN = os.environ.get("TELEGRAM_TOKEN")
    if not TOKEN:
        raise ValueError("Missing TELEGRAM_TOKEN environment configuration parameters.")

    threading.Thread(target=run_health_server, daemon=True).start()

    app = Application.builder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANG: [CallbackQueryHandler(set_language, pattern="^lang_")],
            COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, capture_country)],
            CHANNEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, capture_channel)],
            PACKAGE: [CallbackQueryHandler(process_package_selection, pattern="^pkg_")],
            PAYMENT_HASH: [MessageHandler(filters.TEXT & ~filters.COMMAND, capture_hash)],
            PAYMENT_SCREENSHOT: [MessageHandler(filters.PHOTO, capture_screenshot)],
            TOPIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, finalize_configuration)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    
    app.add_handler(conv_handler)
    print("HyperGenerateBot engine actively running and polling...")
    
    async with app:
        await app.initialize()
        await app.start()
        await app.updater.start_polling()
        while True:
            await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
