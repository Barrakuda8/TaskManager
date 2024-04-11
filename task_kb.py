from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import db.functions as db
import task_texts as texts


class ActionCallbackData(CallbackData, prefix='action'):
    action: str


class IdCallbackData(CallbackData, prefix='id'):
    action: str
    id: int


class ParamCallbackData(CallbackData, prefix='param'):
    action: str
    param: str


class DoubleParamCallbackData(CallbackData, prefix='double'):
    action: str
    first: str
    second: str


async def get_support_request_menu(request, is_started):
    menu = [[InlineKeyboardButton(text='Выполнен',
                                  callback_data=IdCallbackData(action='complete_request_confirm',
                                                               id=request).pack())],
            [InlineKeyboardButton(text='Отменён',
                                  callback_data=IdCallbackData(action='cancel_request_confirm',
                                                               id=request).pack())]]
    if not is_started:
        menu.insert(1, [InlineKeyboardButton(text='Принят в работу', callback_data=IdCallbackData(
            action='start_request_confirm',
            id=request).pack())])
    return InlineKeyboardMarkup(inline_keyboard=menu)


async def get_complete_request_menu(request):
    menu = [[InlineKeyboardButton(text='Да',
                                  callback_data=IdCallbackData(action='complete_request',
                                                               id=request).pack()),
             InlineKeyboardButton(text='Нет',
                                  callback_data=IdCallbackData(action='support_request_menu',
                                                               id=request).pack())]]
    return InlineKeyboardMarkup(inline_keyboard=menu)


async def get_cancel_request_menu(request):
    menu = [[InlineKeyboardButton(text='Да',
                                  callback_data=IdCallbackData(action='cancel_request',
                                                               id=request).pack()),
             InlineKeyboardButton(text='Нет',
                                  callback_data=IdCallbackData(action='support_request_menu',
                                                               id=request).pack())]]
    return InlineKeyboardMarkup(inline_keyboard=menu)


async def get_start_request_menu(request):
    menu = [[InlineKeyboardButton(text='Да',
                                  callback_data=IdCallbackData(action='start_request',
                                                               id=request).pack()),
             InlineKeyboardButton(text='Нет',
                                  callback_data=IdCallbackData(action='support_request_menu',
                                                               id=request).pack())]]
    return InlineKeyboardMarkup(inline_keyboard=menu)


async def get_main_menu(admin, team):
    if admin:
        menu = [[InlineKeyboardButton(text='Исполнители',
                                      callback_data=ActionCallbackData(action='supports_menu').pack())],
                [InlineKeyboardButton(text='Администраторы',
                                      callback_data=ActionCallbackData(action='admins_menu').pack())],
                [InlineKeyboardButton(text='Команды',
                                      callback_data=ActionCallbackData(action='teams_menu').pack())],
                [InlineKeyboardButton(text='Запросы',
                                      callback_data=ActionCallbackData(action='requests_teams_menu').pack())]]
    else:
        menu = [[InlineKeyboardButton(text='Запросы',
                                      callback_data=ParamCallbackData(action='requests_team_menu', param=team).pack())]]

    return InlineKeyboardMarkup(inline_keyboard=menu)


async def get_supports_menu():
    menu = []
    for support in await db.get_supports():
        menu.append([InlineKeyboardButton(text=support[0], callback_data=ParamCallbackData(action='support_menu',
                                                                                           param=support[0]).pack())])

    menu.append([InlineKeyboardButton(text='+ Добавить исполнителя',
                                      callback_data=ActionCallbackData(action='add_support').pack())])

    menu.append([InlineKeyboardButton(text='Назад', callback_data=ActionCallbackData(action='main_menu').pack())])
    return InlineKeyboardMarkup(inline_keyboard=menu)


async def get_support_menu(support):
    menu = [
        [InlineKeyboardButton(text='Изменить username',
                              callback_data=ParamCallbackData(action='change_support_username',
                                                              param=support).pack())],
        [InlineKeyboardButton(text='Изменить ID',
                              callback_data=ParamCallbackData(action='change_support_id',
                                                              param=support).pack())],
        [InlineKeyboardButton(text='Изменить команду',
                              callback_data=ParamCallbackData(action='change_support_team',
                                                              param=support).pack())],
        [InlineKeyboardButton(text='Изменить Lead',
                              callback_data=ParamCallbackData(action='change_support_lead_id',
                                                              param=support).pack())],
        [InlineKeyboardButton(text='Убрать саппорта из базы',
                              callback_data=ParamCallbackData(action='remove_support_confirm',
                                                              param=support).pack())],
        [InlineKeyboardButton(text='Назад', callback_data=ActionCallbackData(action='supports_menu').pack())]
    ]

    return InlineKeyboardMarkup(inline_keyboard=menu)


async def get_team_select():
    menu = []
    for team in await db.get_teams():
        menu.append([InlineKeyboardButton(text=team[0], callback_data=ParamCallbackData(action='team_select',
                                                                                        param=team[0]).pack())])

    menu.append([InlineKeyboardButton(text='Отмена',
                                      callback_data=ActionCallbackData(action='cancel_team_select').pack())])
    return InlineKeyboardMarkup(inline_keyboard=menu)


async def get_new_team_select():
    menu = []
    for team in await db.get_teams():
        menu.append([InlineKeyboardButton(text=team[0], callback_data=ParamCallbackData(action='new_team_select',
                                                                                        param=team[0]).pack())])

    menu.append([InlineKeyboardButton(text='Отмена',
                                      callback_data=ActionCallbackData(action='cancel_new_team_select').pack())])
    return InlineKeyboardMarkup(inline_keyboard=menu)


async def get_remove_support_menu(support):
    menu = [[InlineKeyboardButton(text='Да',
                                  callback_data=ParamCallbackData(action='remove_support',
                                                                  param=support).pack()),
             InlineKeyboardButton(text='Нет',
                                  callback_data=ParamCallbackData(action='support_menu',
                                                                  param=support).pack())]]
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


async def get_teams_menu():
    menu = []
    for team in await db.get_teams():
        menu.append([InlineKeyboardButton(text=team[0], callback_data=ParamCallbackData(action='team_menu',
                                                                                        param=team[0]).pack())])

    menu.append([InlineKeyboardButton(text='+ Добавить команду',
                                      callback_data=ActionCallbackData(action='create_team').pack())])

    menu.append([InlineKeyboardButton(text='Назад', callback_data=ActionCallbackData(action='main_menu').pack())])
    return InlineKeyboardMarkup(inline_keyboard=menu)


async def get_team_menu(team):
    menu = [
        [InlineKeyboardButton(text='Изменить название',
                              callback_data=ParamCallbackData(action='change_team_name',
                                                              param=team).pack())],
        [InlineKeyboardButton(text='Удалить команду',
                              callback_data=ParamCallbackData(action='delete_team_confirm',
                                                              param=team).pack())],
        [InlineKeyboardButton(text='Назад', callback_data=ActionCallbackData(action='teams_menu').pack())]
    ]

    return InlineKeyboardMarkup(inline_keyboard=menu)


async def get_delete_team_menu(team):
    menu = [[InlineKeyboardButton(text='Да',
                                  callback_data=ParamCallbackData(action='delete_team',
                                                                  param=team).pack()),
             InlineKeyboardButton(text='Нет',
                                  callback_data=ParamCallbackData(action='team_menu',
                                                                  param=team).pack())]]
    return InlineKeyboardMarkup(inline_keyboard=menu)


async def get_requests_teams_menu():
    menu = []
    for team in await db.get_teams():
        menu.append([InlineKeyboardButton(text=team[0], callback_data=ParamCallbackData(action='requests_team_menu',
                                                                                        param=team[0]).pack())])

    menu.append([InlineKeyboardButton(text='Назад', callback_data=ActionCallbackData(action='main_menu').pack())])
    return InlineKeyboardMarkup(inline_keyboard=menu)


async def get_requests_team_menu(team, admin):
    menu = [[InlineKeyboardButton(text='Созданные', callback_data=DoubleParamCallbackData(action='requests_menu',
                                                                                          first=team,
                                                                                          second='created').pack())],
            [InlineKeyboardButton(text='В работе', callback_data=DoubleParamCallbackData(action='requests_menu',
                                                                                         first=team,
                                                                                         second='started').pack())],
            [InlineKeyboardButton(text='Назад',
                                  callback_data=ActionCallbackData(action='requests_teams_menu'
                                                                          if admin else 'main_menu').pack())]]
    return InlineKeyboardMarkup(inline_keyboard=menu)


async def get_requests_menu(team, status):
    menu = []
    for request in await db.get_requests(team, status):
        menu.append([InlineKeyboardButton(text=request[1], callback_data=IdCallbackData(action='request_menu',
                                                                                        id=request[0]).pack())])

    menu.append([InlineKeyboardButton(text='Назад', callback_data=ParamCallbackData(action='requests_team_menu',
                                                                                    param=team).pack())])
    return InlineKeyboardMarkup(inline_keyboard=menu)


async def get_request_menu(request, team, status):
    menu = [[InlineKeyboardButton(text='Поменять исполнителя', callback_data=IdCallbackData(action='supports_select',
                                                                                            id=request).pack())],
            [InlineKeyboardButton(text='Назад',
                                  callback_data=DoubleParamCallbackData(action='requests_menu',
                                                                        first=team,
                                                                        second=status).pack())]]
    return InlineKeyboardMarkup(inline_keyboard=menu)


async def get_supports_select_menu(request, team):
    menu = []
    for support in await db.get_team_supports(team):
        menu.append([InlineKeyboardButton(text=support[0],
                                          callback_data=DoubleParamCallbackData(action='change_requests_support',
                                                                                first=str(request),
                                                                                second=support[0]).pack())])

    menu.append([InlineKeyboardButton(text='Назад', callback_data=IdCallbackData(action='request_menu',
                                                                                 id=request).pack())])
    return InlineKeyboardMarkup(inline_keyboard=menu)
