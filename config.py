# -*- coding: utf-8 -*-
"""
config.py — ВСЕ НАСТРОЙКИ БОТА В ОДНОМ МЕСТЕ.

ОПЛАТА: только Paynet Xolis (QR самозанятого).
Покупатель сканирует ваш персональный QR ЛЮБЫМ приложением
(Payme / Click / банковское), вводит уникальную сумму — деньги
падают на бизнес-кошелёк, налог 1% и фискальный чек — автоматически.

Секреты — через переменные окружения (.env / Railway Variables).
"""
import os

# .env для локальной разработки (на Railway не нужен — там Variables)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv не установлен — работаем через окружение

# ---------- СЕКРЕТЫ ----------
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

# [v4] Несколько админов: ADMIN_IDS="111,222" (или старый ADMIN_ID="111")
_raw_admins = os.getenv("ADMIN_IDS") or os.getenv("ADMIN_ID", "0")
ADMIN_IDS: list[int] = [int(x) for x in _raw_admins.split(",") if x.strip().isdigit()]
MAIN_ADMIN: int = ADMIN_IDS[0] if ADMIN_IDS else 0   # карточки/вопросы летят ему

# ---------- ПРОДУКТ ----------
BASE_PRICE: int = 69_000                             # базовая цена, сум
PRICE_TAIL_MAX: int = 299                            # «хвост» уникальной суммы
                                                     # итог: 69 001 ... 69 299

# ---------- PAYNET XOLIS ----------
# Скриншот вашего персонального QR из Xolis → files/qr_xolis.jpg
# Номер бизнес-кошелька показываем покупателю как резервный ориентир.
XOLIS_WALLET: str = "8888 0111 2434 0958"            # ← ваш кошелёк из Xolis

# ---------- КАНАЛ-БОНУС ----------
CHANNEL_LINK: str = "https://t.me/+Z68fr1kYMawyYjVi"         # пригласительная ссылка
                                                     # (включите «заявки на вступление»!)

# ---------- ФАЙЛЫ ----------
FILES_DIR = os.path.join(os.path.dirname(__file__), "files")
PDF_FILE = os.path.join(FILES_DIR, "kitob.pdf")      # книга
QR_XOLIS = os.path.join(FILES_DIR, "qr_xolis.jpg")   # персональный QR из Xolis

# ---------- БАЗА ----------
# [v4] Путь к базе через env — для Railway Volume (база переживает редеплой)
DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "sales.db"))

# ---------- ТАЙМИНГ ----------
CONFIRM_MINUTES = "5–15"


# ---------- ПРОВЕРКА ПЕРЕД СТАРТОМ ----------
def validate() -> list[str]:
    """Список проблем конфигурации. Пусто = готово к запуску."""
    problems = []
    if not BOT_TOKEN:
        problems.append("BOT_TOKEN bo'sh — Railway Variables'da yoki .env'da bering")
    if not ADMIN_IDS:
        problems.append("ADMIN_ID(S) bo'sh — @userinfobot orqali ID'ingizni oling")
    if not os.path.exists(PDF_FILE):
        problems.append(f"Kitob topilmadi: {PDF_FILE} (files/ papkasiga qo'ying)")
    if not os.path.exists(QR_XOLIS):
        problems.append(f"Xolis QR topilmadi: {QR_XOLIS} — bu YAGONA to'lov usuli, majburiy!")
    if "XXXXXXXX" in CHANNEL_LINK:
        problems.append("CHANNEL_LINK hali shablon holida — kanal havolasini qo'ying")
    return problems
