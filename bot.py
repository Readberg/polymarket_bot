from telegram.ext import ApplicationBuilder, CommandHandler
from dotenv import load_dotenv
import os
from api import get_total_value, get_positions

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
WALLET = os.getenv("WALLET_ADDRESS")

async def start(update, context):
    await update.message.reply_text(
        "Привет! Я Polymarket бот.\n"
        "Используй /balance чтобы узнать суммарный баланс и текущие позиции.\n"
        "Используй /positions чтобы увидеть все позиции подробно."
    )

async def balance(update, context):
    data = get_total_value(WALLET)
    if not data or len(data) == 0:
        await update.message.reply_text("Не удалось получить баланс.")
        return

    user_info = data[0]
    user_address = user_info.get("user", "Неизвестен")
    value = user_info.get("value", 0)

    msg = f"Адрес: {user_address}\nСуммарный баланс: {value:.2f} USD\n\nТекущие позиции:\n"

    positions = get_positions(WALLET)
    if not positions or len(positions) == 0:
        msg += "Позиции отсутствуют."
    else:
        for pos in positions[:10]:
            title = pos.get("title", "Неизвестно")
            size = pos.get("size", 0)
            cur_price = pos.get("curPrice", 0)
            total_value = size * cur_price
            msg += f"- {title}: {size} токенов × {cur_price:.2f} USD = {total_value:.2f} USD\n"

    await update.message.reply_text(msg)

# /positions — красиво + корректный расчёт инвестиций
async def positions(update, context):
    positions = get_positions(WALLET, limit=200)  # можно больше

    if not positions or len(positions) == 0:
        await update.message.reply_text("Позиции отсутствуют.")
        return

    formatted_positions = []

    for pos in positions:
        title = pos.get("title", "Неизвестная позиция")
        size = pos.get("size", 0)
        entry = pos.get("avgPrice", 0)
        cur_price = pos.get("curPrice", 0)

        invested = size * entry
        current_value = size * cur_price
        pnl = current_value - invested
        pnl_percent = (pnl / invested * 100) if invested > 0 else 0

        # --- Фильтрация нежелательных позиций ---
        if pnl_percent <= -99:
            continue

        msg = (
            f"📌 <b>{title}</b>\n\n"
            f"💰 Инвестировано: <b>${invested:.2f}</b>\n"
            f"💎 Стоимость сейчас: <b>${current_value:.2f}</b>\n"
            f"{'📈' if pnl >= 0 else '📉'} P&L: <b>{pnl:+.2f}$ ({pnl_percent:+.1f}%)</b>"
        )

        formatted_positions.append(msg)

    if not formatted_positions:
        await update.message.reply_text("Нет актуальных активных позиций.")
        return

    # --- Разбиваем на батчи по 15 ---
    batch_size = 15
    for i in range(0, len(formatted_positions), batch_size):
        batch = formatted_positions[i:i + batch_size]
        text = "\n\n".join(batch)
        await update.message.reply_text(text, parse_mode="HTML")


# запуск
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("balance", balance))
app.add_handler(CommandHandler("positions", positions))

app.run_polling()
