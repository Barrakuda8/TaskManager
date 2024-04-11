import re
from aiogram import F, Router
from aiogram.filters import Command
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
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
    support_lead_id = State()
    admin_id = State()
    admin_name = State()
    team_name = State()
    new_support_username = State()
    new_support_id = State()
    new_support_lead_id = State()
    new_admin_name = State()
    new_team_name = State()


@router.message(Command("chat"))
async def get_chat_id(msg):
    await msg.answer(str(msg.chat.id))


@router.message(Command("completed_chat"))
async def set_completed_chat(msg):
    check = await db.check_admin(msg.from_user.id)
    if check:
        await db.set_completed_chat(msg.chat.id)
        await msg.answer(texts.completed_chat_set)
    else:
        await msg.answer(texts.forbidden_completed_chat)


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
            try:
                await bot.send_message(chat_id=support['id'],
                                       text=texts.request.format(request=request_id, buyer=buyer_id,
                                                                 support=support_id,
                                                                 status=texts.statuses['created'],
                                                                 created_at=created_at.replace(microsecond=0),
                                                                 started_at='-',
                                                                 completed_at='-', text=text),
                                       reply_markup=await kb.get_support_request_menu(request_id, False))
            except TelegramBadRequest:
                response_text = texts.chat_not_found.format(id=request_id)
            await bot.session.close()
        else:
            response_text = texts.support_not_found
    except AttributeError:
        response_text = texts.request_incorrect
    await msg.answer(response_text)


@router.callback_query(kb.IdCallbackData.filter(F.action == 'support_request_menu'))
async def support_request_menu(callback_query, callback_data):
    data = await db.get_request(callback_data.id)
    started_at = data['started_at'].replace(microsecond=0) if data['status'] in ['started', 'completed'] else '-'
    if data['status'] in ['created', 'started']:
        await callback_query.message.edit_text(texts.request.format(request=callback_data.id, buyer=data['buyer_id'],
                                                                    support=data['support'],
                                                                    status=texts.statuses[data['status']],
                                                                    created_at=data['created_at'].replace(microsecond=0),
                                                                    started_at=started_at,
                                                                    completed_at='-',
                                                                    text=data['text']),
                                               reply_markup=await kb.get_support_request_menu(callback_data.id,
                                                                                              data['status'] == 'started'))
    else:
        completed_at = data['completed_at'].replace(microsecond=0) if data['status'] == 'completed_at' else '-'
        await callback_query.message.edit_text(texts.request.format(request=callback_data.id, buyer=data['buyer_id'],
                                                                    support=data['support'],
                                                                    status=texts.statuses[data['status']],
                                                                    created_at=data['created_at'].replace(microsecond=0),
                                                                    started_at=started_at,
                                                                    completed_at=completed_at,
                                                                    text=data['text']))


@router.callback_query(kb.IdCallbackData.filter(F.action == 'start_request_confirm'))
async def start_request_confirm(callback_query, callback_data):
    check = await db.check_request_support(callback_data.id, callback_query.message.chat.id)
    if check:
        await callback_query.message.edit_text(texts.start_request_confirm,
                                               reply_markup=await kb.get_start_request_menu(callback_data.id))
    else:
        await callback_query.message.edit_text(texts.request_support_changed)


@router.callback_query(kb.IdCallbackData.filter(F.action == 'start_request'))
async def start_request(callback_query, callback_data):
    data = await db.change_status(callback_data.id, 'started')
    bot = Bot(token=config.TASK_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await bot.send_message(chat_id=data['chat'],
                           text=texts.request_started.format(request=callback_data.id, buyer=data['buyer_id']))
    await bot.session.close()
    await callback_query.message.edit_text(texts.request.format(request=callback_data.id, buyer=data['buyer_id'],
                                                                support=data['support'],
                                                                status=texts.statuses['started'],
                                                                created_at=data['created_at'].replace(microsecond=0),
                                                                started_at=data['started_at'].replace(microsecond=0),
                                                                completed_at='-',
                                                                text=data['text']),
                                           reply_markup=await kb.get_support_request_menu(callback_data.id, True))


@router.callback_query(kb.IdCallbackData.filter(F.action == 'complete_request_confirm'))
async def complete_request_confirm(callback_query, callback_data):
    check = await db.check_request_support(callback_data.id, callback_query.message.chat.id)
    if check:
        await callback_query.message.edit_text(texts.complete_request_confirm,
                                               reply_markup=await kb.get_complete_request_menu(callback_data.id))
    else:
        await callback_query.message.edit_text(texts.request_support_changed)


@router.callback_query(kb.IdCallbackData.filter(F.action == 'complete_request'))
async def complete_request(callback_query, callback_data):
    data = await db.change_status(callback_data.id, 'completed')
    bot = Bot(token=config.TASK_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await bot.send_message(chat_id=data['chat'],
                           text=texts.request_completed.format(request=callback_data.id, buyer=data['buyer_id']))
    await bot.session.close()
    completed_chat = await db.get_completed_chat()
    if completed_chat is not None:
        await bot.send_message(chat_id=completed_chat,
                               text=texts.request.format(request=callback_data.id, buyer=data['buyer_id'],
                                                         support=data['support'],
                                                         status=texts.statuses['completed'],
                                                         created_at=data['created_at'].replace(microsecond=0),
                                                         started_at=data['started_at'].replace(microsecond=0)
                                                         if data['started_at'] is not None else '-',
                                                         completed_at=data['completed_at'].replace(microsecond=0),
                                                         text=data['text']))
        await bot.session.close()
    await callback_query.message.edit_text(texts.request.format(request=callback_data.id, buyer=data['buyer_id'],
                                                                support=data['support'],
                                                                status=texts.statuses['completed'],
                                                                created_at=data['created_at'].replace(microsecond=0),
                                                                started_at=data['started_at'].replace(microsecond=0)
                                                                if data['started_at'] is not None else '-',
                                                                completed_at=data['completed_at'].replace(microsecond=0),
                                                                text=data['text']))


@router.callback_query(kb.IdCallbackData.filter(F.action == 'cancel_request_confirm'))
async def cancel_request_confirm(callback_query, callback_data):
    check = await db.check_request_support(callback_data.id, callback_query.message.chat.id)
    if check:
        await callback_query.message.edit_text(texts.cancel_request_confirm,
                                               reply_markup=await kb.get_cancel_request_menu(callback_data.id))
    else:
        await callback_query.message.edit_text(texts.request_support_changed)


@router.callback_query(kb.IdCallbackData.filter(F.action == 'cancel_request'))
async def cancel_request(callback_query, callback_data):
    data = await db.change_status(callback_data.id, 'canceled')
    bot = Bot(token=config.TASK_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await bot.send_message(chat_id=data['chat'],
                           text=texts.request_canceled.format(request=callback_data.id, buyer=data['buyer_id']))
    await bot.session.close()
    await callback_query.message.edit_text(texts.request.format(request=callback_data.id, buyer=data['buyer_id'],
                                                                support=data['support'],
                                                                status=texts.statuses['canceled'],
                                                                created_at=data['created_at'].replace(microsecond=0),
                                                                started_at=data['started_at'].replace(microsecond=0)
                                                                if data['started_at'] is not None else '-',
                                                                completed_at='-',
                                                                text=data['text']))


@router.message(Command("start"))
async def start(msg):
    if msg.chat.id > 0:
        check = await db.check_admin(msg.chat.id)
        lead = await db.get_lead(msg.chat.id)
        if check or lead is not None:
            support = await db.get_support(lead[0]) if lead is not None else None
            team = support['team'] if support is not None else '-'
            await msg.answer(texts.main_menu, reply_markup=await kb.get_main_menu(check, team))
        else:
            await msg.answer(texts.start_forbidden)


@router.callback_query(kb.ActionCallbackData.filter(F.action == 'main_menu'))
async def main_menu(callback_query):
    check = await db.check_admin(callback_query.message.chat.id)
    lead = await db.get_lead(callback_query.message.chat.id)
    if check or lead is not None:
        support = await db.get_support(lead[0]) if lead is not None else None
        team = support['team'] if support is not None else '-'
        await callback_query.message.edit_text(texts.main_menu, reply_markup=await kb.get_main_menu(check, team))
    else:
        await callback_query.message.edit_text(texts.forbidden)


@router.callback_query(kb.ActionCallbackData.filter(F.action == 'supports_menu'))
async def supports_menu(callback_query):
    check = await db.check_admin(callback_query.message.chat.id)
    if check:
        await callback_query.message.edit_text(texts.supports_menu, reply_markup=await kb.get_supports_menu())
    else:
        await callback_query.message.edit_text(texts.forbidden)


@router.callback_query(kb.ParamCallbackData.filter(F.action == 'support_menu'))
async def support_menu(callback_query, callback_data):
    check = await db.check_admin(callback_query.message.chat.id)
    support_data = await db.get_support(callback_data.param)
    if check:
        await callback_query.message.edit_text(texts.support_menu.format(id=support_data['id'],
                                                                         username=callback_data.param,
                                                                         team=support_data['team'],
                                                                         lead=support_data['lead_id']),
                                               reply_markup=await kb.get_support_menu(callback_data.param))
    else:
        await callback_query.message.edit_text(texts.forbidden)


@router.callback_query(kb.ActionCallbackData.filter(F.action == 'add_support'))
async def set_support_username(callback_query, state):
    check = await db.check_admin(callback_query.message.chat.id)
    if check:
        await state.set_state(Form.support_username)
        await callback_query.message.edit_text(texts.set_support_username)
    else:
        await callback_query.message.edit_text(texts.forbidden)


@router.message(Form.support_username)
async def set_support_id(msg, state):
    check = await db.check_admin(msg.from_user.id)
    if check:
        if msg.text == '/cancel':
            await state.clear()
            await msg.answer(texts.supports_menu, reply_markup=await kb.get_supports_menu())
        else:
            check = await db.get_support(msg.text)
            if check is None:
                await state.update_data(support_username=msg.text)
                await state.set_state(Form.support_id)
                await msg.answer(texts.set_support_id)
            else:
                await msg.answer(texts.unique_support_username)
    else:
        await state.clear()
        await msg.answer(texts.forbidden)


@router.message(Form.support_id)
async def set_support_team(msg, state):
    check = await db.check_admin(msg.from_user.id)
    if check:
        if msg.text == '/cancel':
            await state.clear()
            await msg.answer(texts.supports_menu, reply_markup=await kb.get_supports_menu())
        elif msg.text.isdigit() or (msg.text[0] == '-' and msg.text[1:].isdigit()):
            await state.update_data(support_id=msg.text)
            await msg.answer(texts.team_select,
                             reply_markup=await kb.get_team_select())
        else:
            await msg.answer(texts.incorrect_support_id)
    else:
        await state.clear()
        await msg.answer(texts.forbidden)


@router.callback_query(kb.ParamCallbackData.filter(F.action == 'team_select'))
async def set_support_lead_id(callback_query, callback_data, state):
    check = await db.check_admin(callback_query.message.chat.id)
    if check:
        await state.set_state(Form.team_name)
        await state.update_data(team_name=callback_data.param)
        await state.set_state(Form.support_lead_id)
        await callback_query.message.edit_text(texts.set_support_lead_id)
    else:
        await state.clear()
        await callback_query.message.edit_text(texts.forbidden)


@router.callback_query(kb.ActionCallbackData.filter(F.action == 'cancel_team_select'))
async def cancel_team_select(callback_query, state):
    await state.clear()
    check = await db.check_admin(callback_query.message.chat.id)
    if check:
        await callback_query.message.edit_text(texts.supports_menu, reply_markup=await kb.get_supports_menu())
    else:
        await callback_query.message.edit_text(texts.forbidden)


@router.message(Form.support_lead_id)
async def add_support(msg, state):
    check = await db.check_admin(msg.from_user.id)
    if check:
        skip = msg.text == '/skip'
        if msg.text == '/cancel':
            await state.clear()
            await msg.answer(texts.supports_menu, reply_markup=await kb.get_supports_menu())
        elif msg.text.isdigit() or skip:
            if not skip:
                check = await db.get_lead(msg.text)
            if skip or check is None:
                data = await state.get_data()
                await state.clear()
                await db.add_support(data['support_id'], data['support_username'], data['team_name'],
                                     None if skip else msg.text)
                await msg.answer(texts.support_menu.format(id=data['support_id'], username=data['support_username'],
                                                           team=data['team_name'],
                                                           lead=f'🟢 {msg.text}' if not skip else '🔴'),
                                 reply_markup=await kb.get_support_menu(data['support_username']))
            else:
                await msg.answer(texts.unique_support_lead_id)
        else:
            await msg.answer(texts.incorrect_support_lead_id)
    else:
        await state.clear()
        await msg.answer(texts.forbidden)


@router.callback_query(kb.ParamCallbackData.filter(F.action == 'change_support_username'))
async def set_new_support_username(callback_query, callback_data, state):
    check = await db.check_admin(callback_query.message.chat.id)
    if check:
        await state.set_state(Form.support_username)
        await state.update_data(support_username=callback_data.param)
        await state.set_state(Form.new_support_username)
        await callback_query.message.edit_text(texts.set_support_username)
    else:
        await callback_query.message.edit_text(texts.forbidden)


@router.message(Form.new_support_username)
async def change_support_username(msg, state):
    check = await db.check_admin(msg.from_user.id)
    if check:
        data = await state.get_data()
        support_data = await db.get_support(data['support_username'])
        if msg.text == '/cancel':
            await state.clear()
            await msg.answer(texts.support_menu.format(id=support_data['id'],
                                                       username=data['support_username'],
                                                       team=support_data['team'],
                                                       lead=support_data['lead_id']),
                             reply_markup=await kb.get_support_menu(data['support_username']))
        else:
            check = await db.get_support(msg.text)
            if check is None or msg.text == data['support_username']:
                await state.clear()
                await db.change_support_username(data['support_username'], msg.text)
                await msg.answer(texts.support_menu.format(id=support_data['id'], username=msg.text,
                                                           team=support_data['team'],
                                                           lead=support_data['lead_id']),
                                 reply_markup=await kb.get_support_menu(msg.text))
            else:
                await msg.answer(texts.unique_support_username)
    else:
        await state.clear()
        await msg.answer(texts.forbidden)


@router.callback_query(kb.ParamCallbackData.filter(F.action == 'change_support_id'))
async def set_new_support_id(callback_query, callback_data, state):
    check = await db.check_admin(callback_query.message.chat.id)
    if check:
        await state.set_state(Form.support_username)
        await state.update_data(support_username=callback_data.param)
        await state.set_state(Form.new_support_id)
        await callback_query.message.edit_text(texts.set_support_id)
    else:
        await callback_query.message.edit_text(texts.forbidden)


@router.message(Form.new_support_id)
async def change_support_id(msg, state):
    check = await db.check_admin(msg.from_user.id)
    if check:
        data = await state.get_data()
        support_data = await db.get_support(data['support_username'])
        if msg.text == '/cancel':
            await state.clear()
            await msg.answer(texts.support_menu.format(id=support_data['id'],
                                                       username=data['support_username'],
                                                       team=support_data['team'],
                                                       lead=support_data['lead_id']),
                             reply_markup=await kb.get_support_menu(data['support_username']))
        elif msg.text.isdigit() or (msg.text[0] == '-' and msg.text[1:].isdigit()):
            await state.clear()
            await db.change_support_id(data['support_username'], msg.text)
            await msg.answer(texts.support_menu.format(id=msg.text, username=data['support_username'],
                                                       team=support_data['team'],
                                                       lead=support_data['lead_id']),
                             reply_markup=await kb.get_support_menu(data['support_username']))
        else:
            await msg.answer(texts.incorrect_support_id)
    else:
        await state.clear()
        await msg.answer(texts.forbidden)


@router.callback_query(kb.ParamCallbackData.filter(F.action == 'change_support_lead_id'))
async def set_new_support_lead_id(callback_query, callback_data, state):
    check = await db.check_admin(callback_query.message.chat.id)
    if check:
        await state.set_state(Form.support_username)
        await state.update_data(support_username=callback_data.param)
        await state.set_state(Form.new_support_lead_id)
        await callback_query.message.edit_text(texts.set_new_support_lead_id)
    else:
        await callback_query.message.edit_text(texts.forbidden)


@router.message(Form.new_support_lead_id)
async def change_support_lead_id(msg, state):
    check = await db.check_admin(msg.from_user.id)
    if check:
        data = await state.get_data()
        support_data = await db.get_support(data['support_username'])
        clear = msg.text == '/clear'
        if msg.text == '/cancel':
            await state.clear()
            await msg.answer(texts.support_menu.format(id=support_data['id'],
                                                       username=data['support_username'],
                                                       team=support_data['team'],
                                                       lead=support_data['lead_id']),
                             reply_markup=await kb.get_support_menu(data['support_username']))
        elif msg.text.isdigit() or clear:
            if not clear:
                check = await db.get_lead(msg.text)
            if clear or check is None:
                data = await state.get_data()
                await state.clear()
                await db.change_support_lead(data['support_username'], msg.text if not clear else None)
                await msg.answer(texts.support_menu.format(id=support_data['id'], username=data['support_username'],
                                                           team=support_data['team'],
                                                           lead=f'🟢 {msg.text}' if not clear else '🔴'),
                                 reply_markup=await kb.get_support_menu(data['support_username']))
            else:
                await msg.answer(texts.unique_support_lead_id)
        else:
            await msg.answer(texts.incorrect_support_lead_id)
    else:
        await state.clear()
        await msg.answer(texts.forbidden)


@router.callback_query(kb.ParamCallbackData.filter(F.action == 'change_support_team'))
async def change_support_team_menu(callback_query, callback_data, state):
    check = await db.check_admin(callback_query.message.chat.id)
    if check:
        await state.set_state(Form.support_username)
        await state.update_data(support_username=callback_data.param)
        await callback_query.message.edit_text(texts.team_select, reply_markup=await kb.get_new_team_select())
    else:
        await callback_query.message.edit_text(texts.forbidden)


@router.callback_query(kb.ParamCallbackData.filter(F.action == 'new_team_select'))
async def change_support_team(callback_query, callback_data, state):
    data = await state.get_data()
    await state.clear()
    check = await db.check_admin(callback_query.message.chat.id)
    if check:
        await db.change_support_team(data['support_username'], callback_data.param)
        support_data = await db.get_support(data['support_username'])
        await callback_query.message.edit_text(texts.support_menu.format(id=support_data['id'],
                                                                         username=data['support_username'],
                                                                         team=support_data['team'],
                                                                         lead=support_data['lead_id']),
                                               reply_markup=await kb.get_support_menu(data['support_username']))
    else:
        await callback_query.message.edit_text(texts.forbidden)


@router.callback_query(kb.ActionCallbackData.filter(F.action == 'cancel_new_team_select'))
async def cancel_new_team_select(callback_query, state):
    data = await state.get_data()
    await state.clear()
    check = await db.check_admin(callback_query.message.chat.id)
    if check:
        support_data = await db.get_support(data['support_username'])
        await callback_query.message.edit_text(texts.support_menu.format(id=support_data['id'],
                                                                         username=data['support_username'],
                                                                         team=support_data['team'],
                                                                         lead=support_data['lead_id']),
                                               reply_markup=await kb.get_support_menu(data['support_username']))
    else:
        await callback_query.message.edit_text(texts.forbidden)


@router.callback_query(kb.ParamCallbackData.filter(F.action == 'remove_support_confirm'))
async def remove_support_confirm(callback_query, callback_data):
    check = await db.check_admin(callback_query.message.chat.id)
    if check:
        await callback_query.message.edit_text(texts.remove_support_confirm,
                                               reply_markup=await kb.get_remove_support_menu(callback_data.param))
    else:
        await callback_query.message.edit_text(texts.forbidden)


@router.callback_query(kb.ParamCallbackData.filter(F.action == 'remove_support'))
async def remove_support(callback_query, callback_data):
    check = await db.check_admin(callback_query.message.chat.id)
    if check:
        await db.remove_support(callback_data.param)
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
        await callback_query.message.edit_text(texts.admin_menu.format(id=callback_data.id, name=name),
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


@router.callback_query(kb.ActionCallbackData.filter(F.action == 'teams_menu'))
async def teams_menu(callback_query):
    check = await db.check_admin(callback_query.message.chat.id)
    if check:
        await callback_query.message.edit_text(texts.teams_menu, reply_markup=await kb.get_teams_menu())
    else:
        await callback_query.message.edit_text(texts.forbidden)


@router.callback_query(kb.ParamCallbackData.filter(F.action == 'team_menu'))
async def team_menu(callback_query, callback_data):
    check = await db.check_admin(callback_query.message.chat.id)
    team_data = await db.get_team(callback_data.param)
    if check:
        await callback_query.message.edit_text(texts.team_menu.format(name=callback_data.param,
                                                                      supports=team_data['supports'],
                                                                      leads=team_data['leads'],
                                                                      requests=team_data['requests']),
                                               reply_markup=await kb.get_team_menu(callback_data.param))
    else:
        await callback_query.message.edit_text(texts.forbidden)


@router.callback_query(kb.ActionCallbackData.filter(F.action == 'create_team'))
async def set_team_name(callback_query, state):
    check = await db.check_admin(callback_query.message.chat.id)
    if check:
        await state.set_state(Form.team_name)
        await callback_query.message.edit_text(texts.set_team_name)
    else:
        await callback_query.message.edit_text(texts.forbidden)


@router.message(Form.team_name)
async def create_team(msg, state):
    check = await db.check_admin(msg.from_user.id)
    if check:
        if msg.text == '/cancel':
            await state.clear()
            await msg.answer(texts.teams_menu, reply_markup=await kb.get_teams_menu())
        else:
            check = await db.get_team(msg.text)
            if check is None:
                await state.clear()
                await db.create_team(msg.text)
                await msg.answer(texts.team_menu.format(name=msg.text, supports='0', leads='-', requests='0'),
                                 reply_markup=await kb.get_team_menu(msg.text))
            else:
                await msg.answer(texts.unique_team_name)
    else:
        await state.clear()
        await msg.answer(texts.forbidden)


@router.callback_query(kb.ParamCallbackData.filter(F.action == 'change_team_name'))
async def set_new_team_name(callback_query, callback_data, state):
    check = await db.check_admin(callback_query.message.chat.id)
    if check:
        await state.set_state(Form.team_name)
        await state.update_data(team_name=callback_data.param)
        await state.set_state(Form.new_team_name)
        await callback_query.message.edit_text(texts.set_new_team_name)
    else:
        await callback_query.message.edit_text(texts.forbidden)


@router.message(Form.new_team_name)
async def change_team_name(msg, state):
    check = await db.check_admin(msg.from_user.id)
    if check:
        data = await state.get_data()
        team_data = await db.get_team(data['team_name'])
        if msg.text == '/cancel':
            await state.clear()
            await msg.answer(texts.team_menu.format(name=data['team_name'],
                                                    supports=team_data['supports'],
                                                    leads=team_data['leads'],
                                                    requests=team_data['requests']),
                             reply_markup=await kb.get_team_menu(data['team_name']))
        else:
            check = await db.get_team(msg.text)
            if check is None or msg.text == data['team_name']:
                await state.clear()
                await db.change_team_name(data['team_name'], msg.text)
                await msg.answer(texts.team_menu.format(name=msg.text, supports=team_data['supports'],
                                                        leads=team_data['leads'],
                                                        requests=team_data['requests']),
                                 reply_markup=await kb.get_team_menu(msg.text))
            else:
                await msg.answer(texts.unique_team_name)
    else:
        await state.clear()
        await msg.answer(texts.forbidden)


@router.callback_query(kb.ParamCallbackData.filter(F.action == 'delete_team_confirm'))
async def delete_team_confirm(callback_query, callback_data):
    check = await db.check_admin(callback_query.message.chat.id)
    if check:
        team_data = await db.get_team(callback_data.param)
        if team_data['supports'] == 0:
            await callback_query.message.edit_text(texts.delete_team_confirm,
                                                   reply_markup=await kb.get_delete_team_menu(callback_data.param))
        else:
            text = texts.not_empty_team + texts.team_menu.format(name=callback_data.param,
                                                                 supports=team_data['supports'],
                                                                 leads=team_data['leads'],
                                                                 requests=team_data['requests'])
            await callback_query.message.edit_text(text, reply_markup=await kb.get_team_menu(callback_data.param))
    else:
        await callback_query.message.edit_text(texts.forbidden)


@router.callback_query(kb.ParamCallbackData.filter(F.action == 'delete_team'))
async def delete_team(callback_query, callback_data):
    check = await db.check_admin(callback_query.message.chat.id)
    if check:
        await db.delete_team(callback_data.param)
        await callback_query.message.edit_text(texts.teams_menu, reply_markup=await kb.get_teams_menu())
    else:
        await callback_query.message.edit_text(texts.forbidden)


@router.callback_query(kb.ActionCallbackData.filter(F.action == 'requests_teams_menu'))
async def requests_teams_menu(callback_query):
    lead = await db.get_lead(callback_query.message.chat.id)
    check = await db.check_admin(callback_query.message.chat.id)
    if check or lead is not None:
        await callback_query.message.edit_text(texts.requests_teams_menu, reply_markup=await kb.get_requests_teams_menu())
    else:
        await callback_query.message.edit_text(texts.forbidden)


@router.callback_query(kb.ParamCallbackData.filter(F.action == 'requests_team_menu'))
async def requests_team_menu(callback_query, callback_data):
    lead = await db.get_lead(callback_query.message.chat.id)
    check = await db.check_admin(callback_query.message.chat.id)
    if check or lead is not None:
        await callback_query.message.edit_text(texts.requests_team_menu,
                                               reply_markup=await kb.get_requests_team_menu(callback_data.param, check))
    else:
        await callback_query.message.edit_text(texts.forbidden)


@router.callback_query(kb.DoubleParamCallbackData.filter(F.action == 'requests_menu'))
async def requests_menu(callback_query, callback_data):
    lead = await db.get_lead(callback_query.message.chat.id)
    check = await db.check_admin(callback_query.message.chat.id)
    if check or lead is not None:
        await callback_query.message.edit_text(texts.requests_menu,
                                               reply_markup=await kb.get_requests_menu(callback_data.first, callback_data.second))
    else:
        await callback_query.message.edit_text(texts.forbidden)


@router.callback_query(kb.IdCallbackData.filter(F.action == 'request_menu'))
async def request_menu(callback_query, callback_data):
    lead = await db.get_lead(callback_query.message.chat.id)
    check = await db.check_admin(callback_query.message.chat.id)
    if check or lead is not None:
        team = await db.get_request_team(callback_data.id)
        data = await db.get_request(callback_data.id)
        await callback_query.message.edit_text(texts.request.format(request=callback_data.id, buyer=data['buyer_id'],
                                                                    support=data['support'],
                                                                    status=texts.statuses[data['status']],
                                                                    created_at=data['created_at'].replace(microsecond=0),
                                                                    started_at=data['started_at'].replace(microsecond=0)
                                                                    if data['started_at'] is not None else '-',
                                                                    completed_at='-',
                                                                    text=data['text']),
                                               reply_markup=await kb.get_request_menu(callback_data.id, team,
                                                                                      data['status']))
    else:
        await callback_query.message.edit_text(texts.forbidden)


@router.callback_query(kb.IdCallbackData.filter(F.action == 'supports_select'))
async def supports_select(callback_query, callback_data):
    lead = await db.get_lead(callback_query.message.chat.id)
    check = await db.check_admin(callback_query.message.chat.id)
    if check or lead is not None:
        team = await db.get_request_team(callback_data.id)
        await callback_query.message.edit_text(texts.supports_select,
                                               reply_markup=await kb.get_supports_select_menu(callback_data.id,
                                                                                              team))
    else:
        await callback_query.message.edit_text(texts.forbidden)


@router.callback_query(kb.DoubleParamCallbackData.filter(F.action == 'change_requests_support'))
async def change_requests_support(callback_query, callback_data):
    lead = await db.get_lead(callback_query.message.chat.id)
    check = await db.check_admin(callback_query.message.chat.id)
    if check or lead is not None:
        await db.change_request_support(callback_data.first, callback_data.second)
        team = await db.get_request_team(callback_data.first)
        data = await db.get_request(callback_data.first)
        support = await db.get_support(callback_data.second)
        request_menu_text = texts.request.format(request=callback_data.first, buyer=data['buyer_id'],
                                                 support=data['support'],
                                                 status=texts.statuses[data['status']],
                                                 created_at=data['created_at'].replace(microsecond=0),
                                                 started_at=data['started_at'].replace(microsecond=0)
                                                 if data['started_at'] is not None else '-',
                                                 completed_at='-',
                                                 text=data['text'])
        response_text = texts.request_support_change_successful
        bot = Bot(token=config.TASK_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        try:
            await bot.send_message(chat_id=support['id'],
                                   text=request_menu_text,
                                   reply_markup=await kb.get_support_request_menu(callback_data.first, False))
        except TelegramBadRequest:
            response_text = texts.chat_not_found.format(id=callback_data.first)
        await bot.session.close()
        await callback_query.message.edit_text(response_text + '\n\n' + request_menu_text,
                                               reply_markup=await kb.get_request_menu(callback_data.first, team,
                                                                                      data['status']))
    else:
        await callback_query.message.edit_text(texts.forbidden)
