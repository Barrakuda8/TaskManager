from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import db.functions as db
import task_texts as texts


class ActionCallbackData(CallbackData, prefix='action'):
    action: str


class IdCallbackData(CallbackData, prefix='id'):
    action: str
    id: int


async def get_request_menu(request):
    menu = [[InlineKeyboardButton(text='Выполнен',
                                  callback_data=IdCallbackData(action='complete_request_confirm',
                                                               id=request).pack()),
             InlineKeyboardButton(text='Отменён',
                                  callback_data=IdCallbackData(action='cancel_request_confirm',
                                                               id=request).pack())]]
    return InlineKeyboardMarkup(inline_keyboard=menu)


async def get_complete_request_menu(request):
    menu = [[InlineKeyboardButton(text='Да',
                                  callback_data=IdCallbackData(action='complete_request',
                                                               id=request).pack()),
             InlineKeyboardButton(text='Нет',
                                  callback_data=IdCallbackData(action='request_menu',
                                                               id=request).pack())]]
    return InlineKeyboardMarkup(inline_keyboard=menu)


async def get_cancel_request_menu(request):
    menu = [[InlineKeyboardButton(text='Да',
                                  callback_data=IdCallbackData(action='cancel_request',
                                                               id=request).pack()),
             InlineKeyboardButton(text='Нет',
                                  callback_data=IdCallbackData(action='request_menu',
                                                               id=request).pack())]]
    return InlineKeyboardMarkup(inline_keyboard=menu)


async def get_main_menu():
    menu = [[InlineKeyboardButton(text='Саппорты', callback_data=ActionCallbackData(action='supports_menu').pack())],
            [InlineKeyboardButton(text='Администраторы', callback_data=ActionCallbackData(action='admins_menu').pack())]]
    return InlineKeyboardMarkup(inline_keyboard=menu)


async def get_supports_menu():
    menu = []
    for support in await db.get_supports():
        menu.append([InlineKeyboardButton(text=support[1], callback_data=IdCallbackData(action='support_menu',
                                                                                             id=support[0]).pack())])

    menu.append([InlineKeyboardButton(text='+ Добавить саппорта',
                                      callback_data=ActionCallbackData(action='add_support').pack())])

    menu.append([InlineKeyboardButton(text='Назад', callback_data=ActionCallbackData(action='main_menu').pack())])
    return InlineKeyboardMarkup(inline_keyboard=menu)


async def get_support_menu(support):
    menu = [
        [InlineKeyboardButton(text='Изменить username',
                              callback_data=IdCallbackData(action='change_support_username',
                                                           id=support).pack())],
        [InlineKeyboardButton(text='Убрать саппорта из базы',
                              callback_data=IdCallbackData(action='remove_support_confirm',
                                                           id=support).pack())],
        [InlineKeyboardButton(text='Назад', callback_data=ActionCallbackData(action='supports_menu').pack())]
    ]

    return InlineKeyboardMarkup(inline_keyboard=menu)


async def get_remove_support_menu(support):
    menu = [[InlineKeyboardButton(text='Да',
                                  callback_data=IdCallbackData(action='remove_support',
                                                               id=support).pack()),
             InlineKeyboardButton(text='Нет',
                                  callback_data=IdCallbackData(action='support_menu',
                                                               id=support).pack())]]
    return InlineKeyboardMarkup(inline_keyboard=menu)


async def get_admins_menu():
    menu = []
    for admin in await db.get_admins():
        menu.append([InlineKeyboardButton(text=admin[1], callback_data=IdCallbackData(action='admin_menu',
                                                                                           id=admin[0]).pack())])

    menu.append([InlineKeyboardButton(text='+ Добавить администратора',
                                      callback_data=ActionCallbackData(action='add_admin').pack())])

    menu.append([InlineKeyboardButton(text='Назад', callback_data=ActionCallbackData(action='main_menu').pack())])
    return InlineKeyboardMarkup(inline_keyboard=menu)


async def get_admin_menu(admin):
    menu = [
        [InlineKeyboardButton(text='Изменить имя',
                              callback_data=IdCallbackData(action='change_admin_name',
                                                           id=admin).pack())],
        [InlineKeyboardButton(text='Убрать администратора из базы',
                              callback_data=IdCallbackData(action='remove_admin_confirm',
                                                           id=admin).pack())],
        [InlineKeyboardButton(text='Назад', callback_data=ActionCallbackData(action='admins_menu').pack())]
    ]

    return InlineKeyboardMarkup(inline_keyboard=menu)


async def get_remove_admin_menu(admin):
    menu = [[InlineKeyboardButton(text='Да',
                                  callback_data=IdCallbackData(action='remove_admin',
                                                               id=admin).pack()),
             InlineKeyboardButton(text='Нет',
                                  callback_data=IdCallbackData(action='admin_menu',
                                                               id=admin).pack())]]
    return InlineKeyboardMarkup(inline_keyboard=menu)