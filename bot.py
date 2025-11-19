from telegram.ext import ApplicationBuilder, CommandHandler
from dotenv import load_dotenv
import os
from api import get_total_value, get_positions  # Импорт функции для работы с API

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

# Хранение адресов кошельков пользователей в памяти
user_wallets = {}

def is_valid_address(address: str) -> bool:
    """
    Проверка, что адрес имеет правильный формат.
    """
    return address.strip().startswith("0x") and len(address.strip()) == 42

async def start(update, context):
    await update.message.reply_text(
        "<b>Привет!</b> Я Polymarket бот. 🌟\n\n"
        "<i>Используй команды, чтобы получить информацию:</i>\n\n"
        "🔹 <b>/balance</b> — узнать суммарный баланс и текущие позиции.\n"
        "🔹 <b>/positions</b> — получить подробную информацию о всех позициях.\n"
        "🔹 <b>/set_wallet</b> — установить свой адрес кошелька.\n"
        "🔹 <b>/remove_wallet</b> — удалить свой адрес кошелька.\n\n"
        "Я помогу отслеживать твои активы на Polymarket! 🚀"
        "\n\n<i>Просто введи команду, и я дам все данные! 📊</i>",
        parse_mode="HTML"
    )

async def set_wallet(update, context):
    user_id = update.message.from_user.id
    wallet_address = ' '.join(context.args)

    if not wallet_address:
        await update.message.reply_text("Пожалуйста, предоставьте свой адрес кошелька после команды /set_wallet. Например: /set_wallet 0x123abc...")
        return

    # Проверка на корректность адреса (передаем в функцию is_valid_address)
    if not is_valid_address(wallet_address):
        await update.message.reply_text("Неверный формат адреса! Адрес должен начинаться с '0x' и иметь длину 42 символа.")
        return

    # Сохраняем адрес для пользователя
    user_wallets[user_id] = wallet_address
    await update.message.reply_text(f"Адрес кошелька успешно сохранён: {wallet_address}")

async def remove_wallet(update, context):
    user_id = update.message.from_user.id

    # Проверяем, есть ли кошелек в памяти
    if user_id in user_wallets:
        del user_wallets[user_id]
        await update.message.reply_text("Адрес кошелька успешно удалён.")
    else:
        await update.message.reply_text("У вас нет сохранённого адреса кошелька.")

async def balance(update, context):
    user_id = update.message.from_user.id
    wallet_address = user_wallets.get(user_id)

    if not wallet_address:
        await update.message.reply_text("Пожалуйста, сначала установите свой адрес кошелька командой /set_wallet.")
        return

    data = get_total_value(wallet_address)
    if not data:
        await update.message.reply_text("Не удалось получить баланс, проверьте формат адреса.")
        return

    user_info = data[0]
    user_address = user_info.get("user", "Неизвестен")
    value = user_info.get("value", 0)

    msg = f"Адрес: {user_address}\nСуммарный баланс: {value:.2f} USD"
    await update.message.reply_text(msg)

async def positions(update, context):
    user_id = update.message.from_user.id
    wallet_address = user_wallets.get(user_id)

    if not wallet_address:
        await update.message.reply_text("Пожалуйста, сначала установите свой адрес кошелька командой /set_wallet.")
        return

    positions = get_positions(wallet_address, limit=200)
    if not positions:
        await update.message.reply_text("Позиции отсутствуют.")
        return

    formatted_positions = []
    total_invested, total_current_value = 0, 0

    for pos in positions:
        title = pos.get("title", "Неизвестная позиция")
        size = pos.get("size", 0)
        entry = pos.get("avgPrice", 0)
        cur_price = pos.get("curPrice", 0)

        invested = size * entry
        current_value = size * cur_price
        pnl = current_value - invested
        pnl_percent = (pnl / invested * 100) if invested > 0 else 0

        if pnl_percent <= -99:
            continue

        formatted_positions.append({
            "title": title,
            "invested": invested,
            "current_value": current_value,
            "pnl": pnl,
            "pnl_percent": pnl_percent
        })

        total_invested += invested
        total_current_value += current_value

    if not formatted_positions:
        await update.message.reply_text("Нет актуальных активных позиций.")
        return

    total_pnl = total_current_value - total_invested
    total_pnl_percent = (total_pnl / total_invested * 100) if total_invested > 0 else 0

    # Sort by P&L in descending order
    formatted_positions.sort(key=lambda x: x["pnl"], reverse=True)

    # Split into batches of 15
    batch_size = 15
    for i in range(0, len(formatted_positions), batch_size):
        batch = formatted_positions[i:i + batch_size]
        text_lines = []

        if i == 0:  # Summary only in the first message
            text_lines.append(
                f"<b>Сумма инвестиций:</b> <i>{total_invested:.2f}$</i>\n"
                f"<b>Стоимость сейчас:</b> <i>{total_current_value:.2f}$</i>\n"
                f"<b>Общий P&L:</b> <i>{total_pnl:+.2f}$ ({total_pnl_percent:+.1f}%)</i>\n"
                "-------------------------------------"
            )

        for pos in batch:
            text_lines.append(
                f"<b>📌 {pos['title']}</b>\n"
                f"<i>Инвестировано:</i> {pos['invested']:.2f}$\n"
                f"<i>Стоимость сейчас:</i> {pos['current_value']:.2f}$\n"
                f"<i>P&L:</i> {pos['pnl']:+.2f}$ ({pos['pnl_percent']:+.1f}%)\n"
            )

        await update.message.reply_text("\n".join(text_lines), parse_mode="HTML")

# Start the bot
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("balance", balance))
app.add_handler(CommandHandler("positions", positions))
app.add_handler(CommandHandler("set_wallet", set_wallet))
app.add_handler(CommandHandler("remove_wallet", remove_wallet))

app.run_polling()
