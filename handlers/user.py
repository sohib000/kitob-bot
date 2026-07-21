# -*- coding: utf-8 -*-
"""
handlers/user.py — ПОЛЬЗОВАТЕЛЬСКИЕ ХЕНДЛЕРЫ.
/start (метка источника), меню, "О книге", FAQ, вопросы → админу.

[FIX v2]
- Имя в приветствии экранируется (html.escape) — имя "<Ali>" больше
  не роняет отправку START-сообщения.
- Пересланный админу вопрос сохраняется в threads —
  админ отвечает обычным reply, бот доставляет автору.
"""
import html

from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from config import ADMIN_IDS, MAIN_ADMIN, BASE_PRICE
from database import db
from keyboards import inline as kb
from utils import texts

router = Router(name="user")


@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject):
    """
    Deep-link: t.me/БОТ?start=reels1 → command.args == "reels1".
    Заказ создаём сразу — метка источника попадает в базу,
    даже если человек ещё не нажал "Купить".
    """
    source = (command.args or "direct")[:32]        # защита от мусорных меток
    db.get_or_create_order(
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
        source=source,
    )
    await message.answer(
        texts.START.format(
            name=html.escape(message.from_user.first_name),   # [FIX]
            price=f"{BASE_PRICE:,}".replace(",", " "),
        ),
        reply_markup=kb.main_menu(),
    )


@router.callback_query(F.data == "home")
async def cb_home(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(texts.HOME, reply_markup=kb.main_menu())
    await callback.answer()


@router.callback_query(F.data == "about")
async def cb_about(callback: CallbackQuery):
    await callback.message.answer(texts.ABOUT, reply_markup=kb.main_menu())
    await callback.answer()


@router.callback_query(F.data == "faq")
async def cb_faq(callback: CallbackQuery):
    await callback.message.answer(texts.FAQ, reply_markup=kb.main_menu())
    await callback.answer()


# ---------- ЛЮБОЙ ТЕКСТ = ВОПРОС → АДМИНУ ----------
# Роутер user подключается ПОСЛЕДНИМ (см. main.py), иначе
# этот хендлер перехватил бы шаги других сценариев.
@router.message(F.text & ~F.text.startswith("/"))
async def any_question(message: Message, bot: Bot):
    if message.from_user.id in ADMIN_IDS:
        return
    fwd = await bot.forward_message(MAIN_ADMIN, message.chat.id, message.message_id)
    db.save_thread(fwd.message_id, message.from_user.id)   # [NEW] для ответа reply'ем
    await message.answer(texts.QUESTION_FORWARDED)
