import re
from aiogram import F, Router
from aiogram.filters import Command
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.state import StatesGroup, State
import config
import db.functions as db
import task_kb as kb
import task_texts as texts


router = Router()


class Form(StatesGroup):
    support_id = State()
    support_username = State()
    admin_id = State()
    admin_name = State()
    new_support_username = State()
    new_admin_name = State()


@router.message(Command("chat"))
async def get_chat_id(msg):
    await msg.answer(str(msg.chat.id))


@router.message(Command("request"))
async def handle_request(msg):
    try:
        buyer_id = re.search(r'Buyer ID: .*\n', msg.text, re.I)
        buyer_id = buyer_id.group().replace('Buyer ID: ', '').replace('\n', '')
        support_id = re.search(r'Support ID: .*\n', msg.text, re.I)
        support_id = support_id.group().replace('Support ID: ', '').replace('\n', '')
        text = '\n'.join(msg.text.split('\n')[3:])
        support = await db.get_support(support_id)
        if support is not None:
            request_id, created_at = await db.create_request(buyer_id, support_id, text, msg.chat.id)
            response_text = texts.request_accepted.format(request=request_id, buyer=buyer_id)
            bot = Bot(token=config.TASK_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
            await bot.send_message(chat_id=support[0],
                                   text=texts.request.format(request=request_id, buyer=buyer_id,
                                                             status=texts.statuses['created'],
                                                             created_at=created_at.replace(microsecond=0),
                                                             completed_at='-', text=text),
                                   reply_markup=await kb.get_request_menu(request_id))
            await bot.session.close()
        else:
            response_text = texts.support_not_found
    except AttributeError:
        response_text = texts.request_incorrect
    await msg.answer(response_text)


@router.callback_query(kb.IdCallbackData.filter(F.action == 'request_menu'))
async def request_menu(callback_query, callback_data):
    data = await db.get_request(callback_data.id)
    if data['status'] == 'created':
        await callback_query.message.edit_text(texts.request.format(request=callback_data.id, buyer=data['buyer_id'],
                                                                    status=texts.statuses['created'],
                                                                    created_at=data['created_at'].replace(microsecond=0),
                                                                    completed_at='-',
                                                                    text=data['text']),
                                               reply_markup=await kb.get_request_menu(callback_data.id))
    else:
        await callback_query.message.edit_text(texts.request.format(request=callback_data.id, buyer=data['buyer_id'],
                                                                    status=texts.statuses[data['status']],
                                                                    created_at=data['created_at'].replace(microsecond=0),
                                                                    completed_at=data['completed_at'].replace(microsecond=0),
                                                                    text=data['text']))


@router.callback_query(kb.IdCallbackData.filter(F.action == 'complete_request_confirm'))
async def complete_request_confirm(callback_query, callback_data):
    await callback_query.message.edit_text(texts.complete_request_confirm,
                                           reply_markup=await kb.get_complete_request_menu(callback_data.id))


@router.callback_query(kb.IdCallbackData.filter(F.action == 'complete_request'))
async def complete_request(callback_query, callback_data):
    data = await db.change_status(callback_data.id, 'completed')
    completed_chat = await db.get_support('@test')
    bot = Bot(token=config.TASK_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await bot.send_message(chat_id=data['chat'],
                           text=texts.request_completed.format(request=callback_data.id, buyer=data['buyer_id']))
    await bot.session.close()
    await bot.send_message(chat_id=completed_chat[0],
                           text=texts.request.format(request=callback_data.id, buyer=data['buyer_id'],
                                                     status=texts.statuses['completed'],
                                                     created_at=data['created_at'].replace(microsecond=0),
                                                     completed_at=data['completed_at'].replace(microsecond=0),
                                                     text=data['text']))
    await bot.session.close()
    await callback_query.message.edit_text(texts.request.format(request=callback_data.id, buyer=data['buyer_id'],
                                                                status=texts.statuses['completed'],
                                                                created_at=data['created_at'].replace(microsecond=0),
                                                                completed_at=data['completed_at'].replace(microsecond=0),
                                                                text=data['text']))


@router.callback_query(kb.IdCallbackData.filter(F.action == 'cancel_request_confirm'))
async def cancel_request_confirm(callback_query, callback_data):
    await callback_query.message.edit_text(texts.cancel_request_confirm,
                                           reply_markup=await kb.get_cancel_request_menu(callback_data.id))


@router.callback_query(kb.IdCallbackData.filter(F.action == 'cancel_request'))
async def cancel_request(callback_query, callback_data):
    data = await db.change_status(callback_data.id, 'canceled')
    bot = Bot(token=config.TASK_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await bot.send_message(chat_id=data['chat'],
                           text=texts.request_canceled.format(request=callback_data.id, buyer=data['buyer_id']))
    await bot.session.close()
    await callback_query.message.edit_text(texts.request.format(request=callback_data.id, buyer=data['buyer_id'],
                                                                status=texts.statuses['canceled'],
                                                                created_at=data['created_at'].replace(microsecond=0),
                                                                completed_at='-',
                                                                text=data['text']))


@router.message(Command("start"))
async def start(msg):
    if msg.chat.id > 0:
        check = await db.check_admin(msg.chat.id)
        if check:
            await msg.answer(texts.main_menu, reply_markup=await kb.get_main_menu())
        else:
            await msg.answer(texts.start_forbidden)


@router.callback_query(kb.ActionCallbackData.filter(F.action == 'main_menu'))
async def main_menu(callback_query):
    check = await db.check_admin(callback_query.message.chat.id)
    if check:
        await callback_query.message.edit_text(texts.main_menu, reply_markup=await kb.get_main_menu())
    else:
        await callback_query.message.edit_text(texts.forbidden)


@router.callback_query(kb.ActionCallbackData.filter(F.action == 'supports_menu'))
async def supports_menu(callback_query):
    check = await db.check_admin(callback_query.message.chat.id)
    if check:
        await callback_query.message.edit_text(texts.supports_menu, reply_markup=await kb.get_supports_menu())
    else:
        await callback_query.message.edit_text(texts.forbidden)


@router.callback_query(kb.IdCallbackData.filter(F.action == 'support_menu'))
async def support_menu(callback_query, callback_data):
    check = await db.check_admin(callback_query.message.chat.id)
    username = await db.get_support_username(callback_data.id)
    if check:
        await callback_query.message.edit_text(texts.support_menu.format(id=callback_data.id, username=username[0]),
                                               reply_markup=await kb.get_support_menu(callback_data.id))
    else:
        await callback_query.message.edit_text(texts.forbidden)


@router.callback_query(kb.ActionCallbackData.filter(F.action == 'add_support'))
async def set_support_id(callback_query, state):
    check = await db.check_admin(callback_query.message.chat.id)
    if check:
        await state.set_state(Form.support_id)
        await callback_query.message.edit_text(texts.set_support_id)
    else:
        await callback_query.message.edit_text(texts.forbidden)


@router.message(Form.support_id)
async def set_support_username(msg, state):
    check = await db.check_admin(msg.from_user.id)
    if check:
        if msg.text == '/cancel':
            await state.clear()
            await msg.answer(texts.supports_menu, reply_markup=await kb.get_supports_menu())
        elif msg.text.isdigit() or (msg.text[0] == '-' and msg.text[1:].isdigit()):
            check = await db.get_support_username(msg.text)
            if check is None:
                await state.update_data(support_id=msg.text)
                await state.set_state(Form.support_username)
                await msg.answer(texts.set_support_username)
            else:
                await msg.answer(texts.unique_support_id)
        else:
            await msg.answer(texts.incorrect_support_id)
    else:
        await state.clear()
        await msg.answer(texts.forbidden)


@router.message(Form.support_username)
async def add_support(msg, state):
    check = await db.check_admin(msg.from_user.id)
    if check:
        if msg.text == '/cancel':
            await state.clear()
            await msg.answer(texts.supports_menu, reply_markup=await kb.get_supports_menu())
        else:
            check = await db.get_support(msg.text)
            if check is None:
                data = await state.get_data()
                await state.clear()
                await db.add_support(data['support_id'], msg.text)
                await msg.answer(texts.support_menu.format(id=data['support_id'], username=msg.text),
                                                           reply_markup=await kb.get_support_menu(data['support_id']))
            else:
                await msg.answer(texts.unique_support_username)
    else:
        await state.clear()
        await msg.answer(texts.forbidden)


@router.callback_query(kb.IdCallbackData.filter(F.action == 'change_support_username'))
async def set_new_support_username(callback_query, callback_data, state):
    check = await db.check_admin(callback_query.message.chat.id)
    if check:
        await state.set_state(Form.support_id)
        await state.update_data(support_id=callback_data.id)
        await state.set_state(Form.new_support_username)
        await callback_query.message.edit_text(texts.set_support_username)
    else:
        await callback_query.message.edit_text(texts.forbidden)


@router.message(Form.new_support_username)
async def change_support_username(msg, state):
    check = await db.check_admin(msg.from_user.id)
    if check:
        data = await state.get_data()
        if msg.text == '/cancel':
            await state.clear()
            await msg.answer(texts.support_menu.format(id=data['support_id'],
                                                       username=await db.get_support_username(data['support_id'])),
                             reply_markup=await kb.get_support_menu(data['support_id']))
        else:
            check = await db.get_support(msg.text)
            if check is None or check == data['support_id']:
                await state.clear()
                await db.change_support_username(data['support_id'], msg.text)
                await msg.answer(texts.support_menu.format(id=data['support_id'], username=msg.text),
                                 reply_markup=await kb.get_support_menu(data['support_id']))
            else:
                await msg.answer(texts.unique_support_username)
    else:
        await state.clear()
        await msg.answer(texts.forbidden)



@router.callback_query(kb.IdCallbackData.filter(F.action == 'remove_support_confirm'))
async def remove_support_confirm(callback_query, callback_data):
    check = await db.check_admin(callback_query.message.chat.id)
    if check:
        await callback_query.message.edit_text(texts.remove_support_confirm,
                                               reply_markup=await kb.get_remove_support_menu(callback_data.id))
    else:
        await callback_query.message.edit_text(texts.forbidden)


@router.callback_query(kb.IdCallbackData.filter(F.action == 'remove_support'))
async def remove_support(callback_query, callback_data):
    check = await db.check_admin(callback_query.message.chat.id)
    if check:
        await db.remove_support(callback_data.id)
        await callback_query.message.edit_text(texts.supports_menu, reply_markup=await kb.get_supports_menu())
    else:
        await callback_query.message.edit_text(texts.forbidden)


@router.callback_query(kb.ActionCallbackData.filter(F.action == 'admins_menu'))
async def admins_menu(callback_query):
    check = await db.check_admin(callback_query.message.chat.id)
    if check:
        await callback_query.message.edit_text(texts.admins_menu, reply_markup=await kb.get_admins_menu())
    else:
        await callback_query.message.edit_text(texts.forbidden)


@router.callback_query(kb.IdCallbackData.filter(F.action == 'admin_menu'))
async def admin_menu(callback_query, callback_data):
    check = await db.check_admin(callback_query.message.chat.id)
    name = await db.get_admin_name(callback_data.id)
    if check:
        await callback_query.message.edit_text(texts.admin_menu.format(id=callback_data.id, name=name[0]),
                                               reply_markup=await kb.get_admin_menu(callback_data.id))
    else:
        await callback_query.message.edit_text(texts.forbidden)


@router.callback_query(kb.ActionCallbackData.filter(F.action == 'add_admin'))
async def set_admin_id(callback_query, state):
    check = await db.check_admin(callback_query.message.chat.id)
    if check:
        await state.set_state(Form.admin_id)
        await callback_query.message.edit_text(texts.set_admin_id)
    else:
        await callback_query.message.edit_text(texts.forbidden)


@router.message(Form.admin_id)
async def set_admin_name(msg, state):
    check = await db.check_admin(msg.from_user.id)
    if check:
        if msg.text == '/cancel':
            await state.clear()
            await msg.answer(texts.admins_menu, reply_markup=await kb.get_admins_menu())
        elif msg.text.isdigit():
            check = await db.get_admin_name(msg.text)
            if check is None:
                await state.update_data(admin_id=msg.text)
                await state.set_state(Form.admin_name)
                await msg.answer(texts.set_admin_name)
            else:
                await msg.answer(texts.unique_admin_id)
        else:
            await msg.answer(texts.incorrect_admin_id)
    else:
        await state.clear()
        await msg.answer(texts.forbidden)


@router.message(Form.admin_name)
async def add_admin(msg, state):
    check = await db.check_admin(msg.from_user.id)
    if check:
        if msg.text == '/cancel':
            await state.clear()
            await msg.answer(texts.admins_menu, reply_markup=await kb.get_admins_menu())
        else:
            data = await state.get_data()
            await state.clear()
            await db.add_admin(data['admin_id'], msg.text)
            await msg.answer(texts.admin_menu.format(id=data['admin_id'], name=msg.text),
                             reply_markup=await kb.get_admin_menu(data['admin_id']))
    else:
        await state.clear()
        await msg.answer(texts.forbidden)


@router.callback_query(kb.IdCallbackData.filter(F.action == 'change_admin_name'))
async def set_new_admin_name(callback_query, callback_data, state):
    check = await db.check_admin(callback_query.message.chat.id)
    if check:
        await state.set_state(Form.admin_id)
        await state.update_data(admin_id=callback_data.id)
        await state.set_state(Form.new_admin_name)
        await callback_query.message.edit_text(texts.set_admin_name)
    else:
        await callback_query.message.edit_text(texts.forbidden)


@router.message(Form.new_admin_name)
async def change_admin_name(msg, state):
    check = await db.check_admin(msg.from_user.id)
    if check:
        data = await state.get_data()
        if msg.text == '/cancel':
            await state.clear()
            await msg.answer(texts.admin_menu.format(id=data['admin_id'],
                                                     name=await db.get_admin_name(data['admin_id'])),
                             reply_markup=await kb.get_admin_menu(data['admin_id']))
        else:
            await state.clear()
            await db.change_admin_name(data['admin_id'], msg.text)
            await msg.answer(texts.admin_menu.format(id=data['admin_id'], name=msg.text),
                             reply_markup=await kb.get_admin_menu(data['admin_id']))
    else:
        await state.clear()
        await msg.answer(texts.forbidden)


@router.callback_query(kb.IdCallbackData.filter(F.action == 'remove_admin_confirm'))
async def remove_admin_confirm(callback_query, callback_data):
    check = await db.check_admin(callback_query.message.chat.id)
    if check:
        await callback_query.message.edit_text(texts.remove_admin_confirm,
                                               reply_markup=await kb.get_remove_admin_menu(callback_data.id))
    else:
        await callback_query.message.edit_text(texts.forbidden)


@router.callback_query(kb.IdCallbackData.filter(F.action == 'remove_admin'))
async def remove_admin(callback_query, callback_data):
    check = await db.check_admin(callback_query.message.chat.id)
    if check:
        await db.remove_admin(callback_data.id)
        await callback_query.message.edit_text(texts.admins_menu, reply_markup=await kb.get_admins_menu())
    else:
        await callback_query.message.edit_text(texts.forbidden)