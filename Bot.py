import urllib.request
import json
import time
import random
import os

TOKEN = os.environ.get("BOT_TOKEN", "9193782655:AAFP7mMmjbL4ITM--2LBuStvO0YcTTc9gOk")
DATA_FILE = "users.json"

# --- КОНФИГУРАЦИЯ CRYPTO PAY API ---
CRYPTO_TOKEN = "673377:AAYoeDgQbzihIIcsYEaN0gvhLcnZEh4mPCs"
CRYPTO_TESTNET = False  # Работа с реальной сетью @CryptoBot

def crypto_api_request(method, payload=None):
    """Универсальная функция запросов к Crypto Pay API через urllib"""
    base_url = "https://cryptometrika.io" if CRYPTO_TESTNET else "https://cryptometrika.io"
    url = f"{base_url}/{method}"
    
    req = urllib.request.Request(url, headers={
        "Crypto-Pay-API-Token": CRYPTO_TOKEN,
        "Content-Type": "application/json"
    })
    if payload:
        req.data = json.dumps(payload).encode("utf-8")
    try:
        response = urllib.request.urlopen(req, timeout=10)
        return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        print(f"Ошибка CryptoBot API {method}:", e)
        return {"ok": False, "error": str(e)}

# --- ФУНКЦИИ TELEGRAM API ---

def api_request(method, payload):
    url = f"https://telegram.org{TOKEN}/{method}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        res = urllib.request.urlopen(req, timeout=10)
        return json.loads(res.read().decode("utf-8"))
    except Exception as e:
        print(f"Ошибка API {method}:", e)
        return None

def send_message(chat_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    api_request("sendMessage", payload)

def edit_message(chat_id, message_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    api_request("editMessageText", payload)

def send_animation(chat_id, emoji):
    api_request("sendDice", {"chat_id": chat_id, "emoji": emoji})

def answer_callback(callback_id):
    api_request("answerCallbackQuery", {"callback_query_id": callback_id})

def send_stars_invoice(chat_id, msg_id, amount_stars, amount_dollars):
    url = f"https://telegram.org{TOKEN}/createInvoiceLink"
    payload = {
        "title": f"Покупка {amount_dollars}$",
        "description": f"Пополнение баланса на {amount_dollars} долларов",
        "payload": f"buy_{amount_dollars}_{amount_stars}",
        "currency": "XTR",
        "prices": [{"label": f"{amount_dollars}$", "amount": amount_stars}]
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        response = urllib.request.urlopen(req, timeout=10)
        result = json.loads(response.read().decode("utf-8"))
        if result.get("ok"):
            invoice_link = result["result"]
            kb = {"inline_keyboard": [[{"text": f"💎 Оплатить {amount_stars} Stars", "url": invoice_link}], [{"text": "⬅️ Назад", "callback_data": "shop"}]]}
            edit_message(chat_id, msg_id, "👇 Нажмите на кнопку ниже, чтобы оплатить:", kb)
    except Exception as e:
        print("Ошибка API:", e)

# --- ЛОГИКА ДЕПОЗИТОВ И ВЫПЛАТ КРИПТЫ ---

def create_crypto_invoice(chat_id, msg_id, amount_dollars):
    payload = {
        "asset": "USDT",
        "amount": str(amount_dollars),
        "description": "Пополнение игрового баланса",
        "payload": f"deposit_{chat_id}_{amount_dollars}" 
    }
    res = crypto_api_request("createInvoice", payload)
    if res.get("ok"):
        invoice = res["result"]
        pay_url = invoice["pay_url"]
        invoice_id = invoice["invoice_id"]
        
        kb = {
            "inline_keyboard": [
                [{"text": f"💳 Оплатить {amount_dollars}$ (USDT)", "url": pay_url}],
                [{"text": "🔄 Проверить оплату", "callback_data": f"check_dep_{invoice_id}"}],
                [{"text": "⬅️ Назад", "callback_data": "profile"}]
            ]
        }
        edit_message(chat_id, msg_id, f"⚡️ <b>Счет на {amount_dollars}$ USDT создан!</b>\n\nПерейдите по кнопке ниже для оплаты, а после подтверждения нажмите «Проверить оплату»:", kb)
    else:
        edit_message(chat_id, msg_id, "❌ Ошибка создания счета. Попробуйте позже.", {"inline_keyboard": [[{"text": "⬅️ Назад", "callback_data": "profile"}]]})

def send_crypto_payout(chat_id, msg_id, amount_dollars, target_tg_id):
    user = get_user(chat_id)
    if user["balance"] < amount_dollars:
        edit_message(chat_id, msg_id, "❌ Ошибка: недостаточно средств для вывода.", {"inline_keyboard": [[{"text": "⬅️ Назад", "callback_data": "profile"}]]})
        return

    spend_id = f"payout_{chat_id}_{int(time.time())}"
    payload = {
        "user_id": int(target_tg_id),
        "asset": "USDT",
        "amount": str(amount_dollars),
        "spend_id": spend_id
    }
    res = crypto_api_request("transfer", payload)
    if res.get("ok"):
        new_balance = user["balance"] - amount_dollars
        update_user(chat_id, balance=new_balance)
        res_text = f"✅ <b>Выплата успешно отправлена!</b>\n\n💰 Переведено: {amount_dollars}$ USDT\n📱 ID Получателя: <code>{target_tg_id}</code>\n💵 Новый баланс: <b>{new_balance}$</b>\n\n"
        
        text, kb = get_main_menu(get_user(chat_id))
        send_message(chat_id, res_text + text, kb)
    else:
        error_name = res.get("error", {}).get("name", "Unknown")
        err_msg = "Ошибка обработки шлюза."
        if error_name == "USER_NOT_FOUND":
            err_msg = "Этот пользователь не найден. Ему нужно хотя бы раз открыть @CryptoBot."
        elif error_name == "NOT_ENOUGH_FUNDS":
            err_msg = "На балансе вашего приложения в CryptoBot не хватает денег для вывода."
        
        kb = {"inline_keyboard": [[{"text": "⬅️ Назад", "callback_data": "profile"}]]}
        send_message(chat_id, f"❌ <b>Ошибка выплаты!</b>\n\n<i>Причина: {err_msg} ({error_name})</i>", kb)

# --- РАБОТА С JSON БД ---

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try: return json.load(f)
            except: return {}
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user(uid):
    data = load_data()
    uid = str(uid)
    if uid not in data:
        data[uid] = {"balance": 10, "wins": 0, "losses": 0, "last_bonus": 0, "name": "Игрок"}
        save_data(data)
    return data[uid]

def update_user(uid, **kwargs):
    data = load_data()
    uid = str(uid)
    if uid not in data:
        data[uid] = {"balance": 10, "wins": 0, "losses": 0, "last_bonus": 0, "name": "Игрок"}
    data[uid].update(kwargs)
    save_data(data)

# --- ИНТЕРФЕЙСЫ МЕНЮ ---

def get_main_menu(user):
    text = (
        f"👤 <b>{user['name']}</b>\n"
        f"💰 Баланс: <b>{user['balance']}$</b> 💵\n"
        f"📈 Статистика: ✅ {user['wins']} | ❌ {user['losses']}\n\n"
        f"🎰 <b>Выберите игру или режим:</b>"
    )
    kb = {
        "inline_keyboard": [
            [{"text": "🎲 (до x216)", "callback_data": "game_dice"}, {"text": "⚽ (до x25)", "callback_data": "game_football"}, {"text": "🏀 (до x25)", "callback_data": "game_basketball"}],
            [{"text": "🎯 (до x36)", "callback_data": "game_darts"}, {"text": "🎳 (до x36)", "callback_data": "game_bowling"}, {"text": "🎰 (до x40)", "callback_data": "game_slots"}],
            [{"text": "👨‍💻 Авторские", "callback_data": "game_custom"}, {"text": "🚀 Турбо", "callback_data": "game_turbo"}, {"text": "🃏 Mini-игры", "callback_data": "game_mini"}],
            [{"text": "💰 Баланс / Крипта", "callback_data": "profile"}, {"text": "🎁 Бонус", "callback_data": "bonus"}, {"text": "💎 Купить $", "callback_data": "shop"}]
        ]
    }
    return text, kb

def get_profile_menu(user):
    text = (
        f"👤 <b>Личный кабинет: {user['name']}</b>\n\n"
        f"💰 Игровой баланс: <b>{user['balance']}$</b> 💵\n"
        f"✅ Побед: {user['wins']}\n"
        f"❌ Поражений: {user['losses']}\n\n"
        f"Вы можете пополнить баланс или моментально вывести USDT через CryptoBot:"
    )
    kb = {
        "inline_keyboard": [
            [{"text": "➕ Пополнить (Крипта)", "callback_data": "crypto_deposit"}, {"text": "➖ Вывести (Крипта)", "callback_data": "crypto_withdraw"}],
            [{"text": "⬅️ Назад", "callback_data": "main_menu"}]
        ]
    }
    return text, kb

def get_crypto_deposit_menu():
    text = "💳 <b>Выберите сумму пополнения в USDT ($):</b>"
    kb = {
        "inline_keyboard": [
            [{"text": "10$", "callback_data": "cryptodep_10"}, {"text": "50$", "callback_data": "cryptodep_50"}],
            [{"text": "100$", "callback_data": "cryptodep_100"}, {"text": "500$", "callback_data": "cryptodep_500"}],
            [{"text": "⬅️ Назад", "callback_data": "profile"}]
        ]
    }
    return text, kb

def get_crypto_withdraw_menu(user):
    text = f"💵 <b>Выберите сумму для вывода USDT:</b>\n\nДоступно на балансе: <b>{user['balance']}$</b>"
    kb = {
        "inline_keyboard": [
            [{"text": "10$", "callback_data": "cryptowd_10"}, {"text": "50$", "callback_data": "cryptowd_50"}],
            [{"text": "100$", "callback_data": "cryptowd_100"}, {"text": "Все средства", "callback_data": f"cryptowd_{user['balance']}"}],
            [{"text": "⬅️ Назад", "callback_data": "profile"}]
        ]
    }
    return text, kb

def get_shop_menu(user):
    text = f"💎 <b>Магазин валюты</b>\n\nВаш баланс: <b>{user['balance']}$</b> 💵\n\nВыберите пакет:"
    kb = {
        "inline_keyboard": [
            [{"text": "100$ за 10 ⭐", "callback_data": "buy_100_10"}],
            [{"text": "500$ за 40 ⭐", "callback_data": "buy_500_40"}],
[{"text": "1000$ за 70 ⭐", "callback_data": "buy_1000_70"}],
[{"text": "⬅️ Назад", "callback_data": "main_menu"}]
]
}
return text, kb
def get_bet_menu(user, game):
game_names = {
"dice": "🎲 Дайс", "darts": "🎯 Дартс", "football": "⚽ Футбол",
"basketball": "🏀 Баскет", "bowling": "🎳 Боулинг", "slots": "🎰 Слоты",
"custom": "👨‍💻 Авторские", "turbo": "🚀 Турбо", "mini": "🃏 Мини-игры"
}
text = f"👤 {user['name']}\n💰 Баланс: {user['balance']}$ 💵\n🎮 Игра: {game_names.get(game, game)}\n\n👇 Выберите ставку:"
kb = {
"inline_keyboard": [
[{"text": "10$", "callback_data": f"bet_{game}10"}, {"text": "50$", "callback_data": f"bet{game}50"}, {"text": "100$", "callback_data": f"bet{game}100"}],
[{"text": "500$", "callback_data": f"bet{game}500"}, {"text": "✍️ Своя", "callback_data": f"custom{game}"}, {"text": "Макс", "callback_data": f"bet_{game}_{user['balance']}"}],
[{"text": "⬅️ Назад", "callback_data": "main_menu"}]
]
}
return text, kb
def get_choice_menu(user, game, bet):
text = f"👤 {user['name']}\n💰 Баланс: {user['balance']}$ 💵\n💵 Ставка: {bet}$\n\n🎯 На что ставим?"
kb = []
if game == "dice":
kb = [
[{"text": "1 (x5)", "callback_data": f"res_{game}{bet}1"}, {"text": "2 (x5)", "callback_data": f"res{game}{bet}2"}, {"text": "3 (x5)", "callback_data": f"res{game}{bet}3"}],
[{"text": "4 (x5)", "callback_data": f"res{game}{bet}4"}, {"text": "5 (x5)", "callback_data": f"res{game}{bet}5"}, {"text": "6 (x5)", "callback_data": f"res{game}{bet}6"}],
[{"text": "⬆️ Больше 3 (x2)", "callback_data": f"res{game}{bet}high"}],
[{"text": "⬇️ Меньше 4 (x2)", "callback_data": f"res{game}{bet}low"}]
]
elif game == "turbo":
kb = [
[{"text": "3 кубика (Сумма > 10) x3", "callback_data": f"res_dice{bet}three_high"}],
[{"text": "Три шестерки (x50)", "callback_data": f"res_dice{bet}three_six"}],
[{"text": "Все > 3 (x5)", "callback_data": f"res_turbo{bet}turbo_high"}],
[{"text": "Все < 4 (x5)", "callback_data": f"res_turbo{bet}turbo_low"}]
]
elif game == "custom":
kb = [
[{"text": "🔥 Мега-Джекпот (x10)", "callback_data": f"res{game}{bet}jackpot"}],
[{"text": "💀 Смертельная ставка (x15)", "callback_data": f"res{game}{bet}death"}]
]
elif game == "mini":
kb = [
[{"text": "🦅 Орел (x2)", "callback_data": f"res{game}{bet}heads"}],
[{"text": "🪙 Решка (x2)", "callback_data": f"res{game}{bet}tails"}]
]
elif game == "football":
kb = [[{"text": "✅ Гол (x1.5)", "callback_data": f"res{game}{bet}goal"}], [{"text": "❌ Мимо (x2.5)", "callback_data": f"res{game}{bet}miss"}]]
elif game == "basketball":
kb = [[{"text": "🏀 2 очка (x1.5)", "callback_data": f"res{game}{bet}2pt"}], [{"text": "🏀 3 очка (x3)", "callback_data": f"res{game}{bet}3pt"}]]
elif game == "darts":
kb = [[{"text": "🎯 В яблочко (x3)", "callback_data": f"res{game}{bet}bull"}], [{"text": "❌ Мимо (x1.5)", "callback_data": f"res{game}{bet}miss"}]]
elif game == "slots":
text = f"👤 {user['name']}\n💰 Баланс: {user['balance']}$ 💵\n💵 Ставка: {bet}$\n\n🎰 Выберите символ (3 в ряд = x16):"
kb = [
[{"text": "🍋 Лимон (x16)", "callback_data": f"res{game}{bet}lemon"}],
[{"text": "🍒 Вишня (x16)", "callback_data": f"res{game}{bet}cherry"}],
[{"text": "💎 Алмаз (x16)", "callback_data": f"res{game}{bet}diamond"}],
[{"text": "7️⃣ Семерка (x16)", "callback_data": f"res{game}{bet}seven"}],
[{"text": "❌ Не выпадет 3 в ряд (x2)", "callback_data": f"res{game}{bet}lose"}]
]
elif game == "bowling":
kb = [
[{"text": "🎳 Страйк (x5)", "callback_data": f"res{game}{bet}strike"}, {"text": "🎯 7-9 (x2.5)", "callback_data": f"res{game}{bet}high"}],
[{"text": "⚪ 1-3 (x1.5)", "callback_data": f"res{game}{bet}low"}, {"text": "❌ Промах (x4)", "callback_data": f"res{game}_{bet}miss"}]
]
kb.append([{"text": "⬅️ Назад", "callback_data": f"game{game}"}])
return text, {"inline_keyboard": kb}

--- ПОЛЛИНГ И ОБРАБОТКА ОБНОВЛЕНИЙ ---

print("Бот запущен...")
offset = 0
user_states = {}
while True:
try:
url = f"telegram.org{TOKEN}/getUpdates?timeout=30&offset={offset}"
response = urllib.request.urlopen(url, timeout=40)
updates = json.loads(response.read().decode("utf-8"))
if not updates.get("ok"):
time.sleep(2)
continue
for update in updates["result"]:
offset = update["update_id"] + 1
if "pre_checkout_query" in update:
api_request("answerPreCheckoutQuery", {"pre_checkout_query_id": update["pre_checkout_query"]["id"], "ok": True})
continue
if "message" in update and "successful_payment" in update["message"]:
msg = update["message"]
chat_id = msg["chat"]["id"]
user_id = msg["from"]["id"]
payload = msg["successful_payment"]["invoice_payload"]
parts = payload.split("_")
if len(parts) == 3:
dollars = int(parts[1])
user = get_user(user_id)
new_bal = user["balance"] + dollars
update_user(user_id, balance=new_bal)
send_message(chat_id, f"✅ Оплата прошла успешно!\nВам начислено {dollars}$ 💵\nВаш баланс: {new_bal}$")
continue
# ОБРАБОТКА CALLBACK КНОПОК
if "callback_query" in update:
cb = update["callback_query"]
cb_id = cb["id"]
chat_id = cb["message"]["chat"]["id"]
msg_id = cb["message"]["message_id"]
user_id = cb["from"]["id"]
data = cb["data"]
answer_callback(cb_id)
user = get_user(user_id)
if user_id in user_states and not data.startswith("res_"):
del user_states[user_id]
if data == "main_menu" or data == "menu":
text, kb = get_main_menu(user)
edit_message(chat_id, msg_id, text, kb)
elif data == "shop":
text, kb = get_shop_menu(user)
edit_message(chat_id, msg_id, text, kb)
elif data.startswith("buy_"):
parts = data.split("_")
send_stars_invoice(chat_id, msg_id, int(parts), int(parts[1]))
# КРИПТО ИНТЕРФЕЙСЫ
elif data == "profile":
text, kb = get_profile_menu(user)
edit_message(chat_id, msg_id, text, kb)
elif data == "crypto_deposit":
text, kb = get_crypto_deposit_menu()
edit_message(chat_id, msg_id, text, kb)
elif data.startswith("cryptodep_"):
amount = int(data.split("_")[1])
create_crypto_invoice(chat_id, msg_id, amount)
elif data.startswith("check_dep_"):
invoice_id = data.split("_")
res = crypto_api_request("getInvoices", {"invoice_ids": [int(invoice_id)]})
is_paid = False
dep_amount = 0.0
if res.get("ok") and res["result"]["items"]:
invoice_data = res["result"]["items"][0]
if invoice_data["status"] == "paid":
is_paid = True
dep_amount = float(invoice_data["amount"])
if is_paid:
new_bal = user["balance"] + dep_amount
update_user(user_id, balance=new_bal)
send_message(chat_id, f"✅ Баланс успешно пополнен на {dep_amount}$ через CryptoBot!")
t, k = get_profile_menu(get_user(user_id))
edit_message(chat_id, msg_id, t, k)
else:
send_message(chat_id, "❌ Оплата не найдена. Сначала оплатите инвойс в приложении CryptoBot.")
elif data == "crypto_withdraw":
text, kb = get_crypto_withdraw_menu(user)
edit_message(chat_id, msg_id, text, kb)
elif data.startswith("cryptowd_"):
amount = float(data.split("_")[1])
if user["balance"] < amount or amount <= 0:
send_message(chat_id, "❌ Недостаточно средств на балансе!")
else:
user_states[user_id] = ("wait_payout_id", amount, msg_id)
edit_message(chat_id, msg_id, f"📤 Вывод суммы: {amount}$ USDT\n\nОтправьте следующим сообщением в чат ваш цифровой Telegram ID, на который будет совершена выплата.\n\nID получателя должен быть зарегистрирован в @CryptoBot!", {"inline_keyboard": [[{"text": "Отмена", "callback_data": "profile"}]]})
elif data == "bonus":
now = int(time.time())
if "last_bonus" in user and now - user["last_bonus"] < 86400:
left = 86400 - (now - user["last_bonus"])
text = f"⏳ Бонус уже получен.\nЖдать: {left//3600}ч {(left%3600)//60}м"
else:
new_bal = user["balance"] + 5
update_user(user_id, balance=new_bal, last_bonus=now)
text = f"🎁 Бонус +5$!\nВаш баланс: {new_bal}$ 💵"
edit_message(chat_id, msg_id, text, {"inline_keyboard": [[{"text": "⬅️ Назад", "callback_data": "main_menu"}]]})
elif data.startswith("game_"):
game = data.split("_")[1]
text, kb = get_bet_menu(user, game)
edit_message(chat_id, msg_id, text, kb)
elif data.startswith("custom_"):
game = data.split("")[1]
user_states[user_id] = (game, msg_id)
text = f"✍️ Напишите сумму вашей ставки в чат (от 10 до {user['balance']}):"
edit_message(chat_id, msg_id, text, {"inline_keyboard": [[{"text": "Отмена", "callback_data": f"game{game}"}]]})
elif data.startswith("bet_"):
parts = data.split("")
game = parts[1]
bet = int(parts)
if bet > user["balance"] or bet < 10:
text = f"❌ Неверная ставка (мин. 10) или недостаточно средств!"
edit_message(chat_id, msg_id, text, {"inline_keyboard": [[{"text": "⬅️ Назад", "callback_data": f"game{game}"}]]})
else:
text, kb = get_choice_menu(user, game, bet)
edit_message(chat_id, msg_id, text, kb)
elif data.startswith("res_"):
parts = data.split("_")
game = parts[1]
bet = int(parts)
choice = parts
edit_message(chat_id, msg_id, f"🎰 Инициализация раунда... Ставка: {bet}$", None)
win = False
multiplier = 1.0
res_detail = ""
if game == "slots":
symbols = ["🍋", "🍒", "💎", "7️⃣"]
results = [random.choice(symbols) for _ in range(3)]
res_detail = f"🎰 Результат: {' '.join(results)}\n"
if choice == "lose":
if results[0] != results[1] or results[1] != results:
win = True; multiplier = 2.0
else:
target_sym = {"lemon": "🍋", "cherry": "🍒", "diamond": "💎", "seven": "7️⃣"}[choice]
if results[0] == results[1] == results == target_sym:
win = True; multiplier = 16.0
elif game == "dice" or game == "turbo":
if choice == "three_high" or choice == "three_six":
d1 = random.randint(1, 6); send_animation(chat_id, "🎲"); time.sleep(1)
d2 = random.randint(1, 6); send_animation(chat_id, "🎲"); time.sleep(1)
d3 = random.randint(1, 6); send_animation(chat_id, "🎲"); time.sleep(1.5)
total = d1 + d2 + d3
res_detail = f"Выпало: {d1}, {d2}, {d3} (Сумма: {total})\n"
if choice == "three_high" and total > 10: win = True; multiplier = 3.0
elif choice == "three_six" and d1 == 6 and d2 == 6 and d3 == 6: win = True; multiplier = 50.0
elif choice == "turbo_high" or choice == "turbo_low":
d1 = random.randint(1, 6); send_animation(chat_id, "🎲"); time.sleep(1)
d2 = random.randint(1, 6); send_animation(chat_id, "🎲"); time.sleep(1)
d3 = random.randint(1, 6); send_animation(chat_id, "🎲"); time.sleep(1.5)
res_detail = f"Выпало: {d1}, {d2}, {d3}\n"
if choice == "turbo_high" and d1 > 3 and d2 > 3 and d3 > 3: win = True
elif choice == "turbo_low" and d1 < 4 and d2 < 4 and d3 < 4: win = True
multiplier = 5.0
else:
val = random.randint(1, 6)
send_animation(chat_id, "🎲"); time.sleep(2)
res_detail = f"Выпало: {val}\n"
if choice.isdigit() and int(choice) == val: win = True; multiplier = 5.0
elif choice == "high" and val > 3: win = True; multiplier = 2.0
elif choice == "low" and val < 4: win = True; multiplier = 2.0
elif game == "custom":
send_animation(chat_id, "🎲"); time.sleep(2)
val = random.randint(1, 100)
res_detail = f"Рулетка судьбы: {val}/100\n"
if choice == "jackpot" and val > 90: win = True; multiplier = 10.0
elif choice == "death" and val > 95: win = True; multiplier = 15.0
elif game == "mini":
val = random.choice(["heads", "tails"])
send_animation(chat_id, "🎲"); time.sleep(2)
res_detail = f"Выпало: {'Орел' if val == 'heads' else 'Решка'}\n"
if choice == val: win = True
multiplier = 2.0
elif game == "football":
val = random.randint(1, 5)
send_animation(chat_id, "⚽"); time.sleep(2)
res_detail = f"Матч окончен.\n"
if choice == "goal" and val >= 3: win = True
elif choice == "miss" and val < 3: win = True
multiplier = 1.5 if choice == "goal" else 2.5
elif game == "basketball":
val = random.randint(1, 10)
send_animation(chat_id, "🏀"); time.sleep(2)
res_detail = f"Бросок выполнен.\n"
if choice == "2pt" and val <= 6: win = True
elif choice == "3pt" and val > 6: win = True
multiplier = 1.5 if choice == "2pt" else 3.0
elif game == "darts":
val = random.randint(1, 6)
send_animation(chat_id, "🎯"); time.sleep(2)
res_detail = f"Дротик брошен.\n"
if choice == "bull" and val == 1: win = True
elif choice == "miss" and val > 1: win = True
multiplier = 3.0 if choice == "bull" else 1.5
elif game == "bowling":
val = random.choices([0, 1, 4, 5, 6, 7, 8, 9, 10], weights=[15, 5, 10, 15, 15, 10, 10, 5, 5, 7])[0]
send_animation(chat_id, "🎳"); time.sleep(2)
res_detail = f"Сбито кеглей: {val}\n"
if choice == "strike" and val == 10: win = True
elif choice == "high" and 7 <= val <= 9: win = True
elif choice == "low" and 1 <= val <= 3: win = True
elif choice == "miss" and val == 0: win = True
if choice == "strike": multiplier = 5.0
elif choice == "high": multiplier = 2.5
elif choice == "low": multiplier = 1.5
elif choice == "miss": multiplier = 4.0
# РАСЧЕТ И ОТПРАВКА ОРИГИНАЛЬНЫХ РЕЗУЛЬТАТОВ ИГРЫ
if win:
win_amount = int(bet * multiplier)
new_bal = user["balance"] + win_amount - bet
update_user(user_id, balance=new_bal, wins=user["wins"] + 1)
res_text = f"🎉 Победа!\n{res_detail}Вы получили: +{win_amount}$ 💵\nЧистая прибыль: +{win_amount - bet}$\n\n"
else:
new_bal = user["balance"] - bet
update_user(user_id, balance=new_bal, losses=user["losses"] + 1)
res_text = f"😢 Проигрыш.\n{res_detail}Потеряно: -{bet}$ 💵\n\n"
text, kb = get_main_menu(get_user(user_id))
send_message(chat_id, res_text + text, kb)
# ОБРАБОТКА ТЕКСТОВЫХ СООБЩЕНИЙ В ЧАТЕ
elif "message" in update and "text" in update["message"]:
msg = update["message"]
chat_id = msg["chat"]["id"]
text_str = msg["text"]
user_id = msg["from"]["id"]
first_name = msg["from"].get("first_name", "Игрок")
user = get_user(user_id)
update_user(user_id, name=first_name)
# Проверка стейтов пользователя (Ввод данных)
if user_id in user_states:
state_info = user_states[user_id]
# 1. Если бот ждал Telegram ID для крипто-выплаты
if isinstance(state_info, tuple) and state_info[0] == "wait_payout_id":
_, amount, msg_id = state_info
if text_str.isdigit():
target_id = int(text_str)
del user_states[user_id]
send_message(chat_id, "⏳ Выполняется транзакция в блокчейне...")
send_crypto_payout(chat_id, msg_id, amount, target_id)
else:
send_message(chat_id, "❌ ID должен состоять только из цифр. Повторите ввод:")
continue
# 2. Если бот ждал ввод ручной суммы ставки
elif isinstance(state_info, tuple):
game, msg_id = state_info
if text_str.isdigit():
bet = int(text_str)
if bet < 10:
edit_message(chat_id, msg_id, "❌ Мин. ставка 10$. Введите другое число:", {"inline_keyboard": [[{"text": "Отмена", "callback_data": f"game_{game}"}]]})
elif bet > user["balance"]:
edit_message(chat_id, msg_id, f"❌ Недостаточно средств (Баланс: {user['balance']}$). Введите другое число:", {"inline_keyboard": [[{"text": "Отмена", "callback_data": f"game_{game}"}]]})
else:
del user_states[user_id]
text, kb = get_choice_menu(user, game, bet)
edit_message(chat_id, msg_id, text, kb)
else:
edit_message(chat_id, msg_id, "❌ Введите число цифрами:", {"inline_keyboard": [[{"text": "Отмена", "callback_data": f"game_{game}"}]]})
continue
cmd = text_str.lower().split()[0] if text_str else ""
if cmd == "/start" or cmd == "/help":
text, kb = get_main_menu(user)
send_message(chat_id, text, kb)
except Exception as e:
print("Ошибка:", e)
time.sleep(2)
