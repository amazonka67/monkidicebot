import urllib.request
import json
import time
import random
import os

TOKEN = os.environ.get("BOT_TOKEN", "9193782655:AAFP7mMmjbL4ITM--2LBuStvO0YcTTc9gOk")
DATA_FILE = "users.json"
BANNER_URL = "https://i.ibb.co/6PZ7Y6w/ducky-style-banner.jpg" 

def api_request(method, payload):
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"Ошибка API {method}:", e)

def send_photo(chat_id, photo_url, caption, reply_markup=None):
    payload = {"chat_id": chat_id, "photo": photo_url, "caption": caption, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    api_request("sendPhoto", payload)

def edit_message_media(chat_id, message_id, photo_url, caption, reply_markup=None):
    media = {"type": "photo", "media": photo_url, "caption": caption, "parse_mode": "HTML"}
    payload = {"chat_id": chat_id, "message_id": message_id, "media": json.dumps(media)}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    api_request("editMessageMedia", payload)

def send_animation(chat_id, emoji):
    api_request("sendDice", {"chat_id": chat_id, "emoji": emoji})

def answer_callback(callback_id):
    api_request("answerCallbackQuery", {"callback_query_id": callback_id})

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

# --- МЕНЮ ---

def get_main_menu(user):
    caption = (
        f"👤 <b>{user['name']}</b>\n"
        f"💰 Баланс: <b>{user['balance']}$</b> 💵\n"
        f"📈 Статистика: ✅ {user['wins']} | ❌ {user['losses']}\n\n"
        f"🎰 <b>Выберите игру (Шанс / Множитель):</b>"
    )
    kb = {
        "inline_keyboard": [
            [{"text": "🎲 Дайс (до x6)", "callback_data": "game_dice"}, {"text": "🎯 Дартс (до x5)", "callback_data": "game_darts"}],
            [{"text": "⚽ Футбол (до x3)", "callback_data": "game_football"}, {"text": "🏀 Баскет (до x3)", "callback_data": "game_basketball"}],
            [{"text": "🎳 Боулинг (до x5)", "callback_data": "game_bowling"}, {"text": "🎰 Слоты (до x5)", "callback_data": "game_slots"}],
            [{"text": "🪙 Монетка (до x2)", "callback_data": "game_coin"}, {"text": "🎡 Рулетка (до x5)", "callback_data": "game_roulette"}],
            [{"text": "💰 Баланс", "callback_data": "profile"}, {"text": "🎁 Бонус", "callback_data": "bonus"}]
        ]
    }
    return caption, kb

def get_bet_menu(user, game):
    game_names = {
        "dice": "🎲 Дайс", "darts": "🎯 Дартс", "football": "⚽ Футбол", 
        "basketball": "🏀 Баскет", "bowling": "🎳 Боулинг", "slots": "🎰 Слоты",
        "coin": "🪙 Монетка", "roulette": "🎡 Рулетка"
    }
    caption = (
        f"👤 <b>{user['name']}</b>\n"
        f"💰 Баланс: <b>{user['balance']}$</b> 💵\n"
        f"🎮 Игра: <b>{game_names.get(game, game)}</b>\n\n"
        f"👇 <b>Выберите ставку:</b>"
    )
    kb = {
        "inline_keyboard": [
            [{"text": "10$", "callback_data": f"bet_{game}_10"}, {"text": "50$", "callback_data": f"bet_{game}_50"}, {"text": "100$", "callback_data": f"bet_{game}_100"}],
            [{"text": "500$", "callback_data": f"bet_{game}_500"}, {"text": "✍️ Своя", "callback_data": f"custom_{game}"}, {"text": "Макс", "callback_data": f"bet_{game}_{user['balance']}"}],
            [{"text": "⬅️ Назад", "callback_data": "menu"}]
        ]
    }
    return caption, kb

def get_choice_menu(user, game, bet):
    caption = (
        f"👤 <b>{user['name']}</b>\n"
        f"💰 Баланс: <b>{user['balance']}$</b> 💵\n"
        f"💵 Ставка: <b>{bet}$</b>\n\n"
        f"🎯 <b>Выберите режим:</b>"
    )
    kb = []
    
    if game == "dice":
        kb = [
            [{"text": "⬆️ Больше 3 (шанс 50%, x2)", "callback_data": f"res_{game}_{bet}_high"}],
            [{"text": "⬇️ Меньше 4 (шанс 50%, x2)", "callback_data": f"res_{game}_{bet}_low"}],
            [{"text": "🎯 Точное 6 (шанс 16%, x6)", "callback_data": f"res_{game}_{bet}_exact"}],
            [{"text": "👥 Дуэль (шанс 45%, x2.2)", "callback_data": f"res_{game}_{bet}_duel"}]
        ]
    elif game == "coin":
        kb = [
            [{"text": "🦅 Орел (шанс 50%, x2)", "callback_data": f"res_{game}_{bet}_heads"}],
            [{"text": "🪙 Решка (шанс 50%, x2)", "callback_data": f"res_{game}_{bet}_tails"}]
        ]
    elif game == "football":
        kb = [
            [{"text": "⚽ Гол (шанс 60%, x1.5)", "callback_data": f"res_{game}_{bet}_goal"}],
            [{"text": "❌ Мимо (шанс 40%, x2.5)", "callback_data": f"res_{game}_{bet}_miss"}],
            [{"text": "🔥 Обе забьют (шанс 30%, x3)", "callback_data": f"res_{game}_{bet}_both"}]
        ]
    elif game == "basketball":
        kb = [
            [{"text": "🏀 2 очка (шанс 60%, x1.5)", "callback_data": f"res_{game}_{bet}_2pt"}],
            [{"text": "🏀 3 очка (шанс 30%, x3)", "callback_data": f"res_{game}_{bet}_3pt"}]
        ]
    elif game == "darts":
        kb = [
            [{"text": "🎯 Яблочко (шанс 20%, x5)", "callback_data": f"res_{game}_{bet}_bull"}],
            [{"text": "🔴 Красное (шанс 50%, x2)", "callback_data": f"res_{game}_{bet}_red"}],
            [{"text": "❌ Мимо (шанс 30%, x1.5)", "callback_data": f"res_{game}_{bet}_miss"}]
        ]
    elif game == "slots":
        kb = [
            [{"text": "💎 3 в ряд (шанс 10%, x5)", "callback_data": f"res_{game}_{bet}_win"}],
            [{"text": "🍒 2 в ряд (шанс 40%, x1.5)", "callback_data": f"res_{game}_{bet}_2row"}]
        ]
    elif game == "bowling":
        kb = [
            [{"text": "🎳 Страйк (шанс 10%, x5)", "callback_data": f"res_{game}_{bet}_strike"}],
            [{"text": "🎯 7-9 (шанс 20%, x2.5)", "callback_data": f"res_{game}_{bet}_high"}],
            [{"text": "⚪ 1-3 (шанс 40%, x1.5)", "callback_data": f"res_{game}_{bet}_low"}],
            [{"text": "❌ Промах (шанс 15%, x4)", "callback_data": f"res_{game}_{bet}_miss"}]
        ]
    elif game == "roulette":
        kb = [
            [{"text": "🔴 Красное (шанс 40%, x2)", "callback_data": f"res_{game}_{bet}_red"}],
            [{"text": "⚫ Черное (шанс 40%, x2)", "callback_data": f"res_{game}_{bet}_black"}],
            [{"text": "🟢 Зеро (шанс 20%, x5)", "callback_data": f"res_{game}_{bet}_zero"}]
        ]
    
    kb.append([{"text": "⬅️ Назад", "callback_data": f"game_{game}"}])
    return caption, {"inline_keyboard": kb}

print("Бот запущен...")
offset = 0
user_states = {}

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
                msg_id = cb["message"]["message_id"]
                user_id = cb["from"]["id"]
                data = cb["data"]
                
                answer_callback(cb_id)
                user = get_user(user_id)

                if user_id in user_states:
                    del user_states[user_id]

                if data == "menu":
                    caption, kb = get_main_menu(user)
                    edit_message_media(chat_id, msg_id, BANNER_URL, caption, kb)
                
                elif data == "profile" or data == "balance":
                    caption = f"👤 <b>{user['name']}</b>\n💰 Баланс: <b>{user['balance']}$</b> 💵\n✅ Побед: {user['wins']}\n❌ Поражений: {user['losses']}"
                    edit_message_media(chat_id, msg_id, BANNER_URL, caption, {"inline_keyboard": [[{"text": "⬅️ Назад", "callback_data": "menu"}]]})
                
                elif data == "bonus":
                    now = int(time.time())
                    if now - user["last_bonus"] < 86400:
                        left = 86400 - (now - user["last_bonus"])
                        caption = f"⏳ Бонус уже получен.\nЖдать: {left//3600}ч {(left%3600)//60}м"
                        edit_message_media(chat_id, msg_id, BANNER_URL, caption, {"inline_keyboard": [[{"text": "⬅️ Назад", "callback_data": "menu"}]]})
                    else:
                        new_bal = user["balance"] + 500
                        update_user(user_id, balance=new_bal, last_bonus=now)
                        caption = f"🎁 Бонус +500$!\nВаш баланс: {new_bal}$ 💵"
                        edit_message_media(chat_id, msg_id, BANNER_URL, caption, {"inline_keyboard": [[{"text": "⬅️ Назад", "callback_data": "menu"}]]})

                elif data.startswith("game_"):
                    game = data.split("_")[1]
                    caption, kb = get_bet_menu(user, game)
                    edit_message_media(chat_id, msg_id, BANNER_URL, caption, kb)

                elif data.startswith("custom_"):
                    game = data.split("_")[1]
                    user_states[user_id] = (game, msg_id)
                    caption = f"✍️ Напишите сумму вашей ставки в чат (от 10 до {user['balance']}):"
                    edit_message_media(chat_id, msg_id, BANNER_URL, caption, {"inline_keyboard": [[{"text": "Отмена", "callback_data": f"game_{game}"}]]})

                elif data.startswith("bet_"):
                    parts = data.split("_")
                    game = parts[1]
                    bet = int(parts[2])
                    
                    if bet > user["balance"] or bet < 10:
                        caption = f"❌ Неверная ставка (мин. 10) или недостаточно средств!"
                        edit_message_media(chat_id, msg_id, BANNER_URL, caption, {"inline_keyboard": [[{"text": "⬅️ Назад", "callback_data": f"game_{game}"}]]})
                    else:
                        caption, kb = get_choice_menu(user, game, bet)
                        edit_message_media(chat_id, msg_id, BANNER_URL, caption, kb)

                elif data.startswith("res_"):
                    parts = data.split("_")
                    game = parts[1]
                    bet = int(parts[2])
                    choice = parts[3]
                    
                    edit_message_media(chat_id, msg_id, BANNER_URL, f"🎰 Крутим... Ставка: {bet}$", None)
                    
                    win = False
                    multiplier = 1.0
                    val = 0

                    if game == "dice":
                        val = random.randint(1, 6)
                        send_animation(chat_id, "🎲")
                        time.sleep(2.5)
                        if choice == "high" and val > 3: win = True; multiplier = 2.0
                        elif choice == "low" and val < 4: win = True; multiplier = 2.0
                        elif choice == "exact" and val == 6: win = True; multiplier = 6.0
                        elif choice == "duel": 
                            # Просто имитация для дуэли
                            if val >= 4: win = True
                            multiplier = 2.2
                        
                    elif game == "coin":
                        val = random.choice(["heads", "tails"])
                        send_animation(chat_id, "🎲")
                        time.sleep(2.5)
                        if choice == val: win = True; multiplier = 2.0
                        
                    elif game == "football":
                        val = random.randint(1, 10)
                        send_animation(chat_id, "⚽")
                        time.sleep(2.5)
                        if choice == "goal" and val > 4: win = True; multiplier = 1.5
                        elif choice == "miss" and val <= 4: win = True; multiplier = 2.5
                        elif choice == "both" and val >= 7: win = True; multiplier = 3.0

                    elif game == "basketball":
                        val = random.randint(1, 10)
                        send_animation(chat_id, "🏀")
                        time.sleep(2.5)
                        if choice == "2pt" and val <= 6: win = True; multiplier = 1.5
                        elif choice == "3pt" and val > 6: win = True; multiplier = 3.0
                        
                    elif game == "darts":
                        val = random.randint(1, 10)
                        send_animation(chat_id, "🎯")
                        time.sleep(2.5)
                        if choice == "bull" and val == 10: win = True; multiplier = 5.0
                        elif choice == "red" and 5 <= val <= 9: win = True; multiplier = 2.0
                        elif choice == "miss" and val <= 3: win = True; multiplier = 1.5

                    elif game == "slots":
                        val = random.randint(1, 10)
                        send_animation(chat_id, "🎰")
                        time.sleep(2.5)
                        if choice == "win" and val == 10: win = True; multiplier = 5.0
                        elif choice == "2row" and val >= 6: win = True; multiplier = 1.5
                    
                    elif game == "bowling":
                        val = random.choices([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10], weights=[15, 5, 10, 15, 15, 10, 10, 5, 5, 3, 7])[0]
                        send_animation(chat_id, "🎳")
                        time.sleep(2.5)
                        if choice == "strike" and val == 10: win = True; multiplier = 5.0
                        elif choice == "high" and 7 <= val <= 9: win = True; multiplier = 2.5
                        elif choice == "low" and 1 <= val <= 3: win = True; multiplier = 1.5
                        elif choice == "miss" and val == 0: win = True; multiplier = 4.0

                    elif game == "roulette":
                        sectors = ["red"] * 4 + ["black"] * 4 + ["zero"] * 2
                        random.shuffle(sectors)
                        result_sector = sectors[random.randint(0, 9)]
                        send_animation(chat_id, "🎲") 
                        time.sleep(2.5)
                        if choice == result_sector: win = True
                        multiplier = 5.0 if choice == "zero" else 2.0

                    if win:
                        win_amount = int(bet * multiplier)
                        new_bal = user["balance"] + win_amount - bet
                        update_user(user_id, balance=new_bal, wins=user["wins"] + 1)
                        res_text = f"🎉 <b>Победа!</b> (x{multiplier})\nВы получили: <b>+{win_amount}$</b> 💵\nЧистая прибыль: +{win_amount - bet}$\n\n"
                    else:
                        new_bal = user["balance"] - bet
                        update_user(user_id, balance=new_bal, losses=user["losses"] + 1)
                        res_text = f"😢 <b>Проигрыш.</b>\nПотеряно: <b>-{bet}$</b> 💵\n\n"
                    
                    caption, kb = get_main_menu(get_user(user_id))
                    send_photo(chat_id, BANNER_URL, res_text + caption, kb)

            elif "message" in update and "text" in update["message"]:
                msg = update["message"]
                chat_id = msg["chat"]["id"]
                text_str = msg["text"]
                user_id = msg["from"]["id"]
                first_name = msg["from"].get("first_name", "Игрок")

                user = get_user(user_id)
                update_user(user_id, name=first_name)

                if user_id in user_states:
                    game, msg_id = user_states[user_id]
                    if text_str.isdigit():
                        bet = int(text_str)
                        if bet < 10:
                            edit_message_media(chat_id, msg_id, BANNER_URL, "❌ Мин. ставка 10$. Введите другое число:", {"inline_keyboard": [[{"text": "Отмена", "callback_data": f"game_{game}"}]]})
                        elif bet > user["balance"]:
                            edit_message_media(chat_id, msg_id, BANNER_URL, f"❌ Недостаточно средств (Баланс: {user['balance']}$). Введите другое число:", {"inline_keyboard": [[{"text": "Отмена", "callback_data": f"game_{game}"}]]})
                        else:
                            del user_states[user_id]
                            caption, kb = get_choice_menu(user, game, bet)
                            edit_message_media(chat_id, msg_id, BANNER_URL, caption, kb)
                    else:
                        edit_message_media(chat_id, msg_id, BANNER_URL, "❌ Введите число цифрами:", {"inline_keyboard": [[{"text": "Отмена", "callback_data": f"game_{game}"}]]})
                    continue

                cmd = text_str.lower().split()[0] if text_str else ""

                if cmd == "/start" or cmd == "/help":
                    caption, kb = get_main_menu(user)
                    send_photo(chat_id, BANNER_URL, caption, kb)

    except Exception as e:
        print("Ошибка:", e)
        time.sleep(2)
