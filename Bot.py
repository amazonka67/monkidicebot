import urllib.request
import json
import time
import random
import os

TOKEN = os.environ.get("BOT_TOKEN", "9193782655:AAFP7mMmjbL4ITM--2LBuStvO0YcTTc9gOk")
DATA_FILE = "users.json"

# Функция отправки обычного текста с кнопками
def send_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print("Ошибка отправки:", e)

# Функция отправки АНИМАЦИИ (кубика)
def send_dice_animation(chat_id, emoji="🎲"):
    url = f"https://api.telegram.org/bot{TOKEN}/sendDice"
    payload = {"chat_id": chat_id, "emoji": emoji}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print("Ошибка анимации:", e)

def answer_callback(callback_id):
    url = f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery"
    data = json.dumps({"callback_query_id": callback_id}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print("Ошибка callback:", e)

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user(uid):
    data = load_data()
    uid = str(uid)
    if uid not in data:
        data[uid] = {"balance": 1000, "wins": 0, "losses": 0, "last_bonus": 0, "name": "Игрок"}
        save_data(data)
    return data[uid]

def update_user(uid, **kwargs):
    data = load_data()
    uid = str(uid)
    if uid not in data:
        data[uid] = {"balance": 1000, "wins": 0, "losses": 0, "last_bonus": 0, "name": "Игрок"}
    data[uid].update(kwargs)
    save_data(data)

# --- Клавиатуры ---
def get_main_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🎲 Играть в Дайс", "callback_data": "play_dice"}],
            [{"text": "💰 Баланс", "callback_data": "balance"}, {"text": "🎁 Бонус", "callback_data": "bonus"}]
        ]
    }

def get_bet_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "10", "callback_data": "bet_10"}, {"text": "50", "callback_data": "bet_50"}],
            [{"text": "100", "callback_data": "bet_100"}, {"text": "500", "callback_data": "bet_500"}],
            [{"text": "⬅️ Назад", "callback_data": "back_main"}]
        ]
    }

def get_choice_keyboard(bet):
    return {
        "inline_keyboard": [
            [{"text": "⬆️ Больше 3 (x2)", "callback_data": f"choice_high_{bet}"}],
            [{"text": "⬇️ Меньше 4 (x2)", "callback_data": f"choice_low_{bet}"}],
            [{"text": "⬅️ Назад", "callback_data": "play_dice"}]
        ]
    }

print("Бот запущен...")
offset = 0

while True:
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?timeout=30&offset={offset}"
        response = urllib.request.urlopen(url, timeout=40)
        updates = json.loads(response.read().decode("utf-8"))

        if not updates.get("ok"):
            time.sleep(2)
            continue

        for update in updates["result"]:
            offset = update["update_id"] + 1

            if "callback_query" in update:
                cb = update["callback_query"]
                cb_id = cb["id"]
                chat_id = cb["message"]["chat"]["id"]
                user_id = cb["from"]["id"]
                data = cb["data"]
                
                answer_callback(cb_id)
                user = get_user(user_id)

                if data == "back_main":
                    send_message(chat_id, "🎰 Главное меню:", get_main_keyboard())
                
                elif data == "balance":
                    send_message(chat_id, f"💰 Баланс: {user['balance']}\nПобед: {user['wins']}\nПоражений: {user['losses']}")
                
                elif data == "bonus":
                    now = int(time.time())
                    if now - user["last_bonus"] < 86400:
                        left = 86400 - (now - user["last_bonus"])
                        send_message(chat_id, f"⏳ Бонус уже получен. Ждать: {left//3600}ч {(left%3600)//60}м")
                    else:
                        new_bal = user["balance"] + 500
                        update_user(user_id, balance=new_bal, last_bonus=now)
                        send_message(chat_id, f"🎁 Бонус +500!\nБаланс: {new_bal}")

                elif data == "play_dice":
                    send_message(chat_id, "Выберите ставку:", get_bet_keyboard())

                elif data.startswith("bet_"):
                    bet = int(data.split("_")[1])
                    if bet > user["balance"]:
                        send_message(chat_id, f"❌ Недостаточно монет! Баланс: {user['balance']}")
                    else:
                        send_message(chat_id, f"Ставка: {bet}. Выберите, что выпадет:", get_choice_keyboard(bet))

                elif data.startswith("choice_"):
                    parts = data.split("_")
                    choice = parts[1]
                    bet = int(parts[2])
                    
                    # 1. Отправляем анимацию кубика
                    send_dice_animation(chat_id)
                    time.sleep(2.5) # Ждем 2.5 секунды, пока крутится анимация
                    
                    # 2. Генерируем результат
                    val = random.randint(1, 6)
                    win = False
                    if choice == "high" and val > 3:
                        win = True
                    elif choice == "low" and val < 4:
                        win = True
                    
                    # 3. Отправляем итог
                    if win:
                        profit = bet * 2
                        new_bal = user["balance"] + profit - bet
                        update_user(user_id, balance=new_bal, wins=user["wins"] + 1)
                        text = f"🎉 <b>Победа!</b>\nВыигрыш: +{profit}\nБаланс: {new_bal}"
                    else:
                        new_bal = user["balance"] - bet
                        update_user(user_id, balance=new_bal, losses=user["losses"] + 1)
                        text = f"😢 <b>Проигрыш.</b>\nПотеряно: -{bet}\nБаланс: {new_bal}"
                    
                    send_message(chat_id, text, get_main_keyboard())

            elif "message" in update and "text" in update["message"]:
                msg = update["message"]
                chat_id = msg["chat"]["id"]
                text = msg["text"].split()
                user_id = msg["from"]["id"]
                first_name = msg["from"].get("first_name", "Игрок")

                get_user(user_id)
                update_user(user_id, name=first_name)

                cmd = text[0].lower()

                if cmd == "/start" or cmd == "/help":
                    send_message(chat_id, f"Привет, {first_name}!\n\nВыбери игру:", get_main_keyboard())

    except Exception as e:
        print("Ошибка:", e)
        time.sleep(2)
