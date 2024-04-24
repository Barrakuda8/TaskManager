import calendar
import os
import re
import time
from datetime import datetime, timedelta
from uuid import uuid4
from pandas import ExcelWriter, DataFrame, set_option
from aiogram import F, Router
from aiogram.filters import Command
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import FSInputFile
from translate import Translator
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
    support_day_start = State()
    support_day_end = State()
    support_days_off = State()
    support_schedule = State()
    team_notification_time = State()
    team_notification_text = State()
    stats_period = State()


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
            english = support['english'] == '🟢'
            bot = Bot(token=config.TASK_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
            try:
                if not english:
                    message_text = texts.request.format(request=request_id, buyer=buyer_id, support=support_id,
                                                        status=texts.statuses['created'],
                                                        created_at=created_at.replace(microsecond=0),
                                                        started_at='-', completed_at='-', text=text)
                else:
                    translator = Translator(to_lang='en', from_lang='ru')
                    message_text = texts.request_eng.format(request=request_id, buyer=buyer_id, support=support_id,
                                                            status=texts.statuses_eng['created'],
                                                            created_at=created_at.replace(microsecond=0),
                                                            started_at='-', completed_at='-',
                                                            text=translator.translate(text))
                await bot.send_message(chat_id=support['id'], text=message_text,
                                       reply_markup=await kb.get_support_request_menu(request_id, 'created',
                                                                                      english))
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
    english = await db.get_request_english(callback_data.id)
    started_at = data['started_at'].replace(microsecond=0) if data['status'] in ['started', 'completed'] else '-'
    completed_at = data['completed_at'].replace(microsecond=0) if data['status'] == 'completed_at' else '-'

    if not english:
        text = texts.request.format(request=callback_data.id, buyer=data['buyer_id'], support=data['support'],
                                    status=texts.statuses[data['status']],
                                    created_at=data['created_at'].replace(microsecond=0), started_at=started_at,
                                    completed_at=completed_at, text=data['text'])
    else:
        translator = Translator(to_lang='en', from_lang='ru')
        text = texts.request_eng.format(request=callback_data.id, buyer=data['buyer_id'], support=data['support'],
                                        status=texts.statuses_eng[data['status']],
                                        created_at=data['created_at'].replace(microsecond=0), started_at=started_at,
                                        completed_at=completed_at, text=translator.translate(data['text']))

    if data['status'] in ['created', 'started']:
        await callback_query.message.edit_text(text, reply_markup=await kb.get_support_request_menu(callback_data.id,
                                                                                                    data['status'],
                                                                                                    english))
    else:
        await callback_query.message.edit_text(text)


@router.callback_query(kb.IdCallbackData.filter(F.action == 'start_request_confirm'))
async def start_request_confirm(callback_query, callback_data):
    check = await db.check_request_support(callback_data.id, callback_query.message.chat.id)
    status = await db.get_request_status(callback_data.id)
    if check and status in ['created', 'delayed']:
        english = await db.get_request_english(callback_data.id)
        await callback_query.message.edit_text(texts.start_request_confirm if not english
                                               else texts.start_request_confirm_eng,
                                               reply_markup=await kb.get_start_request_menu(callback_data.id, english))
    elif status not in ['created', 'delayed']:
        await callback_query.message.edit_text(texts.request_outdated)
    else:
        await callback_query.message.edit_text(texts.request_support_changed)


@router.callback_query(kb.IdCallbackData.filter(F.action == 'start_request'))
async def start_request(callback_query, callback_data):
    check = await db.check_request_support(callback_data.id, callback_query.message.chat.id)
    status = await db.get_request_status(callback_data.id)
    if check and status in ['created', 'delayed']:
        data = await db.change_status(callback_data.id, 'started')
        bot = Bot(token=config.TASK_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        await bot.send_message(chat_id=data['chat'],
                               text=texts.request_started.format(request=callback_data.id, buyer=data['buyer_id']))
        await bot.session.close()
        english = await db.get_request_english(callback_data.id)
        if not english:
            text = texts.request.format(request=callback_data.id, buyer=data['buyer_id'], support=data['support'],
                                        status=texts.statuses['started'],
                                        created_at=data['created_at'].replace(microsecond=0),
                                        started_at=data['started_at'].replace(microsecond=0), completed_at='-',
                                        text=data['text'])
        else:
            translator = Translator(to_lang='en', from_lang='ru')
            text = texts.request_eng.format(request=callback_data.id, buyer=data['buyer_id'], support=data['support'],
                                            status=texts.statuses_eng['started'],
                                            created_at=data['created_at'].replace(microsecond=0),
                                            started_at=data['started_at'].replace(microsecond=0), completed_at='-',
                                            text=translator.translate(data['text']))
        await callback_query.message.edit_text(text,
                                               reply_markup=await kb.get_support_request_menu(callback_data.id,
                                                                                              'started', english))
    elif status not in ['created', 'delayed']:
        await callback_query.message.edit_text(texts.request_outdated)
    else:
        await callback_query.message.edit_text(texts.request_support_changed)


@router.callback_query(kb.IdCallbackData.filter(F.action == 'complete_request_confirm'))
async def complete_request_confirm(callback_query, callback_data):
    check = await db.check_request_support(callback_data.id, callback_query.message.chat.id)
    status = await db.get_request_status(callback_data.id)
    if check and status in ['started', 'delayed']:
        english = await db.get_request_english(callback_data.id)
        await callback_query.message.edit_text(texts.complete_request_confirm if not english
                                               else texts.complete_request_confirm_eng,
                                               reply_markup=await kb.get_complete_request_menu(callback_data.id,
                                                                                               english))
    elif status not in ['started', 'delayed']:
        await callback_query.message.edit_text(texts.request_outdated)
    else:
        await callback_query.message.edit_text(texts.request_support_changed)


@router.callback_query(kb.IdCallbackData.filter(F.action == 'complete_request'))
async def complete_request(callback_query, callback_data):
    check = await db.check_request_support(callback_data.id, callback_query.message.chat.id)
    status = await db.get_request_status(callback_data.id)
    if check and status in ['started', 'delayed']:
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
                                                             started_at=data['started_at'].replace(microsecond=0),
                                                             completed_at=data['completed_at'].replace(microsecond=0),
                                                             text=data['text']))
            await bot.session.close()
        english = await db.get_request_english(callback_data.id)
        if not english:
            text = texts.request.format(request=callback_data.id, buyer=data['buyer_id'], support=data['support'],
                                        status=texts.statuses['completed'],
                                        created_at=data['created_at'].replace(microsecond=0),
                                        started_at=data['started_at'].replace(microsecond=0),
                                        completed_at=data['completed_at'].replace(microsecond=0), text=data['text'])
        else:
            translator = Translator(to_lang='en', from_lang='ru')
            text = texts.request_eng.format(request=callback_data.id, buyer=data['buyer_id'], support=data['support'],
                                            status=texts.statuses_eng['completed'],
                                            created_at=data['created_at'].replace(microsecond=0),
                                            started_at=data['started_at'].replace(microsecond=0),
                                            completed_at=data['completed_at'].replace(microsecond=0),
                                            text=translator.translate(data['text']))
        await callback_query.message.edit_text(text)
    elif status not in ['started', 'delayed']:
        await callback_query.message.edit_text(texts.request_outdated)
    else:
        await callback_query.message.edit_text(texts.request_support_changed)


@router.callback_query(kb.IdCallbackData.filter(F.action == 'cancel_request_confirm'))
async def cancel_request_confirm(callback_query, callback_data):
    check = await db.check_request_support(callback_data.id, callback_query.message.chat.id)
    status = await db.get_request_status(callback_data.id)
    if check and status in ['started', 'delayed']:
        english = await db.get_request_english(callback_data.id)
        await callback_query.message.edit_text(texts.cancel_request_confirm if not english
                                               else texts.cancel_request_confirm_eng,
                                               reply_markup=await kb.get_cancel_request_menu(callback_data.id, english))
    elif status not in ['started', 'delayed']:
        await callback_query.message.edit_text(texts.request_outdated)
    else:
        await callback_query.message.edit_text(texts.request_support_changed)


@router.callback_query(kb.IdCallbackData.filter(F.action == 'cancel_request'))
async def cancel_request(callback_query, callback_data):
    check = await db.check_request_support(callback_data.id, callback_query.message.chat.id)
    status = await db.get_request_status(callback_data.id)
    if check and status in ['started', 'delayed']:
        data = await db.change_status(callback_data.id, 'canceled')
        bot = Bot(token=config.TASK_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        await bot.send_message(chat_id=data['chat'],
                               text=texts.request_canceled.format(request=callback_data.id, buyer=data['buyer_id']))
        await bot.session.close()
        english = await db.get_request_english(callback_data.id)
        if not english:
            text = texts.request.format(request=callback_data.id, buyer=data['buyer_id'], support=data['support'],
                                        status=texts.statuses['canceled'],
                                        created_at=data['created_at'].replace(microsecond=0),
                                        started_at=data['started_at'].replace(microsecond=0),
                                        completed_at='-', text=data['text'])
        else:
            translator = Translator(to_lang='en', from_lang='ru')
            text = texts.request_eng.format(request=callback_data.id, buyer=data['buyer_id'], support=data['support'],
                                            status=texts.statuses_eng['canceled'],
                                            created_at=data['created_at'].replace(microsecond=0),
                                            started_at=data['started_at'].replace(microsecond=0),
                                            completed_at='-', text=translator.translate(data['text']))
        await callback_query.message.edit_text(text)
    elif status not in ['started', 'delayed']:
        await callback_query.message.edit_text(texts.request_outdated)
    else:
        await callback_query.message.edit_text(texts.request_support_changed)


@router.callback_query(kb.IdCallbackData.filter(F.action == 'delay_request_confirm'))
async def delay_request_confirm(callback_query, callback_data):
    check = await db.check_request_support(callback_data.id, callback_query.message.chat.id)
    status = await db.get_request_status(callback_data.id)
    if check and status == 'started':
        english = await db.get_request_english(callback_data.id)
        await callback_query.message.edit_text(texts.delay_request_confirm if not english
                                               else texts.delay_request_confirm_eng,
                                               reply_markup=await kb.get_delay_request_menu(callback_data.id, english))
    elif status != 'started':
        await callback_query.message.edit_text(texts.request_outdated)
    else:
        await callback_query.message.edit_text(texts.request_support_changed)


@router.callback_query(kb.IdCallbackData.filter(F.action == 'delay_request'))
async def delay_request(callback_query, callback_data):
    check = await db.check_request_support(callback_data.id, callback_query.message.chat.id)
    status = await db.get_request_status(callback_data.id)
    if check and status == 'started':
        data = await db.change_status(callback_data.id, 'delayed')
        bot = Bot(token=config.TASK_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        await bot.send_message(chat_id=data['chat'],
                               text=texts.request_delayed.format(request=callback_data.id, buyer=data['buyer_id']))
        await bot.session.close()
        english = await db.get_request_english(callback_data.id)
        if not english:
            text = texts.request.format(request=callback_data.id, buyer=data['buyer_id'], support=data['support'],
                                        status=texts.statuses['delayed'],
                                        created_at=data['created_at'].replace(microsecond=0),
                                        started_at=data['started_at'].replace(microsecond=0),
                                        completed_at='-', text=data['text'])
        else:
            translator = Translator(to_lang='en', from_lang='ru')
            text = texts.request_eng.format(request=callback_data.id, buyer=data['buyer_id'], support=data['support'],
                                            status=texts.statuses_eng['delayed'],
                                            created_at=data['created_at'].replace(microsecond=0),
                                            started_at=data['started_at'].replace(microsecond=0),
                                            completed_at='-', text=translator.translate(data['text']))
        await callback_query.message.edit_text(text,
                                               reply_markup=await kb.get_support_request_menu(callback_data.id,
                                                                                              'delayed', english))
    elif status != 'started':
        await callback_query.message.edit_text(texts.request_outdated)
    else:
        await callback_query.message.edit_text(texts.request_support_changed)


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
                                                                         lead=support_data['lead_id'],
                                                                         english=support_data['english']),
                                               reply_markup=await kb.get_support_menu(callback_data.param,
                                                                                      support_data['english']))
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
                                                           lead=f'🟢 {msg.text}' if not skip else '🔴',
                                                           english='🔴'),
                                 reply_markup=await kb.get_support_menu(data['support_username'], False))
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
                                                       lead=support_data['lead_id'],
                                                       english=support_data['english']),
                             reply_markup=await kb.get_support_menu(data['support_username'],
                                                                    support_data['english']))
        else:
            check = await db.get_support(msg.text)
            if check is None or msg.text == data['support_username']:
                await state.clear()
                await db.change_support_username(data['support_username'], msg.text)
                await msg.answer(texts.support_menu.format(id=support_data['id'], username=msg.text,
                                                           team=support_data['team'],
                                                           lead=support_data['lead_id'],
                                                           english=support_data['english']),
                                 reply_markup=await kb.get_support_menu(msg.text,
                                                                        support_data['english']))
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
                                                       lead=support_data['lead_id'],
                                                       english=support_data['english']),
                             reply_markup=await kb.get_support_menu(data['support_username'],
                                                                    support_data['english']))
        elif msg.text.isdigit() or (msg.text[0] == '-' and msg.text[1:].isdigit()):
            await state.clear()
            await db.change_support_id(data['support_username'], msg.text)
            await msg.answer(texts.support_menu.format(id=msg.text, username=data['support_username'],
                                                       team=support_data['team'],
                                                       lead=support_data['lead_id'],
                                                       english=support_data['english']),
                             reply_markup=await kb.get_support_menu(data['support_username'],
                                                                    support_data['english']))
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
                                                       lead=support_data['lead_id'],
                                                       english=support_data['english']),
                             reply_markup=await kb.get_support_menu(data['support_username'],
                                                                    support_data['english']))
        elif msg.text.isdigit() or clear:
            if not clear:
                check = await db.get_lead(msg.text)
            if clear or check is None:
                await state.clear()
                await db.change_support_lead(data['support_username'], msg.text if not clear else None)
                await msg.answer(texts.support_menu.format(id=support_data['id'], username=data['support_username'],
                                                           team=support_data['team'],
                                                           lead=f'🟢 {msg.text}' if not clear else '🔴',
                                                           english=support_data['english']),
                                 reply_markup=await kb.get_support_menu(data['support_username'],
                                                                        support_data['english']))
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
                                                                         lead=support_data['lead_id'],
                                                                         english=support_data['english']),
                                               reply_markup=await kb.get_support_menu(data['support_username'],
                                                                                      support_data['english']))
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
                                                                         lead=support_data['lead_id'],
                                                                         english=support_data['english']),
                                               reply_markup=await kb.get_support_menu(data['support_username'],
                                                                                      support_data['english']))
    else:
        await callback_query.message.edit_text(texts.forbidden)


@router.callback_query(kb.ParamCallbackData.filter(F.action == 'change_english'))
async def change_english(callback_query, callback_data):
    check = await db.check_admin(callback_query.message.chat.id)
    if check:
        await db.change_english(callback_data.param)
        support_data = await db.get_support(callback_data.param)
        await callback_query.message.edit_text(texts.support_menu.format(id=support_data['id'],
                                                                         username=callback_data.param,
                                                                         team=support_data['team'],
                                                                         lead=support_data['lead_id'],
                                                                         english=support_data['english']),
                                               reply_markup=await kb.get_support_menu(callback_data.param,
                                                                                      support_data['english']))
    else:
        await callback_query.message.edit_text(texts.forbidden)


@router.callback_query(kb.ParamCallbackData.filter(F.action == 'support_schedule_menu'))
async def support_schedule_menu(callback_query, callback_data):
    check = await db.check_admin(callback_query.message.chat.id)
    schedule = await db.get_support_schedule(callback_data.param)
    if check:
        await callback_query.message.edit_text(texts.support_schedule_menu.format(username=callback_data.param,
                                                                                  day_start=schedule['day_start'],
                                                                                  day_end=schedule['day_end'],
                                                                                  days_off=schedule['days_off']),
                                               reply_markup=await kb.get_support_schedule_menu(callback_data.param))
    else:
        await callback_query.message.edit_text(texts.forbidden)


@router.callback_query(kb.ParamCallbackData.filter(F.action == 'change_support_day_start'))
async def set_support_day_start(callback_query, callback_data, state):
    check = await db.check_admin(callback_query.message.chat.id)
    if check:
        await state.set_state(Form.support_username)
        await state.update_data(support_username=callback_data.param)
        await state.set_state(Form.support_day_start)
        await callback_query.message.edit_text(texts.set_support_day_start)
    else:
        await callback_query.message.edit_text(texts.forbidden)


@router.message(Form.support_day_start)
async def change_support_day_start(msg, state):
    check = await db.check_admin(msg.from_user.id)
    if check:
        data = await state.get_data()
        schedule = await db.get_support_schedule(data['support_username'])
        clear = msg.text == '/clear'
        if msg.text == '/cancel':
            await state.clear()
            await msg.answer(texts.support_schedule_menu.format(username=data['support_username'],
                                                                day_start=schedule['day_start'],
                                                                day_end=schedule['day_end'],
                                                                days_off=schedule['days_off']),
                             reply_markup=await kb.get_support_schedule_menu(data['support_username']))
        else:
            try:
                if not clear:
                    datetime.strptime(msg.text, "%H:%M")
                await state.clear()
                await db.change_support_day_start(data['support_username'], msg.text + ':00' if not clear else None)
                await msg.answer(texts.support_schedule_menu.format(username=data['support_username'],
                                                                    day_start=msg.text if not clear else '-',
                                                                    day_end=schedule['day_end'],
                                                                    days_off=schedule['days_off']),
                                 reply_markup=await kb.get_support_schedule_menu(data['support_username']))
            except ValueError:
                await msg.answer(texts.incorrect_support_time_format)
    else:
        await state.clear()
        await msg.answer(texts.forbidden)


@router.callback_query(kb.ParamCallbackData.filter(F.action == 'change_support_day_end'))
async def set_support_day_end(callback_query, callback_data, state):
    check = await db.check_admin(callback_query.message.chat.id)
    if check:
        await state.set_state(Form.support_username)
        await state.update_data(support_username=callback_data.param)
        await state.set_state(Form.support_day_end)
        await callback_query.message.edit_text(texts.set_support_day_end)
    else:
        await callback_query.message.edit_text(texts.forbidden)


@router.message(Form.support_day_end)
async def change_support_day_end(msg, state):
    check = await db.check_admin(msg.from_user.id)
    if check:
        data = await state.get_data()
        schedule = await db.get_support_schedule(data['support_username'])
        clear = msg.text == '/clear'
        if msg.text == '/cancel':
            await state.clear()
            await msg.answer(texts.support_schedule_menu.format(username=data['support_username'],
                                                                day_start=schedule['day_start'],
                                                                day_end=schedule['day_end'],
                                                                days_off=schedule['days_off']),
                             reply_markup=await kb.get_support_schedule_menu(data['support_username']))
        else:
            try:
                if not clear:
                    datetime.strptime(msg.text, "%H:%M")
                await state.clear()
                await db.change_support_day_end(data['support_username'], msg.text + ':00' if not clear else None)
                await msg.answer(texts.support_schedule_menu.format(username=data['support_username'],
                                                                    day_start=schedule['day_start'],
                                                                    day_end=msg.text if not clear else '-',
                                                                    days_off=schedule['days_off']),
                                 reply_markup=await kb.get_support_schedule_menu(data['support_username']))
            except ValueError:
                await msg.answer(texts.incorrect_support_time_format)
    else:
        await state.clear()
        await msg.answer(texts.forbidden)


@router.callback_query(kb.ParamCallbackData.filter(F.action == 'change_support_days_off'))
async def set_support_days_off(callback_query, callback_data, state):
    check = await db.check_admin(callback_query.message.chat.id)
    if check:
        await state.set_state(Form.support_username)
        await state.update_data(support_username=callback_data.param)
        await state.set_state(Form.support_days_off)
        await callback_query.message.edit_text(texts.set_support_days_off)
    else:
        await callback_query.message.edit_text(texts.forbidden)


@router.message(Form.support_days_off)
async def change_support_days_off(msg, state):
    check = await db.check_admin(msg.from_user.id)
    if check:
        data = await state.get_data()
        schedule = await db.get_support_schedule(data['support_username'])
        clear = msg.text == '/clear'
        if msg.text == '/cancel':
            await state.clear()
            await msg.answer(texts.support_schedule_menu.format(username=data['support_username'],
                                                                day_start=schedule['day_start'],
                                                                day_end=schedule['day_end'],
                                                                days_off=schedule['days_off']),
                             reply_markup=await kb.get_support_schedule_menu(data['support_username']))
        else:
            days = ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ', 'ВС']
            entered_days = msg.text.split(' ')
            result_days = []
            result = True
            for day in entered_days:
                day = day.upper()
                if day not in days:
                    result = False
                else:
                    result_days.append(days.index(day))
            result_days.sort()
            if clear or result:
                await state.clear()
                await db.change_support_days_off(data['support_username'], [str(i) for i in result_days] if not clear else None)
                await msg.answer(texts.support_schedule_menu.format(username=data['support_username'],
                                                                    day_start=schedule['day_start'],
                                                                    day_end=schedule['day_end'],
                                                                    days_off=', '.join(
                                                                        [days[day] for day in result_days]
                                                                    ) if not clear else '-'),
                                 reply_markup=await kb.get_support_schedule_menu(data['support_username']))
            else:
                await msg.answer(texts.incorrect_support_days_off)
    else:
        await state.clear()
        await msg.answer(texts.forbidden)


@router.callback_query(kb.ParamCallbackData.filter(F.action == 'change_support_schedule'))
async def set_support_schedule(callback_query, callback_data, state):
    check = await db.check_admin(callback_query.message.chat.id)
    if check:
        await state.set_state(Form.support_username)
        await state.update_data(support_username=callback_data.param)
        await state.set_state(Form.support_schedule)
        await callback_query.message.edit_text(texts.set_support_schedule)
    else:
        await callback_query.message.edit_text(texts.forbidden)


@router.message(Form.support_schedule)
async def change_support_schedule(msg, state):
    check = await db.check_admin(msg.from_user.id)
    if check:
        data = await state.get_data()
        if msg.text == '/cancel':
            await state.clear()
            schedule = await db.get_support_schedule(data['support_username'])
            await msg.answer(texts.support_schedule_menu.format(username=data['support_username'],
                                                                day_start=schedule['day_start'],
                                                                day_end=schedule['day_end'],
                                                                days_off=schedule['days_off']),
                             reply_markup=await kb.get_support_schedule_menu(data['support_username']))
        elif msg.text == '/clear':
            await state.clear()
            await db.change_support_day_start(data['support_username'], None)
            await db.change_support_day_end(data['support_username'], None)
            await db.change_support_days_off(data['support_username'], None)
            await msg.answer(texts.support_schedule_menu.format(username=data['support_username'],
                                                                day_start='-', day_end='-', days_off='-'),
                             reply_markup=await kb.get_support_schedule_menu(data['support_username']))
        else:
            error = False
            params = msg.text.split('\n')
            if len(params) == 3:
                try:
                    datetime.strptime(params[0], '%H:%M')
                    datetime.strptime(params[1], '%H:%M')
                except ValueError:
                    error = True

                if not error:
                    days = ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ', 'ВС']
                    entered_days = params[2].split(' ')
                    result_days = []
                    for day in entered_days:
                        day = day.upper()
                        if day not in days:
                            error = True
                        else:
                            result_days.append(days.index(day))
                    result_days.sort()
                    if not error:
                        await state.clear()
                        await db.change_support_day_start(data['support_username'], params[0] + ':00')
                        await db.change_support_day_end(data['support_username'], params[1] + ':00')
                        await db.change_support_days_off(data['support_username'], [str(i) for i in result_days])
                        await msg.answer(texts.support_schedule_menu.format(username=data['support_username'],
                                                                            day_start=params[0],
                                                                            day_end=params[1],
                                                                            days_off=', '.join(
                                                                                [days[day] for day in result_days]
                                                                            )),
                                         reply_markup=await kb.get_support_schedule_menu(data['support_username']))
            else:
                error = True
            if error:
                await msg.answer(texts.incorrect_support_schedule)
    else:
        await state.clear()
        await msg.answer(texts.forbidden)


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


@router.callback_query(kb.ParamCallbackData.filter(F.action == 'team_notification_menu'))
async def team_notification_menu(callback_query, callback_data):
    check = await db.check_admin(callback_query.message.chat.id)
    if check:
        notification = await db.get_team_notification(callback_data.param)
        await callback_query.message.edit_text(texts.team_notification_menu.format(name=callback_data.param,
                                                                                   time=notification['time'],
                                                                                   text=notification['text']),
                                               reply_markup=await kb.get_team_notification_menu(callback_data.param))
    else:
        await callback_query.message.edit_text(texts.forbidden)


@router.callback_query(kb.ParamCallbackData.filter(F.action == 'change_team_notification_time'))
async def set_new_team_notification_time(callback_query, callback_data, state):
    check = await db.check_admin(callback_query.message.chat.id)
    if check:
        await state.set_state(Form.team_name)
        await state.update_data(team_name=callback_data.param)
        await state.set_state(Form.team_notification_time)
        await callback_query.message.edit_text(texts.set_team_notification_time)
    else:
        await callback_query.message.edit_text(texts.forbidden)


@router.message(Form.team_notification_time)
async def change_team_notification_time(msg, state):
    check = await db.check_admin(msg.from_user.id)
    if check:
        data = await state.get_data()
        notification = await db.get_team_notification(data['team_name'])
        clear = msg.text == '/clear'
        if msg.text == '/cancel':
            await state.clear()
            await msg.answer(texts.team_notification_menu.format(name=data['team_name'],
                                                                 time=notification['time'],
                                                                 text=notification['text']),
                             reply_markup=await kb.get_team_notification_menu(data['team_name']))
        elif msg.text.isdigit() or clear:
            await state.clear()
            await db.change_team_notification_time(data['team_name'], msg.text if not clear else None)
            await msg.answer(texts.team_notification_menu.format(name=data['team_name'],
                                                                 time=msg.text if not clear else '-',
                                                                 text=notification['text']),
                             reply_markup=await kb.get_team_notification_menu(data['team_name']))
        else:
            await msg.answer(texts.incorrect_team_notification_time)
    else:
        await state.clear()
        await msg.answer(texts.forbidden)


@router.callback_query(kb.ParamCallbackData.filter(F.action == 'change_team_notification_text'))
async def set_new_team_notification_text(callback_query, callback_data, state):
    check = await db.check_admin(callback_query.message.chat.id)
    if check:
        await state.set_state(Form.team_name)
        await state.update_data(team_name=callback_data.param)
        await state.set_state(Form.team_notification_text)
        await callback_query.message.edit_text(texts.set_team_notification_text)
    else:
        await callback_query.message.edit_text(texts.forbidden)


@router.message(Form.team_notification_text)
async def change_team_notification_text(msg, state):
    check = await db.check_admin(msg.from_user.id)
    if check:
        data = await state.get_data()
        notification = await db.get_team_notification(data['team_name'])
        clear = msg.text == '/clear'
        if msg.text == '/cancel':
            await state.clear()
            await msg.answer(texts.team_notification_menu.format(name=data['team_name'],
                                                                 time=notification['time'],
                                                                 text=notification['text']),
                             reply_markup=await kb.get_team_notification_menu(data['team_name']))
        else:
            await state.clear()
            await db.change_team_notification_text(data['team_name'], msg.text if not clear else None)
            await msg.answer(texts.team_notification_menu.format(name=data['team_name'],
                                                                 time=notification['time'],
                                                                 text=msg.text if not clear else '-'),
                             reply_markup=await kb.get_team_notification_menu(data['team_name']))
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
                                               reply_markup=await kb.get_requests_menu(callback_data.first,
                                                                                       callback_data.second))
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
        english = support['english'] == '🟢'
        if not english:
            request_menu_text = texts.request.format(request=callback_data.first, buyer=data['buyer_id'],
                                                     support=data['support'],
                                                     status=texts.statuses[data['status']],
                                                     created_at=data['created_at'].replace(microsecond=0),
                                                     started_at=data['started_at'].replace(microsecond=0)
                                                     if data['started_at'] is not None else '-',
                                                     completed_at='-',
                                                     text=data['text'])
        else:
            translator = Translator(to_lang='en', from_lang='ru')
            request_menu_text = texts.request_eng.format(request=callback_data.first, buyer=data['buyer_id'],
                                                         support=data['support'],
                                                         status=texts.statuses_eng[data['status']],
                                                         created_at=data['created_at'].replace(microsecond=0),
                                                         started_at=data['started_at'].replace(microsecond=0)
                                                         if data['started_at'] is not None else '-',
                                                         completed_at='-',
                                                         text=translator.translate(data['text']))
        response_text = texts.request_support_change_successful
        bot = Bot(token=config.TASK_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        try:
            await bot.send_message(chat_id=support['id'],
                                   text=request_menu_text,
                                   reply_markup=await kb.get_support_request_menu(callback_data.first, data['status'],
                                                                                  english))
        except TelegramBadRequest:
            response_text = texts.chat_not_found.format(id=callback_data.first)
        await bot.session.close()
        await callback_query.message.edit_text(response_text + '\n\n' + request_menu_text,
                                               reply_markup=await kb.get_request_menu(callback_data.first, team,
                                                                                      data['status']))
    else:
        await callback_query.message.edit_text(texts.forbidden)


@router.callback_query(kb.ActionCallbackData.filter(F.action == 'get_requests_stats'))
async def set_stats_period(callback_query, state):
    check = await db.check_admin(callback_query.message.chat.id)
    if check:
        await state.set_state(Form.stats_period)
        await callback_query.message.edit_text(texts.set_stats_period)
    else:
        await callback_query.message.edit_text(texts.forbidden)


@router.message(Form.stats_period)
async def get_requests_stats(msg, state):
    check = await db.check_admin(msg.chat.id)
    if check:
        if msg.text == '/cancel':
            await state.clear()
            await msg.answer(texts.main_menu, reply_markup=await kb.get_main_menu(True, '-'))
        elif msg.text.isdigit():
            await state.clear()
            days = int(msg.text)
            today = datetime.now().replace(
                microsecond=0,
                second=0,
                minute=0,
                hour=0
            )
            date = today - timedelta(days=days - 1)
            requests = await db.get_requests_stats(date)
            current_gmt = time.gmtime()
            time_stamp = calendar.timegm(current_gmt)
            file_path = f'stats_files/{time_stamp}-{uuid4().hex}.xlsx'
            if len(requests) > 0:
                data = []
                for request in requests:
                    result = list(request)
                    result[4] = str(result[4])
                    result[5] = texts.statuses[result[5]][2:]
                    data.append(result)
                df = DataFrame(data=data, columns=['ID', 'buyer_id', 'support', 'text', 'chat', 'status', 'created_at',
                               'started_at', 'completed_at']).set_index('ID')
                with ExcelWriter(file_path) as writer:
                    sheet_name = 'Запросы'
                    df.to_excel(writer, sheet_name=sheet_name)
                    worksheet = writer.sheets[sheet_name]
                    for idx, col in enumerate(df):
                        series = df[col]
                        if idx != 2:
                            max_len = max((
                                series.astype(str).map(len).max(),
                                len(str(series.name))
                            )) + 1
                        else:
                            max_len = 20
                        worksheet.set_column(idx + 1, idx + 1, max_len)
                await msg.reply_document(FSInputFile(file_path, filename=f"Requests-Stats-{time_stamp}.xlsx"))
                os.remove(file_path)
            else:
                await msg.answer(texts.empty_stats)
            await msg.answer(texts.main_menu, reply_markup=await kb.get_main_menu(True, '-'))
        else:
            msg.answer(texts.incorrect_stats_period)
    else:
        await msg.answer(texts.main_menu, reply_markup=await kb.get_main_menu(True, '-'))
