
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from usr import User
import time
import os
import asyncio
from aiogram.types import FSInputFile
from dotenv import load_dotenv
import logging
from background import keep_alive

logging.basicConfig(level=logging.INFO)

on_server = True #to understand whether a bot is on the server
try: import replit
except: on_server = False
logging.info(f"Running on {'replit' if on_server else 'local'} server")


load_dotenv()
bot = Bot(token=os.getenv("TOKEN"))
dp = Dispatcher()
established_pipes = {}
waiting_clients = {}


async def find_time_expires_alert(message: types.Message, sleep_time: int = 0):
    await asyncio.sleep(sleep_time)

    if message.chat.id in waiting_clients: 
        await message.answer("К сожалению, мы не смогли найти Вам собеседника\nОтправьте /start, что бы найти ещё раз")
        waiting_clients.pop(message.chat.id)


@dp.message(Command('start'))
async def start(message: types.Message):
    waiting_clients[message.chat.id] = User()
    await message.answer("Поиск собеседника...")

    if len(waiting_clients) > 1:
        for check_user in waiting_clients:

            if check_user != message.chat.id:
                established_pipes[message.chat.id] = User()
                established_pipes[check_user] = User()

                waiting_clients.pop(message.chat.id)
                waiting_clients.pop(check_user)

                established_pipes[check_user].create_pipe(message.chat.id)
                established_pipes[message.chat.id].create_pipe(check_user)

                await message.answer(f"Собеседник найден!")
                await bot.send_message(check_user, f"Собеседник найден!")
                return
    
    await message.answer("Сейчас Вы - единственные, кто ищет собеседника\nМы сообщим Вам, когда он будет найден")
    await find_time_expires_alert(message, 60 * 15)
    
                
@dp.message(Command('stop'))
async def stop(message: types.Message):
    if message.chat.id in established_pipes:
        await bot.send_message(established_pipes[message.chat.id].client_id, f"Собеседник завершил с вами диалог\nЧто бы найти другого собеседника, отправьте команду /start")
        await message.answer("Вы завершили диалог\nЧто бы начать поиск нового собеседника, отправьте команду /start")

        established_pipes.pop(established_pipes[message.chat.id].client_id)
        established_pipes.pop(message.chat.id)
    
    elif message.chat.id in waiting_clients:
        await message.answer("Окей, поиск собеседника прекращён")
        waiting_clients.pop(message.chat.id)

    else: await message.answer("Вы ни с кем не общаетесь")


@dp.message(Command('info'))
async def stop(message: types.Message):
    state = "Ожидание"
    if message.chat.id in established_pipes: state = "В диалоге"
    elif message.chat.id in waiting_clients: state = "Поиск..."

    await message.answer(f"*Текущая задача:*" + 
                            f"\n{state}\n" +
                            f"*Сейчас в диалоге:* {len(established_pipes)}\n" +
                            f"*Ищут собеседника:* {len(waiting_clients)}", parse_mode="Markdown")
            

@dp.message()
async def handle_docs_photo(message: types.Message):

    if message.chat.id in established_pipes: 
        if established_pipes[message.chat.id].last_time + 300 < time.time():
            await bot.send_message(established_pipes[message.chat.id].client_id, f"Превышено время диалога.\nОтправьте /start для начала поиска собеседника")
            await bot.send_message(message.chat.id, f"Превышено время диалога\nОтправьте /start для начала поиска собеседника")

            established_pipes.pop(established_pipes[message.chat.id].client_id)
            established_pipes.pop(message.chat.id)

        else:
            client_id = established_pipes[message.chat.id].client_id

            if message.voice:
                file_id = message.voice.file_id
                file = await bot.get_file(file_id)
                file_path = file.file_path

                await bot.download_file(file_path, f"{message.chat.id}.ogg")
                await bot.send_voice(client_id, FSInputFile(f"{message.chat.id}.ogg"))
                os.remove(f"{message.chat.id}.ogg")

            if message.video_note:
                file_id = message.video_note.file_id
                file = await bot.get_file(file_id)
                file_path = file.file_path

                await bot.download_file(file_path, f"{message.chat.id}.mp4")
                await bot.send_video_note(client_id, FSInputFile(f"{message.chat.id}.mp4"))
                os.remove(f"{message.chat.id}.mp4")

            if message.animation:
                file_id = message.animation.file_id
                file = await bot.get_file(file_id)
                file_path = file.file_path

                await bot.download_file(file_path, f"{message.chat.id}.gif")
                await bot.send_animation(client_id, FSInputFile(f"{message.chat.id}.gif"), caption=message.caption)
                os.remove(f"{message.chat.id}.gif")

            elif message.video:
                file_id = message.video.file_id
                file = await bot.get_file(file_id)
                file_path = file.file_path

                await bot.download_file(file_path, f"{message.chat.id}.mp4")
                await bot.send_video(client_id, FSInputFile(f"{message.chat.id}.mp4"), caption=message.caption)
                os.remove(f"{message.chat.id}.mp4")

            elif message.photo:
                file_id = message.photo[-1].file_id
                file = await bot.get_file(file_id)
                file_path = file.file_path
                path = "".join(file.file_path.split(".")[-1:])

                await bot.download_file(file_path, f"{message.chat.id}.{path}")
                await bot.send_photo(client_id, FSInputFile(f"{message.chat.id}.{path}"), caption=message.caption)
                os.remove(f"{message.chat.id}.{path}")

            elif message.audio:
                file_id = message.audio.file_id
                file = await bot.get_file(file_id)
                file_path = file.file_path

                await bot.download_file(file_path, f"{message.chat.id}.ogg")
                await bot.send_audio(client_id, FSInputFile(f"{message.chat.id}.ogg"), caption=message.caption)
                os.remove(f"{message.chat.id}.ogg")

            elif message.document:
                file_id = message.document.file_id
                file = await bot.get_file(file_id)
                path = "".join(file.file_path.split(".")[-1:])
                file_path = file.file_path

                await bot.download_file(file_path, f"{message.chat.id}.{path}")
                await bot.send_document(client_id, FSInputFile(f"{message.chat.id}.{path}"), caption=message.caption)
                os.remove(f"{message.chat.id}.{path}")
            
            elif message.sticker:
                sticker_id = message.sticker.file_id
                await bot.send_sticker(client_id, sticker=sticker_id)
            
            elif message.text:
                await bot.send_message(client_id, message.text)

            established_pipes[message.chat.id].last_time = time.time()
            established_pipes[established_pipes[message.chat.id].client_id].last_time = time.time()

    
    elif message.chat.id in waiting_clients: await message.answer("Ищем собеседника...")
    else: await message.answer("Отправьте мне /start для начала поиска собеседниа")
    
if on_server: keep_alive()

async def start():
    await dp.start_polling(bot, skip_updates=True)


if __name__ == '__main__':
    # start bot
    asyncio.run(start())