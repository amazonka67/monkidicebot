@@ -109,7 +109,7 @@ def get_bet_menu(user, game):
    return text, kb

def get_count_menu(user, game, bet):
    text = f"👤 <b>{user['name']}</b>\n💰 Баланс: <b>{user['balance']}$</b> 💵\n💵 Ставка: <b>{bet}$</b>\n\n🎯 <b>Выберите количество:</b>"
    text = f"👤 <b>{user['name']}</b>\n💰 Баланс: <b>{user['balance']}$</b> 💵\n💵 Ставка: <b>{bet}$</b>\n\n🎯 <b>Сколько бросков?</b>"
    kb = {"inline_keyboard": [
        [{"text": "1 бросок", "callback_data": f"count_{game}_{bet}_1"}, {"text": "2 броска", "callback_data": f"count_{game}_{bet}_2"}, {"text": "3 броска", "callback_data": f"count_{game}_{bet}_3"}],
        [{"text": "⬅️ Назад", "callback_data": f"game_{game}"}]
@@ -119,19 +119,45 @@ def get_count_menu(user, game, bet):
def get_outcome_menu(user, game, bet, count):
    text = f"👤 <b>{user['name']}</b>\n💰 Баланс: <b>{user['balance']}$</b> 💵\n💵 Ставка: <b>{bet}$</b>\n🎲 Бросков: <b>{count}</b>\n\n🎯 <b>На что ставим?</b>"
    kb = []
    
    if game == "dice":
        kb = [[{"text": "Меньше x2", "callback_data": f"res_{game}_{bet}_{count}_low"}, {"text": "Больше x2", "callback_data": f"res_{game}_{bet}_{count}_high"}], [{"text": "Четное x2", "callback_data": f"res_{game}_{bet}_{count}_even"}, {"text": "Нечетное x2", "callback_data": f"res_{game}_{bet}_{count}_odd"}], [{"text": "Точное 1-6 (x6)", "callback_data": f"res_{game}_{bet}_{count}_exact"}]]
    elif game == "darts":
        kb = [[{"text": "Сектор x3", "callback_data": f"res_{game}_{bet}_{count}_sector"}, {"text": "Отскок x6", "callback_data": f"res_{game}_{bet}_{count}_bounce"}], [{"text": "Центр x6", "callback_data": f"res_{game}_{bet}_{count}_bull"}, {"text": "Промах x3", "callback_data": f"res_{game}_{bet}_{count}_miss"}]]
    elif game == "bowling":
        kb = [[{"text": "1-3 x2", "callback_data": f"res_{game}_{bet}_{count}_low"}, {"text": "4-6 x3", "callback_data": f"res_{game}_{bet}_{count}_mid"}], [{"text": "Страйк x5", "callback_data": f"res_{game}_{bet}_{count}_strike"}, {"text": "Промах x4", "callback_data": f"res_{game}_{bet}_{count}_miss"}]]
        kb = [
            [{"text": "Убывание x10.8", "callback_data": f"res_{game}_{bet}_{count}_dec"}, {"text": "Возрастание x10.8", "callback_data": f"res_{game}_{bet}_{count}_inc"}],
            [{"text": "Все меньше x8", "callback_data": f"res_{game}_{bet}_{count}_low"}, {"text": "Все больше x8", "callback_data": f"res_{game}_{bet}_{count}_high"}],
            [{"text": "Все четные x8", "callback_data": f"res_{game}_{bet}_{count}_even"}, {"text": "Все нечетные x8", "callback_data": f"res_{game}_{bet}_{count}_odd"}],
            [{"text": "Произведение >100 x10.8", "callback_data": f"res_{game}_{bet}_{count}_mult"}]
        ]
    elif game == "football":
        kb = [[{"text": "Гол в центр x5", "callback_data": f"res_{game}_{bet}_{count}_center"}, {"text": "Гол в угол x5", "callback_data": f"res_{game}_{bet}_{count}_corner"}], [{"text": "Любой гол x1.65", "callback_data": f"res_{game}_{bet}_{count}_goal"}], [{"text": "Штанга x2.5", "callback_data": f"res_{game}_{bet}_{count}_post"}, {"text": "Промах x2.5", "callback_data": f"res_{game}_{bet}_{count}_miss"}]]
        kb = [
            [{"text": "Ровно 1 гол x2.31", "callback_data": f"res_{game}_{bet}_{count}_g1"}, {"text": "Ровно 2 гола x3.47", "callback_data": f"res_{game}_{bet}_{count}_g2"}],
            [{"text": "Три гола x4.62", "callback_data": f"res_{game}_{bet}_{count}_g3"}, {"text": "Все мимо x4.62", "callback_data": f"res_{game}_{bet}_{count}_g0"}],
            [{"text": "Лишь 3-й гол x10.41", "callback_data": f"res_{game}_{bet}_{count}_third_only"}]
        ]
    elif game == "basketball":
        kb = [[{"text": "Точный x2", "callback_data": f"res_{game}_{bet}_{count}_goal"}, {"text": "Кольцо x1.5", "callback_data": f"res_{game}_{bet}_{count}_ring"}], [{"text": "Промах x2.5", "callback_data": f"res_{game}_{bet}_{count}_miss"}]]
        kb = [
            [{"text": "Три в центр x125", "callback_data": f"res_{game}_{bet}_{count}_all_center"}],
            [{"text": "Три мимо x15.62", "callback_data": f"res_{game}_{bet}_{count}_all_miss"}],
            [{"text": "Ровно 1 гол x3.47", "callback_data": f"res_{game}_{bet}_{count}_b1"}, {"text": "Ровно 2 гола x2.31", "callback_data": f"res_{game}_{bet}_{count}_b2"}]
        ]
    elif game == "bowling":
        kb = [
            [{"text": "Страйк x216", "callback_data": f"res_{game}_{bet}_{count}_all_strike"}],
            [{"text": "Без промаха x1.72", "callback_data": f"res_{game}_{bet}_{count}_no_miss"}],
            [{"text": "Три одинаково x36", "callback_data": f"res_{game}_{bet}_{count}_same"}]
        ]
    elif game == "darts":
        kb = [
            [{"text": "Отскок x216", "callback_data": f"res_{game}_{bet}_{count}_all_bounce"}, {"text": "Центр x216", "callback_data": f"res_{game}_{bet}_{count}_all_bull"}],
            [{"text": "Красное x8", "callback_data": f"res_{game}_{bet}_{count}_all_red"}, {"text": "Белое x8", "callback_data": f"res_{game}_{bet}_{count}_all_white"}],
            [{"text": "Любой сектор x3.37", "callback_data": f"res_{game}_{bet}_{count}_any_sector"}]
        ]
    elif game == "slots":
        text = f"👤 <b>{user['name']}</b>\n💰 Баланс: <b>{user['balance']}$</b> 💵\n💵 Ставка: <b>{bet}$</b>\n\n🎰 <b>Выберите символ:</b>"
        kb = [[{"text": "3 семерки x64", "callback_data": f"res_{game}_{bet}_3_seven"}, {"text": "3 лимона x64", "callback_data": f"res_{game}_{bet}_3_lemon"}], [{"text": "Любая комбинация x1.6", "callback_data": f"res_{game}_{bet}_3_any"}]]
        text = f"👤 <b>{user['name']}</b>\n💰 Баланс: <b>{user['balance']}$</b> 💵\n💵 Ставка: <b>{bet}$</b>\n\n🎰 <b>Выберите комбинацию:</b>"
        kb = [
            [{"text": "7 в каждом x5.17", "callback_data": f"res_{game}_{bet}_3_seven_each"}, {"text": "Есть тройка x5.68", "callback_data": f"res_{game}_{bet}_3_has_three"}],
            [{"text": "Без семерок x13.31", "callback_data": f"res_{game}_{bet}_3_no_seven"}, {"text": "Все разные x18.96", "callback_data": f"res_{game}_{bet}_3_unique"}]
        ]
    
    kb.append([{"text": "⬅️ Назад", "callback_data": f"bet_{game}_{bet}"}])
    return text, {"inline_keyboard": kb}

@@ -180,8 +206,7 @@ def get_outcome_menu(user, game, bet, count):
                answer_callback(cb_id)
                user = get_user(user_id)

                if user_id in user_states:
                    del user_states[user_id]
                if user_id in user_states: del user_states[user_id]

                if data == "main_menu" or data == "menu":
                    text, kb = get_main_menu(user)
@@ -254,39 +279,51 @@ def get_outcome_menu(user, game, bet, count):
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
                        if choice == "3_has_three":
                            if results[0] == results[1] or results[1] == results[2] or results[0] == results[2]: win = True; multiplier = 5.68
                        elif choice == "3_seven_each":
                            if results.count("7️⃣") > 0: win = True; multiplier = 5.17
                        elif choice == "3_no_seven":
                            if "7️⃣" not in results: win = True; multiplier = 13.31
                        elif choice == "3_unique":
                            if results[0] != results[1] and results[1] != results[2] and results[0] != results[2]: win = True; multiplier = 18.96
                    else:
                        rolls = []
                        for _ in range(count):
                            if game == "dice": rolls.append(random.randint(1, 6)); send_animation(chat_id, "🎲")
                            elif game == "darts": rolls.append(random.choice(["miss", "bounce", "sector", "bull"])); send_animation(chat_id, "🎯")
                            elif game == "football": rolls.append(random.choice(["miss", "post", "goal", "center", "corner"])); send_animation(chat_id, "⚽")
                            elif game == "basketball": rolls.append(random.choice(["miss", "ring", "goal"])); send_animation(chat_id, "🏀")
                            elif game == "bowling": rolls.append(random.choices([0, 1, 3, 5, 10], weights=[20, 30, 25, 15, 10])[0]); send_animation(chat_id, "🎳")
                            elif game == "football": rolls.append(random.choice(["miss", "goal"])); send_animation(chat_id, "⚽")
                            elif game == "basketball": rolls.append(random.choice(["miss", "center"])); send_animation(chat_id, "🏀")
                            elif game == "bowling": rolls.append(random.choice([0, 10])); send_animation(chat_id, "🎳") # Упрощенно для теста
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
                        if choice == "dec" and all(rolls[i] > rolls[i+1] for i in range(len(rolls)-1)): win = True; multiplier = 10.8
                        elif choice == "inc" and all(rolls[i] < rolls[i+1] for i in range(len(rolls)-1)): win = True; multiplier = 10.8
                        elif choice == "low" and all(r < 4 for r in rolls): win = True; multiplier = 8.0
                        elif choice == "high" and all(r > 3 for r in rolls): win = True; multiplier = 8.0
                        elif choice == "even" and all(r % 2 == 0 for r in rolls): win = True; multiplier = 8.0
                        elif choice == "odd" and all(r % 2 != 0 for r in rolls): win = True; multiplier = 8.0
                        elif choice == "mult" and (sum(rolls) * len(rolls) > 100): win = True; multiplier = 10.8 # Упрощенная математика
                        
                        elif choice == "g0" and all(r == "miss" for r in rolls): win = True; multiplier = 4.62
                        elif choice == "g1" and rolls.count("goal") == 1: win = True; multiplier = 2.31
                        elif choice == "g2" and rolls.count("goal") == 2: win = True; multiplier = 3.47
                        elif choice == "g3" and rolls.count("goal") == 3: win = True; multiplier = 4.62
                        
                        elif choice == "all_center" and all(r == "center" for r in rolls): win = True; multiplier = 125.0
                        elif choice == "all_miss" and all(r == "miss" for r in rolls): win = True; multiplier = 15.62
                        elif choice == "b1" and rolls.count("center") == 1: win = True; multiplier = 3.47
                        
                        elif choice == "all_strike" and all(r == 10 for r in rolls): win = True; multiplier = 216.0
                        elif choice == "no_miss" and all(r != 0 for r in rolls): win = True; multiplier = 1.72
                        elif choice == "same" and len(set(rolls)) == 1: win = True; multiplier = 36.0
                        
                        elif choice == "all_bounce" and all(r == "bounce" for r in rolls): win = True; multiplier = 216.0
                        elif choice == "all_bull" and all(r == "bull" for r in rolls): win = True; multiplier = 216.0
                        elif choice == "any_sector" and all(r in ["sector", "bull"] for r in rolls): win = True; multiplier = 3.37
                        elif choice == "all_red" and all(r == "red" for r in rolls): win = True; multiplier = 8.0
                        elif choice == "all_white" and all(r == "white" for r in rolls): win = True; multiplier = 8.0

                    if win:
                        win_amount = int(bet * multiplier)
