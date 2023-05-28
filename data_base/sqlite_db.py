import aiosqlite as sq
# from create_bot import bot
from APIs import current_price
from collections import defaultdict
from APIs.tinkoff_api.tinkoff_client import TinkoffAPI


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

            await base.execute('CREATE TABLE IF NOT EXISTS assets_transactions(figi TEXT, person_id INT, '
                               'is_buy_or_sell BIT, price FLOAT, lot INT, date_operation DATE)')
            await base.execute('CREATE TABLE IF NOT EXISTS all_bonds(figi TEXT, ticker TEXT, currency TEXT, name TEXT, '
                               'exchange TEXT, nominal FLOAT, aci_value FLOAT, country_of_risk TEXT, sector TEXT,'
                               'buy_available_flag BIT, sell_available_flag BIT, floating_coupon_flag BIT,'
                               'perpetual_flag BIT, amortization_flag BIT, for_iis_flag BIT, for_qual_investor_flag BIT,'
                               'risk_level TEXT)')
            await base.execute('CREATE TABLE IF NOT EXISTS all_shares(figi TEXT, ticker TEXT, currency TEXT, name TEXT,'
                               'lot INT, exchange TEXT, nominal FLOAT, country_of_risk TEXT, '
                               'sector TEXT, buy_available_flag BIT, sell_available_flag BIT, div_yield_flag BIT,'
                               'for_iis_flag BIT, for_qual_investor_flag BIT, share_type TEXT)')
            await base.execute('CREATE TABLE IF NOT EXISTS all_etfs(figi TEXT, ticker TEXT, currency TEXT, name TEXT,'
                               'lot INT, exchange TEXT, fixed_commission FLOAT, focus_type TEXT, country_of_risk TEXT, '
                               'sector TEXT, buy_available_flag BIT, sell_available_flag BIT,'
                               'for_iis_flag BIT, for_qual_investor_flag BIT)')
            await base.execute('CREATE TABLE IF NOT EXISTS all_currencies(figi TEXT, ticker TEXT, currency TEXT, '
                               'name TEXT, lot INT, exchange TEXT, nominal FLOAT, country_of_risk TEXT, '
                               'min_price_increment FLOAT, buy_available_flag BIT, sell_available_flag BIT, '
                               'for_iis_flag BIT, for_qual_investor_flag BIT)')

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
async def add_deposit_transaction(user_id, id_deposit, size, is_add_or_take, date_operation) -> None:
        query = f'INSERT INTO deposit_transactions (person_id, id, size, is_add_or_take, date_operation) ' \
                f'VALUES (?, ?, ?, ?, ?)'
        values = (user_id, id_deposit, size, is_add_or_take, date_operation)
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
                               f'WHERE main_deposits.person_id = {user_id} AND main_deposits.is_open = 1 AND '
                               f'main_deposits.id = deposit_transactions.id')
            async for descr, add_or_take, size in curs:
                dict_descr_and_size[descr] += size if add_or_take else -size
    return dict_descr_and_size


@try_connect_sql
async def update_new_percent(user_id, new_percent, deposit_id):
    async with sq.connect('data_base/crypto_transactions.db') as base:
        async with base.cursor() as curs:
            await curs.execute(f'UPDATE main_deposits SET percent = {new_percent} WHERE id = {deposit_id} AND '
                               f'person_id = {user_id}')
        await base.commit()


@try_connect_sql
async def update_close_deposit(user_id, deposit_id):
    async with sq.connect('data_base/crypto_transactions.db') as base:
        async with base.cursor() as curs:
            await curs.execute(f'UPDATE main_deposits SET is_open = 0 WHERE id = {deposit_id} AND person_id = {user_id}')
        await base.commit()


@try_connect_sql
async def select_person_deposits_for_capitalization(user_id: int) -> list:
    async with sq.connect('data_base/crypto_transactions.db') as base:
        async with base.cursor() as curs:
            await curs.execute(f'SELECT id, date_open, percent, percent_capitalization, description FROM main_deposits '
                               f'WHERE person_id = {user_id} AND is_open = 1')
            rows = await curs.fetchall()
    data = [row[:5] for row in rows]
    return data


@try_connect_sql
async def select_all_uniqle_person_id_for_capitalization():
    async with sq.connect('data_base/crypto_transactions.db') as base:
        async with base.cursor() as curs:
            await curs.execute(f'SELECT DISTINCT person_id FROM main_deposits')
            rows = await curs.fetchall()
    unique_id = [int(row[0]) for row in rows]
    return unique_id


async def add_deposit(user_id: int, description, date_operation, percent, percent_capitalization) -> int:
    query = f'INSERT INTO main_deposits (person_id, description, date_open, percent, percent_capitalization) ' \
            f'VALUES (?, ?, ?, ?, ?)'
    values = (user_id, description, date_operation, percent, percent_capitalization)
    async with sq.connect('data_base/crypto_transactions.db') as base:
        async with base.cursor() as curs:
            await curs.execute(query, values)
        await base.commit()
        return int(curs.lastrowid)


# ------------------------ASSETS-------------------------------------
class AssetsSQL:
    @staticmethod
    async def add_and_update_bonds(values_of_bonds):
        query = f'INSERT INTO all_bonds (figi, ticker, currency, name, exchange, nominal, aci_value, country_of_risk,' \
                f'sector, buy_available_flag, sell_available_flag, floating_coupon_flag, perpetual_flag,' \
                f'amortization_flag, for_iis_flag, for_qual_investor_flag, risk_level) ' \
                f'VALUES ({"?," * 16 + "?"})'
        async with sq.connect('data_base/crypto_transactions.db') as base:
            async with base.cursor() as curs:
                for row in values_of_bonds.instruments:
                    values = (
                        row.figi,
                        row.ticker,
                        row.currency,
                        row.name,
                        row.exchange,
                        TinkoffAPI.cast_money(row.nominal),
                        TinkoffAPI.cast_money(row.aci_value),
                        row.country_of_risk,
                        row.sector,
                        row.buy_available_flag,
                        row.sell_available_flag,
                        row.floating_coupon_flag,
                        row.perpetual_flag,
                        row.amortization_flag,
                        row.for_iis_flag,
                        row.for_qual_investor_flag,
                        row.risk_level
                    )
                    await curs.execute(query, values)
            await base.commit()

    @staticmethod
    async def add_and_update_shares(values_of_shares):
        query = f'INSERT INTO all_shares (figi, ticker, currency, name, lot, exchange, nominal, country_of_risk, sector,' \
                f'buy_available_flag, sell_available_flag, div_yield_flag, for_iis_flag, for_qual_investor_flag,' \
                f'share_type) VALUES ({"?," * 14 + "?"})'
        async with sq.connect('data_base/crypto_transactions.db') as base:
            async with base.cursor() as curs:
                for row in values_of_shares.instruments:
                    values = (
                        row.figi,
                        row.ticker,
                        row.currency,
                        row.name,
                        row.lot,
                        row.exchange,
                        TinkoffAPI.cast_money(row.nominal),
                        row.country_of_risk,
                        row.sector,
                        row.buy_available_flag,
                        row.sell_available_flag,
                        row.div_yield_flag,
                        row.for_iis_flag,
                        row.for_qual_investor_flag,
                        row.share_type
                    )
                    await curs.execute(query, values)
            await base.commit()

    @staticmethod
    async def add_and_update_etfs(values_of_etfs):
        query = f'INSERT INTO all_etfs (figi, ticker, currency, name, lot, exchange, fixed_commission, focus_type, ' \
                f'country_of_risk, sector, buy_available_flag, sell_available_flag, for_iis_flag, ' \
                f'for_qual_investor_flag) VALUES ({"?," * 13 + "?"})'
        async with sq.connect('data_base/crypto_transactions.db') as base:
            async with base.cursor() as curs:
                for row in values_of_etfs.instruments:
                    values = (
                        row.figi,
                        row.ticker,
                        row.currency,
                        row.name,
                        row.lot,
                        row.exchange,
                        TinkoffAPI.cast_money(row.fixed_commission),
                        row.focus_type,
                        row.country_of_risk,
                        row.sector,
                        row.buy_available_flag,
                        row.sell_available_flag,
                        row.for_iis_flag,
                        row.for_qual_investor_flag,
                        )
                    await curs.execute(query, values)
            await base.commit()

    @staticmethod
    async def add_and_update_currencies(values_of_currincies):
        query = f'INSERT INTO all_currencies (figi, ticker, currency, name, lot, exchange, nominal, country_of_risk, ' \
                f'min_price_increment, buy_available_flag, sell_available_flag, for_iis_flag, for_qual_investor_flag)' \
                f' VALUES ({"?," * 12 + "?"})'
        async with sq.connect('data_base/crypto_transactions.db') as base:
            async with base.cursor() as curs:
                for row in values_of_currincies.instruments:
                    values = (
                        row.figi,
                        row.ticker,
                        row.currency,
                        row.name,
                        row.lot,
                        row.exchange,
                        TinkoffAPI.cast_money(row.nominal),
                        row.country_of_risk,
                        TinkoffAPI.cast_money(row.min_price_increment),
                        row.buy_available_flag,
                        row.sell_available_flag,
                        row.for_iis_flag,
                        row.for_qual_investor_flag,
                    )
                    await curs.execute(query, values)
            await base.commit()

    @staticmethod
    async def get_assets_info(assets_type: str, ticker: str):
        if assets_type == 'share':
            query = f'SELECT figi, name, currency, lot, country_of_risk, buy_available_flag, ' \
                    f'sell_available_flag, for_iis_flag, for_qual_investor_flag FROM all_shares ' \
                    f'WHERE ticker = "{ticker.upper()}"'
        elif assets_type == 'bond':
            query = f'SELECT figi, name, currency, aci_value, country_of_risk, buy_available_flag, ' \
                    f'sell_available_flag, floating_coupon_flag, perpetual_flag, amortization_flag, for_iis_flag, ' \
                    f'for_qual_investor_flag, risk_level FROM all_bonds WHERE ticker = "{ticker.upper()}"'
        elif assets_type == 'etf':
            query = f'SELECT figi, name, currency, lot, fixed_commission, country_of_risk, buy_available_flag, ' \
                    f'sell_available_flag, for_iis_flag, for_qual_investor_flag FROM all_etfs ' \
                    f'WHERE ticker = "{ticker.upper()}"'
        else:
            query = f'SELECT figi, name, lot, buy_available_flag, sell_available_flag, for_iis_flag, ' \
                    f'for_qual_investor_flag FROM all_currencies WHERE ticker = "{ticker.upper()}"'
        async with sq.connect('data_base/crypto_transactions.db') as base:
            async with base.cursor() as curs:
                await curs.execute(query)
                assets = await curs.fetchall()
                return assets

    @staticmethod
    @try_connect_sql
    async def add_assets_transaction(figi, person_id, is_buy_or_sell, price, lot, date_operation) -> None:
            query = f'INSERT INTO assets_transactions (figi, person_id, is_buy_or_sell, price, lot, date_operation) ' \
                    f'VALUES (?, ?, ?, ?, ?, ?)'
            values = (figi, person_id, is_buy_or_sell, price, lot, date_operation)
            async with sq.connect('data_base/crypto_transactions.db') as base:
                async with base.cursor() as curs:
                    await curs.execute(query, values)
                await base.commit()





