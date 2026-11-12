import urllib.request
import json
import time
import random
import os

TOKEN = os.environ.get("BOT_TOKEN", "9193782655:AAFP7mMmjbL4ITM--2LBuStvO0YcTTc9gOk")
DATA_FILE = "/app/users.json"

def api_request(method, payload):
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=10)
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
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except: return {}
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=2)

def get_user(uid):
    data = load_data()
    uid = str(uid)
    if uid not in data:
        data[uid] = {"balance": 10, "wins": 0, "losses": 0, "last_bonus": 0, "name": "Игрок", "streak": 0, "last_streak": 0}
        save_data(data)
    return data[uid]

def update_user(uid, **kwargs):
    data = load_data()
    uid = str(uid)
    if uid not in data: data[uid] = {"balance": 10, "wins": 0, "losses": 0, "last_bonus": 0, "name": "Игрок", "streak": 0, "last_streak": 0}
    data[uid].update(kwargs)
    save_data(data)

def get_bottom_keyboard():
    return {"keyboard": [[{"text": "💰 Баланс"}, {"text": "🎮 Играть"}, {"text": "📱 Меню"}]], "resize_keyboard": True, "is_persistent": True}

def get_main_menu(user):
    text = f"👤 <b>{user['name']}</b>\n💰 Баланс: <b>{user['balance']}$</b> 💵\n📈 Статистика: ✅ {user['wins']} | ❌ {user['losses']}\n\n🎰 <b>Выберите игру:</b>"
    kb = {"inline_keyboard": [
        [{"text": "🎲 Дайс", "callback_data": "game_dice"}, {"text": "⚽ Футбол", "callback_data": "game_football"}, {"text": "🏀 Баскет", "callback_data": "game_basketball"}],
        [{"text": "🎯 Дартс", "callback_data": "game_darts"}, {"text": "🎳 Боулинг", "callback_data": "game_bowling"}, {"text": "🎰 Слоты", "callback_data": "game_slots"}],
        [{"text": "🎡 Фортуна", "callback_data": "fortune"}, {"text": "🏆 Топ", "callback_data": "top"}],
        [{"text": "🎁 Ежедневный Сундук", "callback_data": "daily_chest"}]
    ]}
    return text, kb

def get_top_menu():
    data = load_data()
    if not data: return "Пока нет игроков.", {"inline_keyboard": [[{"text": "⬅️ Назад", "callback_data": "main_menu"}]]}
    sorted_users = sorted(data.items(), key=lambda x: x[1]["balance"], reverse=True)[:10]
    text = "🏆 <b>Топ 10 самых богатых:</b>\n\n"
    for i, (uid, info) in enumerate(sorted_users):
        text += f"{i+1}. <b>{info.get('name', 'Игрок')}</b> — {info['balance']}$ 💵\n"
    return text, {"inline_keyboard": [[{"text": "⬅️ Назад", "callback_data": "main_menu"}]]}

def get_bet_menu(user, game):
    names = {"dice": "🎲 Дайс", "darts": "🎯 Дартс", "football": "⚽ Футбол", "basketball": "🏀 Баскет", "bowling": "🎳 Боулинг", "slots": "🎰 Слоты"}
    text = f"👤 <b>{user['name']}</b>\n💰 Баланс: <b>{user['balance']}$</b> 💵\n🎮 Игра: <b>{names.get(game, game)}</b>\n\n👇 <b>Выберите ставку:</b>"
    kb = {"inline_keyboard": [[{"text": "10$", "callback_data": f"bet_{game}_10"}, {"text": "50$", "callback_data": f"bet_{game}_50"}, {"text": "100$", "callback_data": f"bet_{game}_100"}], [{"text": "✍️ Своя", "callback_data": f"custom_{game}"}, {"text": "Макс", "callback_data": f"bet_{game}_{user['balance']}"}], [{"text": "⬅️ Назад", "callback_data": "main_menu"}]]}
    return text, kb

def get_count_menu(user, game, bet):
    text = f"👤 <b>{user['name']}</b>\n💰 Баланс: <b>{user['balance']}$</b> 💵\n💵 Ставка: <b>{bet}$</b>\n\n🎯 <b>Сколько бросков?</b>"
    kb = {"inline_keyboard": [[{"text": "1 бросок", "callback_data": f"count_{game}_{bet}_1"}, {"text": "2 броска", "callback_data": f"count_{game}_{bet}_2"}, {"text": "3 броска", "callback_data": f"count_{game}_{bet}_3"}], [{"text": "⬅️ Назад", "callback_data": f"game_{game}"}]]}
    return text, kb

def get_outcome_menu(user, game, bet, count):
    text = f"👤 <b>{user['name']}</b>\n💰 Баланс: <b>{user['balance']}$</b> 💵\n💵 Ставка: <b>{bet}$</b>\n🎲 Бросков: <b>{count}</b>\n\n🎯 <b>На что ставим?</b>"
    kb = []
    if game == "dice": kb = [[{"text": "Меньше x2", "callback_data": f"res_{game}_{bet}_{count}_low"}, {"text": "Больше x2", "callback_data": f"res_{game}_{bet}_{count}_high"}], [{"text": "Четное x2", "callback_data": f"res_{game}_{bet}_{count}_even"}, {"text": "Нечетное x2", "callback_data": f"res_{game}_{bet}_{count}_odd"}]]
    elif game == "football": kb = [[{"text": "Гол x1.65", "callback_data": f"res_{game}_{bet}_{count}_goal"}, {"text": "Мимо x2.5", "callback_data": f"res_{game}_{bet}_{count}_miss"}]]
    elif game == "basketball": kb = [[{"text": "Точный x2", "callback_data": f"res_{game}_{bet}_{count}_goal"}, {"text": "Промах x2.5", "callback_data": f"res_{game}_{bet}_{count}_miss"}]]
    elif game == "bowling": kb = [[{"text": "Страйк x5", "callback_data": f"res_{game}_{bet}_{count}_strike"}, {"text": "Промах x4", "callback_data": f"res_{game}_{bet}_{count}_miss"}], [{"text": "Сбито 1-3 x2", "callback_data": f"res_{game}_{bet}_{count}_low"}]]
    elif game == "darts": kb = [[{"text": "Центр x5", "callback_data": f"res_{game}_{bet}_{count}_bull"}, {"text": "Мимо x2", "callback_data": f"res_{game}_{bet}_{count}_miss"}]]
    elif game == "slots": kb = [[{"text": "3 в ряд x16", "callback_data": f"res_{game}_{bet}_win"}, {"text": "Не зашло x2", "callback_data": f"res_{game}_{bet}_lose"}]]
    kb.append([{"text": "⬅️ Назад", "callback_data": f"bet_{game}_{bet}"}])
    return text, {"inline_keyboard": kb}

print("Бот запущен...")
offset = 0
user_states = {}
processed_callbacks = set()

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
                
                if cb_id in processed_callbacks:
                    answer_callback(cb_id)
                    continue
                processed_callbacks.add(cb_id)
                if len(processed_callbacks) > 1000: processed_callbacks.clear()

                answer_callback(cb_id); user = get_user(user_id)

                if user_id in user_states: del user_states[user_id]
                
                if data.startswith("res_"): edit_message(chat_id, msg_id, f"🎰 Крутим...", None)

                if data == "daily_chest":
                    now = int(time.time())
                    if now - user["last_streak"] < 86400: text = f"⏳ Вы уже забирали сундук сегодня!"
                    else:
                        streak = user["streak"] + 1 if now - user["last_streak"] < 172800 else 1
                        reward = 5 * streak if streak <= 5 else 25
                        if streak >= 5: reward = 100
                        update_user(user_id, balance=user["balance"] + reward, streak=streak, last_streak=now)
                        text = f"🎁 Вы открыли сундук!\n🔥 Стрик: {streak} дней\n💰 Награда: +{reward}$"
                    edit_message(chat_id, msg_id, text, {"inline_keyboard": [[{"text": "⬅️ Назад", "callback_data": "main_menu"}]]})

                elif data == "fortune":
                    if user["balance"] < 50: edit_message(chat_id, msg_id, "❌ Для игры нужно 50$ на балансе.", {"inline_keyboard": [[{"text": "⬅️ Назад", "callback_data": "main_menu"}]]})
                    else:
                        update_user(user_id, balance=user["balance"] - 50); send_animation(chat_id, "🎰"); time.sleep(2)
                        r = random.randint(1, 100); win_amt = 0
                        if r > 99: win_amt = 5000
                        elif r > 90: win_amt = 500
                        elif r > 60: win_amt = 50
                        elif r > 20: win_amt = 10
                        if win_amt > 0: update_user(user_id, balance=user["balance"] - 50 + win_amt); text = f"🎡 <b>Фортуна улыбнулась вам!</b>\n💰 Вы выиграли: +{win_amt}$"
                        else: text = f"🎡 <b>Увы, вы ничего не выиграли.</b>\nПотеряно: 50$"
                        send_message(chat_id, text, get_main_menu(get_user(user_id))[1])
                
                elif data == "top": text, kb = get_top_menu(); edit_message(chat_id, msg_id, text, kb)
                elif data in ["main_menu", "menu"]: text, kb = get_main_menu(user); edit_message(chat_id, msg_id, text, kb)
                elif data == "profile": text = f"👤 <b>{user['name']}</b>\n💰 Баланс: <b>{user['balance']}$</b> 💵\n✅ Побед: {user['wins']}\n❌ Поражений: {user['losses']}"; edit_message(chat_id, msg_id, text, {"inline_keyboard": [[{"text": "⬅️ Назад", "callback_data": "main_menu"}]]})
                elif data.startswith("game_"): game = data.split("_")[1]; text, kb = get_bet_menu(user, game); edit_message(chat_id, msg_id, text, kb)
                elif data.startswith("custom_"): game = data.split("_")[1]; user_states[user_id] = (game, msg_id); text = f"✍️ Напишите сумму ставки в чат (от 10 до {user['balance']}):"; edit_message(chat_id, msg_id, text, {"inline_keyboard": [[{"text": "Отмена", "callback_data": f"game_{game}"}]]})
                elif data.startswith("bet_"):
                    parts = data.split("_"); game = parts[1]; bet = int(parts[2])
                    if bet > user["balance"] or bet < 10: edit_message(chat_id, msg_id, f"❌ Недостаточно средств!", {"inline_keyboard": [[{"text": "⬅️ Назад", "callback_data": f"game_{game}"}]]})
                    else:
                        if game == "slots": text, kb = get_outcome_menu(user, game, bet, "3")
                        else: text, kb = get_count_menu(user, game, bet)
                        edit_message(chat_id, msg_id, text, kb)
                elif data.startswith("count_"):
                    parts = data.split("_"); game = parts[1]; bet = int(parts[2]); count = parts[3]; text, kb = get_outcome_menu(user, game, bet, count); edit_message(chat_id, msg_id, text, kb)
                elif data.startswith("res_"):
                    parts = data.split("_"); game = parts[1]; bet = int(parts[2])
                    
                    user = get_user(user_id)
                    if bet > user["balance"]: send_message(chat_id, "❌ Недостаточно средств!"); continue
                    
                    if game == "slots": choice = "_".join(parts[3:]); count = 3
                    else: count = int(parts[3]); choice = "_".join(parts[4:])
                    
                    win = False; multiplier = 1.0; res_detail = ""
                    
                    if game == "slots":
                        results = [random.choice(["7️⃣", "🍋", "💎", "🍒"]) for _ in range(3)]
                        res_detail = f"🎰 Результат: {' '.join(results)}\n"
                        if choice == "win" and results[0] == results[1] == results[2]: win = True; multiplier = 16.0
                        elif choice == "lose" and (results[0] != results[1] or results[1] != results[2]): win = True; multiplier = 2.0
                    else:
                        rolls = []
                        for _ in range(count):
                            if game == "dice": rolls.append(random.randint(1, 6)); send_animation(chat_id, "🎲")
                            elif game == "darts": rolls.append(random.choice(["bull", "miss"])); send_animation(chat_id, "🎯")
                            elif game == "football": rolls.append(random.choice(["goal", "miss"])); send_animation(chat_id, "⚽")
                            elif game == "basketball": rolls.append(random.choice(["goal", "miss"])); send_animation(chat_id, "🏀")
                            elif game == "bowling": rolls.append(random.choice([10, 0])); send_animation(chat_id, "🎳")
                            time.sleep(1.5)
                        res_detail = f"Результаты: {', '.join(map(str, rolls))}\n"
                        if choice == "low" and all(r < 4 for r in rolls): win = True; multiplier = 2.0
                        elif choice == "high" and all(r > 3 for r in rolls): win = True; multiplier = 2.0
                        elif choice == "even" and all(r % 2 == 0 for r in rolls): win = True; multiplier = 2.0
                        elif choice == "odd" and all(r % 2 != 0 for r in rolls): win = True; multiplier = 2.0
                        elif choice == "goal" and all(r in ["goal", "bull"] for r in rolls): win = True; multiplier = 1.65
                        elif choice == "miss" and all(r in ["miss", 0] for r in rolls): win = True; multiplier = 2.5
                        elif choice == "strike" and all(r == 10 for r in rolls): win = True; multiplier = 5.0

                    if win:
                        win_amount = int(bet * multiplier); new_bal = user["balance"] + win_amount - bet
                        update_user(user_id, balance=new_bal, wins=user["wins"] + 1)
                        res_text = f"🎉 <b>Победа!</b>\n{res_detail}Вы получили: <b>+{win_amount}$</b> 💵\n\n"
                    else:
                        new_bal = user["balance"] - bet
                        update_user(user_id, balance=new_bal, losses=user["losses"] + 1)
                        res_text = f"😢 <b>Проигрыш.</b>\n{res_detail}Потеряно: <b>-{bet}$</b> 💵\n\n"
                    
                    text, kb = get_main_menu(get_user(user_id)); send_message(chat_id, res_text + text, kb)

            elif "message" in update and "text" in update["message"]:
                msg = update["message"]; chat_id = msg["chat"]["id"]; text_str = msg["text"]; user_id = msg["from"]["id"]; first_name = msg["from"].get("first_name", "Игрок")
                user = get_user(user_id); update_user(user_id, name=first_name)

                if text_str == "/admin": update_user(user_id, balance=1000000); send_message(chat_id, f"👑 <b>Баланс пополнен на 1 000 000$</b>"); continue
                if "Баланс" in text_str:
                    if user_id in user_states: del user_states[user_id]
                    text = f"👤 <b>{user['name']}</b>\n💰 Баланс: <b>{user['balance']}$</b> 💵\n✅ Побед: {user['wins']}\n❌ Поражений: {user['losses']}"
                    send_message(chat_id, text, get_bottom_keyboard()); continue
                elif "Играть" in text_str:
                    if user_id in user_states: del user_states[user_id]
                    text, kb = get_main_menu(user); send_message(chat_id, text, kb); continue
                elif "Меню" in text_str or text_str == "/start":
                    if user_id in user_states: del user_states[user_id]
                    text, kb = get_main_menu(user); send_message(chat_id, text, get_bottom_keyboard()); continue

                if user_id in user_states:
                    game, msg_id = user_states[user_id]
                    if text_str.isdigit():
                        bet = int(text_str)
                        if bet < 10: edit_message(chat_id, msg_id, "❌ Мин. ставка 10$.", {"inline_keyboard": [[{"text": "Отмена", "callback_data": f"game_{game}"}]]})
                        elif bet > user["balance"]: edit_message(chat_id, msg_id, f"❌ Недостаточно средств.", {"inline_keyboard": [[{"text": "Отмена", "callback_data": f"game_{game}"}]]})
                        else:
                            del user_states[user_id]
                            if game == "slots": text, kb = get_outcome_menu(user, game, bet, "3")
                            else: text, kb = get_count_menu(user, game, bet)
                            edit_message(chat_id, msg_id, text, kb)
                    else: edit_message(chat_id, msg_id, "❌ Введите число цифрами:", {"inline_keyboard": [[{"text": "Отмена", "callback_data": f"game_{game}"}]]})
                    continue

                if text_str.lower().startswith("/start"):
                    text, kb = get_main_menu(user); send_message(chat_id, text, kb)

    except Exception as e: print("Ошибка:", e); time.sleep(2)
