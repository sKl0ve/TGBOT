import telebot
from pdf2docx import parse
from docx2pdf import convert
from telebot import types
from pdf2image import convert_from_path
import pathlib
import sqlite3
import pandas as pd
from datetime import datetime


def read_file(file_name):
    with open(file_name, 'r') as file:
        return file.read()

bot = telebot.TeleBot(read_file('token.ini'))

@bot.message_handler(commands=['start'])
def main(message):
    bot.send_message(message.chat.id, f'Добро пожаловать, <b>{message.from_user.first_name}</b>!\nДля того чтобы начать конвертировать отправьте мне команду <u>/convert</u>', parse_mode='html')
    conn = sqlite3.connect('users.sql')
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS users (id int auto_increment primary key, convert varchar(50), first_name varchar(50), last_name varchar(50), username varchar(50), datetime varchar(50))')
    cur.execute('REPLACE INTO  users (id, first_name, last_name, username) VALUES ("%d", "%s", "%s", "%s")' % (message.chat.id, message.chat.first_name, message.chat.last_name, message.chat.username))
    conn.commit()
    cur.close()
    conn.close()
    

@bot.message_handler(commands=['convert'])
def conv(message):
    markup = types.InlineKeyboardMarkup()
    btn_pdf = types.InlineKeyboardButton('📜 Из PDF', callback_data='from_pdf')
    btn_docx = types.InlineKeyboardButton('📄 Из DOCX', callback_data='from_docx')
    btn_xlsx = types.InlineKeyboardButton('📊 Из Excel', callback_data='from_xlsx')
    btn_cad = types.InlineKeyboardButton('📑 Из DWG', callback_data='from_dwg')
    markup.row(btn_pdf, btn_docx, btn_xlsx)
    bot.send_message(message.chat.id, 'Из какого формата вы хотите конвертировать?', parse_mode='html', reply_markup=markup)

@bot.callback_query_handler(func=lambda callback: True)
def callback_message(callback):
    curent_date = datetime.now()
    variants = ['docx_to_pdf', 'pdf_to_docx', 'pdf_to_jpg', 'xlsx_to_csv', 'dwg_to_pdf']
    markup = types.InlineKeyboardMarkup()
    btn_docx_to_pdf = types.InlineKeyboardButton('📜 В PDF', callback_data='docx_to_pdf')
    btn_pdf_to_jpg = types.InlineKeyboardButton('🖼 В JPG', callback_data='pdf_to_jpg')
    btn_pdf_to_docx = types.InlineKeyboardButton('📄 В DOCX', callback_data='pdf_to_docx')
    btn_xlsx_to_csv = types.InlineKeyboardButton('📊 В CSV', callback_data='xlsx_to_csv')
    btn_dwg_to_pdf = types.InlineKeyboardButton('📜 В PDF', callback_data='dwg_to_pdf')
    data = callback.data
    conn = sqlite3.connect('users.sql')
    cur = conn.cursor()
    set_buttons = {"from_docx" : [btn_docx_to_pdf], 
            "from_xlsx" : [btn_xlsx_to_csv], 
            "from_pdf" : [btn_pdf_to_docx, btn_pdf_to_jpg],
            "from_dwg" : [btn_dwg_to_pdf]}
    

    if data in set_buttons:
        bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id, reply_markup=None)
        markup.row(*set_buttons[f"{data}"])
        bot.send_message(callback.message.chat.id, f'Из формата <b>{data[data.find("_")+1:].upper()}</b> в какой формат файла вы хотите конвертировать?', reply_markup=markup, parse_mode='html') 
    elif data in variants:
        bot.edit_message_reply_markup(callback.message.chat.id, callback.message.message_id, reply_markup=None)
        bot.send_message(callback.message.chat.id, f'В формат <b>{data[data.rfind("_")+1:].upper()}</b>!\nОтправьте ваш файл в формате <b>{data[:data.find("_")].upper()}</b>', parse_mode='html')
        cur.execute("UPDATE users SET convert = ('%s'), datetime = ('%s')  WHERE id = ('%d')" % (data, curent_date, callback.message.chat.id))
        conn.commit()
        cur.close()
        conn.close()
    

@bot.message_handler(commands=['help'])
def main(message):
    bot.send_message(message.chat.id, f'🤖 <b>{message.from_user.first_name}</b>, сейчас я расскажу о своих функциях!\n📄 Моей основной функцией является конвертирование файлов из одного формата в другой!', parse_mode='html')


@bot.message_handler(content_types=['photo'])
def get_file(message):
    bot.reply_to(message, 'Это что за красота невероятная?')


@bot.message_handler(content_types=['document'])
def get_file(message):
    conn = sqlite3.connect('users.sql')
    cur = conn.cursor()
    cur.execute('SELECT * FROM users WHERE id="%d"' % message.chat.id)
    car = cur.fetchall()[0][1]
    if '.docx' in message.document.file_name:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        src = './files/' + message.document.file_name
        with open(src, 'wb') as new_file:
                new_file.write(downloaded_file)

        if car == 'docx_to_pdf' and ('.' + car[:3] in message.document.file_name):
            bot.send_message(message.chat.id, '✅ Происходит конвертация, ожидайте!\nКонвертация может занимать до 2 минут.')
            pdf = src.replace('.docx', '.pdf')   
            convert(src, pdf)
            file = open(pdf, 'rb')
            bot.send_document(message.chat.id, file)
            file.close()
            delete = pathlib.Path(pdf)
            delete.unlink()
            delete = pathlib.Path(src)
            delete.unlink()

        else:
            bot.send_message(message.chat.id, '❌ Неправильный формат файла!')

    elif '.pdf' in message.document.file_name:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        src = './files/' + message.document.file_name
        with open(src, 'wb') as new_file:
                new_file.write(downloaded_file)

        if car == 'pdf_to_docx' and ('.' + car[:3] in message.document.file_name):
            bot.send_message(message.chat.id, '✅ Происходит конвертация, ожидайте!')
            output_src = src.replace('.pdf', '.docx')
            parse(src, output_src)
            file = open(output_src, 'rb')
            bot.send_document(message.chat.id, file)
            file.close()
            delete = pathlib.Path(output_src)
            delete.unlink()
            delete = pathlib.Path(src)
            delete.unlink()

        elif car == 'pdf_to_jpg' and ('.' + car[:3] in message.document.file_name):
            bot.send_message(message.chat.id, '✅ Происходит конвертация, ожидайте!')
            images = convert_from_path(src)
            for i in range(len(images)):
                images[i].save('./files/page' + str(i) + '.jpg', 'JPEG')
                file = open('./files/page' + str(i) + '.jpg', 'rb')
                bot.send_photo(message.chat.id, file)
                file.close()
                delete = pathlib.Path('./files/page' + str(i) + '.jpg')
                delete.unlink()
                delete = pathlib.Path(src)
                delete.unlink()
        else:
            bot.send_message(message.chat.id, '❌ Неправильный формат файла!')
    elif '.xlsx' in message.document.file_name:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        src = './files/' + message.document.file_name
        with open(src, 'wb') as new_file:
                new_file.write(downloaded_file)

        if car == 'xlsx_to_csv' and ('.' + car[:4] in message.document.file_name):
            bot.send_message(message.chat.id, '✅ Происходит конвертация, ожидайте!')
            df = pd.read_excel(src)
            output_src = src.replace('.xlsx', '.csv')
            df.to_csv(output_src, index=None, header=True)
            file = open(output_src, 'rb')
            bot.send_document(message.chat.id, file)
            file.close()
            delete = pathlib.Path(output_src)
            delete.unlink()
            delete = pathlib.Path(src)
            delete.unlink()
        else:
            bot.send_message(message.chat.id, '❌ Неправильный формат файла!')
    elif '.dwg' in message.document.file_name:
        import aspose.cad as cad
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        src = './files/' + message.document.file_name
        with open(src, 'wb') as new_file:
                new_file.write(downloaded_file)
        if car == 'dwg_to_pdf' and ('.' + car[:3] in message.document.file_name):
            output_src = src.replace('.dwg', '.pdf')
            bot.send_message(message.chat.id, '✅ Происходит конвертация, ожидайте!')
            image = cad.Image.load(src)
            pdfOptions = cad.imageoptions.PdfOptions()
            image.save(output_src, pdfOptions)
            file_out = open(output_src, 'rb')
            bot.send_document(message.chat.id, file_out)
            file_out.close()
            #delete_inp = pathlib.Path(src)
            delete_out = pathlib.Path(output_src)
            #delete_inp.unlink()
            delete_out.unlink()
        else:
            bot.send_message(message.chat.id, '❌ Неправильный формат файла!')


    cur.close()
    conn.close()

bot.infinity_polling(timeout=10, long_polling_timeout = 5)
