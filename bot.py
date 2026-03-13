import requests
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import asyncio

# =====================
# CONFIG
# =====================

TOKEN = "8499285711:AAFOUKo-ww9y2dRoMcKxXxCW5AQMzo8GLKg"
MP_ACCESS_TOKEN = "APP_USR-5861693151731886-030420-ba25ca80cb6f09ddae75270c8b781c72-254598124"
EBOOK_FILE = "ebook.pdf"

bot = Bot(token=TOKEN)
app = Flask(__name__)

# =====================
# TELEGRAM BOT
# =====================

application = ApplicationBuilder().token(TOKEN).build()

# =====================
# COMANDO START
# =====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_id = update.effective_chat.id

    payment_data = {
        "transaction_amount": 10,
        "description": "Compra Ebook",
        "payment_method_id": "pix",
        "payer": {
            "email": "afonsocanalyou@gmail.com"
        },
        "metadata": {
            "chat_id": chat_id
        }
    }

    headers = {
        "Authorization": f"Bearer {MP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    r = requests.post(
        "https://api.mercadopago.com/v1/payments",
        json=payment_data,
        headers=headers
    )

    data = r.json()

    pix = data["point_of_interaction"]["transaction_data"]["qr_code"]

    await context.bot.send_message(
        chat_id=chat_id,
        text=f"Pague este PIX para receber o ebook:\n\n{pix}"
    )

application.add_handler(CommandHandler("start", start))

# =====================
# TELEGRAM WEBHOOK
# =====================

@app.route("/telegram", methods=["POST"])
def telegram_webhook():

    update = Update.de_json(request.json, bot)

    asyncio.run(application.process_update(update))

    return "ok"

# =====================
# MERCADO PAGO WEBHOOK
# =====================

@app.route("/webhook", methods=["POST"])
def mp_webhook():

    data = request.json

    if "data" in data:

        payment_id = data["data"]["id"]

        headers = {
            "Authorization": f"Bearer {MP_ACCESS_TOKEN}"
        }

        r = requests.get(
            f"https://api.mercadopago.com/v1/payments/{payment_id}",
            headers=headers
        )

        payment = r.json()

        if payment["status"] == "approved":

            chat_id = payment["metadata"]["chat_id"]

            bot.send_document(
                chat_id=chat_id,
                document=open(EBOOK_FILE, "rb")
            )

    return "ok"

# =====================
# START SERVER
# =====================

if __name__ == "__main__":

    print("Bot rodando...")

    app.run(host="0.0.0.0", port=8000)