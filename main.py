import asyncio
import logging
import sys
from os import getenv

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message as TelegramMessage, KeyboardButton, InlineKeyboardButton, CallbackQuery, InlineKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from sqlalchemy import select, insert, desc, delete as sql_delete
from sqlalchemy.orm import Session
from aiogram.utils.i18n import gettext as _, lazy_gettext as __, I18n, FSMI18nMiddleware

from models import Base, engine, User, Message

load_dotenv()

TOKEN = getenv("BOT_TOKEN")

dp = Dispatcher()
session = Session(bind=engine)


def buttons_menu():
    rkb = ReplyKeyboardBuilder()
    rkb.add(*[
        KeyboardButton(text=_("Leave a comment")),
        KeyboardButton(text=_("My comments")),
        KeyboardButton(text=_("Language"))
    ])
    rkb.adjust(3, 1)
    return rkb.as_markup(resize_keyboard=True)

def delete_button(note_id: int):
    ikb = InlineKeyboardBuilder()
    ikb.button(text=_("Delete"), callback_data=f"delete_note:{note_id}")
    return ikb.as_markup()

class NoteForm(StatesGroup):
    note = State()

@dp.message(F.text == __("Language"))
async def language_handler(message: TelegramMessage, state: FSMContext) -> None:
    btns = [KeyboardButton(text="English"), KeyboardButton(text="Uzbek")]
    rkb = ReplyKeyboardBuilder()
    rkb.add(*btns)
    rkb.adjust(2)
    btn = rkb.as_markup(resize_keyboard=True)
    await message.answer(_("Choose language"), reply_markup=btn)

@dp.message(F.text.in_(["English", "Uzbek"]))
async def choice_lang_handler(message: TelegramMessage, state: FSMContext, i18n: I18n):
    map_lang = {
        "English": "en",
        "Uzbek": "uz"
    }
    lang = map_lang.get(message.text)
    await state.update_data({"locale": lang})
    i18n.current_locale = lang
    btn = buttons_menu()
    await message.answer(_("Change language"), reply_markup=btn)

@dp.message(CommandStart())
async def command_start_handler(message: TelegramMessage) -> None:
    query = select(User).where(User.id == message.from_user.id)
    data = session.execute(query).scalar()
    if not data:
        query = insert(User).values(id=message.from_user.id, first_name=message.from_user.first_name)
        session.execute(query)
        session.commit()
    btn = buttons_menu()
    await message.answer(_("Hello!").format(name=message.from_user.first_name), reply_markup=btn)


@dp.message(F.text == __("Leave a comment"))
async def add_note_handler(message: TelegramMessage, state: FSMContext) -> None:
    await state.set_state(NoteForm.note)
    await message.answer(_("Enter note title"))


@dp.message(F.text, NoteForm.note)
async def save_note_handler(message: TelegramMessage, state: FSMContext) -> None:
    note = message.text
    query = insert(Message).values(thought=note, user_id=message.from_user.id)
    session.execute(query)
    session.commit()
    await state.clear()
    btn = buttons_menu()
    await message.answer(_("Successfully added"), reply_markup=btn)


@dp.message(F.text == __("My comments"))
async def my_notes_handler(message: TelegramMessage, state: FSMContext) -> None:
    query = select(Message).where(Message.user_id == message.from_user.id).order_by(desc(Message.id)).limit(5)
    result = session.execute(query)
    messages = result.scalars().all()

    if messages:
        for msg in messages:
            keyboard = delete_button(msg.id)
            await message.answer(text=msg.thought, reply_markup=keyboard)
    else:
        await message.answer(_("You don't have any notes yet"))


@dp.callback_query(F.data.startswith("delete_note:"))
async def delete_note_callback(call: CallbackQuery):
    note_id = int(call.data.split(":")[1])
    stmt = sql_delete(Message).where(Message.id == note_id)
    session.execute(stmt)
    session.commit()
    await call.message.delete()
    await call.answer(_("Deleted successfully!"), show_alert=True)


async def main() -> None:
    i18n = I18n(path="locales", default_locale="en", domain="messages")
    Base.metadata.create_all(engine)
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp.update.middleware(FSMI18nMiddleware(i18n=i18n))

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())