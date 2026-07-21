# -*- coding: utf-8 -*-
"""
main.py — ТОЧКА ВХОДА. Сборка бота из модулей и запуск.

Порядок роутеров ВАЖЕН:
  1. admin    — ok:/no:, /stats, reply-ответы покупателям
  2. payment  — buy, paid:, скриншоты (FSM + восстановление)
  3. user     — /start, меню и В КОНЦЕ "любой текст → админу"

[FIX v2]
- parse_mode=HTML задан ГЛОБАЛЬНО через DefaultBotProperties —
  в хендлерах его больше не надо повторять (и невозможно забыть).
- Перед стартом config.validate(): проверка токена, ADMIN_ID,
  наличия PDF/QR — понятные ошибки вместо загадочных падений.

Запуск локально:   python main.py
Запуск на Railway: Start Command = python main.py
                   Variables: BOT_TOKEN, ADMIN_ID
"""
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

import config
from database import db
from handlers import admin, payment, user
from middleware.throttling import ThrottlingMiddleware


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    log = logging.getLogger("main")

    # --- проверка конфигурации до старта ---
    problems = config.validate()
    fatal = [p for p in problems if not p.startswith("Ogohlantirish")]
    for p in problems:
        log.warning("CONFIG: %s", p)
    if fatal:
        log.error("Jiddiy muammolar bor — bot ishga tushmadi.")
        sys.exit(1)

    db.init_db()

    bot = Bot(
        config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),  # [FIX]
    )
    dp = Dispatcher(storage=MemoryStorage())

    # [v4] анти-спам на все апдейты (админы не ограничены)
    dp.message.middleware(ThrottlingMiddleware())
    dp.callback_query.middleware(ThrottlingMiddleware())

    dp.include_router(admin.router)     # порядок важен — см. докстринг
    dp.include_router(payment.router)
    dp.include_router(user.router)

    await bot.delete_webhook(drop_pending_updates=True)
    log.info("Bot ishga tushdi ✅")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
