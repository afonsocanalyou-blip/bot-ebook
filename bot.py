import os
import asyncio
import requests
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ==========================================
# CONFIGURAÇÃO (Lendo da aba 'Variables')
# ==========================================
TOKEN = os.getenv("TOKEN_TELEGRAM")
MP_ACCESS_TOKEN = os.getenv("TOKEN_MERCADO_PAGO")
EBOOK_FILE = "ebook.pdf"

app = Flask(__name__)

# Criamos a aplicação do bot
application = ApplicationBuilder().token(TOKEN).build()

# ==========================================
# COMANDO /START
# ==========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    # Dados para gerar o PIX no Mercado Pago
    payment_data = {
        "transaction_amount": 10.00,
        "description": "Compra de E-book",
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

    try:
        r = requests.post(
            "https://api.mercadopago.com/v1/payments",
            json=payment_data,
            headers=headers
        )
        data = r.json()
        
        # Puxa o código copia e cola
        pix_code = data["point_of_interaction"]["transaction_data"]["qr_code"]
        
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"✅ *Pedido Gerado!*\n\nCopie o código PIX abaixo para pagar:\n\n`{pix_code}`",
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Erro ao gerar pagamento: {e}")
        await context.bot.send_message(chat_id=chat_id, text="Desculpe, houve um erro ao gerar o PIX.")

application.add_handler(CommandHandler("start", start))

# ==========================================
# WEBHOOK DO TELEGRAM
# ==========================================
@app.route("/telegram", methods=["POST"])
async def telegram_webhook():
    # Garante que o bot esteja inicializado para evitar RuntimeError
    if not application.active:
        await application.initialize()
        await application.start()
        
    update = Update.de_json(request.get_json(), application.bot)
    await application.process_update(update)
    return "ok", 200

# ==========================================
# WEBHOOK DO MERCADO PAGO (Entrega o E-book)
# ==========================================
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
                    await application.bot.send_document(
                        chat_id=chat_id, 
                        document=doc, 
                        caption="🙌 Pagamento confirmado! Aqui está seu e-book."
                    )
            except FileNotFoundError:
                print("ERRO: O arquivo ebook.pdf não foi encontrado no servidor.")

    return "ok", 200

# ==========================================
# INICIALIZAÇÃO DO SERVIDOR
# ==========================================
if __name__ == "__main__":
    # Usa a porta fornecida pela Railway ou a 8000 por padrão
    port = int(os.environ.get("PORT", 8000))
    print(f"Bot rodando na porta {port}...")
    app.run(host="0.0.0.0", port=port)