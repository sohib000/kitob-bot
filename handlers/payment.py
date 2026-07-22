# -*- coding: utf-8 -*-
"""
handlers/payment.py — СЦЕНАРИЙ ОПЛАТЫ (сторона покупателя).

Шаги:
1. "Купить"     → QR Paynet Xolis + УНИКАЛЬНАЯ сумма (единственный способ)
2. "Я оплатил"  → FSM: ждём скриншот
3. Фото         → карточка админу; не фото → просим скриншот

[FIX v2]
- Имя покупателя экранируется (html.escape) — имя с < > больше
  не ломает HTML-разметку и отправку карточки админу.
- Старая кнопка "Я оплатил" по закрытому заказу → вежливое
  "заказ неактуален" вместо тихого воскрешения заказа.
- Восстановление после рестарта: FSM в памяти обнулился, но если
  человек прислал фото и у него есть открытый заказ — принимаем
  как чек (раньше фото молча игнорировалось — покупатель зависал).
"""
import html
import os

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, FSInputFile

from config import ADMIN_IDS, MAIN_ADMIN, QR_XOLIS
from database import db
from keyboards import inline as kb
from utils import texts
from utils.states import Payment

router = Router(name="payment")


def _fmt(amount: int) -> str:
    return f"{amount:,}".replace(",", " ")


async def _send_admin_card(bot: Bot, message: Message, order_id: int) -> None:
    """Карточка чека админу: скрин + данные + кнопки. Используется в 2 местах."""
    amount = db.get_amount(order_id)
    user = message.from_user
    username = f"@{user.username}" if user.username else "(username yo'q)"
    await bot.send_photo(
        MAIN_ADMIN,
        message.photo[-1].file_id,
        caption=texts.ADMIN_NEW_ORDER.format(
            oid=order_id,
            full_name=html.escape(user.full_name),   # [FIX] экранирование
            username=html.escape(username),
            user_id=user.id,
            amount=_fmt(amount or 0),
        ),
        reply_markup=kb.admin_decision(order_id),
    )


# ---------- ШАГ 1: СЧЁТ ----------
@router.callback_query(F.data == "buy")
async def cb_buy(callback: CallbackQuery):
    order_id, amount = db.get_or_create_order(
        user_id=callback.from_user.id,
        username=callback.from_user.username,
        full_name=callback.from_user.full_name,
        source="button",
    )

    # Единственный способ оплаты — персональный QR Paynet Xolis.
    # Покупатель сканирует его ЛЮБЫМ приложением (Payme/Click/банк).
    if os.path.exists(QR_XOLIS):
        await callback.message.answer_photo(
            FSInputFile(QR_XOLIS), caption=texts.QR_XOLIS_CAPTION)

    await callback.message.answer(
        texts.INVOICE.format(oid=order_id, amount=_fmt(amount)),
        reply_markup=kb.paid_button(order_id),
    )
    await callback.answer()


# ---------- ШАГ 2: "Я ОПЛАТИЛ" ----------
@router.callback_query(F.data.startswith("paid:"))
async def cb_paid(callback: CallbackQuery, state: FSMContext):
    order_id = int(callback.data.split(":")[1])

    # [FIX v2] закрытый заказ не оживляем; [FIX v4] и только СВОЙ заказ —
    # подделанный callback_data с чужим order_id здесь умирает
    if not db.set_waiting(order_id, callback.from_user.id):
        await callback.message.answer(
            texts.ORDER_STALE, reply_markup=kb.main_menu())
        return await callback.answer()

    await state.set_state(Payment.waiting_screenshot)
    await state.update_data(order_id=order_id)
    await callback.message.answer(texts.ASK_SCREENSHOT)
    await callback.answer()


# ---------- ШАГ 3а: СКРИНШОТ (штатный путь, внутри FSM) ----------
@router.message(Payment.waiting_screenshot, F.photo)
async def got_screenshot(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    order_id = data["order_id"]
    await _send_admin_card(bot, message, order_id)
    await state.clear()
    await message.answer(texts.SCREENSHOT_RECEIVED)


# ---------- КОМАНДА ВО ВРЕМЯ ОЖИДАНИЯ СКРИНА [FIX v4.1] ----------
@router.message(Payment.waiting_screenshot, F.text.startswith("/"))
async def command_in_waiting(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(texts.STATE_CANCELLED)


# ---------- ШАГ 3б: НЕ ФОТО ----------
@router.message(Payment.waiting_screenshot)
async def not_photo(message: Message):
    await message.answer(texts.NOT_A_PHOTO)


# ---------- ВОССТАНОВЛЕНИЕ: фото БЕЗ состояния FSM ----------
# Бот перезапустился (MemoryStorage забыл шаг) или человек прислал чек,
# не нажав "Я оплатил". Есть открытый заказ → принимаем как чек.
@router.message(F.photo)
async def photo_without_state(message: Message, bot: Bot):
    if message.from_user.id in ADMIN_IDS:
        return
    order = db.find_open_order(message.from_user.id)
    if order is None:
        await message.answer(texts.PHOTO_NO_ORDER, reply_markup=kb.main_menu())
        return
    db.set_waiting(order["id"], message.from_user.id)
    await _send_admin_card(bot, message, order["id"])
    await message.answer(texts.SCREENSHOT_RECEIVED)
