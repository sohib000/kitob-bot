# -*- coding: utf-8 -*-
"""
utils/texts.py — ВСЕ ТЕКСТЫ БОТА (узбекский).
Логика отдельно, тексты отдельно.
Оплата: только Paynet Xolis QR.
"""
from config import XOLIS_WALLET, CHANNEL_LINK, CONFIRM_MINUTES

# ---------- ПРИВЕТСТВИЕ ----------
START = (
    "Assalomu alaykum, {name}! 👋\n\n"
    "Bu — <b>«Sun'iy intellektdan to'g'ri foydalanish san'ati»</b> "
    "kitobining rasmiy boti.\n\n"
    "📘 42 sahifa • 30 tayyor prompt • 15 AI taqqoslash\n"
    "💰 Narxi: <b>{price} so'm</b> (PDF, darhol yuboriladi)\n\n"
    "Quyidan tanlang 👇"
)

HOME = "Bosh menyu 👇"

# ---------- О КНИГЕ ----------
ABOUT = (
    "<b>Kitob ichida:</b>\n\n"
    "1️⃣ AI tarixi va kelajagi — oddiy tilda\n"
    "2️⃣ 15 ta AI taqqoslash: qaysi vazifaga qaysi biri\n"
    "3️⃣ Narxlar va to'lov yo'riqnomasi\n"
    "4️⃣ Prompt san'ati: 5 elementli formula\n"
    "5️⃣ 20 ta keng tarqalgan xato va yechimlari\n"
    "6️⃣ 30 ta tayyor prompt-shablon\n"
    "7️⃣ Xavfsizlik: firibgarlardan himoya\n"
    "8️⃣ AI bilan daromad: 30 kunlik reja\n\n"
    "✍️ Muallif: Ergashev Soyibjon (AI hamkorligida)\n"
    "📄 Format: PDF, rangli illyustratsiyalar bilan"
)

# ---------- FAQ ----------
FAQ = (
    "❓ <b>Savol-javob</b>\n\n"
    "<b>Qanday to'lanadi?</b>\n"
    "QR kodni istalgan ilova bilan skanerlaysiz: Payme, Click yoki "
    "bank ilovangiz. To'lov rasmiy — sizga avtomatik <b>fiskal chek</b> "
    "beriladi.\n\n"
    "<b>Kitob qanday yuboriladi?</b>\n"
    f"To'lov tasdiqlangach — shu botning o'zida PDF fayl keladi "
    f"(odatda {CONFIRM_MINUTES} daqiqa ichida).\n\n"
    "<b>Bonus bormi?</b>\n"
    "Ha! Kitob bilan birga AI yangiliklari kanalimizga taklif olasiz.\n\n"
    "<b>Boshqa savol bo'lsa?</b>\n"
    "Shu yerga yozib qoldiring — javob beramiz."
)

# ---------- ОПЛАТА (только Xolis QR) ----------
INVOICE = (
    "🧾 Buyurtma №{oid}\n\n"
    "1️⃣ Yuqoridagi <b>QR kodni skanerlang</b> — Payme, Click yoki "
    "bank ilovangiz bilan (istalgani bo'ladi).\n\n"
    "2️⃣ Summa maydoniga <b>aynan shuni</b> yozing:\n"
    "💰 <b>{amount} so'm</b>\n"
    "⚠️ Oxirgi raqamlar to'lovingizni tanib olishga yordam beradi — "
    "iltimos, aniq kiriting.\n\n"
    "3️⃣ To'lagach «✅ To'lov qildim» tugmasini bosing.\n\n"
    f"ℹ️ Qabul qiluvchi: rasmiy o'zini o'zi band qilgan shaxs "
    f"(hamyon: <code>{XOLIS_WALLET}</code>). "
    "To'lovingizga avtomatik <b>fiskal chek</b> beriladi — hammasi qonuniy ✅"
)

QR_XOLIS_CAPTION = (
    "📱 Paynet Xolis QR — Payme, Click yoki bank ilovangiz bilan skanerlang"
)

ASK_SCREENSHOT = (
    "📸 To'lov chekining skrinshotini shu yerga yuboring.\n"
    "Tasdiqlangach kitob darhol keladi!"
)

NOT_A_PHOTO = "Iltimos, chekni <b>rasm (skrinshot)</b> ko'rinishida yuboring 🙂"

SCREENSHOT_RECEIVED = (
    "✅ Chek qabul qilindi!\n"
    f"Odatda {CONFIRM_MINUTES} daqiqada tasdiqlanadi. Kitob shu yerga keladi 📬"
)

ORDER_STALE = (
    "⚠️ Bu buyurtma eskirgan yoki allaqachon yakunlangan.\n"
    "Iltimos, «Sotib olish» tugmasini qaytadan bosing 👇"
)

PHOTO_NO_ORDER = (
    "Rasm qabul qilindi, lekin sizda ochiq buyurtma ko'rinmayapti 🤔\n"
    "Kitob olish uchun «Sotib olish» tugmasini bosing 👇"
)

# ---------- ВЫДАЧА ----------
BOOK_CAPTION = "📘 Mana kitobingiz! Foydali o'qish tilaymiz 🙌"

BONUS_CHANNEL = (
    "🎁 <b>Bonus:</b> AI olamidagi yangiliklar, yangi promptlar va "
    "amaliy maslahatlar — bepul kanalimizda.\n"
    "Kitob o'quvchilari uchun maxsus:\n\n"
    f"👉 {CHANNEL_LINK}\n\n"
    "Kitob yoqsa — do'stlaringizga shu botni ulashing 😉"
)

REJECTED = (
    "❌ Afsuski, to'lovni tasdiqlay olmadik.\n"
    "Summa yoki chek noto'g'ri bo'lishi mumkin. "
    "Iltimos, tekshirib qayta urinib ko'ring yoki shu yerga yozing — "
    "birga hal qilamiz."
)

QUESTION_FORWARDED = "Xabaringiz qabul qilindi, tez orada javob beramiz 🙂"

ADMIN_ANSWER = "💬 <b>Javob:</b>\n\n{answer}"

# ---------- АДМИН ----------
ADMIN_NEW_ORDER = (
    "🆕 Buyurtma №{oid}\n"
    "👤 {full_name} {username}\n"
    "🆔 <code>{user_id}</code>\n"
    "💰 Kutilgan summa: <b>{amount} so'm</b>\n"
    "🔎 Xolis → Tushumlar tarixi'da shu summani tekshiring"
)

ADMIN_CONFIRMED_SUFFIX = "\n\n✅ TASDIQLANDI — kitob yuborildi"
ADMIN_REJECTED_SUFFIX = "\n\n❌ RAD ETILDI"
ADMIN_DELIVERY_FAIL_SUFFIX = "\n\n⚠️ XATO: kitob yuborilmadi (blok/fayl yo'q)"

STATS = (
    "📊 <b>Statistika</b>\n\n"
    "✅ Sotilgan: <b>{total}</b> ta (bugun: {today})\n"
    "💰 Tushum: <b>{revenue} so'm</b>\n"
    "⏳ Tasdiq kutmoqda: {waiting}\n\n"
    "📍 Manbalar (start bosganlar):\n{sources}"
)

STATE_CANCELLED = (
    "✅ Kutish bekor qilindi.\n"
    "Davom etish uchun /start bosing yoki menyudan tanlang."
)


# ---------- [v5] АДМИН-ПАНЕЛЬ ----------
ADMIN_MENU = "🛠 <b>Admin panel</b>\nBo'limni tanlang 👇"

ADMIN_NO_PENDING = "✅ Kutilayotgan buyurtmalar yo'q — hammasi yopilgan."

ADMIN_PENDING_ITEM = (
    "🧾 №{oid} • <b>{amount} so'm</b>\n"
    "👤 {full_name} {username} (<code>{user_id}</code>)\n"
    "🕘 {created}"
)

ADMIN_RECENT_HEADER = "🕘 <b>Oxirgi buyurtmalar</b>\n"
ADMIN_RECENT_ITEM = "{icon} №{oid} • {amount} so'm • {name} • {source}"

BC_ASK = (
    "📣 <b>Xabar yuborish</b>\n\n"
    "Xaridorlarga yuboriladigan xabarni yozing (matn/rasm bo'lishi mumkin).\n"
    "Bekor qilish: /admin"
)
BC_PREVIEW = (
    "👆 Xabar shu ko'rinishda ketadi.\n"
    "Qabul qiluvchilar: <b>{count} ta xaridor</b>.\nYuboramizmi?"
)
BC_NO_BUYERS = "Hozircha xaridorlar yo'q — yuboradigan hech kim topilmadi."
BC_DONE = "📣 Yuborildi: <b>{ok}</b> ta ✅ | yetmadi (blok): {fail} ta"
BC_CANCELLED = "Bekor qilindi."
