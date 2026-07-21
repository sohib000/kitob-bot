# -*- coding: utf-8 -*-
"""
middleware/throttling.py — [v4] ЗАЩИТА ОТ СПАМА.
Без внешних зависимостей (никаких cachetools/redis) —
обычный dict с отметками времени и периодической чисткой.

Правило: не чаще N событий за WINDOW секунд от одного пользователя.
Превысил — событие тихо гасится (кнопкам отвечаем, чтобы не «висели часики»).
Админы не ограничиваются.
"""
import time
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

from config import ADMIN_IDS

WINDOW = 3.0        # окно, сек
MAX_EVENTS = 4      # событий в окно (человеку хватает, скрипту — нет)
CLEAN_EVERY = 300   # чистка старых записей, сек


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        self._hits: dict[int, list[float]] = {}
        self._last_clean = time.monotonic()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user is None or user.id in ADMIN_IDS:
            return await handler(event, data)

        now = time.monotonic()

        # периодическая чистка, чтобы dict не рос вечно
        if now - self._last_clean > CLEAN_EVERY:
            self._hits = {
                uid: ts for uid, ts in self._hits.items()
                if ts and now - ts[-1] < WINDOW * 2
            }
            self._last_clean = now

        ts = [t for t in self._hits.get(user.id, []) if now - t < WINDOW]
        if len(ts) >= MAX_EVENTS:
            self._hits[user.id] = ts
            # гасим тихо; callback'у отвечаем, чтобы кнопка не «зависла»
            if isinstance(event, CallbackQuery):
                await event.answer("Sekinroq 🙂", show_alert=False)
            return  # хендлер не вызывается
        ts.append(now)
        self._hits[user.id] = ts
        return await handler(event, data)
