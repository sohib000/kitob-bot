# -*- coding: utf-8 -*-
"""
handlers/admin.py — АДМИНСКАЯ ЧАСТЬ.

✅ Tasdiqlash → PDF + канал покупателю; заказ → paid
❌ Rad etish  → вежливый отказ;          заказ → rejected
/stats        → продажи, выручка, источники
Reply на пересланный вопрос → ответ уходит покупателю  [NEW v2]

[FIX v2]
- Отправка книги обёрнута в try/except: если покупатель заблокировал
  бота или PDF отсутствует — админ видит понятную ошибку, а заказ
  НЕ помечается оплаченным зря (сначала шлём, потом фиксируем? — нет:
  фиксация до отправки защищает от двойной выдачи; при ошибке
  админу приходит алерт с ID покупателя для ручной связи).
- edit_caption в try: истёкший/изменённый месседж не роняет хендлер.
- Отклонённому покупателю — кнопка "Купить заново".
"""
import logging

from aiogram import Router, F, Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, FSInputFile

import html as _html

from config import ADMIN_IDS, PDF_FILE
from database import db
from keyboards import inline as kb
from utils import texts

router = Router(name="admin")
log = logging.getLogger(__name__)


def _fmt(n: int) -> str:
    return f"{n:,}".replace(",", " ")


async def _mark_card(callback: CallbackQuery, suffix: str) -> None:
    """Помечаем карточку у админа; сбой редактирования не критичен."""
    try:
        await callback.message.edit_caption(
            caption=(callback.message.caption or "") + suffix)
    except TelegramAPIError as e:
        log.warning("edit_caption failed: %s", e)


# ---------- ПОДТВЕРДИТЬ ----------
@router.callback_query(F.data.startswith("ok:"))
async def cb_confirm(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id not in ADMIN_IDS:
        return await callback.answer("Faqat admin uchun", show_alert=True)

    order_id = int(callback.data.split(":")[1])
    user_id = db.confirm_order(order_id)   # None = не найден / уже paid

    if user_id is None:
        return await callback.answer(
            "Topilmadi yoki allaqachon tasdiqlangan", show_alert=True)

    # [FIX] покупатель мог заблокировать бота / PDF мог потеряться
    try:
        await bot.send_document(
            user_id, FSInputFile(PDF_FILE), caption=texts.BOOK_CAPTION)
        await bot.send_message(user_id, texts.BONUS_CHANNEL,
                               disable_web_page_preview=True)
    except (TelegramAPIError, FileNotFoundError) as e:
        log.error("delivery failed for order %s: %s", order_id, e)
        await _mark_card(callback, texts.ADMIN_DELIVERY_FAIL_SUFFIX)
        return await callback.answer(
            f"XATO: yuborilmadi! User ID: {user_id}. "
            "Qo'lda bog'laning.", show_alert=True)

    await _mark_card(callback, texts.ADMIN_CONFIRMED_SUFFIX)
    await callback.answer("Yuborildi ✅")


# ---------- ОТКЛОНИТЬ ----------
@router.callback_query(F.data.startswith("no:"))
async def cb_reject(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id not in ADMIN_IDS:
        return await callback.answer("Faqat admin uchun", show_alert=True)

    order_id = int(callback.data.split(":")[1])
    user_id = db.reject_order(order_id)   # None = не найден / уже ОПЛАЧЕН

    if user_id is None:
        return await callback.answer(
            "Topilmadi yoki allaqachon TO'LANGAN — rad etib bo'lmaydi",
            show_alert=True)

    try:
        await bot.send_message(user_id, texts.REJECTED,
                               reply_markup=kb.retry_button())
    except TelegramAPIError as e:
        log.warning("reject notify failed: %s", e)

    await _mark_card(callback, texts.ADMIN_REJECTED_SUFFIX)
    await callback.answer("Rad etildi")


# ---------- /stats ----------
@router.message(Command("stats"))
async def cmd_stats(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    s = db.get_stats()
    sources = "\n".join(f"  • {name}: {n}" for name, n in s["sources"]) or "—"
    await message.answer(texts.STATS.format(
        total=s["total"], today=s["today"],
        revenue=_fmt(s["revenue"]), waiting=s["waiting"], sources=sources))


# ---------- ОТВЕТ НА ВОПРОС ПОКУПАТЕЛЯ [NEW] ----------
# Админ делает reply на пересланное ботом сообщение —
# бот по таблице threads находит автора и доставляет ответ.
@router.message(F.reply_to_message, F.from_user.id.in_(ADMIN_IDS))
async def admin_reply(message: Message, bot: Bot):
    target = db.get_thread_user(message.reply_to_message.message_id)
    if target is None:
        return await message.answer(
            "Bu xabar savolga bog'lanmagan (yoki bot qayta ishga tushgan).")
    try:
        await bot.send_message(target, texts.ADMIN_ANSWER.format(
            answer=_html.escape(message.text or "")))  # [FIX v4]
        await message.answer("Javob yuborildi ✅")
    except TelegramAPIError:
        await message.answer("Yuborilmadi — foydalanuvchi botni bloklagan.")
