import urllib.request
import json
import time
import random
import os

TOKEN = os.environ.get("BOT_TOKEN", "9193782655:AAFP7mMmjbL4ITM--2LBuStvO0YcTTc9gOk")
WEBAPP_URL = "https://amazonka67.github.io/monkidicebot/?v=2"

def api_request(method, payload):
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try: urllib.request.urlopen(req, timeout=10)
    except Exception as e: print(f"Ошибка API {method}:", e)

def send_message(chat_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup: payload["reply_markup"] = reply_markup
    api_request("sendMessage", payload)

def edit_message(chat_id, message_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "HTML"}
    if reply_markup: payload["reply_markup"] = reply_markup
    api_request("editMessageText", payload)

def send_animation(chat_id, emoji):
    api_request("sendDice", {"chat_id": chat_id, "emoji": emoji})

def answer_callback(callback_id):
    api_request("answerCallbackQuery", {"callback_query_id": callback_id})

def load_data():
    if os.path.exists("/app/users.json"):
        try:
            with open("/app/users.json", "r", encoding="utf-8") as f: return json.load(f)
        except: return {}
    return {}

def save_data(data):
    with open("/app/users.json", "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=2)

def get_user(uid):
    data = load_data()
    uid = str(uid)
    if uid not in data:
        data[uid] = {"balance": 10, "wins": 0, "losses": 0, "name": "Игрок"}
        save_data(data)
    return data[uid]

def update_user(uid, **kwargs):
    data = load_data()
    uid = str(uid)
    if uid not in data: data[uid] = {"balance": 10, "wins": 0, "losses": 0, "name": "Игрок"}
    data[uid].update(kwargs)
    save_data(data)

def get_main_menu(user):
    text = f"👤 <b>{user['name']}</b>\n💰 Баланс: <b>{user['balance']}$</b> 💵\n\n🎰 <b>Выберите игру:</b>"
    kb = {"inline_keyboard": [
        [{"text": "🎮 Открыть Mini App (Колесо)", "web_app": {"url": WEBAPP_URL}}],
        [{"text": "🎲 Текстовый Дайс", "callback_data": "game_dice"}, {"text": "🎯 Дартс", "callback_data": "game_darts"}],
        [{"text": "🎁 Бонус", "callback_data": "bonus"}]
    ]}
    return text, kb

def get_bet_menu(user, game):
    text = f"👤 <b>{user['name']}</b>\n💰 Баланс: <b>{user['balance']}$</b> 💵\n\n👇 <b>Выберите ставку:</b>"
    kb = {"inline_keyboard": [[{"text": "10$", "callback_data": f"bet_{game}_10"}, {"text": "50$", "callback_data": f"bet_{game}_50"}], [{"text": "⬅️ Назад", "callback_data": "main_menu"}]]}
    return text, kb

def get_outcome_menu(user, game, bet):
    text = f"👤 <b>{user['name']}</b>\n💰 Баланс: <b>{user['balance']}$</b> 💵\n💵 Ставка: <b>{bet}$</b>\n\n🎯 <b>На что ставим?</b>"
    if game == "dice": kb = [[{"text": "Больше 3 x2", "callback_data": f"res_{game}_{bet}_high"}, {"text": "Меньше 4 x2", "callback_data": f"res_{game}_{bet}_low"}]]
    else: kb = [[{"text": "В центр x3", "callback_data": f"res_{game}_{bet}_bull"}, {"text": "Мимо x2", "callback_data": f"res_{game}_{bet}_miss"}]]
    kb.append([{"text": "⬅️ Назад", "callback_data": f"game_{game}"}])
    return text, {"inline_keyboard": kb}

print("Бот запущен...")
offset = 0

while True:
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?timeout=30&offset={offset}"
        response = urllib.request.urlopen(url, timeout=40)
        updates = json.loads(response.read().decode("utf-8"))
        if not updates.get("ok"): time.sleep(2); continue

        for update in updates["result"]:
            offset = update["update_id"] + 1

            if "callback_query" in update:
                cb = update["callback_query"]
                cb_id = cb["id"]; chat_id = cb["message"]["chat"]["id"]; msg_id = cb["message"]["message_id"]; user_id = cb["from"]["id"]; data = cb["data"]
                answer_callback(cb_id); user = get_user(user_id)

                if data == "main_menu": text, kb = get_main_menu(user); edit_message(chat_id, msg_id, text, kb)
                elif data == "bonus":
                    new_bal = user["balance"] + 10; update_user(user_id, balance=new_bal)
                    edit_message(chat_id, msg_id, f"🎁 Вы получили 10$!\nНовый баланс: {new_bal}$", {"inline_keyboard": [[{"text": "⬅️ Назад", "callback_data": "main_menu"}]]})
                elif data.startswith("game_"):
                    game = data.split("_")[1]; text, kb = get_bet_menu(user, game); edit_message(chat_id, msg_id, text, kb)
                elif data.startswith("bet_"):
                    parts = data.split("_"); game = parts[1]; bet = int(parts[2])
                    if bet > user["balance"]: edit_message(chat_id, msg_id, "❌ Недостаточно средств!")
                    else: text, kb = get_outcome_menu(user, game, bet); edit_message(chat_id, msg_id, text, kb)
                elif data.startswith("res_"):
                    parts = data.split("_"); game = parts[1]; bet = int(parts[2]); choice = parts[3]
                    edit_message(chat_id, msg_id, "🎰 Крутим...", None)
                    
                    if game == "dice":
                        val = random.randint(1, 6); send_animation(chat_id, "🎲"); time.sleep(2)
                        win = (choice == "high" and val > 3) or (choice == "low" and val < 4)
                        multiplier = 2
                    else:
                        val = random.choice(["bull", "miss"]); send_animation(chat_id, "🎯"); time.sleep(2)
                        win = (choice == val)
                        multiplier = 3 if choice == "bull" else 2

                    if win:
                        win_amt = bet * multiplier; new_bal = user["balance"] + win_amt - bet
                        update_user(user_id, balance=new_bal, wins=user["wins"] + 1)
                        res = f"🎉 Победа! Выигрыш: +{win_amt}$"
                    else:
                        new_bal = user["balance"] - bet
                        update_user(user_id, balance=new_bal, losses=user["losses"] + 1)
                        res = f"😢 Проигрыш. Потеряно: -{bet}$"
                    
                    text, kb = get_main_menu(get_user(user_id)); send_message(chat_id, f"{res}\n\n{text}", kb)

            elif "message" in update and "text" in update["message"]:
                msg = update["message"]; chat_id = msg["chat"]["id"]; text_str = msg["text"]; user_id = msg["from"]["id"]; first_name = msg["from"].get("first_name", "Игрок")
                user = get_user(user_id); update_user(user_id, name=first_name)
                if text_str == "/start": text, kb = get_main_menu(user); send_message(chat_id, text, kb)

    except Exception as e: print("Ошибка:", e); time.sleep(2)
