import asyncio
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums.parse_mode import ParseMode
from translate import Translator
import config
from db import functions as db
import task_kb as kb
import task_texts as texts


async def send_messages(bot, day_requests, day_status):
    day_data = {
        'start': texts.day_start_notification,
        'end': texts.day_end_notification
    }
    for support in day_requests:
        support, chat_id, english, requests = support
        await bot.send_message(chat_id=chat_id, text=day_data[day_status])
        for request in requests:
            print(request)
            request_id, buyer_id, status, created_at, started_at, request_text = request
            if not english:
                text = texts.request.format(request=request_id, buyer=buyer_id, support=support,
                                            status=texts.statuses[status],
                                            created_at=created_at.replace(microsecond=0),
                                            started_at=started_at.replace(microsecond=0)
                                            if started_at is not None else '-',
                                            completed_at='-', text=request_text)
            else:
                translator = Translator(to_lang='en', from_lang='ru')
                text = texts.request_eng.format(request=request_id, buyer=buyer_id, support=support,
                                                status=texts.statuses[status],
                                                created_at=created_at.replace(microsecond=0),
                                                started_at=started_at.replace(microsecond=0)
                                                if started_at is not None else '-',
                                                completed_at='-', text=translator.translate(request_text))
            await bot.send_message(chat_id=chat_id, text=text,
                                   reply_markup=await kb.get_support_request_menu(request_id, status, english))


async def main():
    await db.start_db()
    interval = 5
    requests = await db.get_requests_notifications(interval)
    start_requests = await db.get_supports_start_notifications(interval)
    end_requests = await db.get_supports_end_notifications(interval)

    bot = Bot(token=config.TASK_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    for team in requests:
        supports = []
        for request in team[1]:
            chat_id, request_id, buyer_id, created_at, request_text, support = request
            english = await db.get_request_english(request_id)
            if not english:
                text = texts.request.format(request=request_id, buyer=buyer_id, support=support,
                                            status=texts.statuses['started'],
                                            created_at=created_at.replace(microsecond=0),
                                            started_at='-', completed_at='-',
                                            text=request_text)
            else:
                translator = Translator(to_lang='en', from_lang='ru')
                text = texts.request_eng.format(request=request_id, buyer=buyer_id, support=support,
                                                status=texts.statuses['started'],
                                                created_at=created_at.replace(microsecond=0),
                                                started_at='-', completed_at='-',
                                                text=translator.translate(request_text))
            if support not in supports:
                supports.append(supports)
                await bot.send_message(chat_id=chat_id, text=team[0])
            await bot.send_message(chat_id=chat_id, text=text,
                                   reply_markup=await kb.get_support_request_menu(request_id, 'created', english))

    await send_messages(bot, start_requests, 'start')
    await send_messages(bot, end_requests, 'end')

    await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())