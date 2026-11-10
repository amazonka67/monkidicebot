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

# --- КЛАВИАТУРА СНИЗУ ---
def get_bottom_keyboard():
    return {
        "keyboard": [
            [{"text": "💰 Баланс"}, {"text": "🎮 Играть"}, {"text": "📱 Меню"}]
        ],
        "resize_keyboard": True,
        "is_persistent": True
    }

# --- МЕНЮ ---

def get_main_menu(user):
    text = (
        f"👤 <b>{user['name']}</b>\n"
        f"💰 Баланс: <b>{user['balance']}$</b> 💵\n"
        f"📈 Статистика: ✅ {user['wins']} | ❌ {user['losses']}\n\n"
        f"🎰 <b>Выберите игру:</b>"
    )
    kb = {
        "inline_keyboard": [
            [{"text": "🎲 (до x216)", "callback_data": "game_dice"}, {"text": "⚽ (до x25)", "callback_data": "game_football"}, {"text": "🏀 (до x25)", "callback_data": "game_basketball"}],
            [{"text": "🎯 (до x36)", "callback_data": "game_darts"}, {"text": "🎳 (до x36)", "callback_data": "game_bowling"}, {"text": "🎰 (до x40)", "callback_data": "game_slots"}],
            [{"text": "👨‍💻 Авторские", "callback_data": "game_custom"}, {"text": "🚀 Турбо", "callback_data": "game_turbo"}, {"text": "🃏 Мини-игры", "callback_data": "game_mini"}],
            [{"text": "💰 Баланс", "callback_data": "profile"}, {"text": "🎁 Бонус", "callback_data": "bonus"}, {"text": "💎 Купить $", "callback_data": "shop"}]
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
    text = f"👤 <b>{user['name']}</b>\n💰 Баланс: <b>{user['balance']}$</b> 💵\n🎮 Игра: <b>{game_names.get(game, game)}</b>\n\n👇 <b>Выберите ставку:</b>"
    kb = {
        "inline_keyboard": [
            [{"text": "10$", "callback_data": f"bet_{game}_10"}, {"text": "50$", "callback_data": f"bet_{game}_50"}, {"text": "100$", "callback_data": f"bet_{game}_100"}],
            [{"text": "500$", "callback_data": f"bet_{game}_500"}, {"text": "✍️ Своя", "callback_data": f"custom_{game}"}, {"text": "Макс", "callback_data": f"bet_{game}_{user['balance']}"}],
            [{"text": "⬅️ Назад", "callback_data": "main_menu"}]
        ]
    }
    return text, kb

def get_choice_menu(user, game, bet):
    text = f"👤 <b>{user['name']}</b>\n💰 Баланс: <b>{user['balance']}$</b> 💵\n💵 Ставка: <b>{bet}$</b>\n\n🎯 <b>На что ставим?</b>"
    kb = []
    
    if game == "darts":
        kb = [
            [{"text": "🔴 Красное (x2)", "callback_data": f"res_{game}_{bet}_red"}],
            [{"text": "⚪ Белое (x2)", "callback_data": f"res_{game}_{bet}_white"}],
            [{"text": "🎯 Центр (x5)", "callback_data": f"res_{game}_{bet}_bull"}],
            [{"text": "❌ Промах (x3)", "callback_data": f"res_{game}_{bet}_miss"}]
        ]
    elif game == "bowling":
        kb = [
            [{"text": "🎳 Страйк (10) x5", "callback_data": f"res_{game}_{bet}_strike"}],
            [{"text": "🎯 7-9 кеглей (x2.5)", "callback_data": f"res_{game}_{bet}_high"}],
            [{"text": "⚪ 1-3 кегли (x1.5)", "callback_data": f"res_{game}_{bet}_low"}],
            [{"text": "❌ Промах (0) x4", "callback_data": f"res_{game}_{bet}_miss"}]
        ]
    elif game == "football":
        kb = [
            [{"text": "⚽ Гол (x1.5)", "callback_data": f"res_{game}_{bet}_goal"}],
            [{"text": "❌ Мимо (x2.5)", "callback_data": f"res_{game}_{bet}_miss"}],
            [{"text": "🔥 Обе забьют (x3)", "callback_data": f"res_{game}_{bet}_both"}]
        ]
    elif game == "basketball":
        kb = [
            [{"text": "2 очка (x1.5)", "callback_data": f"res_{game}_{bet}_2pt"}],
            [{"text": "3 очка (x3)", "callback_data": f"res_{game}_{bet}_3pt"}],
            [{"text": "Промах (x2)", "callback_data": f"res_{game}_{bet}_miss"}]
        ]
    elif game == "dice":
        kb = [
            [{"text": "1 бросок: Больше 3 (x2)", "callback_data": f"res_{game}_{bet}_1_high"}, {"text": "1 бросок: Меньше 4 (x2)", "callback_data": f"res_{game}_{bet}_1_low"}],
            [{"text": "2 броска: Сумма > 7 (x2)", "callback_data": f"res_{game}_{bet}_2_high"}, {"text": "2 броска: Сумма < 7 (x2)", "callback_data": f"res_{game}_{bet}_2_low"}],
            [{"text": "2 броска: Ровно 7 (x5)", "callback_data": f"res_{game}_{bet}_2_seven"}]
        ]
    elif game == "turbo":
        kb = [
            [{"text": "3 кубика (Сумма > 10) x3", "callback_data": f"res_dice_{bet}_three_high"}],
            [{"text": "Три шестерки (x50)", "callback_data": f"res_dice_{bet}_three_six"}],
            [{"text": "Все > 3 (x5)", "callback_data": f"res_turbo_{bet}_turbo_high"}],
            [{"text": "Все < 4 (x5)", "callback_data": f"res_turbo_{bet}_turbo_low"}]
        ]
    elif game == "custom":
        kb = [
            [{"text": "🔥 Мега-Джекпот (x10)", "callback_data": f"res_{game}_{bet}_jackpot"}],
            [{"text": "💀 Смертельная ставка (x15)", "callback_data": f"res_{game}_{bet}_death"}]
        ]
    elif game == "mini":
        kb = [
            [{"text": "🦅 Орел (x2)", "callback_data": f"res_{game}_{bet}_heads"}],
            [{"text": "🪙 Решка (x2)", "callback_data": f"res_{game}_{bet}_tails"}]
        ]
    elif game == "slots":
        kb = [
            [{"text": "🍋 Лимон (x16)", "callback_data": f"res_{game}_{bet}_lemon"}],
            [{"text": "🍒 Вишня (x16)", "callback_data": f"res_{game}_{bet}_cherry"}],
            [{"text": "💎 Алмаз (x16)", "callback_data": f"res_{game}_{bet}_diamond"}],
            [{"text": "7️⃣ Семерка (x16)", "callback_data": f"res_{game}_{bet}_seven"}],
            [{"text": "❌ Не выпадет 3 в ряд (x2)", "callback_data": f"res_{game}_{bet}_lose"}]
        ]
    kb.append([{"text": "⬅️ Назад", "callback_data": f"game_{game}"}])
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

                # Если нажали Inline-кнопку, сбрасываем режим ввода ставки
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
                        text, kb = get_choice_menu(user, game, bet)
                        edit_message(chat_id, msg_id, text, kb)

                elif data.startswith("res_"):
                    parts = data.split("_")
                    game = parts[1]
                    bet = int(parts[2])
                    choice = parts[3]
                    edit_message(chat_id, msg_id, f"🎰 Крутим... Ставка: {bet}$", None)
                    
                    win = False
                    multiplier = 1.0
                    res_detail = ""

                    if game == "darts":
                        sectors = ["red", "red", "white", "white", "miss", "miss", "bull", "bull"]
                        result_sector = random.choice(sectors)
                        send_animation(chat_id, "🎯"); time.sleep(2)
                        res_detail = f"Дротик попал: <b>{result_sector.upper()}</b>\n"
                        if choice == result_sector: win = True
                        multiplier = {"red": 2.0, "white": 2.0, "miss": 3.0, "bull": 5.0}[choice]
                        
                    elif game == "dice":
                        if choice == "1_high" or choice == "1_low":
                            val = random.randint(1, 6)
                            send_animation(chat_id, "🎲"); time.sleep(2)
                            res_detail = f"Выпало: {val}\n"
                            if choice == "1_high" and val > 3: win = True
                            elif choice == "1_low" and val < 4: win = True
                            multiplier = 2.0
                        else:
                            d1 = random.randint(1, 6); send_animation(chat_id, "🎲"); time.sleep(1)
                            d2 = random.randint(1, 6); send_animation(chat_id, "🎲"); time.sleep(1.5)
                            total = d1 + d2
                            res_detail = f"Выпало: {d1} + {d2} = {total}\n"
                            if choice == "2_high" and total > 7: win = True; multiplier = 2.0
                            elif choice == "2_low" and total < 7: win = True; multiplier = 2.0
                            elif choice == "2_seven" and total == 7: win = True; multiplier = 5.0

                    elif game == "slots":
                        symbols = ["🍋", "🍒", "💎", "7️⃣"]
                        results = [random.choice(symbols) for _ in range(3)]
                        res_detail = f"🎰 Результат: {' '.join(results)}\n"
                        if choice == "lose":
                            if results[0] != results[1] or results[1] != results[2]:
                                win = True; multiplier = 2.0
                        else:
                            target_sym = {"lemon": "🍋", "cherry": "🍒", "diamond": "💎", "seven": "7️⃣"}[choice]
                            if results[0] == results[1] == results[2] == target_sym:
                                win = True; multiplier = 16.0

                    elif game == "football":
                        val = random.randint(1, 5)
                        send_animation(chat_id, "⚽"); time.sleep(2)
                        res_detail = f"Матч окончен.\n"
                        if choice == "goal" and val >= 3: win = True
                        elif choice == "miss" and val < 3: win = True
                        elif choice == "both" and val == 5: win = True
                        multiplier = 1.5 if choice == "goal" else (2.5 if choice == "miss" else 3.0)
                    
                    elif game == "basketball":
                        val = random.randint(1, 10)
                        send_animation(chat_id, "🏀"); time.sleep(2)
                        res_detail = f"Брошено мячей: {val}\n"
                        if choice == "2pt" and val <= 6: win = True
                        elif choice == "3pt" and val > 6: win = True
                        elif choice == "miss" and val == 1: win = True
                        multiplier = 1.5 if choice == "2pt" else (3.0 if choice == "3pt" else 2.0)
                    
                    elif game == "bowling":
                        val = random.choices([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10], weights=[15, 5, 10, 15, 15, 10, 10, 5, 5, 3, 7])[0]
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

                    elif game == "turbo":
                        if choice == "turbo_high" or choice == "turbo_low":
                            d1 = random.randint(1, 6); send_animation(chat_id, "🎲"); time.sleep(1)
                            d2 = random.randint(1, 6); send_animation(chat_id, "🎲"); time.sleep(1)
                            d3 = random.randint(1, 6); send_animation(chat_id, "🎲"); time.sleep(1.5)
                            res_detail = f"Выпало: {d1}, {d2}, {d3}\n"
                            if choice == "turbo_high" and d1 > 3 and d2 > 3 and d3 > 3: win = True
                            elif choice == "turbo_low" and d1 < 4 and d2 < 4 and d3 < 4: win = True
                            multiplier = 5.0
                        else:
                            d1 = random.randint(1, 6); send_animation(chat_id, "🎲"); time.sleep(1)
                            d2 = random.randint(1, 6); send_animation(chat_id, "🎲"); time.sleep(1)
                            d3 = random.randint(1, 6); send_animation(chat_id, "🎲"); time.sleep(1.5)
                            total = d1 + d2 + d3
                            res_detail = f"Выпало: {d1}, {d2}, {d3} (Сумма: {total})\n"
                            if choice == "three_high" and total > 10: win = True; multiplier = 3.0
                            elif choice == "three_six" and d1 == 6 and d2 == 6 and d3 == 6: win = True; multiplier = 50.0
                            
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

                    if win:
                        win_amount = int(bet * multiplier)
                        new_bal = user["balance"] + win_amount - bet
                        update_user(user_id, balance=new_bal, wins=user["wins"] + 1)
                        res_text = f"🎉 <b>Победа!</b>\n{res_detail}Вы получили: <b>+{win_amount}$</b> 💵\nЧистая прибыль: +{win_amount - bet}$\n\n"
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

                # ИСПРАВЛЕНИЕ: Проверяем нижние кнопки ДО того, как проверять ввод ставки
                if text_str == "💰 Баланс":
                    if user_id in user_states: del user_states[user_id] # Сбрасываем ввод
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

                # Обработка ввода своей ставки
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
