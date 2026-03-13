import os
import asyncio
import requests
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# CONFIGURAÇÃO - Puxa os dados da aba 'Variables' da Railway
TOKEN = os.getenv("TOKEN_TELEGRAM")
MP_ACCESS_TOKEN = os.getenv("TOKEN_MERCADO_PAGO")
EBOOK_FILE = "ebook.pdf"

app = Flask(__name__)

# Inicializa a aplicação do bot de forma global
application = ApplicationBuilder().token(TOKEN).build()

# Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    payment_data = {
        "transaction_amount": 10.00,
        "description": "E-book Digital",
        "payment_method_id": "pix",
        "payer": {"email": "cliente@email.com"},
        "metadata": {"chat_id": chat_id}
    }

    headers = {
        "Authorization": f"Bearer {MP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        r = requests.post("https://api.mercadopago.com/v1/payments", json=payment_data, headers=headers)
        res = r.json()
        pix_code = res["point_of_interaction"]["transaction_data"]["qr_code"]
        
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"🚀 *Pedido gerado!*\n\nCopie o código PIX abaixo para pagar:\n\n`{pix_code}`",
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Erro MP: {e}")
        await context.bot.send_message(chat_id=chat_id, text="Erro ao gerar PIX. Tente novamente.")

# Adiciona o comando à aplicação
application.add_handler(CommandHandler("start", start))

@app.route("/telegram", methods=["POST"])
async def telegram_webhook():
    # Inicializa o bot se ele ainda não estiver ativo (resolve o erro 502/500)
    if not application.active:
        await application.initialize()
        await application.start()
        
    # Processa a mensagem vinda do Telegram
    update = Update.de_json(request.get_json(), application.bot)
    await application.process_update(update)
    return "ok", 200

@app.route("/webhook", methods=["POST"])
async def mp_webhook():
    data = request.get_json()
    if data and data.get("type") == "payment":
        payment_id = data["data"]["id"]
        headers = {"Authorization": f"Bearer {MP_ACCESS_TOKEN}"}
        r = requests.get(f"https://api.mercadopago.com/v1/payments/{payment_id}", headers=headers)
        payment = r.json()

        if payment.get("status") == "approved":
            chat_id = payment["metadata"]["chat_id"]
            try:
                with open(EBOOK_FILE, "rb") as doc:
                    await application.bot.send_document(chat_id=chat_id, document=doc, caption="✅ Pagamento aprovado!")
            except:
                print("Arquivo não encontrado.")
                
    return "ok", 200

if __name__ == "__main__":
    # A Railway define a porta automaticamente na variável PORT
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)