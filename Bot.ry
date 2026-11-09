import urllib.request
import json
import time
import random
import os

TOKEN = os.environ.get("BOT_TOKEN", "9193782655:AAFP7mMmjbL4ITM--2LBuStvO0YcTTc9gOk")
DATA_FILE = "users.json"

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = json.dumps({"chat_id": chat_id, "text": text}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print("Ошибка отправки:", e)

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

            if "message" not in update or "text" not in update["message"]:
                continue

            msg = update["message"]
            chat_id = msg["chat"]["id"]
            text = msg["text"].split()
            user_id = msg["from"]["id"]
            first_name = msg["from"].get("first_name", "Игрок")

            get_user(user_id)
            update_user(user_id, name=first_name)

            cmd = text[0].lower()

            if cmd == "/start" or cmd == "/help":
                send_message(chat_id, f"Привет, {first_name}!\n\nКоманды:\n/dice - кубик\n/bet 100 - ставка\n/balance - баланс\n/bonus - бонус\n/top - топ")

            elif cmd == "/dice":
                val = random.randint(1, 6)
                send_message(chat_id, f"🎲 Выпало: {val}")

            elif cmd == "/bet":
                if len(text) < 2 or not text[1].isdigit():
                    send_message(chat_id, "Использование: /bet 100")
                    continue
                bet = int(text[1])
                user = get_user(user_id)
                if bet < 10:
                    send_message(chat_id, "Минимальная ставка - 10.")
                    continue
                if bet > user["balance"]:
                    send_message(chat_id, f"Недостаточно монет! Баланс: {user['balance']}")
                    continue
                
                val = random.randint(1, 6)
                if val >= 4:
                    new_bal = user["balance"] + bet
                    update_user(user_id, balance=new_bal, wins=user["wins"] + 1)
                    send_message(chat_id, f"🎉 Победа! Выпало: {val}\nВыигрыш: +{bet}\nБаланс: {new_bal}")
                else:
                    new_bal = user["balance"] - bet
                    update_user(user_id, balance=new_bal, losses=user["losses"] + 1)
                    send_message(chat_id, f"😢 Проигрыш. Выпало: {val}\nПотеряно: -{bet}\nБаланс: {new_bal}")

            elif cmd == "/balance":
                user = get_user(user_id)
                send_message(chat_id, f"💰 Баланс: {user['balance']}\nПобед: {user['wins']}\nПоражений: {user['losses']}")

            elif cmd == "/bonus":
                user = get_user(user_id)
                now = int(time.time())
                if now - user["last_bonus"] < 86400:
                    left = 86400 - (now - user["last_bonus"])
                    send_message(chat_id, f"Бонус уже получен. Ждать: {left//3600}ч {(left%3600)//60}м")
                    continue
                new_bal = user["balance"] + 500
                update_user(user_id, balance=new_bal, last_bonus=now)
                send_message(chat_id, f"🎁 Бонус +500!\nБаланс: {new_bal}")

            elif cmd == "/top":
                data = load_data()
                if not data:
                    send_message(chat_id, "Пока нет игроков.")
                    continue
                sorted_users = sorted(data.items(), key=lambda x: x[1]["balance"], reverse=True)[:10]
                lines = ["🏆 Топ игроков:"]
                for i, (uid, info) in enumerate(sorted_users):
                    name = info.get("name") or f"Игрок {uid}"
                    lines.append(f"{i+1}. {name} — {info['balance']} (✅{info['wins']} / ❌{info['losses']})")
                send_message(chat_id, "\n".join(lines))

    except Exception as e:
        print("Ошибка:", e)
        time.sleep(2)
