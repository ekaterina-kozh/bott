import aiosqlite

# Зададим имя базы данных
DB_NAME = 'quiz_bot1.db'

async def create_table():
    # Создаем соединение с базой данных (если она не существует, то она будет создана)
    async with aiosqlite.connect(DB_NAME) as db:
        # Выполняем SQL-запрос к базе данных
        await db.execute('''CREATE TABLE IF NOT EXISTS quiz_state (
        user_id INTEGER PRIMARY KEY,
        question_index INTEGER,
        last_score INTEGER DEFAULT 0
        )''')
        # Сохраняем изменения
        await db.commit()

async def update_quiz_index(user_id: int, index: int, last_score: int):
    # Создаем соединение с базой данных (если она не существует, она будет создана)
    async with aiosqlite.connect(DB_NAME) as db:
        # Вставляем новую запись или заменяем ее, если с данным user_id уже существует
        await db.execute('INSERT OR REPLACE INTO quiz_state(user_id, question_index, last_score) VALUES(?, ?, ?)', (user_id, index, last_score))
        # Сохраняем изменения
        await db.commit()

async def get_last_user_score(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT last_score FROM quiz_state WHERE user_id = ?', (user_id, )) as cursor:
            result = await cursor.fetchone()
            if result:
                return result[0]
            return 0


async def get_player_statistics():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute('SELECT user_id, last_score FROM quiz_state') as cursor:
            return await cursor.fetchall()

async def get_quiz_index(user_id: int):
     # Подключаемся к базе данных
     async with aiosqlite.connect(DB_NAME) as db:
        # Получаем запись для заданного пользователя
        async with db.execute('SELECT question_index FROM quiz_state WHERE user_id = (?)', (user_id, )) as cursor:
            # Возвращаем результат
            results = await cursor.fetchone()
            if results is not None:
                return results[0]
            else:
                return 0