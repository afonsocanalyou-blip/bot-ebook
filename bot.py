import mercadopago
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from flask import Flask, request
import threading

TOKEN = "8499285711:AAFOUKo-ww9y2dRoMcKxXxCW5AQMzo8GLKg"
MP_TOKEN = "APP_USR-5861693151731886-030420-ba25ca80cb6f09ddae75270c8b781c72-254598124"

ARQUIVO_PRODUTO = "ebook.pdf"

usuarios_pagamento = {}

def criar_pagamento(user_id):
    sdk = mercadopago.SDK(MP_TOKEN)

    payment_data = {
        "transaction_amount": 19.90,
        "description": "Ebook O Código da Atração",
        "payment_method_id": "pix",
        "payer": {
            "email": "afonsocanalyou@gmail.com"
        }
    }

    payment_response = sdk.payment().create(payment_data)
    payment = payment_response["response"]

    payment_id = payment["id"]
    usuarios_pagamento[payment_id] = user_id

    return payment["point_of_interaction"]["transaction_data"]["ticket_url"]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton("📚 Comprar Ebook - R$19,90", callback_data="comprar")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "📚 Ebook O Código da Atração\n\nClique no botão abaixo para comprar:",
        reply_markup=reply_markup
    )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    if query.data == "comprar":

        user_id = query.from_user.id

        link_pagamento = criar_pagamento(user_id)

        await query.edit_message_text(
            text=f"💰 Clique no link para pagar:\n\n{link_pagamento}\n\nApós pagar você receberá o ebook automaticamente."
        )


app_flask = Flask(__name__)

@app_flask.route("/webhook", methods=["POST"])
def webhook():

    data = request.json

    if "data" in data and "id" in data["data"]:

        payment_id = int(data["data"]["id"])

        sdk = mercadopago.SDK(MP_TOKEN)

        payment_info = sdk.payment().get(payment_id)

        status = payment_info["response"]["status"]

        if status == "approved":

            if payment_id in usuarios_pagamento:

                user_id = usuarios_pagamento[payment_id]

                import asyncio

                asyncio.run(
                    application.bot.send_document(
                        chat_id=user_id,
                        document=open(ARQUIVO_PRODUTO, "rb"),
                        caption="✅ Pagamento confirmado!\nAqui está seu ebook."
                    )
                )

    return "ok"

def rodar_flask():
    app_flask.run(port=8000)


def main():

    global application

    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))

    threading.Thread(target=rodar_flask).start()

    print("Bot rodando...")


if __name__ == "__main__":
    main()