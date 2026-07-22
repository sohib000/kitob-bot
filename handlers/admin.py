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

import asyncio

from aiogram.fsm.context import FSMContext
from config import ADMIN_IDS, PDF_FILE
from database import db
from keyboards import inline as kb
from utils.states import Broadcast
from utils import texts

router = Router(name="admin")
log = logging.getLogger(__name__)


def _fmt(n: int) -> str:
    return f"{n:,}".replace(",", " ")


async def _mark_card(callback: CallbackQuery, suffix: str) -> None:
    """
    Помечаем карточку у админа; сбой редактирования не критичен.
    [v5] Карточка бывает фото (скрин чека) ИЛИ текстом (список pending) —
    редактируем соответствующим методом.
    """
    try:
        if callback.message.photo:
            await callback.message.edit_caption(
                caption=(callback.message.caption or "") + suffix)
        else:
            await callback.message.edit_text(
                (callback.message.text or "") + suffix)
    except TelegramAPIError as e:
        log.warning("mark card failed: %s", e)


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


# ---------- [v5] АДМИН-ПАНЕЛЬ: /admin и /stats открывают меню ----------
@router.message(Command("stats", "admin"))
async def cmd_admin(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    await message.answer(texts.ADMIN_MENU, reply_markup=kb.admin_menu())


def _stats_text() -> str:
    s = db.get_stats()
    sources = "\n".join(f"  • {name}: {n}" for name, n in s["sources"]) or "—"
    return texts.STATS.format(
        total=s["total"], today=s["today"],
        revenue=_fmt(s["revenue"]), waiting=s["waiting"], sources=sources)


@router.callback_query(F.data == "adm:stats")
async def cb_adm_stats(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return await callback.answer()
    await callback.message.answer(_stats_text())
    await callback.answer()


# ---------- [v5] СПИСОК ОЖИДАЮЩИХ: карточки с кнопками ✅/❌ ----------
# Решает проблему «карточка потерялась в переписке»: заказ подтверждается
# из этого списка теми же ok:/no: колбэками.
@router.callback_query(F.data == "adm:pending")
async def cb_adm_pending(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return await callback.answer()
    rows = db.get_pending_orders()
    if not rows:
        await callback.message.answer(texts.ADMIN_NO_PENDING)
        return await callback.answer()
    import html as _h
    for r in rows:
        uname = f"@{r['username']}" if r["username"] else "(username yo'q)"
        await callback.message.answer(
            texts.ADMIN_PENDING_ITEM.format(
                oid=r["id"], amount=_fmt(r["amount"]),
                full_name=_h.escape(r["full_name"] or ""),
                username=_h.escape(uname),
                user_id=r["user_id"], created=r["created"][:16].replace("T", " ")),
            reply_markup=kb.admin_decision(r["id"]))
    await callback.answer()


# ---------- [v5] ПОСЛЕДНИЕ ЗАКАЗЫ ----------
@router.callback_query(F.data == "adm:recent")
async def cb_adm_recent(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return await callback.answer()
    rows = db.get_recent_orders(10)
    icons = {"paid": "✅", "waiting": "⏳", "rejected": "❌", "new": "🆕"}
    import html as _h
    lines = [texts.ADMIN_RECENT_HEADER]
    for r in rows:
        name = _h.escape(r["full_name"] or r["username"] or "-")
        lines.append(texts.ADMIN_RECENT_ITEM.format(
            icon=icons.get(r["status"], "•"), oid=r["id"],
            amount=_fmt(r["amount"]), name=name, source=r["source"] or "direct"))
    await callback.message.answer("\n".join(lines) if rows else "Buyurtmalar yo'q.")
    await callback.answer()


# ---------- [v5] РАССЫЛКА ПО ПОКУПАТЕЛЯМ ----------
@router.callback_query(F.data == "adm:bc")
async def cb_adm_bc(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        return await callback.answer()
    if not db.get_buyer_ids():
        await callback.message.answer(texts.BC_NO_BUYERS)
        return await callback.answer()
    await state.set_state(Broadcast.waiting_content)
    await callback.message.answer(texts.BC_ASK)
    await callback.answer()


@router.message(Broadcast.waiting_content, F.from_user.id.in_(ADMIN_IDS))
async def bc_content(message: Message, state: FSMContext, bot: Bot):
    # /admin и любая команда отменяют рассылку
    if message.text and message.text.startswith("/"):
        await state.clear()
        return await message.answer(texts.BC_CANCELLED)
    # предпросмотр: копия сообщения + подтверждение
    await bot.copy_message(message.chat.id, message.chat.id, message.message_id)
    await state.update_data(chat_id=message.chat.id, msg_id=message.message_id)
    count = len(db.get_buyer_ids())
    await message.answer(texts.BC_PREVIEW.format(count=count),
                         reply_markup=kb.broadcast_confirm())


@router.callback_query(F.data == "bc:cancel")
async def bc_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(texts.BC_CANCELLED)
    await callback.answer()


@router.callback_query(F.data == "bc:go")
async def bc_go(callback: CallbackQuery, state: FSMContext, bot: Bot):
    if callback.from_user.id not in ADMIN_IDS:
        return await callback.answer()
    data = await state.get_data()
    await state.clear()
    if "msg_id" not in data:
        return await callback.answer("Xabar topilmadi, qaytadan boshlang", show_alert=True)
    ok = fail = 0
    for uid in db.get_buyer_ids():
        try:
            await bot.copy_message(uid, data["chat_id"], data["msg_id"])
            ok += 1
        except TelegramAPIError:
            fail += 1
        await asyncio.sleep(0.1)          # мягкий rate-limit
    await callback.message.answer(texts.BC_DONE.format(ok=ok, fail=fail))
    await callback.answer("Tayyor")


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
