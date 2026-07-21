# -*- coding: utf-8 -*-
"""
utils/states.py — СОСТОЯНИЯ FSM (конечного автомата).
FSM = бот "помнит", на каком шаге диалога находится пользователь.

У нас один сценарий с ожиданием: после кнопки "Я оплатил"
бот ждёт именно СКРИНШОТ — и никакое другое сообщение
не собьёт его с этого шага.
"""
from aiogram.fsm.state import State, StatesGroup


class Payment(StatesGroup):
    waiting_screenshot = State()   # ждём фото чека от покупателя
