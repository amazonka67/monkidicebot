<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>MonkiDice App</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        body {
            margin: 0;
            padding: 0;
            background-color: #1a1a1a; /* Темный фон как в Rakes */
            color: white;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
        }
        .card {
            background: #2a2a2a;
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            width: 80%;
            max-width: 400px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.5);
        }
        h1 { margin: 0 0 10px 0; font-size: 24px; }
        .balance { font-size: 32px; color: #4ade80; margin: 15px 0; font-weight: bold; }
        .btn {
            background-color: #3b82f6;
            color: white;
            border: none;
            padding: 15px 30px;
            font-size: 18px;
            border-radius: 10px;
            cursor: pointer;
            width: 100%;
            margin-top: 10px;
            font-weight: bold;
            transition: 0.2s;
        }
        .btn:active { transform: scale(0.95); }
        .btn-game { background-color: #8b5cf6; }
    </style>
</head>
<body>
    <div class="card">
        <h1 id="username">Загрузка...</h1>
        <div class="balance" id="balance">0 $</div>
        <button class="btn" onclick="claimBonus()">🎁 Забрать бонус</button>
        <button class="btn btn-game" onclick="playDice()">🎲 Играть в Дайс</button>
    </div>

    <script>
        // Инициализация Telegram WebApp
        const tg = window.Telegram.WebApp;
        tg.expand(); // Разворачиваем на весь экран
        tg.ready();

        // Данные пользователя
        const user = tg.initDataUnsafe?.user;
        if (user) {
            document.getElementById('username').innerText = user.first_name;
        }

        // Фейковый баланс для теста (потом будем брать с сервера)
        let currentBalance = 150;
        document.getElementById('balance').innerText = currentBalance + ' $';

        // Функция для отправки данных боту
        function sendDataToBot(action) {
            tg.sendData(JSON.stringify({ action: action, user_id: user.id }));
        }

        function claimBonus() {
            // Здесь мы потом будем запрашивать бонус у сервера
            currentBalance += 10;
            document.getElementById('balance').innerText = currentBalance + ' $';
            tg.showAlert("Вы получили 10$!");
        }

        function playDice() {
            tg.showAlert("Игра в разработке, но данные уже улетели боту!");
            // Отправляем команду боту, чтобы он знал, что нажали на Дайс
            sendDataToBot("play_dice");
        }
    </script>
</body>
</html>
