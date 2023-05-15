from apscheduler.schedulers.asyncio import AsyncIOScheduler
from data_base import sqlite_db
from datetime import datetime


async def daily_check_percent_capitalization():
    print('DOOOOO IT')
    unique_id = await sqlite_db.select_all_uniqle_person_id_for_capitalization()
    date_now = datetime.today().date()

    for person_id in unique_id:
        data = await sqlite_db.select_person_deposits_for_capitalization(person_id)

        for deposit_id, date_open, percent, percent_capitalization in data:
            date_open = datetime.strptime(date_open, '%d.%m.%Y').date()
            print(((date_now - date_open).days % 30) == 0)
            print(percent_capitalization.lower() == 'ежемесячная')
            if ((date_now - date_open).days % 30) == 0 and percent_capitalization.lower() == 'ежемесячная':
                deposit_size = await sqlite_db.count_deposits_money(person_id)
                print(deposit_size)
                size = deposit_size * (1 + percent / 100 / 12)
                await sqlite_db.add_deposit_transaction(person_id, deposit_id, size, 1,
                                                        datetime.strftime(date_now, '%d.%m.%Y'))


schedulers = AsyncIOScheduler(timezone='Asia/Vladivostok')
schedulers.add_job(daily_check_percent_capitalization, trigger='cron', hour=22, minute=28)
# schedulers.start()

# async def daily_check_percent_capitalization():
#     unique_id = await sqlite_db.select_all_uniqle_person_id_for_capitalization
#     date_now = datetime.today().date()
#
#     for person_id in unique_id:
#
#     data = await sqlite_db.select_person_deposits_for_capitalization()
#
#     all_persons_deposits = {}
#
#     for deposit_id, person_id, date_open, percent, percent_capitalization, descr in data:
#         date_open = datetime.strptime(date_open, '%d.%m.%Y').data()
#
#         if (date_now - date_open).days % 30 == 0 and percent_capitalization.lower() == 'ежемесячная':
#             if person_id not in all_persons_deposits.keys():
#                 all_persons_deposits[person_id] = await sqlite_db.count_deposits_money(person_id)
#
#             size = all_persons_deposits[person_id][descr] * (1 + percent / 100 / 12)
#             await sqlite_db.add_deposit_transaction(person_id, deposit_id, size, 1,
#                                                     datetime.strftime(date_now, '%d.%m.%Y'))