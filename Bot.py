import urllib.request
import json
import time
import random
import os

TOKEN = os.environ.get("BOT_TOKEN", "9193782655:AAFP7mMmjbL4ITM--2LBuStvO0YcTTc9gOk")
DATA_FILE = "users.json"

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

def send_animation(chat_id, emoji):
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
            [{"text": "🎲 Дайс", "callback_data": "play_dice"}, {"text": "🎯 Дартс", "callback_data": "play_darts"}],
            [{"text": "⚽ Футбол", "callback_data": "play_football"}, {"text": "🏀 Баскетбол", "callback_data": "play_basketball"}],
            [{"text": "🎰 Слоты", "callback_data": "play_slots"}, {"text": "🎳 Боулинг", "callback_data": "play_bowling"}],
            [{"text": "💰 Баланс", "callback_data": "balance"}, {"text": "🎁 Бонус", "callback_data": "bonus"}]
        ]
    }

def get_bet_keyboard(game):
    return {
        "inline_keyboard": [
            [{"text": "10", "callback_data": f"bet_{game}_10"}, {"text": "50", "callback_data": f"bet_{game}_50"}],
            [{"text": "100", "callback_data": f"bet_{game}_100"}, {"text": "500", "callback_data": f"bet_{game}_500"}],
            [{"text": "✍️ Своя ставка", "callback_data": f"custom_{game}"}],
            [{"text": "⬅️ Назад", "callback_data": "back_main"}]
        ]
    }

def get_choice_keyboard(game, bet):
    kb = []
    if game == "dice":
        kb = [
            [{"text": "⬆️ Больше 3 (x2)", "callback_data": f"res_{game}_{bet}_high"}],
            [{"text": "⬇️ Меньше 4 (x2)", "callback_data": f"res_{game}_{bet}_low"}]
        ]
    elif game == "football":
        kb = [
            [{"text": "⚽ Гол (x1.5)", "callback_data": f"res_{game}_{bet}_goal"}],
            [{"text": "❌ Мимо (x2.5)", "callback_data": f"res_{game}_{bet}_miss"}]
        ]
    elif game == "basketball":
        kb = [
            [{"text": "🏀 Гол (x2.5)", "callback_data": f"res_{game}_{bet}_goal"}],
            [{"text": "❌ Промах (x1.5)", "callback_data": f"res_{game}_{bet}_miss"}]
        ]
    elif game == "darts":
        kb = [
            [{"text": "🎯 В яблочко (x3)", "callback_data": f"res_{game}_{bet}_bull"}],
            [{"text": "❌ Мимо (x1.5)", "callback_data": f"res_{game}_{bet}_miss"}]
        ]
    elif game == "slots":
        kb = [
            [{"text": "💎 3 в ряд (x5)", "callback_data": f"res_{game}_{bet}_win"}],
            [{"text": "❌ Не зашло (x1.2)", "callback_data": f"res_{game}_{bet}_lose"}]
        ]
    elif game == "bowling":
        kb = [
            [{"text": "🎳 Страйк 10/10 (x5)", "callback_data": f"res_{game}_{bet}_strike"}],
            [{"text": "🎯 Сбито 7-9 (x2.5)", "callback_data": f"res_{game}_{bet}_high"}],
            [{"text": "⚪ Сбито 1-3 (x1.5)", "callback_data": f"res_{game}_{bet}_low"}],
            [{"text": "❌ Промах 0 (x4)", "callback_data": f"res_{game}_{bet}_miss"}]
        ]
    
    kb.append([{"text": "⬅️ Назад", "callback_data": f"play_{game}"}])
    return {"inline_keyboard": kb}

print("Бот запущен...")
offset = 0
user_states = {} # Храним, кто сейчас вводит свою ставку

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

                # Сбрасываем состояние ввода ставки, если нажали на кнопку
                if user_id in user_states:
                    del user_states[user_id]

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

                elif data.startswith("play_"):
                    game = data.split("_")[1]
                    send_message(chat_id, f"Выберите ставку:", get_bet_keyboard(game))

                elif data.startswith("custom_"):
                    game = data.split("_")[1]
                    user_states[user_id] = game
                    send_message(chat_id, f"✍️ Напишите сумму вашей ставки в чат (от 10 до {user['balance']}):")

                elif data.startswith("bet_"):
                    parts = data.split("_")
                    game = parts[1]
                    bet = int(parts[2])
                    
                    if bet > user["balance"]:
                        send_message(chat_id, f"❌ Недостаточно монет! Баланс: {user['balance']}")
                    else:
                        send_message(chat_id, f"Ставка: {bet}. На что ставим?", get_choice_keyboard(game, bet))

                elif data.startswith("res_"):
                    parts = data.split("_")
                    game = parts[1]
                    bet = int(parts[2])
                    choice = parts[3]
                    
                    emoji = {"dice": "🎲", "darts": "🎯", "football": "⚽", "basketball": "🏀", "slots": "🎰", "bowling": "🎳"}[game]
                    send_animation(chat_id, emoji)
                    time.sleep(2.5)
                    
                    win = False
                    multiplier = 1.0
                    val = 0

                    if game == "dice":
                        val = random.randint(1, 6)
                        if choice == "high" and val > 3: win = True
                        elif choice == "low" and val < 4: win = True
                        multiplier = 2.0
                        
                    elif game == "football":
                        val = random.randint(1, 5)
                        if choice == "goal" and val >= 3: win = True
                        elif choice == "miss" and val < 3: win = True
                        multiplier = 1.5 if choice == "goal" else 2.5

                    elif game == "basketball":
                        val = random.randint(1, 5)
                        if choice == "goal" and val >= 3: win = True # Голы выпадают 3, 4, 5
                        elif choice == "miss" and val < 3: win = True
                        multiplier = 2.5 if choice == "goal" else 1.5
                        
                    elif game == "darts":
                        val = random.randint(1, 6)
                        if choice == "bull" and val == 1: win = True
                        elif choice == "miss" and val > 1: win = True
                        multiplier = 3.0 if choice == "bull" else 1.5

                    elif game == "slots":
                        val = random.randint(1, 64)
                        if choice == "win" and val == 1: win = True
                        elif choice == "lose" and val > 1: win = True
                        multiplier = 5.0 if choice == "win" else 1.2
                    
                    elif game == "bowling":
                        val = random.choices([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10], weights=[15, 5, 10, 15, 15, 10, 10, 5, 5, 3, 7])[0]
                        if choice == "strike" and val == 10: win = True
                        elif choice == "high" and 7 <= val <= 9: win = True
                        elif choice == "low" and 1 <= val <= 3: win = True
                        elif choice == "miss" and val == 0: win = True
                        
                        if choice == "strike": multiplier = 5.0
                        elif choice == "high": multiplier = 2.5
                        elif choice == "low": multiplier = 1.5
                        elif choice == "miss": multiplier = 4.0
                    
                    # ИСПРАВЛЕННАЯ МАТЕМАТИКА
                    if win:
                        win_amount = int(bet * multiplier)
                        new_bal = user["balance"] + win_amount - bet
                        update_user(user_id, balance=new_bal, wins=user["wins"] + 1)
                        text = f"🎉 <b>Победа!</b>\nСтавка сгорела, но вы получили: <b>+{win_amount}</b> 🪙\nИтого прибыль: <b>+{win_amount - bet}</b>\nБаланс: <b>{new_bal}</b>"
                    else:
                        new_bal = user["balance"] - bet
                        update_user(user_id, balance=new_bal, losses=user["losses"] + 1)
                        text = f"😢 <b>Проигрыш.</b>\nПотеряно: <b>-{bet}</b> 🪙\nБаланс: <b>{new_bal}</b>"
                    
                    send_message(chat_id, text, get_main_keyboard())

            elif "message" in update and "text" in update["message"]:
                msg = update["message"]
                chat_id = msg["chat"]["id"]
                text_str = msg["text"]
                user_id = msg["from"]["id"]
                first_name = msg["from"].get("first_name", "Игрок")

                user = get_user(user_id)
                update_user(user_id, name=first_name)

                # Обработка ввода собственной ставки
                if user_id in user_states:
                    game = user_states[user_id]
                    if text_str.isdigit():
                        bet = int(text_str)
                        if bet < 10:
                            send_message(chat_id, "❌ Минимальная ставка — 10 монет. Введите другую сумму:")
                        elif bet > user["balance"]:
                            send_message(chat_id, f"❌ Недостаточно монет! Ваш баланс: {user['balance']}. Введите другую сумму:")
                        else:
                            del user_states[user_id] # Сбрасываем состояние
                            send_message(chat_id, f"Ставка: {bet}. На что ставим?", get_choice_keyboard(game, bet))
                    else:
                        send_message(chat_id, "❌ Пожалуйста, введите целое число (цифрами).")
                    continue # Пропускаем остальные команды

                cmd = text_str.lower().split()[0] if text_str else ""

                if cmd == "/start" or cmd == "/help":
                    send_message(chat_id, f"Привет, {first_name}!\n\nВыбери игру:", get_main_keyboard())

    except Exception as e:
        print("Ошибка:", e)
        time.sleep(2)
