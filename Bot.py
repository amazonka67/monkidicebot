import urllib.request, json, time, random, os

BOT_TOKEN = os.environ.get("BOT_TOKEN", "9193782655:AAFP7mMmjbL4ITM--2LBuStvO0YcTTc9gOk")
CRYPTO_TOKEN = os.environ.get("CRYPTO_TOKEN", "673588:AAeEcZ2RWDF3cGjfiB0zZZaUjlguDytrdAD")
TG_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
CRYPTO_API = "https://pay.crypt.bot/api"

DATA_FILE = "users.json"
MIN_BET = 10

# --- УТИЛИТЫ И API ---
def tg(method, payload):
    req = urllib.request.Request(f"{TG_API}/{method}", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    try: return json.loads(urllib.request.urlopen(req, timeout=15).read().decode())
    except Exception as e: print(f"TG Error {method}: {e}")

def crypto(method, payload=None):
    req = urllib.request.Request(f"{CRYPTO_API}/{method}", data=json.dumps(payload).encode() if payload else None, headers={"Crypto-Pay-API-Token": CRYPTO_TOKEN, "Content-Type": "application/json"}, method="POST" if payload else "GET")
    try: return json.loads(urllib.request.urlopen(req, timeout=15).read().decode())
    except Exception as e: return {"ok": False, "error": str(e)}

def send(cid, txt, kb=None):
    return tg("sendMessage", {"chat_id": cid, "text": txt, "parse_mode": "HTML", "reply_markup": kb})

def edit(cid, mid, txt, kb=None):
    if not mid: return send(cid, txt, kb)
    return tg("editMessageText", {"chat_id": cid, "message_id": mid, "text": txt, "parse_mode": "HTML", "reply_markup": kb})

def btn(t, d=None, u=None): return {"text": t, "callback_data": d} if d else {"text": t, "url": u}
def kb(*rows): return {"inline_keyboard": [list(r) for r in rows]}

# --- БАЗА ДАННЫХ ---
def get_user(uid):
    data = json.load(open(DATA_FILE, "r", encoding="utf-8")) if os.path.exists(DATA_FILE) else {}
    uid = str(uid)
    if uid not in data: data[uid] = {"balance": 10.0, "wins": 0, "losses": 0, "last_bonus": 0, "name": "Игрок", "paid": []}
    return data[uid]

def save_user(uid, **kwargs):
    data = json.load(open(DATA_FILE, "r", encoding="utf-8")) if os.path.exists(DATA_FILE) else {}
    uid = str(uid)
    if uid not in data: data[uid] = {}
    data[uid].update(kwargs)
    json.dump(data, open(DATA_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# --- ИНТЕРФЕЙС ---
def menu_main(u):
    return f"👤 <b>{u['name']}</b>\n💰 Баланс: <b>{u['balance']}$</b>\n✅ {u['wins']} | ❌ {u['losses']}\n\n🎰 <b>Игры:</b>", kb(
        (btn("🎲 Дайс", "game_dice"), btn("⚽ Футбол", "game_football"), btn("🏀 Баскет", "game_basketball")),
        (btn("🎯 Дартс", "game_darts"), btn("🎳 Боулинг", "game_bowling"), btn("🎰 Слоты", "game_slots")),
        (btn("👨‍💻 Авторские", "game_custom"), btn("🚀 Турбо", "game_turbo"), btn("🃏 Mini", "game_mini")),
        (btn("💰 Баланс", "profile"), btn("🎁 Бонус", "bonus"), btn("💎 Купить $", "shop"))
    )

def menu_choice(g, bet, bal):
    t = f"💵 Ставка: <b>{bet}$</b>\n🎯 <b>На что ставим?</b>"
    if g == 'dice': r = [[btn(str(i), f"res_dice_{bet}_{i}") for i in range(1,4)], [btn(str(i), f"res_dice_{bet}_{i}") for i in range(4,7)], [btn("⬆️ >3 (x2)", f"res_dice_{bet}_high"), btn("⬇️ <4 (x2)", f"res_dice_{bet}_low")]]
    elif g == 'turbo': r = [[btn("3 кубика (>10) x3", f"res_dice_{bet}_three_high")], [btn("Три шестёрки (x50)", f"res_dice_{bet}_three_six")], [btn("Все > 3 (x5)", f"res_turbo_{bet}_turbo_high")], [btn("Все < 4 (x5)", f"res_turbo_{bet}_turbo_low")]]
    elif g == 'custom': r = [[btn("🔥 Джекпот (x10)", f"res_custom_{bet}_jackpot")], [btn("💀 Смертельная (x15)", f"res_custom_{bet}_death")]]
    elif g == 'mini': r = [[btn("🦅 Орёл", f"res_mini_{bet}_heads"), btn("🪙 Решка", f"res_mini_{bet}_tails")]]
    elif g == 'football': r = [[btn("✅ Гол (x1.5)", f"res_football_{bet}_goal")], [btn("❌ Мимо (x2.5)", f"res_football_{bet}_miss")]]
    elif g == 'basketball': r = [[btn("🏀 2 очка (x1.5)", f"res_basketball_{bet}_2pt")], [btn("🏀 3 очка (x3)", f"res_basketball_{bet}_3pt")]]
    elif g == 'darts': r = [[btn("🎯 В яблочко (x3)", f"res_darts_{bet}_bull")], [btn("❌ Мимо (x1.5)", f"res_darts_{bet}_miss")]]
    elif g == 'slots': r = [[btn(f"{s} ({n})", f"res_slots_{bet}_{k}")] for s, n, k in [("🍋 Лимон","x16","lemon"), ("🍒 Вишня","x16","cherry"), ("💎 Алмаз","x16","diamond"), ("7️⃣ Семёрка","x16","seven"), ("❌ Не 3 в ряд","x2","lose")]]
    elif g == 'bowling': r = [[btn("🎳 Страйк (x5)", f"res_bowling_{bet}_strike"), btn("🎯 7-9 (x2.5)", f"res_bowling_{bet}_high")], [btn("⚪ 1-3 (x1.5)", f"res_bowling_{bet}_low"), btn("❌ Промах (x4)", f"res_bowling_{bet}_miss")]]
    r.append([btn("⬅️ Назад", f"game_{g}")])
    return t, kb(*r)

# --- ЛОГИКА ИГР ---
def play(g, choice, bet):
    if g == 'slots':
        res = [random.choice("🍋🍒💎7️⃣") for _ in range(3)]
        m = {'lemon':'🍋','cherry':'🍒','diamond':'💎','seven':'7️⃣'}.get(choice)
        w = (choice == 'lose' and len(set(res)) > 1) or (m and res == [m]*3)
        return w, (16.0 if m else 2.0), f"🎰 {' '.join(res)}"
    if g in ('dice', 'turbo'):
        if choice in ('1','2','3','4','5','6','high','low'):
            v = random.randint(1,6)
            w = (choice == str(v)) or (choice == 'high' and v > 3) or (choice == 'low' and v < 4)
            return w, (5.0 if choice.isdigit() else 2.0), f"🎲 Выпало: {v}"
        d = [random.randint(1,6) for _ in range(3)]
        w = (choice=='three_high' and sum(d)>10) or (choice=='three_six' and sum(d)==18) or (choice=='turbo_high' and all(x>3 for x in d)) or (choice=='turbo_low' and all(x<4 for x in d))
        return w, {'three_high':3.0, 'three_six':50.0, 'turbo_high':5.0, 'turbo_low':5.0}[choice], f"🎲 {d[0]} {d[1]} {d[2]}"
    if g == 'custom':
        v = random.randint(1,100)
        return (choice=='jackpot' and v>90) or (choice=='death' and v>95), (10.0 if choice=='jackpot' else 15.0), f"🎲 {v}/100"
    if g == 'mini':
        v = random.choice(['heads','tails'])
        return choice == v, 2.0, f"Выпало: {'Орел' if v=='heads' else 'Решка'}"
    if g == 'football':
        v = random.randint(1,5)
        return (choice=='goal' and v>=3) or (choice=='miss' and v<3), (1.5 if choice=='goal' else 2.5), f"⚽ {v}/5"
    if g == 'basketball':
        v = random.randint(1,10)
        return (choice=='2pt' and v<=6) or (choice=='3pt' and v>6), (1.5 if choice=='2pt' else 3.0), f"🏀 {v}/10"
    if g == 'darts':
        v = random.randint(1,6)
        return (choice=='bull' and v==1) or (choice=='miss' and v>1), (3.0 if choice=='bull' else 1.5), f"🎯 {v}/6"
    if g == 'bowling':
        v = random.choices(range(11), weights=[15,5,10,15,15,10,10,5,5,3,7])[0]
        w = (choice=='strike' and v==10) or (choice=='high' and 7<=v<=9) or (choice=='low' and 1<=v<=3) or (choice=='miss' and v==0)
        return w, {'strike':5.0, 'high':2.5, 'low':1.5, 'miss':4.0}[choice], f"🎳 {v}/10"

# --- ОБРАБОТЧИКИ ---
def on_cb(cb):
    data, cid, mid, uid = cb["data"], cb["message"]["chat"]["id"], cb["message"]["message_id"], cb["from"]["id"]
    tg("answerCallbackQuery", {"callback_query_id": cb["id"]})
    u = get_user(uid)

    if data in ("main_menu", "menu"): edit(cid, mid, *menu_main(u))
    elif data == "profile":
        edit(cid, mid, f"👤 <b>Кабинет: {u['name']}</b>\n💰 Баланс: <b>{u['balance']}$</b>\n\nПополнение/вывод USDT:", kb((btn("➕ Пополнить", "crypto_deposit"), btn("➖ Вывести", "crypto_withdraw")), (btn("⬅️ Назад", "main_menu"),)))
    elif data == "shop":
        edit(cid, mid, "💎 <b>Магазин:</b>", kb((btn("100$ за 10 ⭐", "buy_100_10"),), (btn("500$ за 40 ⭐", "buy_500_40"),), (btn("1000$ за 70 ⭐", "buy_1000_70"),), (btn("⬅️ Назад", "main_menu"),)))
    elif data.startswith("buy_"):
        p = data.split("_"); 
        res = tg("createInvoiceLink", {"title": f"Покупка {p[1]}$", "payload": f"stars:{p[1]}:{p[2]}", "currency": "XTR", "prices": [{"label": f"{p[1]}$", "amount": int(p[2])}]})
        if res.get("ok"): edit(cid, mid, "👇 Оплатите:", kb((btn(f"💎 Оплатить {p[2]} Stars", u=res["result"]),), (btn("⬅️ Назад", "shop"),)))
    elif data == "crypto_deposit":
        edit(cid, mid, "💳 <b>Сумма пополнения:</b>", kb((btn("10$", "cryptodep_10"), btn("50$", "cryptodep_50"), btn("100$", "cryptodep_100")), (btn("⬅️ Назад", "profile"),)))
    elif data.startswith("cryptodep_"):
        amt = data.split("_")[1]
        res = crypto("createInvoice", {"asset": "USDT", "amount": amt, "payload": f"dep_{uid}_{time.time()}"})
        if res.get("ok"): edit(cid, mid, f"⚡️ Счёт на {amt}$ создан:", kb((btn(f"💳 Оплатить {amt}$", u=res["result"]["pay_url"]),), (btn("🔄 Проверить", f"check_{res['result']['invoice_id']}"),), (btn("⬅️ Назад", "profile"),)))
    elif data.startswith("check_"):
        inv = data.split("_")[1]
        res = crypto("getInvoices", {"invoice_ids": str(inv)})
        if res.get("ok") and res["result"]["items"] and res["result"]["items"][0]["status"] == "paid":
            if str(inv) not in u["paid"]:
                amt = float(res["result"]["items"][0]["amount"])
                u["paid"].append(str(inv))
                save_user(uid, balance=round(u["balance"]+amt,2), paid=u["paid"])
                send(cid, f"✅ Баланс пополнен на {amt}$!")
            else: send(cid, "ℹ️ Уже зачислено.")
        else: send(cid, "❌ Оплата не найдена.")
    elif data == "crypto_withdraw":
        edit(cid, mid, f"💵 Выберите сумму (Доступно: {round(u['balance'],2)}$):", kb((btn("10$", "wd_10"), btn("50$", "wd_50"), btn("Все", f"wd_{round(u['balance'],2)}")), (btn("⬅️ Назад", "profile"),)))
    elif data.startswith("wd_"):
        amt = float(data.split("_")[1])
        if 0 < amt <= u["balance"]:
            states[uid] = ("wd", amt, mid)
            edit(cid, mid, f"📤 Вывод {amt}$. Отправьте Telegram ID получателя:", kb((btn("Отмена", "profile"),)))
    elif data == "bonus":
        if time.time() - u.get("last_bonus", 0) < 86400: send(cid, "⏳ Уже получен.")
        else:
            save_user(uid, balance=round(u["balance"]+5,2), last_bonus=time.time())
            edit(cid, mid, f"🎁 Бонус +5$! Баланс: {round(u['balance']+5,2)}$")
    elif data.startswith("game_"): edit(cid, mid, f"🎮 Игра: <b>{data[5:]}</b>\n👇 Ставка:", kb((btn("10$", f"bet_{data[5:]}_10"), btn("50$", f"bet_{data[5:]}_50"), btn("100$", f"bet_{data[5:]}_100")), (btn("✍️ Своя", f"custom_{data[5:]}"), btn("Макс", f"bet_{data[5:]}_{round(u['balance'],2)}")), (btn("⬅️ Назад", "main_menu"),)))
    elif data.startswith("custom_"):
        states[uid] = (data[7:], mid)
        edit(cid, mid, f"✍️ Введите сумму (от {MIN_BET} до {u['balance']}):", kb((btn("Отмена", "main_menu"),)))
    elif data.startswith("bet_"):
        p = data.split("_"); b = float(p[2])
        if MIN_BET <= b <= u["balance"]: edit(cid, mid, *menu_choice(p[1], b, u["balance"]))
        else: send(cid, f"❌ Ставка от {MIN_BET}$ до {u['balance']}$")
    elif data.startswith("res_"):
        p = data.split("_"); g, b = p[1], float(p[2])
        if MIN_BET <= b <= u["balance"]:
            edit(cid, mid, f"🎰 Крутим... {b}$")
            w, m, det = play(g, p[3], b)
            prof = round(b*m - b, 2) if w else -b
            save_user(uid, balance=round(u["balance"]+prof,2), wins=u["wins"]+(1 if w else 0), losses=u["losses"]+(0 if w else 1))
            res = f"{'🎉 Победа!' if w else '😢 Проигрыш.'}\n{det}\n💰 {'+' if w else ''}{prof}$\n\n"
            t, k = menu_main(get_user(uid)); send(cid, res + t, k)

def on_msg(msg):
    cid, txt, uid = msg["chat"]["id"], msg["text"].strip(), msg["from"]["id"]
    u = get_user(uid)
    save_user(uid, name=msg["from"].get("first_name", "Игрок"))
    if txt.startswith("/start"):
        states.pop(uid, None)
        return send(cid, *menu_main(get_user(uid)))
    
    st = states.get(uid)
    if not st: return
    if st[0] == "wd" and txt.isdigit():
        del states[uid]; send(cid, "⏳ Отправляем...")
        res = crypto("transfer", {"user_id": int(txt), "asset": "USDT", "amount": str(st[1]), "spend_id": f"p_{uid}_{time.time()}"})
        if res.get("ok"):
            save_user(uid, balance=round(u["balance"]-st[1],2))
            send(cid, f"✅ Выплата {st[1]}$ отправлена!", menu_main(get_user(uid))[1])
        else: send(cid, f"❌ Ошибка: {res.get('error')}")
    elif isinstance(st[0], str):
        try: b = float(txt)
        except: return edit(cid, st[1], "❌ Введите число:")
        if not (MIN_BET <= b <= u["balance"]): return edit(cid, st[1], f"❌ От {MIN_BET} до {u['balance']}$")
        del states[uid]
        edit(cid, st[1], *menu_choice(st[0], b, u["balance"]))

# --- ЗАПУСК ---
print("Бот запущен...")
offset, states = 0, {}
while True:
    try:
        upd = json.loads(urllib.request.urlopen(f"{TG_API}/getUpdates?timeout=30&offset={offset}", timeout=40).read().decode())
        for u in upd.get("result", []):
            offset = u["update_id"] + 1
            if "pre_checkout_query" in u: tg("answerPreCheckoutQuery", {"pre_checkout_query_id": u["pre_checkout_query"]["id"], "ok": True})
            elif "message" in u and "successful_payment" in u["message"]:
                d = int(u["message"]["successful_payment"]["invoice_payload"].split(":")[1])
                usr = get_user(u["message"]["from"]["id"])
                save_user(u["message"]["from"]["id"], balance=round(usr["balance"]+d,2))
                send(u["message"]["chat"]["id"], f"✅ +{d}$")
            elif "callback_query" in u: on_cb(u["callback_query"])
            elif "message" in u and "text" in u["message"]: on_msg(u["message"])
    except Exception as e:
        print("Err:", e); time.sleep(2)
