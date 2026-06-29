import telebot
import pandas as pd
import os
import re
from telebot import types
from io import BytesIO

TOKEN = '7111268710:AAFMiOW1eQ0L6NWAOUO3OOrRFc6uu6KemOQ'
bot = telebot.TeleBot(TOKEN)

VIP_FILE = 'vip_users.txt'
ADMIN_CHAT_IDS = [6002941406, 1399715535]  # Replace with your list of admin chat IDs

user_files = {}
user_names = {}

def load_vip_users():
    if not os.path.exists(VIP_FILE):
        return []
    with open(VIP_FILE, 'r') as file:
        return [int(line.strip()) for line in file]

def save_vip_users(vip_users):
    with open(VIP_FILE, 'w') as file:
        for user_id in vip_users:
            file.write(f"{user_id}\n")

VIP_USERS = load_vip_users()

def is_vip_user(chat_id):
    return chat_id in VIP_USERS

def is_admin(chat_id):
    return chat_id in ADMIN_CHAT_IDS

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if not is_vip_user(message.chat.id):
        bot.reply_to(message, f"WELCOME TO LUO YI BOT CV\n \nPRICE : \nPAKET MiNGGUAN = Rp 500.000\nPAKET BULANAN    = Rp 1.800.000\n\nJAM OPERASIONAL ADMIN : \n10.00 - 22.00 WIB\n\nPM ADMIN : @chuakxz\n\nCHAT ID KAMU : {message.chat.id} \n\nNOTED : \nKIRIMKAN CHAT ID DI ATAS KE ADMIN\nDI DALAM FILE JANGAN SAMPE ADA TULISAN HARUS BERSIH ISINYA NOMOR")
        return
    bot.reply_to(message, "Halo! Kirimkan file XLSX, CSV, atau TXT Anda untuk diubah menjadi VCF, atau masukkan daftar nomor telepon langsung dalam format teks.")

@bot.message_handler(commands=['addvip'])
def add_vip(message):
    if not is_admin(message.chat.id):
        bot.reply_to(message, "Anda tidak memiliki izin untuk menggunakan perintah ini.")
        return
    
    try:
        user_id = int(message.text.split()[1])
        if user_id not in VIP_USERS:
            VIP_USERS.append(user_id)
            save_vip_users(VIP_USERS)
            bot.reply_to(message, f"User {user_id} telah ditambahkan ke daftar VIP.")
        else:
            bot.reply_to(message, "User sudah ada dalam daftar VIP.")
    except (IndexError, ValueError):
        bot.reply_to(message, "Format perintah salah. Gunakan /addvip <user_id>")

@bot.message_handler(commands=['removevip'])
def remove_vip(message):
    if not is_admin(message.chat.id):
        bot.reply_to(message, "Anda tidak memiliki izin untuk menggunakan perintah ini.")
        return
    
    try:
        user_id = int(message.text.split()[1])
        if user_id in VIP_USERS:
            VIP_USERS.remove(user_id)
            save_vip_users(VIP_USERS)
            bot.reply_to(message, f"User {user_id} telah dihapus dari daftar VIP.")
        else:
            bot.reply_to(message, "User tidak ditemukan dalam daftar VIP.")
    except (IndexError, ValueError):
        bot.reply_to(message, "Format perintah salah. Gunakan /removevip <user_id>")

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    if not is_vip_user(message.chat.id):
        bot.reply_to(message, "Anda tidak memiliki akses untuk menggunakan bot ini.")
        return
    
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        file_name = message.document.file_name
        file_extension = file_name.split('.')[-1]
        
        # Validasi ekstensi file
        if file_extension not in ['xlsx', 'csv', 'txt', 'xls']:
            bot.reply_to(message, "Format file tidak didukung. Silakan kirim file XLSX, CSV, atau TXT.")
            return
        
        # Memuat file ke dalam DataFrame
        df = None
        if file_extension in ['csv', 'txt']:
            df = pd.read_csv(BytesIO(downloaded_file), header=None)  # Tambahkan header=None
        elif file_extension == 'xlsx':
            df = pd.read_excel(BytesIO(downloaded_file), engine='openpyxl', header=None)
        elif file_extension == 'xls':
            df = pd.read_excel(BytesIO(downloaded_file), engine='xlrd', header=None)
        
        if df is None:
            raise ValueError("Format file tidak didukung atau file kosong.")
        
        user_files[message.chat.id] = {'df': df, 'file_name': file_name, 'extension': file_extension}
        
        if file_extension == 'txt':
            msg = bot.reply_to(message, "File berhasil diunggah. Masukkan ukuran partisi:")
            bot.register_next_step_handler(msg, get_txt_partition)
        else:
            msg = bot.reply_to(message, "File berhasil diunggah. SILAHKAN MASUKKAN NAMA KONTAK:")
            bot.register_next_step_handler(msg, get_name)
    except Exception as e:
        bot.reply_to(message, f"Terjadi kesalahan: {e}")

@bot.message_handler(content_types=['text'])
def handle_text(message):
    if not is_vip_user(message.chat.id):
        bot.reply_to(message, "Anda tidak memiliki akses untuk menggunakan bot ini.")
        return
    
    try:
        phone_numbers = message.text.split()
        df = pd.DataFrame(phone_numbers, columns=['Phone'])
        user_files[message.chat.id] = {'df': df, 'file_name': 'direct_input'}
        
        msg = bot.reply_to(message, "Nomor telepon berhasil diunggah. SILAHKAN MASUKKAN NAMA KONTAK:")
        bot.register_next_step_handler(msg, get_name)
    except Exception as e:
        bot.reply_to(message, f"Terjadi kesalahan: {e}")

def get_txt_partition(message):
    if not is_vip_user(message.chat.id):
        bot.reply_to(message, "Anda tidak memiliki akses untuk menggunakan bot ini.")
        return
    
    chat_id = message.chat.id
    try:
        partition = message.text.strip().lower()
        if partition.isdigit():
            partition = int(partition)
        else:
            bot.reply_to(message, "Format partisi tidak valid. Harap masukkan angka.")
            return
        
        user_files[chat_id]['partition'] = partition
        msg = bot.reply_to(message, "MASUKKAN NAMA FILE TXT:")
        bot.register_next_step_handler(msg, get_txt_name)
    except ValueError:
        bot.reply_to(message, "Format partisi tidak valid. Harap masukkan angka.")

def get_name(message):
    if not is_vip_user(message.chat.id):
        bot.reply_to(message, "Anda tidak memiliki akses untuk menggunakan bot ini.")
        return
    
    try:
        user_names[message.chat.id] = message.text
        bot.reply_to(message, "Nama berhasil disimpan. SILAHKAN MASUKKAN UKURAN PARTISI VCF:")
        bot.register_next_step_handler(message, get_vcf_partition)
    except Exception as e:
        bot.reply_to(message, f"Terjadi kesalahan: {e}")

def get_txt_name(message):
    if not is_vip_user(message.chat.id):
        bot.reply_to(message, "Anda tidak memiliki akses untuk menggunakan bot ini.")
        return
    
    try:
        chat_id = message.chat.id
        user_files[chat_id]['txt_name'] = message.text
        handle_txt_partition(message, user_files[chat_id]['partition'])
    except Exception as e:
        bot.reply_to(message, f"Terjadi kesalahan: {e}")

def get_vcf_partition(message):
    if not is_vip_user(message.chat.id):
        bot.reply_to(message, "Anda tidak memiliki akses untuk menggunakan bot ini.")
        return
    
    try:
        partition = message.text.strip().lower()
        if partition.isdigit():
            partition = int(partition)
        else:
            bot.reply_to(message, "Format partisi tidak valid. Harap masukkan angka.")
            return
        
        user_files[message.chat.id]['partition'] = partition
        msg = bot.reply_to(message, "MASUKKAN NAMA FILE VCF:")
        bot.register_next_step_handler(msg, get_vcf_name)
    except ValueError:
        bot.reply_to(message, "Format partisi tidak valid. Harap masukkan angka.")

def get_vcf_name(message):
    if not is_vip_user(message.chat.id):
        bot.reply_to(message, "Anda tidak memiliki akses untuk menggunakan bot ini.")
        return
    
    try:
        chat_id = message.chat.id
        user_files[chat_id]['vcf_name'] = message.text
        handle_partition(message, user_files[chat_id]['partition'])
    except Exception as e:
        bot.reply_to(message, f"Terjadi kesalahan: {e}")

def handle_partition(message, partition):
    chat_id = message.chat.id

    if not is_vip_user(chat_id):
        bot.reply_to(message, "Anda tidak memiliki akses untuk menggunakan bot ini.")
        return

    if chat_id in user_files:
        user_name = user_names[chat_id]
        df = user_files[chat_id]['df']  # Mendapatkan DataFrame dari user_files
        vcf_base_name = user_files[chat_id].get('vcf_name', user_name)
        try:
            df_copy = df.copy()  # Copy DataFrame
            
            if partition != 'all':
                partition = int(partition)
                chunks = [df_copy[i:i + partition] for i in range(0, df_copy.shape[0], partition)]
            else:
                chunks = [df_copy]
            
            for i, chunk in enumerate(chunks):
                with BytesIO() as vcf:
                    for index, row in chunk.iterrows():
                        phone_number = re.sub(r'[+\- ]', ' ', str(row[0]))  # Menghapus tanda "+", "-", dan " "
                        phone_number = '+' + phone_number  # Menambahkan tanda "+" di awal
                        
                        # Membuat nomor urut dengan '0' di depan untuk indeks satuan dan puluhan
                        if 1 <= index + 1 <= 9:
                            user_index = f"00{index + 1}"
                        elif 10 <= index + 1 <= 99:
                            user_index = f"0{index + 1}"
                        else:
                            user_index = str(index + 1)
                        
                        vcf.write(f"BEGIN:VCARD\nVERSION:3.0\nN:{user_name} 0{user_index};;;\nTEL;TYPE=CELL:{phone_number}\nEND:VCARD\n".encode())
                    
                    vcf.name = f"{vcf_base_name}_{i + 1}.vcf"  # Menetapkan nama file saat menulis ke BytesIO
                    vcf.seek(0)
                    bot.send_document(chat_id, vcf)
            
            del user_files[chat_id]
            del user_names[chat_id]
            bot.reply_to(message, "File VCF telah dikirim.")
        except Exception as e:
            bot.reply_to(message, f"Terjadi kesalahan saat memproses file: {e}")
    else:
        bot.reply_to(message, "Tidak ada file yang ditemukan. Silakan unggah file terlebih dahulu.")

def handle_txt_partition(message, partition):
    chat_id = message.chat.id

    if not is_vip_user(chat_id):
        bot.reply_to(message, "Anda tidak memiliki akses untuk menggunakan bot ini.")
        return

    if chat_id in user_files:
        df = user_files[chat_id]['df']  # Mendapatkan DataFrame dari user_files
        txt_base_name = user_files[chat_id].get('txt_name', 'partisi')
        try:
            df_copy = df.copy()  # Copy DataFrame
            
            if partition != 'all':
                partition = int(partition)
                chunks = [df_copy[i:i + partition] for i in range(0, df_copy.shape[0], partition)]
            else:
                chunks = [df_copy]
            
            for i, chunk in enumerate(chunks):
                with BytesIO() as txt:
                    for index, row in chunk.iterrows():
                        phone_number = re.sub(r'[+\- ]', ' ', str(row[0]))  # Menghapus tanda "+", "-", dan " "
                        txt.write(f"{phone_number}\n".encode())
                    
                    txt.name = f"{txt_base_name}_{i + 1}.txt"  # Menetapkan nama file saat menulis ke BytesIO
                    txt.seek(0)
                    bot.send_document(chat_id, txt)
            
            del user_files[chat_id]
            bot.reply_to(message, "File TXT telah dipartisi dan dikirim.")
        except Exception as e:
            bot.reply_to(message, f"Terjadi kesalahan saat memproses file: {e}")
    else:
        bot.reply_to(message, "Tidak ada file yang ditemukan. Silakan unggah file terlebih dahulu.")

bot.polling()
