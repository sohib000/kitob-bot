# -*- coding: utf-8 -*-
"""
keyboards/inline.py — ВСЕ КНОПКИ БОТА.
Каждая функция возвращает готовую клавиатуру.
callback_data — "адрес" кнопки, по нему хендлер понимает, что нажали.
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import BASE_PRICE


def main_menu() -> InlineKeyboardMarkup:
    """Главное меню после /start."""
    price = f"{BASE_PRICE:,}".replace(",", " ")
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📖 Kitob haqida", callback_data="about")],
        [InlineKeyboardButton(text=f"🛒 Sotib olish — {price} so'm",
                              callback_data="buy")],
        [InlineKeyboardButton(text="❓ Savol-javob", callback_data="faq")],
    ])


def paid_button(order_id: int) -> InlineKeyboardMarkup:
    """Под счётом: 'Я оплатил' (несёт номер заказа) + назад."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ To'lov qildim",
                              callback_data=f"paid:{order_id}")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="home")],
    ])


def admin_decision(order_id: int) -> InlineKeyboardMarkup:
    """Под скрином чека у админа: подтвердить / отклонить."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash",
                                 callback_data=f"ok:{order_id}"),
            InlineKeyboardButton(text="❌ Rad etish",
                                 callback_data=f"no:{order_id}"),
        ],
    ])


def retry_button() -> InlineKeyboardMarkup:
    """[v2] Под сообщением об отказе: попробовать снова."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Qayta urinish", callback_data="buy")],
        [InlineKeyboardButton(text="❓ Savol yozish", callback_data="faq")],
    ])
