request_accepted = 'Запрос принят\n' \
                   'ID запроса: {request}\n' \
                   'Buyer ID: {buyer}'
request_incorrect = 'Запрос оформлен неправильно. Корректная форма запроса:\n' \
                    '/request\n' \
                    'Buyer ID: *buyer_id*\n' \
                    'Support ID: *support_id*\n' \
                    '*text*'
support_not_found = 'Указанный Support ID не найден в базе. Внесите его в базу или введите другой Support ID.'
request = 'ID запроса: {request}\n' \
          'Buyer ID: {buyer}\n' \
          'Статус: {status}\n' \
          'Создан: {created_at}\n' \
          'Выполнен: {completed_at}\n\n' \
          '{text}'
complete_request_confirm = 'Вы уверены, что хотите изменить статус этого запроса на "Выполнен"?'
cancel_request_confirm = 'Вы уверены, что хотите изменить статус этого запроса на "Отменён"?'
request_completed = 'Запрос выполнен\n' \
                    'ID запроса: {request}\n' \
                    'Buyer ID: {buyer}'
request_canceled = 'Запрос отменён\n' \
                   'ID запроса: {request}\n' \
                   'Buyer ID: {buyer}'
main_menu = 'Здравствуйте!\n' \
            'Что вы хотели бы сделать?'
start_forbidden = 'Здравствуйте, вам отказано в доступе к работе с этим ботом.'
forbidden = 'Ваш уровень доступа был понижен.\n\n'
supports_menu = 'Пожалуйста, выберите саппорта.'
support_menu = 'ID: {id}\n' \
               'Username: {username}'
admins_menu = 'Пожалуйста, выберите администратора.'
admin_menu = 'ID: {id}\n' \
             'Имя: {name}'
set_support_id = 'Пожалуйста, введите ID чата этого саппорта. Помните, он должен состоять только из цифр.\n\n' \
                 'Для отмены ввода нажмите /cancel'
set_support_username = 'Пожалуйста, введите username этого саппорта. Помните, он должен быть уникален.\n\n' \
                       'Для отмены ввода нажмите /cancel'
set_admin_id = 'Пожалуйста, введите ID учётной записи телеграм этого администратора. ' \
               'Помните, он должен состоять только из цифр.\n\nДля отмены ввода нажмите /cancel'
set_admin_name = 'Пожалуйста, введите имя для этого администратора.\n\nДля отмены ввода нажмите /cancel'
unique_support_id = 'Саппорт с таким ID уже существует! Введите другой ID или нажмите /cancel'
incorrect_support_id = 'ID должен состоять только из цифр!\n\nДля отмены ввода нажмите /cancel'
unique_support_username = 'Саппорт с таким username уже существует! Введите другой username или нажмите /cancel'
remove_support_confirm = 'Вы точно хотите убрать этого саппорта из базы?'
unique_admin_id = 'Администратор с таким ID уже существует! Введите другой ID или нажмите /cancel'
incorrect_admin_id = 'ID должен состоять только из цифр!\n\nДля отмены ввода нажмите /cancel'
remove_admin_confirm = 'Вы точно хотите убрать этого администратора из базы, тем самым лишив его прав администратора?'

statuses = {
    'created': '⚪ Создан',
    'completed': '🟢 Выполнен',
    'canceled': '🔴 Отменён'
}
