import os
import requests
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "8499285711:AAFOUKo-ww9y2dRoMcKxXxCW5AQMzo8GLKg"
MP_ACCESS_TOKEN = "APP_USR-5861693151731886-030420-ba25ca80cb6f09ddae75270c8b781c72-254598124"
EBOOK_PATH = "ebook.pdf"

app = Flask(__name__)
bot = Bot(token=TOKEN)

# comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    payment_data = {
        "transaction_amount": 10,
        "description": "Compra do Ebook",
        "payment_method_id": "pix",
        "payer": {
            "email": "afonsocanalyou@gmail.com"
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

    pix_code = data["point_of_interaction"]["transaction_data"]["qr_code"]

    await context.bot.send_message(
        chat_id=chat_id,
        text=f"Pague o PIX abaixo para receber o ebook:\n\n{pix_code}"
    )

# webhook do mercado pago
@app.route("/webhook", methods=["POST"])
def webhook():

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
                document=open(EBOOK_PATH, "rb")
            )

    return "ok"

# iniciar bot telegram
def start_bot():
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.run_polling()

# iniciar servidor
if __name__ == "__main__":
    import threading

    print("Bot rodando...")

    threading.Thread(target=start_bot).start()

    app.run(host="0.0.0.0", port=8000)