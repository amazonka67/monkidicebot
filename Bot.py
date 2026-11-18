import urllib.request
import json
import time
import random
import os

TOKEN = os.environ.get("BOT_TOKEN", "9193782655:AAFP7mMmjbL4ITM--2LBuStvO0YcTTc9gOk")

# ⚠️ ВАША ССЫЛКА НА САЙТ ⚠️
WEBAPP_URL = "https://amazonka67.github.io/monkidicebot/" 

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

def get_webapp_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🎮 Открыть Казино", "web_app": {"url": WEBAPP_URL}}]
        ]
    }

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

            # Обработка команд
            if "message" in update and "text" in update["message"]:
                msg = update["message"]; chat_id = msg["chat"]["id"]; text_str = msg["text"]; first_name = msg["from"].get("first_name", "Игрок")

                if text_str == "/start":
                    text = f"👋 Привет, <b>{first_name}</b>!\n\nДобро пожаловать в MonkiDice. Нажми на кнопку ниже, чтобы открыть Mini App!"
                    send_message(chat_id, text, get_webapp_keyboard())

    except Exception as e: print("Ошибка:", e); time.sleep(2)
