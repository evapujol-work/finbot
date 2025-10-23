import json
import os
import re
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from openai import OpenAI   # Necessari per parlar amb Ollama

# 🔹 Configura OLLAMA (no cal cap API key)
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)

# 🔑 Només necessites la clau del bot de Telegram
import os
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# 🧾 Fitxer on guardarem les despeses
DATA_FILE = "finances.json"

# ⚙️ Carrega o crea el fitxer
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        finances = json.load(f)
else:
    finances = {}

# 💸 Funció per guardar les dades
def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(finances, f, indent=2)

# 🧠 Funció IA per entendre el text amb OLLAMA
def process_message(user, text):
    # Carreguem les dades actuals del fitxer
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            finances = json.load(f)
    else:
        finances = {}

    # Recuperem les dades de l'usuari (o inicialitzem si no n'hi ha)
    dades_usuari = finances.get(user, {"ingressos": 0, "despeses": []})
    total_despeses = sum(dades_usuari["despeses"])
    total_ingressos = dades_usuari["ingressos"]
    saldo = total_ingressos - total_despeses

    # Convertim les dades a text per enviar-les a l'IA
    dades_text = (
        f"Ingressos totals: {total_ingressos} €. "
        f"Despeses totals: {total_despeses} €. "
        f"Saldo restant: {saldo} €."
    )

    prompt = f"""
Ets FinBot, un assessor financer personal i simpàtic.
Recorda sempre el context financer de l'usuari.
Usa aquesta informació per respondre amb sentit:

Dades actuals: {dades_text}

Missatge de l'usuari: {text}

Respon en català amb un to natural, breu i amable.
Si detectes noves despeses o ingressos, comenta-ho positivament.
Dona recomanacions senzilles per estalviar o controlar millor el pressupost.
"""

    try:
        response = client.chat.completions.create(
            model="llama3",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ Error amb Ollama: {e}"

# 👋 Comanda /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hola! Sóc FinBot, el teu assistent financer personal.\n"
        "Pots escriure'm coses com:\n"
        "• 'He gastat 20€ al súper'\n"
        "• 'Quant he gastat aquest mes?'\n"
        "• 'Afegeix un ingrés de 1000€'\n"
        "• 'Mostra el meu balanç'"
    )

# 💬 Processa qualsevol missatge
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = str(update.message.chat_id)
    text = update.message.text

    # Si l'usuari no té dades, les crea
    if user not in finances:
        finances[user] = {"ingressos": 0, "despeses": []}

    match = re.search(r"(\d+[\.,]?\d*)\s*€", text)
    if match:
        quantitat = float(match.group(1).replace(",", "."))
        finances[user]["despeses"].append(quantitat)
        save_data()
        resposta = f"💸 He afegit una despesa de {quantitat} €.\nTotal gastat: {sum(finances[user]['despeses']):.2f} €"
    else:
        resposta = process_message(user, text)

    await update.message.reply_text(resposta)

# 🚀 Inicialitza el bot
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("🤖 Bot funcionant! Prem Ctrl+C per aturar.")
app.run_polling()
