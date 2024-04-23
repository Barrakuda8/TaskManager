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
          'Support ID: {support}\n' \
          'Статус: {status}\n' \
          'Создан: {created_at}\n' \
          'Принят в работу: {started_at}\n' \
          'Выполнен: {completed_at}\n\n' \
          '{text}'
request_eng = 'Request ID: {request}\n' \
              'Buyer ID: {buyer}\n' \
              'Support ID: {support}\n' \
              'Status: {status}\n' \
              'Created at: {created_at}\n' \
              'Started at: {started_at}\n' \
              'Completed at: {completed_at}\n\n' \
              '{text}'
complete_request_confirm = 'Вы уверены, что хотите изменить статус этого запроса на "Выполнен"?'
cancel_request_confirm = 'Вы уверены, что хотите изменить статус этого запроса на "Отменён"?'
start_request_confirm = 'Вы уверены, что хотите изменить статус этого запроса на "Принят в работу"?'
delay_request_confirm = 'Вы уверены, что хотите изменить статус этого запроса на "Отложен"?'
complete_request_confirm_eng = 'Are you sure you want to change the status of this request to "Completed"?'
cancel_request_confirm_eng = 'Are you sure you want to change the status of this request to "Canceled"?'
start_request_confirm_eng = 'Are you sure you want to change the status of this request to "In progress"?'
delay_request_confirm_eng = 'Are you sure you want to change the status of this request to "Delayed"?'
request_completed = 'Запрос выполнен\n' \
                    'ID запроса: {request}\n' \
                    'Buyer ID: {buyer}'
request_canceled = 'Запрос отменён\n' \
                   'ID запроса: {request}\n' \
                   'Buyer ID: {buyer}'
request_started = 'Запрос принят в работу\n' \
                   'ID запроса: {request}\n' \
                   'Buyer ID: {buyer}'
request_delayed = 'Запрос отложен\n' \
                  'ID запроса: {request}\n' \
                  'Buyer ID: {buyer}'
main_menu = 'Здравствуйте!\n' \
            'Что вы хотели бы сделать?'
start_forbidden = 'Здравствуйте, вам отказано в доступе к работе с этим ботом.'
forbidden = 'Ваш уровень доступа был понижен.\n\n'
supports_menu = 'Пожалуйста, выберите исполнителя.'
support_menu = 'Username: {username}\n' \
               'ID: {id}\n' \
               'Команда: {team}\n' \
               'Lead: {lead}\n' \
               'ENG: {english}'
support_schedule_menu = 'Username: {username}\n' \
                        'Начало дня: {day_start}\n' \
                        'Конец дня: {day_end}\n' \
                        'Выходные: {days_off}'
admins_menu = 'Пожалуйста, выберите администратора.'
admin_menu = 'ID: {id}\n' \
             'Имя: {name}'
teams_menu = 'Пожалуйста, выберите команду.'
team_menu = 'Название: {name}\n' \
            'Участников: {supports}\n' \
            'Лиды: {leads}\n' \
            'Текущих запросов: {requests}'
set_support_id = 'Пожалуйста, введите ID чата этого исполнителя. Помните, он должен состоять только из цифр.\n\n' \
                 'Для отмены ввода нажмите /cancel'
set_support_username = 'Пожалуйста, введите username этого исполнителя. Помните, он должен быть уникален.\n\n' \
                       'Для отмены ввода нажмите /cancel'
set_admin_id = 'Пожалуйста, введите ID учётной записи телеграм этого администратора. ' \
               'Помните, он должен состоять только из цифр.\n\nДля отмены ввода нажмите /cancel'
set_admin_name = 'Пожалуйста, введите имя для этого администратора.\n\nДля отмены ввода нажмите /cancel'
incorrect_support_id = 'ID должен состоять только из цифр!\n\nДля отмены ввода нажмите /cancel'
unique_support_username = 'Исполнитель с таким username уже существует! Введите другой username или нажмите /cancel'
remove_support_confirm = 'Вы точно хотите убрать этого исполнителя из базы?'
unique_admin_id = 'Администратор с таким ID уже существует! Введите другой ID или нажмите /cancel'
incorrect_admin_id = 'ID должен состоять только из цифр!\n\nДля отмены ввода нажмите /cancel'
remove_admin_confirm = 'Вы точно хотите убрать этого администратора из базы, тем самым лишив его прав администратора?'
team_select = 'Пожалуйста, выберите команду для этого саппорта'
set_support_lead_id = 'Пожалуйста, введите ID пользователя телеграм, если хотите сделать его Team Lead или нажмите /skip'
set_new_support_lead_id = 'Пожалуйста, введите ID пользователя телеграм, если хотите сделать его Team Lead или нажмите /clear'
unique_support_lead_id = 'Lead с таким ID пользователя уже существует! Введите другой ID или нажмите /cancel'
incorrect_support_lead_id = 'ID должен состоять только из цифр!\n\nДля отмены ввода нажмите /cancel'
set_team_name = 'Пожалуйста, введите название новой команды.\n\nДля отмены ввода нажмите /cancel'
set_new_team_name = 'Пожалуйста, введите новое название для команды.\n\nДля отмены ввода нажмите /cancel'
unique_team_name = 'Команда с таким названием уже существует! Введите другое название или нажмите /cancel'
delete_team_confirm = 'Вы точно хотите удалить эту команду?'
not_empty_team = 'В этой команде есть участники. Уберите из базы участников или поменяйте их команды и повторите попытку.\n\n'
requests_teams_menu = 'Пожалуйста, выберите команду, запросы которой вы хотели бы посмотреть.'
requests_team_menu = 'Пожалуйста, выберите какие запросы вы хотели бы посмотреть.'
requests_menu = 'Пожалуйста, выберите запрос, который вы бы хотели посмотреть.'
supports_select = 'Выберите исполнителя, которому вы хотите передать этот запрос.'
chat_not_found = 'Чата с таким ID не существует. Проверьте ID исполнителя.\n' \
                 'Запрос уже создан (ID: {id}). Для повторной отправки, убедившись, что ID исполнителя исправлен на корректный,' \
                 ' переназначьте этого же исполнителя для этого запроса.'
completed_chat_set = 'Этот чат установлен в качестве чата для пересылки выполненных запросов.'
forbidden_completed_chat = 'Вам необходимо обладать правами администратора для совершения этого действия.'
request_support_changed = 'Вы больше не являетесь исполнителем данного запроса.'
request_support_change_successful = 'Исполнитель данного запроса успешно изменён!'
set_support_day_start = 'Пожалуйста, введите время начала рабочего дня исполнителя в формате "ЧЧ:ММ".\n' \
                        'Пример: 9:00\n\n' \
                        'Для сброса параметра нажмите /clear\n' \
                        'Для отмены ввода нажмите /cancel'
set_support_day_end = 'Пожалуйста, введите время окончания рабочего дня исполнителя в формате "ЧЧ:ММ".\n' \
                        'Пример: 18:00\n\n' \
                        'Для сброса параметра нажмите /clear\n' \
                        'Для отмены ввода нажмите /cancel'
incorrect_support_time_format = 'Время должно быть введено в формате "ЧЧ:ММ"!\n' \
                                'Пример: 9:00\n\n' \
                                'Для отмены ввода нажмите /cancel'
set_support_days_off = 'Пожалуйста, введите сокращения всех выходных дней исполнителя через пробел.\n' \
                       'Пример: ПН ВТ СР ЧТ ПТ СБ ВС\n\n' \
                       'Для сброса параметра нажмите /clear\n' \
                       'Для отмены ввода нажмите /cancel'
incorrect_support_days_off = 'Выходные дни должны быть указаны в виде перечисления сокращений через пробел!\n' \
                             'Пример: ПН ВТ СР ЧТ ПТ СБ ВС\n\n' \
                             'Для отмены ввода нажмите /cancel'
set_support_schedule = 'Пожалуйста, введите, каждое с новой строки:\n' \
                       '1) время начала рабочего дня исполнителя в формате "ЧЧ:ММ".\n' \
                       '2) время окончания рабочего дня исполнителя в формате "ЧЧ:ММ".\n' \
                       '3) сокращения всех выходных дней исполнителя через пробел.\n' \
                       'Пример:\n' \
                       '9:00\n' \
                       '18:00\n'\
                       'СБ ВС\n' \
                       'Для сброса всех параметров нажмите /clear\n' \
                       'Для отмены ввода нажмите /cancel'
incorrect_support_schedule = 'Введены некорректные данные. Внимательно прочитайте инструкции в предыдущем сообщении. \n' \
                             'Для отмены ввода нажмите /cancel'
team_notification_menu = 'Команда: {name}\n' \
                         'Время от создания задачи: {time}\n' \
                         'Текст уведомления:\n' \
                         '{text}'
set_team_notification_time = 'Пожалуйста, введите время от создания задачи до отправки уведомления в минутах числом.\n' \
                             'Пример для 5 минут: 5\n' \
                             'Для отмены ввода нажмите /cancel'
incorrect_team_notification_time = 'Время в минутах должно быть числом!\n' \
                                   'Для отмены ввода нажмите /cancel'
set_team_notification_text = 'Пожалуйста, введите текст уведомления.\n' \
                             'Для отмены ввода нажмите /cancel'
day_start_notification = 'Здравствуйте! Отправляю вам накопившиеся задачи перед началом рабочего дня:'
day_end_notification = 'Здравствуйте! Отправляю вам не выполненные и не отложенные задачи. ' \
                       'Пожалуйста, измените их статус перед окончанием рабочего дня.:'
set_stats_period = 'Введите количество дней, за которое вы хотите получить отчёт.\n\nДля отмены ввода нажмите /cancel'
incorrect_stats_period = 'Количество дней должно быть числом!\n\nДля отмены ввода нажмите /cancel'
empty_stats = 'Не найдено событий, созданных в этот промежуток времени.'

statuses = {
    'created': '⚪ Создан',
    'started': '🔵 Принят в работу',
    'delayed': '🟡 Отложен',
    'completed': '🟢 Выполнен',
    'canceled': '🔴 Отменён'
}

statuses_eng = {
    'created': '⚪ Created',
    'started': '🔵 In progress',
    'delayed': '🟡 Delayed',
    'completed': '🟢 Completed',
    'canceled': '🔴 Canceled'
}
