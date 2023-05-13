import aiosqlite as sq
from create_bot import bot
from APIs import current_price
from collections import defaultdict


async def sql_start():
    async with sq.connect('data_base/crypto_transactions.db') as base:
        async with base.cursor() as cur:
            if base:
                print('Connected with database')
            await base.execute('CREATE TABLE IF NOT EXISTS transactions(person_id INT, buy_or_sell BIT, ticker_1 CHAR, '
                               'ticker_2 CHAR, size FLOAT, price FLOAT, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
            await base.execute('CREATE TABLE IF NOT EXISTS rub_investing(person_id INT,'
                               'size FLOAT, usd FLOAT, date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
            await base.execute('CREATE TABLE IF NOT EXISTS main_deposits(id INTEGER PRIMARY KEY AUTOINCREMENT, '
                               'person_id INT, description TEXT, is_open BIT DEFAULT 1, date_open DATE, '
                               'percent TINYINT, percent_capitalization TEXT)')
            await base.execute('CREATE TABLE IF NOT EXISTS deposit_transactions(id INT, person_id INT, '
                               'is_add_or_take BIT, size INT, date_operation DATE)')
            await base.commit()


def try_connect_sql(func):
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ValueError as ex:
            print(f'Ошибка при запросе к БД! \n {ex}!')
    return wrapper


@try_connect_sql
async def sql_add_command(state, user_id: int, buy_or_sell: int = None, ticker_1: str = None, ticker_2: str = None,
                          size: float = None, price: float = None) -> None:
    async with state.proxy() as data:
        query = f'INSERT INTO transactions (person_id, buy_or_sell, ticker_1, ticker_2, size, price) ' \
                f'VALUES (?, ?, ?, ?, ?, ?)'
        values = ((user_id, *data.values()) if buy_or_sell is None else
                  (user_id, buy_or_sell, ticker_1, ticker_2, size, price))
        async with sq.connect('data_base/crypto_transactions.db') as base:
            async with base.cursor() as curs:
                await curs.execute(query, values)
                await base.commit()


@try_connect_sql
async def read_db(user_id: int) -> str:
    mes = ''
    async with sq.connect('data_base/crypto_transactions.db') as base:
        async with base.cursor() as curs:
            await curs.execute('SELECT * FROM transactions WHERE person_id = ?', (user_id,))
            async for row in curs:
                mes += f'\n{"Покупка" if row[1] else "Продажа"} {row[2]} {row[3]} {row[4]} {row[5]} {row[6]}'
    return mes


@try_connect_sql
async def count_portfolio_cost(user_id: int) -> dict:
    ticker_cost = {}
    queue = 'SELECT ticker_1, buy_or_sell, size FROM transactions WHERE person_id = ?'
    values = (user_id,)
    async with sq.connect('data_base/crypto_transactions.db') as base:
        async with base.cursor() as curs:
            await curs.execute(queue, values)
            async for ticker, buy_or_sell, size in curs:
                if ticker in ticker_cost.keys():
                    ticker_cost[ticker][1] += size if buy_or_sell else -size
                else:
                    price_current = await current_price(ticker, user_id=user_id)
                    ticker_cost[ticker] = [price_current, size if buy_or_sell else -size]
    return ticker_cost


@try_connect_sql
async def select_all_unique_person_id() -> list:
    async with sq.connect('data_base/crypto_transactions.db') as base:
        async with base.cursor() as curs:
            await curs.execute(f'SELECT DISTINCT person_id FROM transactions')
            rows = await curs.fetchall()
    unique_id = [int(row[0]) for row in rows]
    return unique_id


@try_connect_sql
async def add_in_sql_rub_size(user_id: int, state: dict) -> None:
    async with sq.connect('data_base/crypto_transactions.db') as base:
        async with base.cursor() as curs:
            await curs.execute(f'INSERT INTO rub_investing (person_id, size, usd) VALUES (?, ?, ?)',
                                (user_id, state['size_rub'], state['usdt_size']))
            await base.commit()


@try_connect_sql
async def count_all_investing(user_id: int) -> None:
    queue = 'SELECT SUM(size) as rub, SUM(usd) as usd FROM rub_investing WHERE person_id = ?'
    async with sq.connect('data_base/crypto_transactions.db') as base:
        async with base.cursor() as curs:
            await curs.execute(queue, (user_id,))
            rub, usd = await curs.fetchone()
            return (rub, usd)


# --------------------------DEPOSITS---------------------------------
@try_connect_sql
async def add_deposit(user_id: int, description, date_operation, percent, percent_capitalization) -> int:
        query = f'INSERT INTO main_deposits (person_id, description, date_open, percent, percent_capitalization) ' \
                f'VALUES (?, ?, ?, ?, ?)'
        values = (user_id, description, date_operation, percent, percent_capitalization)
        async with sq.connect('data_base/crypto_transactions.db') as base:
            async with base.cursor() as curs:
                await curs.execute(query, values)
            await base.commit()
            return int(curs.lastrowid)


@try_connect_sql
async def add_deposit_transaction(user_id, id_deposit, size, is_add_or_take, date_operetion) -> None:
        query = f'INSERT INTO deposit_transactions (person_id, id, size, is_add_or_take, date_operation) ' \
                f'VALUES (?, ?, ?, ?, ?)'
        values = (user_id, id_deposit, size, is_add_or_take, date_operetion)
        async with sq.connect('data_base/crypto_transactions.db') as base:
            async with base.cursor() as curs:
                await curs.execute(query, values)
            await base.commit()


@try_connect_sql
async def select_all_person_deposits(user_id: int) -> list:
    async with sq.connect('data_base/crypto_transactions.db') as base:
        async with base.cursor() as curs:
            await curs.execute(f'SELECT id, description FROM main_deposits WHERE person_id = {user_id}')
            rows = await curs.fetchall()
    id_and_description = [row[:2] for row in rows]
    return id_and_description


@try_connect_sql
async def count_deposits_money(user_id):
    dict_descr_and_size = defaultdict(int)
    async with sq.connect('data_base/crypto_transactions.db') as base:
        async with base.cursor() as curs:
            await curs.execute(f'SELECT main_deposits.description, deposit_transactions.is_add_or_take, '
                               f'deposit_transactions.size FROM main_deposits, deposit_transactions '
                               f'WHERE main_deposits.person_id = {user_id} AND main_deposits.id = deposit_transactions.id')
            async for descr, add_or_take, size in curs:
                dict_descr_and_size[descr] += size if add_or_take else -size
    return dict_descr_and_size
