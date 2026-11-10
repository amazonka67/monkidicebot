import urllib.request
import json
import time
import random
import os

TOKEN = os.environ.get("BOT_TOKEN", "9193782655:AAFP7mMmjbL4ITM--2LBuStvO0YcTTc9gOk")
DATA_FILE = "users.json"

def api_request(method, payload):
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"Ошибка API {method}:", e)

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
    url = f"https://api.telegram.org/bot{TOKEN}/createInvoiceLink"
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

def get_bottom_keyboard():
    return {"keyboard": [[{"text": "💰 Баланс"}, {"text": "🎮 Играть"}, {"text": "📱 Меню"}]], "resize_keyboard": True, "is_persistent": True}

def get_main_menu(user):
    text = f"👤 <b>{user['name']}</b>\n💰 Баланс: <b>{user['balance']}$</b> 💵\n📈 Статистика: ✅ {user['wins']} | ❌ {user['losses']}\n\n🎰 <b>Выберите игру:</b>"
    kb = {"inline_keyboard": [
        [{"text": "🎲 Дайс", "callback_data": "game_dice"}, {"text": "⚽ Футбол", "callback_data": "game_football"}, {"text": "🏀 Баскет", "callback_data": "game_basketball"}],
        [{"text": "🎯 Дартс", "callback_data": "game_darts"}, {"text": "🎳 Боулинг", "callback_data": "game_bowling"}, {"text": "🎰 Слоты", "callback_data": "game_slots"}],
        [{"text": "💰 Баланс", "callback_data": "profile"}, {"text": "🎁 Бонус", "callback_data": "bonus"}, {"text": "💎 Купить $", "callback_data": "shop"}]
    ]}
    return text, kb

def get_shop_menu(user):
    text = f"💎 <b>Магазин валюты</b>\n\nВаш баланс: <b>{user['balance']}$</b> 💵\n\nВыберите пакет:"
    kb = {"inline_keyboard": [[{"text": "100$ за 10 ⭐", "callback_data": "buy_100_10"}], [{"text": "500$ за 40 ⭐", "callback_data": "buy_500_40"}], [{"text": "⬅️ Назад", "callback_data": "main_menu"}]]}
    return text, kb

def get_bet_menu(user, game):
    names = {"dice": "🎲 Дайс", "darts": "🎯 Дартс", "football": "⚽ Футбол", "basketball": "🏀 Баскет", "bowling": "🎳 Боулинг", "slots": "🎰 Слоты"}
    text = f"👤 <b>{user['name']}</b>\n💰 Баланс: <b>{user['balance']}$</b> 💵\n🎮 Игра: <b>{names.get(game, game)}</b>\n\n👇 <b>Выберите ставку:</b>"
    kb = {"inline_keyboard": [
        [{"text": "10$", "callback_data": f"bet_{game}_10"}, {"text": "50$", "callback_data": f"bet_{game}_50"}, {"text": "100$", "callback_data": f"bet_{game}_100"}],
        [{"text": "✍️ Своя", "callback_data": f"custom_{game}"}, {"text": "Макс", "callback_data": f"bet_{game}_{user['balance']}"}],
        [{"text": "⬅️ Назад", "callback_data": "main_menu"}]
    ]}
    return text, kb

def get_count_menu(user, game, bet):
    text = f"👤 <b>{user['name']}</b>\n💰 Баланс: <b>{user['balance']}$</b> 💵\n💵 Ставка: <b>{bet}$</b>\n\n🎯 <b>Выберите количество:</b>"
    kb = {"inline_keyboard": [
        [{"text": "1 бросок", "callback_data": f"count_{game}_{bet}_1"}, {"text": "2 броска", "callback_data": f"count_{game}_{bet}_2"}, {"text": "3 броска", "callback_data": f"count_{game}_{bet}_3"}],
        [{"text": "⬅️ Назад", "callback_data": f"game_{game}"}]
    ]}
    return text, kb

def get_outcome_menu(user, game, bet, count):
    text = f"👤 <b>{user['name']}</b>\n💰 Баланс: <b>{user['balance']}$</b> 💵\n💵 Ставка: <b>{bet}$</b>\n🎲 Бросков: <b>{count}</b>\n\n🎯 <b>На что ставим?</b>"
    kb = []
    if game == "dice":
        kb = [[{"text": "Меньше x2", "callback_data": f"res_{game}_{bet}_{count}_low"}, {"text": "Больше x2", "callback_data": f"res_{game}_{bet}_{count}_high"}], [{"text": "Четное x2", "callback_data": f"res_{game}_{bet}_{count}_even"}, {"text": "Нечетное x2", "callback_data": f"res_{game}_{bet}_{count}_odd"}], [{"text": "Точное 1-6 (x6)", "callback_data": f"res_{game}_{bet}_{count}_exact"}]]
    elif game == "darts":
        kb = [[{"text": "Сектор x3", "callback_data": f"res_{game}_{bet}_{count}_sector"}, {"text": "Отскок x6", "callback_data": f"res_{game}_{bet}_{count}_bounce"}], [{"text": "Центр x6", "callback_data": f"res_{game}_{bet}_{count}_bull"}, {"text": "Промах x3", "callback_data": f"res_{game}_{bet}_{count}_miss"}]]
    elif game == "bowling":
        kb = [[{"text": "1-3 x2", "callback_data": f"res_{game}_{bet}_{count}_low"}, {"text": "4-6 x3", "callback_data": f"res_{game}_{bet}_{count}_mid"}], [{"text": "Страйк x5", "callback_data": f"res_{game}_{bet}_{count}_strike"}, {"text": "Промах x4", "callback_data": f"res_{game}_{bet}_{count}_miss"}]]
    elif game == "football":
        kb = [[{"text": "Гол в центр x5", "callback_data": f"res_{game}_{bet}_{count}_center"}, {"text": "Гол в угол x5", "callback_data": f"res_{game}_{bet}_{count}_corner"}], [{"text": "Любой гол x1.65", "callback_data": f"res_{game}_{bet}_{count}_goal"}], [{"text": "Штанга x2.5", "callback_data": f"res_{game}_{bet}_{count}_post"}, {"text": "Промах x2.5", "callback_data": f"res_{game}_{bet}_{count}_miss"}]]
    elif game == "basketball":
        kb = [[{"text": "Точный x2", "callback_data": f"res_{game}_{bet}_{count}_goal"}, {"text": "Кольцо x1.5", "callback_data": f"res_{game}_{bet}_{count}_ring"}], [{"text": "Промах x2.5", "callback_data": f"res_{game}_{bet}_{count}_miss"}]]
    elif game == "slots":
        text = f"👤 <b>{user['name']}</b>\n💰 Баланс: <b>{user['balance']}$</b> 💵\n💵 Ставка: <b>{bet}$</b>\n\n🎰 <b>Выберите символ:</b>"
        kb = [[{"text": "3 семерки x64", "callback_data": f"res_{game}_{bet}_3_seven"}, {"text": "3 лимона x64", "callback_data": f"res_{game}_{bet}_3_lemon"}], [{"text": "Любая комбинация x1.6", "callback_data": f"res_{game}_{bet}_3_any"}]]
    kb.append([{"text": "⬅️ Назад", "callback_data": f"bet_{game}_{bet}"}])
    return text, {"inline_keyboard": kb}

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
                    send_message(chat_id, f"✅ Оплата прошла успешно!\nВам начислено <b>{dollars}$</b> 💵\nВаш баланс: {new_bal}$")
                continue

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

                if data == "main_menu" or data == "menu":
                    text, kb = get_main_menu(user)
                    edit_message(chat_id, msg_id, text, kb)
                elif data == "shop":
                    text, kb = get_shop_menu(user)
                    edit_message(chat_id, msg_id, text, kb)
                elif data.startswith("buy_"):
                    parts = data.split("_")
                    send_stars_invoice(chat_id, msg_id, int(parts[2]), int(parts[1]))
                elif data == "profile":
                    text = f"👤 <b>{user['name']}</b>\n💰 Баланс: <b>{user['balance']}$</b> 💵\n✅ Побед: {user['wins']}\n❌ Поражений: {user['losses']}"
                    edit_message(chat_id, msg_id, text, {"inline_keyboard": [[{"text": "⬅️ Назад", "callback_data": "main_menu"}]]})
                elif data == "bonus":
                    now = int(time.time())
                    if now - user["last_bonus"] < 86400:
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
                    game = data.split("_")[1]
                    user_states[user_id] = (game, msg_id)
                    text = f"✍️ Напишите сумму вашей ставки в чат (от 10 до {user['balance']}):"
                    edit_message(chat_id, msg_id, text, {"inline_keyboard": [[{"text": "Отмена", "callback_data": f"game_{game}"}]]})
                elif data.startswith("bet_"):
                    parts = data.split("_")
                    game = parts[1]
                    bet = int(parts[2])
                    if bet > user["balance"] or bet < 10:
                        text = f"❌ Неверная ставка (мин. 10) или недостаточно средств!"
                        edit_message(chat_id, msg_id, text, {"inline_keyboard": [[{"text": "⬅️ Назад", "callback_data": f"game_{game}"}]]})
                    else:
                        if game == "slots":
                            text, kb = get_outcome_menu(user, game, bet, "3")
                        else:
                            text, kb = get_count_menu(user, game, bet)
                        edit_message(chat_id, msg_id, text, kb)
                elif data.startswith("count_"):
                    parts = data.split("_")
                    game = parts[1]
                    bet = int(parts[2])
                    count = parts[3]
                    text, kb = get_outcome_menu(user, game, bet, count)
                    edit_message(chat_id, msg_id, text, kb)
                elif data.startswith("res_"):
                    parts = data.split("_")
                    game = parts[1]
                    bet = int(parts[2])
                    if game == "slots":
                        choice = "_".join(parts[3:])
                        count = 3
                    else:
                        count = int(parts[3])
                        choice = "_".join(parts[4:])
                        
                    edit_message(chat_id, msg_id, f"🎰 Крутим... Ставка: {bet}$", None)
                    win = False
                    multiplier = 1.0
                    res_detail = ""

                    if game == "slots":
                        symbols = ["7️⃣", "🍋", "💎", "🍒"]
                        results = [random.choice(symbols) for _ in range(3)]
                        res_detail = f"🎰 Результат: {' '.join(results)}\n"
                        if choice == "3_any":
                            if results[0] != results[1] or results[1] != results[2]:
                                win = True; multiplier = 1.6
                        else:
                            target = choice.split("_")[1]
                            target_sym = {"seven": "7️⃣", "lemon": "🍋", "diamond": "💎", "cherry": "🍒"}[target]
                            if results[0] == results[1] == results[2] == target_sym:
                                win = True; multiplier = 64.0
                    else:
                        rolls = []
                        for _ in range(count):
                            if game == "dice": rolls.append(random.randint(1, 6)); send_animation(chat_id, "🎲")
                            elif game == "darts": rolls.append(random.choice(["miss", "bounce", "sector", "bull"])); send_animation(chat_id, "🎯")
                            elif game == "football": rolls.append(random.choice(["miss", "post", "goal", "center", "corner"])); send_animation(chat_id, "⚽")
                            elif game == "basketball": rolls.append(random.choice(["miss", "ring", "goal"])); send_animation(chat_id, "🏀")
                            elif game == "bowling": rolls.append(random.choices([0, 1, 3, 5, 10], weights=[20, 30, 25, 15, 10])[0]); send_animation(chat_id, "🎳")
                            time.sleep(1.5)
                        res_detail = f"Результаты: {', '.join(map(str, rolls))}\n"
                        
                        if choice == "low" and all(r < 4 for r in rolls): win = True; multiplier = 2.0
                        elif choice == "high" and all(r > 3 for r in rolls): win = True; multiplier = 2.0
                        elif choice == "even" and all(r % 2 == 0 for r in rolls): win = True; multiplier = 2.0
                        elif choice == "odd" and all(r % 2 != 0 for r in rolls): win = True; multiplier = 2.0
                        elif choice == "exact" and all(r == random.randint(1,6) for r in rolls): win = True; multiplier = 6.0
                        elif choice == "sector" and all(r == "sector" for r in rolls): win = True; multiplier = 3.0
                        elif choice == "bounce" and all(r == "bounce" for r in rolls): win = True; multiplier = 6.0
                        elif choice == "bull" and all(r == "bull" for r in rolls): win = True; multiplier = 6.0
                        elif choice == "goal" and all(r in ["goal", "center", "corner"] for r in rolls): win = True; multiplier = 1.65
                        elif choice == "center" and all(r == "center" for r in rolls): win = True; multiplier = 5.0
                        elif choice == "corner" and all(r == "corner" for r in rolls): win = True; multiplier = 5.0
                        elif choice == "post" and all(r == "post" for r in rolls): win = True; multiplier = 2.5
                        elif choice == "strike" and all(r == 10 for r in rolls): win = True; multiplier = 5.0
                        elif choice == "mid" and all(4 <= r <= 6 for r in rolls): win = True; multiplier = 3.0

                    if win:
                        win_amount = int(bet * multiplier)
                        new_bal = user["balance"] + win_amount - bet
                        update_user(user_id, balance=new_bal, wins=user["wins"] + 1)
                        res_text = f"🎉 <b>Победа!</b>\n{res_detail}Вы получили: <b>+{win_amount}$</b> 💵\n\n"
                    else:
                        new_bal = user["balance"] - bet
                        update_user(user_id, balance=new_bal, losses=user["losses"] + 1)
                        res_text = f"😢 <b>Проигрыш.</b>\n{res_detail}Потеряно: <b>-{bet}$</b> 💵\n\n"
                    
                    text, kb = get_main_menu(get_user(user_id))
                    send_message(chat_id, res_text + text, kb)

            elif "message" in update and "text" in update["message"]:
                msg = update["message"]
                chat_id = msg["chat"]["id"]
                text_str = msg["text"]
                user_id = msg["from"]["id"]
                first_name = msg["from"].get("first_name", "Игрок")

                user = get_user(user_id)
                update_user(user_id, name=first_name)

                if text_str == "💰 Баланс":
                    if user_id in user_states: del user_states[user_id]
                    text = f"👤 <b>{user['name']}</b>\n💰 Баланс: <b>{user['balance']}$</b> 💵\n✅ Побед: {user['wins']}\n❌ Поражений: {user['losses']}"
                    send_message(chat_id, text, get_bottom_keyboard())
                    continue
                elif text_str == "🎮 Играть":
                    if user_id in user_states: del user_states[user_id]
                    text, kb = get_main_menu(user)
                    send_message(chat_id, text, kb)
                    continue
                elif text_str == "📱 Меню" or text_str == "/start" or text_str == "/help":
                    if user_id in user_states: del user_states[user_id]
                    text, kb = get_main_menu(user)
                    send_message(chat_id, text, get_bottom_keyboard())
                    continue

                if user_id in user_states:
                    game, msg_id = user_states[user_id]
                    if text_str.isdigit():
                        bet = int(text_str)
                        if bet < 10:
                            edit_message(chat_id, msg_id, "❌ Мин. ставка 10$. Введите другое число:", {"inline_keyboard": [[{"text": "Отмена", "callback_data": f"game_{game}"}]]})
                        elif bet > user["balance"]:
                            edit_message(chat_id, msg_id, f"❌ Недостаточно средств (Баланс: {user['balance']}$). Введите другое число:", {"inline_keyboard": [[{"text": "Отмена", "callback_data": f"game_{game}"}]]})
                        else:
                            del user_states[user_id]
                            if game == "slots":
                                text, kb = get_outcome_menu(user, game, bet, "3")
                            else:
                                text, kb = get_count_menu(user, game, bet)
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
