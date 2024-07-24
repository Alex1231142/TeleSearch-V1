import os
import re
import tempfile
import zipfile
import rarfile
import gzip
import logging
import json
import csv
import pandas as pd
from telethon import TelegramClient, errors
import pdfplumber
from io import BytesIO, TextIOWrapper
from tqdm.asyncio import tqdm
import asyncio
from concurrent.futures import ThreadPoolExecutor


with open('config.json', 'r') as f:
    config = json.load(f)


logging.basicConfig(
    filename='log.log',
    level=getattr(logging, config["logging_level"].upper()),
    format='%(asctime)s - %(levelname)s - %(message)s'
)

api_id = config['api_id']
api_hash = config['api_hash']
phone_number = config['phone_number']
channel_username = config['channel_username']
results_file = config['results_file']
errors_file = 'errors.txt'
max_workers = config.get('max_workers', 5)
semaphore_limit = config.get('semaphore_limit', 5)

client = TelegramClient('session_name', api_id, api_hash)


semaphore = asyncio.Semaphore(semaphore_limit)

async def search_in_file(file, search_term, filename):
    found = False
    search_term = search_term.lower()  
    try:
        if filename.lower().endswith('.pdf'):
            with pdfplumber.open(file) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text and re.search(search_term, text, re.IGNORECASE):
                        logging.info(f'Найдено в файле {filename}, страница {page_num + 1}')
                        with open(results_file, 'a', encoding='utf-8') as f:
                            f.write(f'Найдено в файле {filename}, страница {page_num + 1}\n')
                            f.write(f'Текст: {text}\n')
                        found = True
        elif filename.lower().endswith('.csv'):
            reader = csv.reader(TextIOWrapper(file, encoding='utf-8', errors='ignore'))
            for i, row in enumerate(reader):
                line_str = ' '.join(row)
                if re.search(search_term, line_str, re.IGNORECASE):
                    logging.info(f'Найдено в файле {filename}, строка {i + 1}')
                    with open(results_file, 'a', encoding='utf-8') as f:
                        f.write(f'Найдено в файле {filename}, строка {i + 1}\n')
                        f.write(f'Строка: {line_str}\n')
                    found = True
        elif filename.lower().endswith('.xlsx'):
            df = pd.read_excel(file)
            for i, row in df.iterrows():
                line_str = ' '.join(map(str, row.values))
                if re.search(search_term, line_str, re.IGNORECASE):
                    logging.info(f'Найдено в файле {filename}, строка {i + 1}')
                    with open(results_file, 'a', encoding='utf-8') as f:
                        f.write(f'Найдено в файле {filename}, строка {i + 1}\n')
                        f.write(f'Строка: {line_str}\n')
                    found = True
        elif filename.lower().endswith('.gz'):
            with gzip.open(file, 'rt', encoding='utf-8', errors='ignore') as gz_file:
                for i, line in enumerate(gz_file):
                    if re.search(search_term, line, re.IGNORECASE):
                        logging.info(f'Найдено в файле {filename}, строка {i + 1}')
                        with open(results_file, 'a', encoding='utf-8') as f:
                            f.write(f'Найдено в файле {filename}, строка {i + 1}\n')
                            f.write(f'Строка: {line}\n')
                        found = True
        else:
            for i, line in enumerate(file):
                line_str = line.decode('utf-8', errors='ignore')
                if re.search(search_term, line_str, re.IGNORECASE):
                    logging.info(f'Найдено в файле {filename}, строка {i + 1}')
                    with open(results_file, 'a', encoding='utf-8') as f:
                        f.write(f'Найдено в файле {filename}, строка {i + 1}\n')
                        f.write(f'Строка: {line_str}\n')
                    found = True
    except Exception as e:
        logging.error(f'Ошибка при поиске в файле {filename}: {e}')
    return found

async def process_message(message, search_term, executor):
    async with semaphore:
        if message.file:
            logging.info(f'Обработка файла {message.file.name}...')
            try:
                file_bytes = await message.download_media(file=BytesIO())
                logging.info(f'Файл {message.file.name} загружен.')
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    temp_file.write(file_bytes.getvalue())
                    temp_file_path = temp_file.name
                try:
                    if temp_file_path.endswith('.zip'):
                        with zipfile.ZipFile(temp_file_path, 'r') as zip_ref:
                            for file_info in zip_ref.infolist():
                                await asyncio.get_event_loop().run_in_executor(executor, process_zip_file, zip_ref, file_info, search_term, message.id)
                    elif temp_file_path.endswith('.rar'):
                        with rarfile.RarFile(temp_file_path) as rar_ref:
                            for file_info in rar_ref.infolist():
                                await asyncio.get_event_loop().run_in_executor(executor, process_rar_file, rar_ref, file_info, search_term, message.id)
                    else:
                        with open(temp_file_path, 'rb') as file:
                            if not await search_in_file(file, search_term, message.file.name):
                                logging.info(f'Данные не найдены в файле {message.file.name}')
                                with open(errors_file, 'a', encoding='utf-8') as f:
                                    f.write(f'Данные не найдены в файле: {message.file.name}\n')
                finally:
                    os.remove(temp_file_path)
            except errors.FloodWaitError as e:
                logging.warning(f'Превышен лимит запросов, ожидание {e.seconds} секунд.')
                await asyncio.sleep(e.seconds)
                await process_message(message, search_term, executor)  
            except ConnectionResetError as e:
                logging.error(f'Ошибка подключения: {e}. Повторная попытка через 5 секунд.')
                await asyncio.sleep(5)
                await process_message(message, search_term, executor) 
            except Exception as e:
                logging.error(f'Ошибка при обработке сообщения {message.id} с файлом {message.file.name}: {e}')
                with open(errors_file, 'a', encoding='utf-8') as f:
                    f.write(f'Ошибка при обработке файла: {message.file.name}, ошибка: {e}\n')

def process_zip_file(zip_ref, file_info, search_term, message_id):
    try:
        with zip_ref.open(file_info) as file:
            if not search_in_file(file, search_term, file_info.filename):
                logging.info(f'Данные не найдены в архиве {message_id} в файле {file_info.filename}')
                with open(errors_file, 'a', encoding='utf-8') as f:
                    f.write(f'Данные не найдены в архиве: {message_id}, файл: {file_info.filename}\n')
    except Exception as e:
        logging.error(f'Ошибка при обработке zip файла {file_info.filename} из сообщения {message_id}: {e}')
        with open(errors_file, 'a', encoding='utf-8') as f:
            f.write(f'Ошибка при обработке zip файла: {file_info.filename} из сообщения {message_id}, ошибка: {e}\n')

def process_rar_file(rar_ref, file_info, search_term, message_id):
    try:
        with rar_ref.open(file_info) as file:
            if not search_in_file(file, search_term, file_info.filename):
                logging.info(f'Данные не найдены в архиве {message_id} в файле {file_info.filename}')
                with open(errors_file, 'a', encoding='utf-8') as f:
                    f.write(f'Данные не найдены в архиве: {message_id}, файл: {file_info.filename}\n')
    except Exception as e:
        logging.error(f'Ошибка при обработке rar файла {file_info.filename} из сообщения {message_id}: {e}')
        with open(errors_file, 'a', encoding='utf-8') as f:
            f.write(f'Ошибка при обработке rar файла: {file_info.filename} из сообщения {message_id}, ошибка: {e}\n')

def should_skip_search(search_term, filename):
    if search_term.isdigit() and filename.isdigit():
        return True
    return False

async def main():
    
    os.system('cls' if os.name == 'nt' else 'clear')

    
    search_term = input('Введите данные для поиска: ').strip()

    
    await client.start()
    channel = await client.get_entity(channel_username)
    messages = await client.get_messages(channel, limit=None)  

   
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        
        tasks = []
        for message in messages:
            if not should_skip_search(search_term, message.file.name if message.file else ''):
                tasks.append(process_message(message, search_term, executor))

        
        progress_bar = tqdm(total=len(tasks), desc="Обработка сообщений", ncols=100, ascii=True)

        for i, task in enumerate(asyncio.as_completed(tasks)):
            try:
                await task
            except Exception as e:
                logging.error(f'Ошибка при выполнении задачи: {e}')
            progress_bar.update(1)

            
            if i % 1 == 0:
                os.system('cls' if os.name == 'nt' else 'clear')
                progress_bar.set_description(f'Обработка сообщений: {i + 1}/{len(tasks)}')

            
            await asyncio.sleep(2)

    
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())