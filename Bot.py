import urllib.request
import urllib.error
import json
import time
import random
import os

# ============================================================
# КОНФИГ
# ============================================================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "9193782655:AAFP7mMmjbL4ITM--2LBuStvO0YcTTc9gOk")
CRYPTO_TOKEN = os.environ.get("CRYPTO_TOKEN", "673588:AAeEcZ2RWDF3cGjfiB0zZZaUjlguDytrdAD")

TG_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
CRYPTO_API = "https://pay.crypt.bot/api"

DATA_FILE = "users.json"
DEPOSIT_AMOUNTS = [10, 50, 100, 500]
MIN_BET = 10
BONUS_AMOUNT = 5
BONUS_COOLDOWN = 86400


# ============================================================
# TELEGRAM API
# ============================================================
def api_request(method, payload):
    url = f"{TG_API}/{method}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        res = urllib.request.urlopen(req, timeout=15)
        return json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            print(f"HTTP {method}: {e.code} {e.read().decode()}")
        except Exception:
            print(f"HTTP {method}: {e.code}")
        return None
    except Exception as e:
        print(f"Ошибка API {method}: {e}")
        return None


def send_message(chat_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return api_request("sendMessage", payload)


def edit_message(chat_id, message_id, text, reply_markup=None):
    if not message_id:
        return send_message(chat_id, text, reply_markup)
    payload = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return api_request("editMessageText", payload)


def send_dice_result(chat_id, emoji, value):
    return send_message(chat_id, f"{emoji} <b>{value}</b>")


def answer_callback(callback_id, text=None):
    payload = {"callback_query_id": callback_id}
    if text:
        payload["text"] = text
    return api_request("answerCallbackQuery", payload)


# ============================================================
# CRYPTO PAY API
# ============================================================
def crypto_api_request(method, payload=None):
    url = f"{CRYPTO_API}/{method}"
    headers = {"Crypto-Pay-API-Token": CRYPTO_TOKEN, "Content-Type": "application/json"}
    data = json.dumps(payload).encode("utf-8") if payload else None
    req = urllib.request.Request(url, data=data, headers=headers, method="POST" if data else "GET")
    try:
        res = urllib.request.urlopen(req, timeout=15)
        return json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode("utf-8"))
            print(f"Crypto HTTP {method}: {e.code} {body}")
            return body
        except Exception:
            print(f"Crypto HTTP {method}: {e.code}")
            return {"ok": False, "error": str(e)}
    except Exception as e:
        print(f"Ошибка CryptoPay {method}: {e}")
        return {"ok": False, "error": str(e)}


# ============================================================
# STARS INVOICE
# ============================================================
def send_stars_invoice(chat_id, msg_id, amount_stars, amount_dollars):
    url = f"{TG_API}/createInvoiceLink"
    payload = {
        "title": f"Покупка {amount_dollars}$",
        "description": f"Пополнение баланса на {amount_dollars} долларов",
        "payload": f"stars:{amount_dollars}:{amount_stars}",
        "currency": "XTR",
        "prices": [{"label": f"{amount_dollars}$", "amount": amount_stars}],
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        result = json.loads(urllib.request.urlopen(req, timeout=15).read().decode("utf-8"))
        if result.get("ok"):
            kb = {"inline_keyboard": [
                [{"text": f"💎 Оплатить {amount_stars} Stars", "url": result["result"]}],
                [{"text": "⬅️ Назад", "callback_data": "shop"}],
            ]}
            edit_message(chat_id, msg_id, "👇 Нажмите на кнопку ниже, чтобы оплатить:", kb)
        else:
            print("createInvoiceLink failed:", result)
            edit_message(chat_id, msg_id, "❌ Ошибка создания счёта Stars.",
                         {"inline_keyboard": [[{"text": "⬅️ Назад", "callback_data": "shop"}]]})
    except Exception as e:
        print("Ошибка Stars API:", e)


# ============================================================
# CRYPTO INVOICE / PAYOUT
# ============================================================
def create_crypto_invoice(chat_id, msg_id, amount_dollars):
    payload = {
        "asset": "USDT",
        "amount": str(amount_dollars),
        "description": "Пополнение игрового баланса",
        "payload": f"deposit_{chat_id}_{amount_dollars}_{int(time.time())}",
        "allow_comments": False,
        "allow_anonymous": False,
    }
    res = crypto_api_request("createInvoice", payload)
    if res.get("ok"):
        invoice = res["result"]
        kb = {"inline_keyboard": [
            [{"text": f"💳 Оплатить {amount_dollars}$ (USDT)", "url": invoice["pay_url"]}],
            [{"text": "🔄 Проверить оплату", "callback_data": f"check_dep_{invoice['invoice_id']}"}],
            [{"text": "⬅️ Назад", "callback_data": "profile"}],
        ]}
        edit_message(chat_id, msg_id,
                     f"⚡️ <b>Счёт на {amount_dollars}$ USDT создан!</b>\n\n"
                     f"Оплатите по кнопке ниже и нажмите «Проверить оплату»:",
                     kb)
    else:
        print("createInvoice failed:", res.get("error"))
        edit_message(chat_id, msg_id, "❌ Ошибка создания счёта. Проверьте токен CryptoBot.",
                     {"inline_keyboard": [[{"text": "⬅️ Назад", "callback_data": "profile"}]]})


def send_crypto_payout(chat_id, msg_id, amount_dollars, target_tg_id):
    user = get_user(chat_id)
    amount_dollars = round(float(amount_dollars), 2)
    if user["balance"] < amount_dollars:
        edit_message(chat_id, msg_id, "❌ Недостаточно средств для вывода.",
                     {"inline_keyboard": [[{"text": "⬅️ Назад", "callback_data": "profile"}]]})
        return
    spend_id = f"payout_{chat_id}_{int(time.time())}_{random.randint(1000, 9999)}"
    payload = {
        "user_id": int(target_tg_id),
        "asset": "USDT",
        "amount": str(amount_dollars),
        "spend_id": spend_id,
        "comment": "Вывод игрового баланса",
    }
    res = crypto_api_request("transfer", payload)
    if res.get("ok"):
        new_balance = round(user["balance"] - amount_dollars, 2)
        update_user(chat_id, balance=new_balance)
        text, kb = get_main_menu(get_user(chat_id))
        send_message(chat_id,
                     f"✅ <b>Выплата отправлена!</b>\n\n"
                     f"💰 Переведено: {amount_dollars}$ USDT\n"
                     f"📱 ID: <code>{target_tg_id}</code>\n"
                     f"💵 Новый баланс: <b>{new_balance}$</b>\n\n" + text, kb)
    else:
        error_obj = res.get("error")
        error_name = error_obj.get("name", "Unknown") if isinstance(error_obj, dict) else str(error_obj)
        err_msg = "Ошибка шлюза."
        if error_name == "USER_NOT_FOUND":
            err_msg = "Пользователь не найден. Ему нужно открыть @CryptoBot."
        elif error_name == "NOT_ENOUGH_FUNDS":
            err_msg = "На балансе приложения в CryptoBot не хватает денег."
        elif error_name == "FORBIDDEN" or "403" in str(error_name):
            err_msg = "Вывод отключён в настройках приложения CryptoBot (включите Transfer)."
        send_message(chat_id, f"❌ <b>Ошибка выплаты!</b>\n\n<i>{err_msg} ({error_name})</i>",
                     {"inline_keyboard": [[{"text": "⬅️ Назад", "callback_data": "profile"}]]})


# ============================================================
# ХРАНИЛИЩЕ
# ============================================================
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _default_user():
    return {"balance": 10.0, "wins": 0, "losses": 0, "last_bonus": 0,
            "name": "Игрок", "paid_invoices": []}


def get_user(uid):
    data = load_data()
    uid = str(uid)
    if uid not in data:
        data[uid] = _default_user()
        save_data(data)
    else:
        for k, v in _default_user().items():
            data[uid].setdefault(k, v)
    return data[uid]


def update_user(uid, **kwargs):
    data = load_data()
    uid = str(uid)
    if uid not in data:
        data[uid] = _default_user()
    data[uid].update(kwargs)
    save_data(data)


def mark_invoice_paid(uid, invoice_id):
    data = load_data()
    uid = str(uid)
    if uid not in data:
        data[uid] = _default_user()
    paid = data[uid].get("paid_invoices", [])
    inv = str(invoice_id)
    if inv in paid:
        return False
    paid.append(inv)
    data[uid]["paid_invoices"] = paid
    save_data(data)
    return True


# ============================================================
# МЕНЮ
# ============================================================
def get_main_menu(user):
    text = (f"👤 <b>{user.get('name','Игрок')}</b>\n"
            f"💰 Баланс: <b>{user['balance']}$</b> 💵\n"
            f"📈 Статистика: ✅ {user['wins']} | ❌ {user['losses']}\n\n"
            f"🎰 <b>Выберите игру или режим:</b>")
    kb = {"inline_keyboard": [
        [{"text": "🎲 (до x216)", "callback_data": "game_dice"}, {"text": "⚽ (до x25)", "callback_data": "game_football"}, {"text": "🏀 (до x25)", "callback_data": "game_basketball"}],
        [{"text": "🎯 (до x36)", "callback_data": "game_darts"}, {"text": "🎳 (до x36)", "callback_data": "game_bowling"}, {"text": "🎰 (до x40)", "callback_data": "game_slots"}],
        [{"text": "👨‍💻 Авторские", "callback_data": "game_custom"}, {"text": "🚀 Турбо", "callback_data": "game_turbo"}, {"text": "🃏 Mini-игры", "callback_data": "game_mini"}],
        [{"text": "💰 Баланс / Крипта", "callback_data": "profile"}, {"text": "🎁 Бонус", "callback_data": "bonus"}, {"text": "💎 Купить $", "callback_data": "shop"}],
    ]}
    return text, kb


def get_profile_menu(user):
    text = (f"👤 <b>Личный кабинет: {user.get('name','Игрок')}</b>\n\n"
            f"💰 Игровой баланс: <b>{user['balance']}$</b> 💵\n"
            f"✅ Побед: {user['wins']}\n"
            f"❌ Поражений: {user['losses']}\n\n"
            f"Пополнение и вывод USDT через CryptoBot:")
    kb = {"inline_keyboard": [
        [{"text": "➕ Пополнить (Крипта)", "callback_data": "crypto_deposit"}, {"text": "➖ Вывести (Крипта)", "callback_data": "crypto_withdraw"}],
        [{"text": "⬅️ Назад", "callback_data": "main_menu"}],
    ]}
    return text, kb


def get_crypto_deposit_menu():
    return "💳 <b>Выберите сумму пополнения в USDT ($):</b>", {"inline_keyboard": [
        [{"text": "10$", "callback_data": "cryptodep_10"}, {"text": "50$", "callback_data": "cryptodep_50"}],
        [{"text": "100$", "callback_data": "cryptodep_100"}, {"text": "500$", "callback_data": "cryptodep_500"}],
        [{"text": "⬅️ Назад", "callback_data": "profile"}],
    ]}


def get_crypto_withdraw_menu(user):
    bal = round(float(user["balance"]), 2)
    return (f"💵 <b>Выберите сумму для вывода USDT:</b>\n\nДоступно: <b>{bal}$</b>",
            {"inline_keyboard": [
                [{"text": "10$", "callback_data": "cryptowd_10"}, {"text": "50$", "callback_data": "cryptowd_50"}],
                [{"text": "100$", "callback_data": "cryptowd_100"}, {"text": "Все средства", "callback_data": f"cryptowd_{bal}"}],
                [{"text": "⬅️ Назад", "callback_data": "profile"}],
            ]})


def get_shop_menu(user):
    return (f"💎 <b>Магазин валюты</b>\n\nБаланс: <b>{user['balance']}$</b> 💵\n\nВыберите пакет:",
            {"inline_keyboard": [
                [{"text": "100$ за 10 ⭐", "callback_data": "buy_100_10"}],
                [{"text": "500$ за 40 ⭐", "callback_data": "buy_500_40"}],
                [{"text": "1000$ за 70 ⭐", "callback_data": "buy_1000_70"}],
                [{"text": "⬅️ Назад", "callback_data": "main_menu"}],
            ]})


def get_bet_menu(user, game):
    names = {"dice": "🎲 Дайс", "darts": "🎯 Дартс", "football": "⚽ Футбол",
             "basketball": "🏀 Баскет", "bowling": "🎳 Боулинг", "slots": "🎰 Слоты",
             "custom": "👨‍💻 Авторские", "turbo": "🚀 Турбо", "mini": "🃏 Мини-игры"}
    max_bet = round(float(user["balance"]), 2)
    text = (f"👤 <b>{user.get('name','Игрок')}</b>\n"
            f"💰 Баланс: <b>{user['balance']}$</b> 💵\n"
            f"🎮 Игра: <b>{names.get(game, game)}</b>\n\n"
            f"👇 <b>Выберите ставку:</b>")
    kb = {"inline_keyboard": [
        [{"text": "10$", "callback_data": f"bet_{game}_10"}, {"text": "50$", "callback_data": f"bet_{game}_50"}, {"text": "100$", "callback_data": f"bet_{game}_100"}],
        [{"text": "500$", "callback_data": f"bet_{game}_500"}, {"text": "✍️ Своя", "callback_data": f"custom_{game}"}, {"text": "Макс", "callback_data": f"bet_{game}_{max_bet}"}],
        [{"text": "⬅️ Назад", "callback_data": "main_menu"}],
    ]}
    return text, kb


def get_choice_menu(user, game, bet):
    text = (f"👤 <b>{user.get('name','Игрок')}</b>\n"
            f"💰 Баланс: <b>{user['balance']}$</b> 💵\n"
            f"💵 Ставка: <b>{bet}$</b>\n\n🎯 <b>На что ставим?</b>")
    kb = []
    if game == "dice":
        kb = [
            [{"text": "1 (x5)", "callback_data": f"res_dice_{bet}_1"}, {"text": "2 (x5)", "callback_data": f"res_dice_{bet}_2"}, {"text": "3 (x5)", "callback_data": f"res_dice_{bet}_3"}],
            [{"text": "4 (x5)", "callback_data": f"res_dice_{bet}_4"}, {"text": "5 (x5)", "callback_data": f"res_dice_{bet}_5"}, {"text": "6 (x5)", "callback_data": f"res_dice_{bet}_6"}],
            [{"text": "⬆️ Больше 3 (x2)", "callback_data": f"res_dice_{bet}_high"}],
            [{"text": "⬇️ Меньше 4 (x2)", "callback_data": f"res_dice_{bet}_low"}],
        ]
    elif game == "turbo":
        kb = [
            [{"text": "3 кубика (>10) x3", "callback_data": f"res_dice_{bet}_three_high"}],
            [{"text": "Три шестёрки (x50)", "callback_data": f"res_dice_{bet}_three_six"}],
            [{"text": "Все > 3 (x5)", "callback_data": f"res_turbo_{bet}_turbo_high"}],
            [{"text": "Все < 4 (x5)", "callback_data": f"res_turbo_{bet}_turbo_low"}],
        ]
    elif game == "custom":
        kb = [
            [{"text": "🔥 Мега-Джекпот (x10)", "callback_data": f"res_custom_{bet}_jackpot"}],
            [{"text": "💀 Смертельная (x15)", "callback_data": f"res_custom_{bet}_death"}],
        ]
    elif game == "mini":
        kb = [
            [{"text": "🦅 Орёл (x2)", "callback_data": f"res_mini_{bet}_heads"}],
            [{"text": "🪙 Решка (x2)", "callback_data": f"res_mini_{bet}_tails"}],
        ]
    elif game == "football":
        kb = [[{"text": "✅ Гол (x1.5)", "callback_data": f"res_football_{bet}_goal"}],
              [{"text": "❌ Мимо (x2.5)", "callback_data": f"res_football_{bet}_miss"}]]
    elif game == "basketball":
        kb = [[{"text": "🏀 2 очка (x1.5)", "callback_data": f"res_basketball_{bet}_2pt"}],
              [{"text": "🏀 3 очка (x3)", "callback_data": f"res_basketball_{bet}_3pt"}]]
    elif game == "darts":
        kb = [[{"text": "🎯 В яблочко (x3)", "callback_data": f"res_darts_{bet}_bull"}],
              [{"text": "❌ Мимо (x1.5)", "callback_data": f"res_darts_{bet}_miss"}]]
    elif game == "slots":
        text = (f"👤 <b>{user.get('name','Игрок')}</b>\n"
                f"💰 Баланс: <b>{user['balance']}$</b> 💵\n"
                f"💵 Ставка: <b>{bet}$</b>\n\n🎰 <b>Выберите символ:</b>")
        kb = [
            [{"text": "🍋 Лимон (x16)", "callback_data": f"res_slots_{bet}_lemon"}],
            [{"text": "🍒 Вишня (x16)", "callback_data": f"res_slots_{bet}_cherry"}],
            [{"text": "💎 Алмаз (x16)", "callback_data": f"res_slots_{bet}_diamond"}],
            [{"text": "7️⃣ Семёрка (x16)", "callback_data": f"res_slots_{bet}_seven"}],
            [{"text": "❌ Не 3 в ряд (x2)", "callback_data": f"res_slots_{bet}_lose"}],
        ]
    elif game == "bowling":
        kb = [
            [{"text": "🎳 Страйк (x5)", "callback_data": f"res_bowling_{bet}_strike"},
             {"text": "🎯 7-9 (x2.5)", "callback_data": f"res_bowling_{bet}_high"}],
            [{"text": "⚪ 1-3 (x1.5)", "callback_data": f"res_bowling_{bet}_low"},
             {"text": "❌ Промах (x4)", "callback_data": f"res_bowling_{bet}_miss"}],
        ]
    kb.append([{"text": "⬅️ Назад", "callback_data": f"game_{game}"}])
    return text, {"inline_keyboard": kb}
# ============================================================
# ИГРЫ
# ============================================================
def resolve_game(chat_id, game, bet, choice):
    win, multiplier, res_detail = False, 1.0, ""

    if game == "slots":
        symbols = ["🍋", "🍒", "💎", "7️⃣"]
        results = [random.choice(symbols) for _ in range(3)]
        res_detail = f"🎰 Результат: {' '.join(results)}\n"
        if choice == "lose":
            if not (results[0] == results[1] == results[2]):
                win, multiplier = True, 2.0
        else:
            target = {"lemon": "🍋", "cherry": "🍒", "diamond": "💎", "seven": "7️⃣"}.get(choice)
            if target and results[0] == results[1] == results[2] == target:
                win, multiplier = True, 16.0

    elif game in ("dice", "turbo"):
        if choice in ("three_high", "three_six"):
            d1, d2, d3 = random.randint(1, 6), random.randint(1, 6), random.randint(1, 6)
            send_dice_result(chat_id, "🎲", d1); time.sleep(0.5)
            send_dice_result(chat_id, "🎲", d2); time.sleep(0.5)
            send_dice_result(chat_id, "🎲", d3); time.sleep(0.5)
            total = d1 + d2 + d3
            res_detail = f"Выпало: {d1}, {d2}, {d3} (Сумма: {total})\n"
            if choice == "three_high" and total > 10:
                win, multiplier = True, 3.0
            elif choice == "three_six" and d1 == d2 == d3 == 6:
                win, multiplier = True, 50.0
        elif choice in ("turbo_high", "turbo_low"):
            d1, d2, d3 = random.randint(1, 6), random.randint(1, 6), random.randint(1, 6)
            send_dice_result(chat_id, "🎲", d1); time.sleep(0.5)
            send_dice_result(chat_id, "🎲", d2); time.sleep(0.5)
            send_dice_result(chat_id, "🎲", d3); time.sleep(0.5)
            res_detail = f"Выпало: {d1}, {d2}, {d3}\n"
            if choice == "turbo_high" and d1 > 3 and d2 > 3 and d3 > 3:
                win, multiplier = True, 5.0
            elif choice == "turbo_low" and d1 < 4 and d2 < 4 and d3 < 4:
                win, multiplier = True, 5.0
        else:
            val = random.randint(1, 6)
            send_dice_result(chat_id, "🎲", val); time.sleep(1)
            res_detail = f"Выпало: {val}\n"
            if choice.isdigit() and int(choice) == val:
                win, multiplier = True, 5.0
            elif choice == "high" and val > 3:
                win, multiplier = True, 2.0
            elif choice == "low" and val < 4:
                win, multiplier = True, 2.0

    elif game == "custom":
        val = random.randint(1, 100)
        send_dice_result(chat_id, "🎲", val); time.sleep(1)
        res_detail = f"Рулетка судьбы: {val}/100\n"
        if choice == "jackpot" and val > 90:
            win, multiplier = True, 10.0
        elif choice == "death" and val > 95:
            win, multiplier = True, 15.0

    elif game == "mini":
        val = random.choice(["heads", "tails"])
        emoji_val = "🦅 Орёл" if val == "heads" else "🪙 Решка"
        send_message(chat_id, emoji_val); time.sleep(1)
        res_detail = f"Выпало: {emoji_val}\n"
        if choice == val:
            win, multiplier = True, 2.0

    elif game == "football":
        val = random.randint(1, 5)
        send_dice_result(chat_id, "⚽", val); time.sleep(1)
        res_detail = f"Результат удара: {val}/5\n"
        if choice == "goal" and val >= 3:
            win, multiplier = True, 1.5
        elif choice == "miss" and val < 3:
            win, multiplier = True, 2.5

    elif game == "basketball":
        val = random.randint(1, 10)
        send_dice_result(chat_id, "🏀", val); time.sleep(1)
        res_detail = f"Бросок: {val}/10\n"
        if choice == "2pt" and val <= 6:
            win, multiplier = True, 1.5
        elif choice == "3pt" and val > 6:
            win, multiplier = True, 3.0

    elif game == "darts":
        val = random.randint(1, 6)
        send_dice_result(chat_id, "🎯", val); time.sleep(1)
        res_detail = f"Сектор: {val}/6\n"
        if choice == "bull" and val == 1:
            win, multiplier = True, 3.0
        elif choice == "miss" and val > 1:
            win, multiplier = True, 1.5

    elif game == "bowling":
        val = random.choices([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                             weights=[15, 5, 10, 15, 15, 10, 10, 5, 5, 3, 7])[0]
        send_dice_result(chat_id, "🎳", val); time.sleep(1)
        res_detail = f"Сбито кеглей: {val}/10\n"
        if choice == "strike" and val == 10:
            win, multiplier = True, 5.0
        elif choice == "high" and 7 <= val <= 9:
            win, multiplier = True, 2.5
        elif choice == "low" and 1 <= val <= 3:
            win, multiplier = True, 1.5
        elif choice == "miss" and val == 0:
            win, multiplier = True, 4.0

    return win, multiplier, res_detail


# ============================================================
# MAIN LOOP — часть 1: старт, платежи, callback
# ============================================================
print("Бот запущен...")
offset = 0
user_states = {}

while True:
    try:
        url = f"{TG_API}/getUpdates?timeout=30&offset={offset}"
        updates = json.loads(urllib.request.urlopen(url, timeout=40).read().decode("utf-8"))
        if not updates.get("ok"):
            time.sleep(2)
            continue

        for update in updates["result"]:
            offset = update["update_id"] + 1

            if "pre_checkout_query" in update:
                api_request("answerPreCheckoutQuery", {
                    "pre_checkout_query_id": update["pre_checkout_query"]["id"], "ok": True})
                continue

            if "message" in update and "successful_payment" in update["message"]:
                msg = update["message"]
                chat_id = msg["chat"]["id"]
                user_id = msg["from"]["id"]
                payload = msg["successful_payment"].get("invoice_payload", "")
                try:
                    if payload.startswith("stars:"):
                        dollars = int(payload.split(":")[1])
                    else:
                        dollars = int(payload.split("_")[1])
                    user = get_user(user_id)
                    new_bal = round(user["balance"] + dollars, 2)
                    update_user(user_id, balance=new_bal)
                    send_message(chat_id, f"✅ Оплата прошла!\nНачислено: <b>{dollars}$</b>\nБаланс: {new_bal}$")
                except Exception as e:
                    print("successful_payment:", e)
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

                if user_id in user_states and not data.startswith("res_"):
                    del user_states[user_id]

                try:
                    if data in ("main_menu", "menu"):
                        t, k = get_main_menu(user)
                        edit_message(chat_id, msg_id, t, k)
                    elif data == "shop":
                        t, k = get_shop_menu(user)
                        edit_message(chat_id, msg_id, t, k)
                    elif data.startswith("buy_"):
                        p = data.split("_")
                        send_stars_invoice(chat_id, msg_id, int(p[2]), int(p[1]))
                    elif data == "profile":
                        t, k = get_profile_menu(user)
                        edit_message(chat_id, msg_id, t, k)
                    elif data == "crypto_deposit":
                        t, k = get_crypto_deposit_menu()
                        edit_message(chat_id, msg_id, t, k)
                    elif data.startswith("cryptodep_"):
                        amount = int(data.split("_")[1])
                        if amount in DEPOSIT_AMOUNTS:
                            create_crypto_invoice(chat_id, msg_id, amount)
                        else:
                            send_message(chat_id, "❌ Неверная сумма.")
                    elif data.startswith("check_dep_"):
                        invoice_id = data.split("_")[2]
                        res = crypto_api_request("getInvoices", {"invoice_ids": str(invoice_id)})
                        is_paid, dep_amount = False, 0.0
                        if res.get("ok") and res.get("result", {}).get("items"):
                            inv = res["result"]["items"][0]
                            if inv.get("status") == "paid":
                                is_paid = True
                                dep_amount = float(inv["amount"])
                        if is_paid:
                            if mark_invoice_paid(user_id, invoice_id):
                                new_bal = round(user["balance"] + dep_amount, 2)
                                update_user(user_id, balance=new_bal)
                                send_message(chat_id, f"✅ Баланс пополнен на {dep_amount}$!")
                            else:
                                send_message(chat_id, "ℹ️ Этот счёт уже был зачислен.")
                            t, k = get_profile_menu(get_user(user_id))
                            edit_message(chat_id, msg_id, t, k)
                        else:
                            send_message(chat_id, "❌ Оплата не найдена. Сначала оплатите счёт.")
                    elif data == "crypto_withdraw":
                        t, k = get_crypto_withdraw_menu(user)
                        edit_message(chat_id, msg_id, t, k)
                    elif data.startswith("cryptowd_"):
                        amount = float(data.split("_")[1])
                        if user["balance"] < amount or amount <= 0:
                            send_message(chat_id, "❌ Недостаточно средств!")
                        else:
                            user_states[user_id] = ("wait_payout_id", amount, msg_id)
                            edit_message(chat_id, msg_id,
                                         f"📤 <b>Вывод: {amount}$ USDT</b>\n\n"
                                         f"Отправьте ваш <b>Telegram ID</b> получателя.\n"
                                         f"<i>ID должен быть зарегистрирован в @CryptoBot!</i>",
                                         {"inline_keyboard": [[{"text": "Отмена", "callback_data": "profile"}]]})
                    elif data == "bonus":
                        now = int(time.time())
                        if user.get("last_bonus") and now - user["last_bonus"] < BONUS_COOLDOWN:
                            left = BONUS_COOLDOWN - (now - user["last_bonus"])
                            text = f"⏳ Бонус уже получен.\nЖдать: {left//3600}ч {(left%3600)//60}м"
                            edit_message(chat_id, msg_id, text,
                                         {"inline_keyboard": [[{"text": "⬅️ Назад", "callback_data": "main_menu"}]]})
                        else:
                            new_bal = round(user["balance"] + BONUS_AMOUNT, 2)
                            update_user(user_id, balance=new_bal, last_bonus=now)
                            text = f"🎁 Бонус +{BONUS_AMOUNT}$!\nВаш баланс: {new_bal}$ 💵"
                            edit_message(chat_id, msg_id, text,
                                         {"inline_keyboard": [[{"text": "⬅️ Назад", "callback_data": "main_menu"}]]})
                    elif data.startswith("game_"):
                        game = data.split("_", 1)[1]
                        t, k = get_bet_menu(user, game)
                        edit_message(chat_id, msg_id, t, k)
                    elif data.startswith("custom_"):
                        game = data.split("_", 1)[1]
                        user_states[user_id] = (game, msg_id)
                        edit_message(chat_id, msg_id,
                                     f"✍️ Напишите сумму ставки в чат (от {MIN_BET} до {user['balance']}):",
                                     {"inline_keyboard": [[{"text": "Отмена", "callback_data": f"game_{game}"}]]})
                    elif data.startswith("bet_"):
                        parts = data.split("_")
                        game = parts[1]
                        try:
                            bet = float(parts[2])
                        except ValueError:
                            bet = 0
                        if bet > user["balance"] or bet < MIN_BET:
                            edit_message(chat_id, msg_id,
                                         f"❌ Неверная ставка (мин. {MIN_BET}) или недостаточно средств!",
                                         {"inline_keyboard": [[{"text": "⬅️ Назад", "callback_data": f"game_{game}"}]]})
                        else:
                            t, k = get_choice_menu(user, game, bet)
                            edit_message(chat_id, msg_id, t, k)
                    elif data.startswith("res_"):
                        parts = data.split("_")
                        game = parts[1] if len(parts) > 1 else ""
                        try:
                            bet = float(parts[2]) if len(parts) > 2 else 0
                        except ValueError:
                            bet = 0
                        choice = parts[3] if len(parts) > 3 else ""

                        if bet > user["balance"] or bet < MIN_BET:
                            edit_message(chat_id, msg_id, "❌ Ставка недействительна.",
                                         {"inline_keyboard": [[{"text": "⬅️ Назад", "callback_data": "main_menu"}]]})
                            continue

                        edit_message(chat_id, msg_id, f"🎰 Крутим... Ставка: {bet}$", None)
                        win, multiplier, res_detail = resolve_game(chat_id, game, bet, choice)

                        if win:
                            win_amount = round(bet * multiplier, 2)
                            profit = round(win_amount - bet, 2)
                            new_bal = round(user["balance"] + profit, 2)
                            update_user(user_id, balance=new_bal, wins=user["wins"] + 1)
                            res_text = (f"🎉 <b>Победа!</b>\n{res_detail}"
                                        f"💵 Выплата: <b>+{win_amount}$</b> (включая ставку)\n"
                                        f"📈 Чистая прибыль: <b>+{profit}$</b>\n\n")
                        else:
                            new_bal = round(user["balance"] - bet, 2)
                            update_user(user_id, balance=new_bal, losses=user["losses"] + 1)
                            res_text = f"😢 <b>Проигрыш.</b>\n{res_detail}Потеряно: <b>-{bet}$</b>\n\n"

                        text, kb = get_main_menu(get_user(user_id))
                        send_message(chat_id, res_text + text, kb)

                except Exception as e:
                    print("Callback error:", e)
                continue

            # --- TEXT MESSAGE ---
            if "message" in update and "text" in update["message"]:
                msg = update["message"]
                chat_id = msg["chat"]["id"]
                text_str = msg["text"].strip()
                user_id = msg["from"]["id"]
                first_name = msg["from"].get("first_name", "Игрок")
                user = get_user(user_id)
                update_user(user_id, name=first_name)

                if not text_str:
                    continue

                cmd = text_str.lower().split()[0]
                if cmd in ("/start", "/help"):
                    user_states.pop(user_id, None)
                    t, k = get_main_menu(get_user(user_id))
                    send_message(chat_id, t, k)
                    continue

                state_info = user_states.get(user_id)
                if state_info:
                    if isinstance(state_info, tuple) and state_info[0] == "wait_payout_id":
                        _, amount, state_msg_id = state_info
                        if text_str.isdigit():
                            target_id = int(text_str)
                            del user_states[user_id]
                            send_message(chat_id, "⏳ Выполняется транзакция...")
                            send_crypto_payout(chat_id, state_msg_id, amount, target_id)
                        else:
                            send_message(chat_id, "❌ ID должен состоять только из цифр. Повторите ввод:")
                        continue

                    elif isinstance(state_info, tuple):
                        game, state_msg_id = state_info
                try:
                            bet = float(text_str)
                except ValueError:
                            edit_message(chat_id, state_msg_id, "❌ Введите число цифрами:",
                                         {"inline_keyboard": [[{"text": "Отмена", "callback_data": f"game_{game}"}]]})
                            continue
                        if bet < MIN_BET:
                            edit_message(chat_id, state_msg_id,
                                         f"❌ Мин. ставка {MIN_BET}$. Введите другое число:",
                                         {"inline_keyboard": [[{"text": "Отмена", "callback_data": f"game_{game}"}]]})
                        elif bet > user["balance"]:
                            edit_message(chat_id, state_msg_id,
                                         f"❌ Недостаточно средств (Баланс: {user['balance']}$). Введите другое число:",
                                         {"inline_keyboard": [[{"text": "Отмена", "callback_data": f"game_{game}"}]]})
                        else:
                            del user_states[user_id]
                            t, k = get_choice_menu(user, game, bet)
                            edit_message(chat_id, state_msg_id, t, k)
                        continue

    except Exception as e:
        print("Main loop error:", e)
        time.sleep(2)
                            
