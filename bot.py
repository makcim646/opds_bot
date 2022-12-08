from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from Opds import Opds


bot = Bot('') #Telegram bot token
dp = Dispatcher(bot, storage=MemoryStorage())

user_opds = dict()
user_callback_edit = dict()

opds_url = {'opds.su': 'http://opds.su/opds', 'flibusta.net': 'http://flibusta.net/opds'}


class StartSearch(StatesGroup):
    waiting_text = State()


@dp.message_handler(content_types=types.ContentType.TEXT, state=StartSearch.waiting_text)
async def send_text(msg: types.Message, state: FSMContext):
    userid = str(msg.chat.id)
    msgid = user_callback_edit[userid]
    text = msg.text
    opds = user_opds[userid]

    opds = user_opds[userid]
    opds.search(text)
    buttons = [{"text":text,"callback_data":f'{hash(text)}'} for text in opds.hop_menu.keys()]
    buttons.append({"text":'<< back',"callback_data":'back'})
    otvet = InlineKeyboardMarkup(row_width=1).add(*buttons)


    await bot.delete_message(msg.chat.id, msg.message_id)
    await bot.edit_message_text(f"Искать {text}", msg.chat.id, msgid, reply_markup=otvet)

    await state.finish()


@dp.message_handler(commands=['start', 'help'])
async def send_hello(msg: types.Message):
    await msg.answer('Для выбора источника книг введи комнду \n/opds \nпо вопросам @makcim646')




@dp.message_handler(commands=['opds'])
async def send_opds(msg: types.Message, state: FSMContext):
    buttons = [{"text":text,"callback_data":f'url_{text}'} for text in opds_url.keys()]
    otvet = InlineKeyboardMarkup(row_width=1).add(*buttons)

    await state.finish()
    await msg.answer('Выбери источник', reply_markup=otvet)



@dp.callback_query_handler(lambda c: c.data[:3] == 'url')
async def set_OPDS(callback: types.CallbackQuery):
    usrid = str(callback.from_user.id)
    msgid = callback.message.message_id
    data_callback = callback.data[4:]

    print(usrid, msgid, opds_url[data_callback])

    user_opds[usrid] = Opds(opds_url[data_callback])

    buttons = [{"text":text,"callback_data":f'{hash(text)}'} for text in user_opds[usrid].hop_menu.keys()]
    otvet = InlineKeyboardMarkup(row_width=1).add(*buttons)


    await bot.edit_message_text("Выбери следующий этап", chat_id=callback.from_user.id,
                                 message_id=callback.message.message_id,  reply_markup=otvet)
    await callback.answer()



@dp.callback_query_handler(lambda c: c.data == 'back', state=StartSearch.waiting_text)
async def back_state(callback: types.CallbackQuery, state: FSMContext):
    userid = str(callback.from_user.id)
    opds = user_opds[userid]
    opds.back_hop()
    buttons = [{"text":text,"callback_data":f'{hash(text)}'} for text in opds.hop_menu.keys()]
    buttons.append({"text":'<< back',"callback_data":'back'})
    otvet = InlineKeyboardMarkup(row_width=1).add(*buttons)


    await bot.edit_message_text("Выбери следующий этап", chat_id=callback.from_user.id,
                                 message_id=callback.message.message_id,  reply_markup=otvet)
    await state.finish()
    await callback.answer()


@dp.callback_query_handler(lambda c: c.data == 'back')
async def back(callback: types.CallbackQuery):
    userid = str(callback.from_user.id)
    opds = user_opds[userid]
    opds.back_hop()
    buttons = [{"text":text,"callback_data":f'{hash(text)}'} for text in opds.hop_menu.keys()]
    buttons.append({"text":'<< back',"callback_data":'back'})
    otvet = InlineKeyboardMarkup(row_width=1).add(*buttons)

    try:
        await bot.edit_message_text("Выбери следующий этап", chat_id=callback.from_user.id,
                                     message_id=callback.message.message_id,  reply_markup=otvet)
        await callback.answer()

    except Exception as e:
        await callback.answer('это начальнольное меню')


@dp.callback_query_handler(lambda c: int(c.data) == hash('search'))
async def search(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(StartSearch.waiting_text.state)
    #await bot.send_message(callback.from_user.id, "Введи то что хочешь найти")
    otvet = InlineKeyboardMarkup(row_width=1).add({"text":'<< back',"callback_data":'back'})
    user_callback_edit[str(callback.from_user.id)] = callback.message.message_id

    await bot.edit_message_text("Отправь то что хочешь найти", chat_id=callback.from_user.id,
                                 message_id=callback.message.message_id,  reply_markup=otvet)

    await callback.answer()



async def send_msg(usr_id:int, msg_id:int, text:str):
    try:
        c = 0
        firs = 0
        last = 100
        msg_c = len(text.split('\n'))
        otvet = InlineKeyboardMarkup(row_width=1).add({"text":'<< back',"callback_data":'back'})
        while True:
            if msg_c < last and c == 0:
                await bot.edit_message_text(text, chat_id=usr_id,
                                 message_id=msg_id,
                                 reply_markup=otvet, parse_mode='MARKDOWN',
                                 disable_web_page_preview=True)
                break

            elif msg_c - last < 0:
                await bot.send_message(usr_id, '\n'.join(text.split('\n')[firs:]),
                                        reply_markup=otvet,
                                        parse_mode="Markdown",
                                        disable_web_page_preview=True)
                break

            await bot.send_message(usr_id, '\n'.join(text.split('\n')[firs:last]),
                                            parse_mode="Markdown",
                                            disable_web_page_preview=True)

            firs += 100
            last += 100
            c += 1

    except Exception as e:
        logging.exception(e)




@dp.callback_query_handler()
async def next_hop(callback: types.CallbackQuery):
    userid = str(callback.from_user.id)
    hop_hash = int(callback.data)
    opds = user_opds[userid]


    for key in opds.hop_menu.keys():
        if hash(key) == hop_hash:
            hop_name = key


    opds.next_hop(hop_name)
    if opds.have_next_hop:
        buttons = [{"text":text,"callback_data":f'{hash(text)}'} for text in opds.hop_menu.keys()]
        buttons.append({"text":'<< back',"callback_data":'back'})
        otvet = InlineKeyboardMarkup(row_width=1).add(*buttons)
        await bot.edit_message_text("Выбери следующий этап", chat_id=callback.from_user.id,
                                 message_id=callback.message.message_id,  reply_markup=otvet)
        await callback.answer()

    else:
        text = ''
        for title, book_url in opds.book_menu.items():
            text += title + '\n'
            text += ', '.join([f'[{tip}]({url})' for tip, url in book_url.items() ])
            text += '\n'


        #otvet = InlineKeyboardMarkup(row_width=1).add({"text":'<< back',"callback_data":'back'})
        await send_msg(callback.from_user.id, callback.message.message_id, text)
        await callback.answer()


if __name__ == '__main__':
    executor.start_polling(dp)