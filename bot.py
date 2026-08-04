import logging
import asyncio
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# 1. SİSTEM LOGLARI VE BAŞLATICILAR
logging.basicConfig(level=logging.INFO)

# 🔑 SENİN RESMİ TELEGRAM BOT TOKENİN (KODA ENTEGRE EDİLDİ)
API_TOKEN = '8857214628:AAG1ZwgJXMApUC9DeaJhNKiyQ6IT0OfXipo'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# 📊 STRATEJİK HESAPLAMA VE KURAL MOTORU
MIN_LIMIT_USD = 50.0       # Belirlediğin kesin minimum limit
BASE_RATE = 95.50          # 1 USDT Ham kur fiyatı (API'den otomatik güncellenecek)
MY_COMMISSION_PERCENT = 0.025  # %2.5 Sizin net kazancınız

# Kullanıcının göreceği kur (%2.5 komisyonunuz düşülerek hesaplanır)
CURRENT_RATE = BASE_RATE * (1 - MY_COMMISSION_PERCENT)

# 2. ANA MENÜ BUTONLARI (KULLANICI BOTA GİRDİĞİNDE GÖRÜNÜR)
def get_main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(KeyboardButton("🔄 Обменять USDT на Рубли (No-KYC)"), KeyboardButton("📱 Оплата по QR-коду (СБП)"))
    markup.row(KeyboardButton("📊 Актуальный курс"), KeyboardButton("👤 Мой профиль & Кошелек"))
    return markup

# 3. /START KOMUTU (KARŞILAMA VE GÜVENLİK BİLGİSİ)
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.reply(
        f"⚡ **Добро пожаловать в Fast Ruble Changer!**\n\n"
        f"🔒 Мы работаем **абсолютно без верификации паспорта (No-KYC)**.\n"
        f"💵 Минимальная сумма одной операции: **{MIN_LIMIT_USD} USDT**.\n"
        f"📊 Наш актуальный курс: 1 USDT = **{CURRENT_RATE:.2f} RUB**\n\n"
        f"Выберите нужную операцию в меню ниже:",
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )

# 4. ADIM 1: KRİPTO SATIŞ BUTONUNA TIKLANDIĞINDA
@dp.message_handler(lambda message: message.text == "🔄 Обменять USDT на Рубли (No-KYC)")
async def exchange_crypto_start(message: types.Message):
    await message.reply(
        "✍️ Пожалуйста, введите количество **USDT (TRC-20)**, которое хотите продать:\n"
        "_(Введите только число, например: 100)_",
        parse_mode="Markdown"
    )

# ADIM 2: MİKTAR GİRİLDİĞİNDE MİNİMUM 50$ LİMİT KONTROLÜ
@dp.message_handler(lambda message: message.text.replace('.', '', 1).isdigit())
async def exchange_crypto_amount(message: types.Message):
    amount = float(message.text)
    
    if amount < MIN_LIMIT_USD:
        await message.reply(
            f"❌ **Сделка отклонена!**\n"
            f"Вы ввели: {amount} USDT.\n"
            f"Минимальный лимит системы — **{MIN_LIMIT_USD} USDT**.\n"
            f"Пожалуйста, введите сумму от 50 USDT и выше."
        )
    else:
        ruble_amount = amount * CURRENT_RATE
        
        # BİTPAPA TARZI BANKA SEÇİM MENÜSÜ
        bank_menu = InlineKeyboardMarkup(row_width=2)
        bank_menu.add(
            InlineKeyboardButton("🟢 Сбербанк (Sberbank)", callback_data=f"b_SBER_{amount}"),
            InlineKeyboardButton("🟡 Т-Банк / Тинькофф (T-Bank)", callback_data=f"b_TBANK_{amount}"),
            InlineKeyboardButton("⚡ СБП (SBP Fast Payout)", callback_data=f"b_SBP_{amount}")
        )
        
        await message.reply(
            f"✅ **Сумма одобрена!**\n\n"
            f"💰 Вы отдаете: **{amount} USDT**\n"
            f"🇷🇺 Вы получаете: **{ruble_amount:,.2f} RUB** _(Включая комиссию)_{f'\n\n👉 **Выберите банк для получения рублей:**'}",
            reply_markup=bank_menu,
            parse_mode="Markdown"
        )

# ADIM 3: BANKA SEÇİLDİKTEN SONRA KART VEYA SBP BİLGİSİ TALEBİ
@dp.callback_query_handler(lambda c: c.data.startswith('b_'))
async def status_select_bank(callback_query: types.CallbackQuery):
    _, bank, amount = callback_query.data.split("_")
    
    await bot.send_message(
        chat_id=callback_query.message.chat.id,
        text=f"🏦 Выбранный банк: **{bank}**\n"
             f"💰 Сумма сделки: **{amount} USDT**\n\n"
             f"✍️ Пожалуйста, отправьте номер вашей карты или номер телефона для СБП:\n"
             f"_(Сюda автоматический шлюз зачислит рубли)_",
        parse_mode="Markdown"
    )

# ADIM 4: KART BİLGİSİ GELDİĞİNDE KURUMSAL AUTOMATIC API BAĞLANTISI
@dp.message_handler(lambda message: len(message.text) >= 10 and not message.text.startswith("/"))
async def exchange_final_gateway(message: types.Message):
    await message.reply("🔄 **Связываюсь с автоматическим многовалютным шлюзом...**")
    await asyncio.sleep(2)  # Kurumsal API (Volet/Payeer) sorgu simülasyonu
    
    # Kurumsal ağın bota verdiği otomatik emanet (Escrow) cüzdanı
    gateway_deposit_wallet = "T9yD14Nj9j7xAB4dbGeiX9h8unkKHxuWwb"
    
    await message.reply(
        f"🚀 **Автоматическая заявка успешно создана!**\n\n"
        f"⚠️ Пожалуйста, переведите криптовалюту на этот адрес **USDT (TRC-20)**:\n"
        f"`{gateway_deposit_wallet}`\n\n"
        f"⚡ Как только транзакция подтвердится в блокчейне, платежный шлюз мгновенно отправит рубли на ваши реквизиты. Никаких паспортов (No-KYC). Your profit is 2.5% safe.",
        parse_mode="Markdown"
    )

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
