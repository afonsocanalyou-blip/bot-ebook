import os
import asyncio
import requests
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# =====================
# CONFIGURAÇÃO (Variáveis da Railway)
# =====================
TOKEN = os.getenv("8499285711:AAFOUKo-ww9y2dRoMcKxXxCW5AQMzo8GLKg")
MP_ACCESS_TOKEN = os.getenv("APP_USR-5861693151731886-030420-ba25ca80cb6f09ddae75270c8b781c72-254598124")
EBOOK_FILE = "ebook.pdf"

app = Flask(__name__)

# Criamos a aplicação globalmente
application = ApplicationBuilder().token(TOKEN).build()

# =====================
# COMANDO START
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    # Criando o pagamento no Mercado Pago
    payment_data = {
        "transaction_amount": 10.00,
        "description": "E-book Digital",
        "payment_method_id": "pix",
        "payer": {
            "email": "afonsocanalyou@gmail.com" # O MP exige um e-mail do pagador
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
        res = r.json()
        
        # Puxando o código Copia e Cola do PIX
        pix_code = res["point_of_interaction"]["transaction_data"]["qr_code"]
        
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"🚀 *Seu pedido foi gerado!*\n\nCopie o código PIX abaixo para pagar:\n\n`{pix_code}`",
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Erro ao gerar Pix: {e}")
        await context.bot.send_message(chat_id=chat_id, text="Erro ao gerar pagamento. Tente novamente.")

# Adiciona o comando /start ao bot
application.add_handler(CommandHandler("start", start))

# =====================
# ROTAS (WEBHOOKS)
# =====================

@app.route("/telegram", methods=["POST"])
async def telegram_webhook():
    # Esta parte evita o erro "Application not initialized"
    if not application.active:
        await application.initialize()
        await application.start()
        
    update = Update.de_json(request.get_json(), application.bot)
    await application.process_update(update)
    return "ok", 200

@app.route("/webhook", methods=["POST"])
async def mp_webhook():
    data = request.get_json()
    
    # O Mercado Pago avisa quando o status muda
    if data and data.get("type") == "payment":
        payment_id = data["data"]["id"]
        
        headers = {"Authorization": f"Bearer {MP_ACCESS_TOKEN}"}
        r = requests.get(f"https://api.mercadopago.com/v1/payments/{payment_id}", headers=headers)
        payment = r.json()

        if payment.get("status") == "approved":
            chat_id = payment["metadata"]["chat_id"]
            
            # Envia o arquivo PDF
            try:
                with open(EBOOK_FILE, "rb") as doc:
                    await application.bot.send_document(chat_id=chat_id, document=doc, caption="✅ Pagamento aprovado! Aqui está seu e-book.")
            except FileNotFoundError:
                print("ERRO: Arquivo ebook.pdf não encontrado!")
                
    return "ok", 200

# =====================
# INICIALIZAÇÃO
# =====================
if __name__ == "__main__":
    print("Bot rodando com sucesso...")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))