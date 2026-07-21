# -*- coding: utf-8 -*-
"""
database/db.py — ВСЯ РАБОТА С БАЗОЙ (SQLite).
Хендлеры не пишут SQL сами — только вызывают эти функции.

Статусы заказа:
  new      — нажал "Купить", получил реквизиты
  waiting  — прислал скрин, ждёт подтверждения админа
  paid     — подтверждено, книга выдана
  rejected — отклонено админом

[FIX v2] set_waiting проверяет статус (нельзя "оживить" отклонённый заказ
         старой кнопкой), reject не трогает уже оплаченные,
         + find_open_order (восстановление после рестарта),
         + таблица threads (ответы админа на вопросы покупателей).
"""
import random
import sqlite3
from datetime import datetime

from config import DB_PATH, BASE_PRICE, PRICE_TAIL_MAX


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")       # [v4] меньше блокировок
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def init_db() -> None:
    """Создаёт таблицы при первом запуске. Вызывается из main.py."""
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS orders(
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id   INTEGER NOT NULL,
                username  TEXT,
                full_name TEXT,
                amount    INTEGER NOT NULL,
                source    TEXT,
                status    TEXT DEFAULT 'new',
                created   TEXT,
                paid_at   TEXT
            )
        """)
        # связь "пересланный админу вопрос → кто спросил":
        # админ отвечает reply'ем на пересланное сообщение,
        # бот по этой таблице находит адресата
        conn.execute("""
            CREATE TABLE IF NOT EXISTS threads(
                admin_msg_id INTEGER PRIMARY KEY,
                user_id      INTEGER NOT NULL
            )
        """)


# ---------- ЗАКАЗЫ ----------
def get_or_create_order(user_id: int, username: str,
                        full_name: str, source: str) -> tuple[int, int]:
    """
    (order_id, amount). Открытый заказ пользователя переиспользуем —
    сумма не меняется при повторных нажатиях "Купить".
    Новому заказу — уникальная сумма BASE_PRICE + 1..PRICE_TAIL_MAX,
    не совпадающая с другими ОТКРЫТЫМИ заказами.
    """
    with _connect() as conn:
        row = conn.execute(
            "SELECT id, amount FROM orders "
            "WHERE user_id=? AND status IN ('new','waiting')",
            (user_id,)
        ).fetchone()
        if row:
            return row["id"], row["amount"]

        while True:
            amount = BASE_PRICE + random.randint(1, PRICE_TAIL_MAX)
            busy = conn.execute(
                "SELECT 1 FROM orders "
                "WHERE amount=? AND status IN ('new','waiting')",
                (amount,)
            ).fetchone()
            if not busy:
                break

        cur = conn.execute(
            "INSERT INTO orders(user_id, username, full_name, amount, source, created) "
            "VALUES(?,?,?,?,?,?)",
            (user_id, username or "", full_name, amount, source,
             datetime.now().isoformat(timespec="seconds"))
        )
        return cur.lastrowid, amount


def find_open_order(user_id: int) -> sqlite3.Row | None:
    """
    [FIX v2] Открытый заказ пользователя (new/waiting) или None.
    Нужен для восстановления: бот перезапустился, FSM забыт,
    а человек прислал скрин — по этой функции понимаем контекст.
    """
    with _connect() as conn:
        return conn.execute(
            "SELECT id, amount, status FROM orders "
            "WHERE user_id=? AND status IN ('new','waiting') "
            "ORDER BY id DESC LIMIT 1",
            (user_id,)
        ).fetchone()


def set_waiting(order_id: int, user_id: int) -> bool:
    """
    [FIX v2] Переводит в waiting ТОЛЬКО открытый заказ.
    [FIX v4 SECURITY] ...и только СВОЙ: callback_data можно подделать
    модифицированным клиентом, поэтому order_id всегда сверяется
    с user_id нажавшего. Чужой заказ тронуть невозможно.
    """
    with _connect() as conn:
        cur = conn.execute(
            "UPDATE orders SET status='waiting' "
            "WHERE id=? AND user_id=? AND status IN ('new','waiting')",
            (order_id, user_id)
        )
        return cur.rowcount > 0


def confirm_order(order_id: int) -> int | None:
    """
    user_id покупателя или None (не найден / уже paid).
    [FIX v4] Атомарно: сначала UPDATE с условием — из двух одновременных
    кликов ✅ (два админа) выиграет ровно один, второй получит None.
    """
    with _connect() as conn:
        cur = conn.execute(
            "UPDATE orders SET status='paid', paid_at=? "
            "WHERE id=? AND status != 'paid'",
            (datetime.now().isoformat(timespec="seconds"), order_id)
        )
        if cur.rowcount == 0:
            return None
        row = conn.execute(
            "SELECT user_id FROM orders WHERE id=?", (order_id,)
        ).fetchone()
        return row["user_id"] if row else None


def reject_order(order_id: int) -> int | None:
    """
    [FIX v2] Отклонить можно только НЕоплаченный заказ.
    [FIX v4] Атомарно, как confirm_order: из одновременных кликов ❌
    выигрывает один; повторный reject тоже возвращает None.
    """
    with _connect() as conn:
        cur = conn.execute(
            "UPDATE orders SET status='rejected' "
            "WHERE id=? AND status NOT IN ('paid','rejected')",
            (order_id,)
        )
        if cur.rowcount == 0:
            return None
        row = conn.execute(
            "SELECT user_id FROM orders WHERE id=?", (order_id,)
        ).fetchone()
        return row["user_id"] if row else None


def get_amount(order_id: int) -> int | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT amount FROM orders WHERE id=?", (order_id,)
        ).fetchone()
        return row["amount"] if row else None


def get_stats() -> dict:
    with _connect() as conn:
        total, revenue = conn.execute(
            "SELECT COUNT(*), COALESCE(SUM(amount),0) "
            "FROM orders WHERE status='paid'"
        ).fetchone()
        today = conn.execute(
            "SELECT COUNT(*) FROM orders "
            "WHERE status='paid' AND date(paid_at)=date('now','localtime')"
        ).fetchone()[0]
        waiting = conn.execute(
            "SELECT COUNT(*) FROM orders WHERE status='waiting'"
        ).fetchone()[0]
        sources = conn.execute(
            "SELECT source, COUNT(*) FROM orders "
            "GROUP BY source ORDER BY 2 DESC"
        ).fetchall()
    return {
        "total": total, "revenue": revenue, "today": today,
        "waiting": waiting,
        "sources": [(s or "direct", n) for s, n in sources],
    }


# ---------- ДИАЛОГИ С АДМИНОМ ----------
def save_thread(admin_msg_id: int, user_id: int) -> None:
    """Запоминаем: пересланное админу сообщение № → от какого пользователя."""
    with _connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO threads(admin_msg_id, user_id) VALUES(?,?)",
            (admin_msg_id, user_id)
        )


def get_thread_user(admin_msg_id: int) -> int | None:
    """По reply админа находим, кому отправить ответ."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT user_id FROM threads WHERE admin_msg_id=?", (admin_msg_id,)
        ).fetchone()
        return row["user_id"] if row else None
