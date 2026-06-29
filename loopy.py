import telebot
import pandas as pd
import os
import re
from telebot import types
from io import BytesIO

TOKEN = '6693775586:AAG1mzRrxkXqtPU2WSnCR14QPxArpuQ3mZs'  # Ganti dengan token bot Anda
bot = telebot.TeleBot(TOKEN)

os.chdir(os.path.dirname(os.path.abspath(__file__)))
VIP_FILE = 'vip_users_mail_v2.txt'
ADMIN_CHAT_IDS = [6002941406, 1869375888]  # Ganti dengan ID chat admin Anda

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
        bot.reply_to(message, f"WELCOME TO MAIL BOT CV\n \nPRICE : \nPAKET MiNGGUAN = Rp 500.000\nPAKET BULANAN    = Rp 1.800.000\n\nJAM OPERASIONAL ADMIN : \n10.00 - 22.00 WIB\n\nPM ADMIN : @chuakxz\n\nCHAT ID KAMU : {message.chat.id} \n\nNOTED : \nKIRIMKAN CHAT ID DI ATAS KE ADMIN\nDI DALAM FILE JANGAN SAMPE ADA TULISAN HARUS BERSIH ISINYA NOMOR")
        return
    bot.reply_to(message, "Halo! Kirimkan file XLSX, CSV, atau TXT Anda untuk diubah menjadi VCF, atau kirimkan file VCF untuk di partisi")

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
        
        if file_extension not in ['xlsx', 'csv', 'txt', 'xls', 'vcf']:
            bot.reply_to(message, "Format file tidak didukung. Silakan kirim file XLSX, CSV, TXT, atau VCF.")
            return
        
        if file_extension == 'txt':
            file_content = downloaded_file.decode('utf-8')
            lines = file_content.strip().split('\n')
            line_count = len(lines)
            df = pd.DataFrame(lines, columns=['Nomor Telepon'])
            
            file_id = len(user_files.get(message.chat.id, {})) + 1
            user_files.setdefault(message.chat.id, {})[file_id] = {'df': df, 'file_name': file_name}
            
            bot.reply_to(message, f"File TXT berhasil diunggah.\nJumlah baris: {line_count}\nFile ID: {file_id}\nSILAHKAN MASUKKAN NAMA KONTAK UNTUK FILE {file_id}:")
        elif file_extension in ['csv', 'xlsx', 'xls']:
            if file_extension == 'csv':
                df = pd.read_csv(BytesIO(downloaded_file))
            elif file_extension == 'xlsx':
                df = pd.read_excel(BytesIO(downloaded_file), engine='openpyxl')
            elif file_extension == 'xls':
                df = pd.read_excel(BytesIO(downloaded_file), engine='xlrd')
            
            file_id = len(user_files.get(message.chat.id, {})) + 1
            user_files.setdefault(message.chat.id, {})[file_id] = {'df': df, 'file_name': file_name}
            
            bot.reply_to(message, f"File {file_extension.upper()} berhasil diunggah.\nFile ID: {file_id}\nSILAHKAN MASUKKAN NAMA KONTAK UNTUK FILE {file_id}:")
        elif file_extension == 'vcf':
            handle_vcf_file(message, downloaded_file, file_name)
            return
        
        bot.register_next_step_handler(message, get_name, file_id)
    except Exception as e:
        bot.reply_to(message, f"Terjadi kesalahan: {e}")

def get_name(message, file_id):
    if not is_vip_user(message.chat.id):
        bot.reply_to(message, "Anda tidak memiliki akses untuk menggunakan bot ini.")
        return
    
    try:
        user_names.setdefault(message.chat.id, {})[file_id] = message.text
        bot.reply_to(message, f"Nama berhasil disimpan untuk file {file_id}. SILAHKAN MASUKKAN FORMAT UNTUK FILE {file_id}:")
    except Exception as e:
        bot.reply_to(message, f"Terjadi kesalahan: {e}")

@bot.message_handler(content_types=['text'])
def handle_text(message):
    if not is_vip_user(message.chat.id):
        bot.reply_to(message, "Anda tidak memiliki akses untuk menggunakan bot ini.")
        return
    
    try:
        lines = message.text.strip().split('\n')
        file_info = []
        
        for line in lines:
            parts = line.split(',')
            if len(parts) == 3:
                partition_size = parts[0].strip()
                vcf_name = parts[1].strip()
                file_number = int(parts[2].strip())
                
                if file_number in user_files.get(message.chat.id, {}):
                    df = user_files[message.chat.id][file_number]['df']
                    user_files[message.chat.id][file_number]['partition'] = partition_size
                    user_files[message.chat.id][file_number]['vcf_name'] = vcf_name
                    file_info.append((file_number, partition_size, vcf_name))
                else:
                    bot.reply_to(message, f"File {file_number} tidak ditemukan.")
                    return
        
        for file_number, partition_size, vcf_name in file_info:
            handle_partition(message, file_number, partition_size)
        
    except Exception as e:
        bot.reply_to(message, f"Terjadi kesalahan: {e}")

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if not is_vip_user(call.message.chat.id):
        bot.reply_to(call.message.chat.id, "Anda tidak memiliki akses untuk menggunakan bot ini.")
        return

    try:
        file_id, partition = call.data.split('_')
        file_id = int(file_id)
        
        if file_id in user_files.get(call.message.chat.id, {}):
            user_files[call.message.chat.id][file_id]['partition'] = partition
            msg = bot.send_message(call.message.chat.id, f"MASUKKAN NAMA FILE VCF UNTUK FILE {file_id}:")
            bot.register_next_step_handler(msg, get_vcf_name, file_id)
        else:
            bot.reply_to(call.message.chat.id, "File tidak ditemukan.")
    except Exception as e:
        bot.reply_to(call.message.chat.id, f"Terjadi kesalahan: {e}")

def get_vcf_name(message, file_id):
    if not is_vip_user(message.chat.id):
        bot.reply_to(message, "Anda tidak memiliki akses untuk menggunakan bot ini.")
        return
    
    try:
        chat_id = message.chat.id
        user_files[chat_id][file_id]['vcf_name'] = message.text
        handle_partition(message, file_id, user_files[chat_id][file_id]['partition'])
    except Exception as e:
        bot.reply_to(message, f"Terjadi kesalahan: {e}")

def handle_partition(message, file_id, partition):
    chat_id = message.chat.id

    if not is_vip_user(chat_id):
        bot.reply_to(message, "Anda tidak memiliki akses untuk menggunakan bot ini.")
        return

    if chat_id in user_files and file_id in user_files[chat_id]:
        user_name = user_names[chat_id].get(file_id, "No Name")
        df = user_files[chat_id][file_id]['df']
        vcf_base_name = user_files[chat_id][file_id].get('vcf_name', user_name)
        
        try:
            df_copy = df.copy()
            
            if partition != 'all':
                partition = int(partition)
                chunks = [df_copy[i:i + partition] for i in range(0, df_copy.shape[0], partition)]
            else:
                chunks = [df_copy]
            
            for i, chunk in enumerate(chunks):
                with BytesIO() as vcf:
                    for index, row in chunk.iterrows():
                        phone_number = re.sub(r'[+\- ]', ' ', str(row[0]))
                        phone_number = '+' + phone_number
                        
                        if 1 <= index + 1 <= 9:
                            user_index = f"00{index + 1}"
                        elif 10 <= index + 1 <= 99:
                            user_index = f"0{index + 1}"
                        else:
                            user_index = str(index + 1)
                        
                        vcf.write(f"BEGIN:VCARD\nVERSION:3.0\nN:{user_name} 0{user_index};;;\nTEL;TYPE=CELL:{phone_number}\nEND:VCARD\n".encode())
                    
                    vcf.name = f"{vcf_base_name}_{i + 1}.vcf"
                    vcf.seek(0)
                    bot.send_document(chat_id, vcf)
            
            del user_files[chat_id][file_id]
            if not user_files[chat_id]:
                del user_files[chat_id]
            bot.reply_to(message, f"File VCF {file_id} telah dikirim.")
        except Exception as e:
            bot.reply_to(message, f"Terjadi kesalahan saat memproses file: {e}")
    else:
        bot.reply_to(message, "File tidak ditemukan. Silakan unggah file terlebih dahulu.")

def handle_vcf_file(message, downloaded_file, file_name):
    chat_id = message.chat.id
    
    # Menghitung jumlah kontak dari file VCF
    vcf_content = downloaded_file.decode('utf-8')
    contact_count = vcf_content.count("BEGIN:VCARD")
    
    # Mengirimkan pesan untuk meminta jumlah kontak per file VCF
    bot.reply_to(message, f"File VCF {file_name} berhasil diunggah.\nJumlah kontak: {contact_count}\nSILAHKAN MASUKKAN JUMLAH KONTAK PER FILE VCF:")
    bot.register_next_step_handler(message, partition_vcf_file, downloaded_file, file_name)

def partition_vcf_file(message, downloaded_file, file_name):
    chat_id = message.chat.id
    
    try:
        # Mendapatkan jumlah kontak per file dari pesan pengguna
        contacts_per_file = int(message.text.strip())
        
        # Membaca dan memproses file VCF
        vcf_content = downloaded_file.decode('utf-8')
        vcf_lines = vcf_content.splitlines()
        
        # Membagi file VCF berdasarkan jumlah kontak per file
        vcf_entries = []
        current_entry = []
        count = 0
        for line in vcf_lines:
            current_entry.append(line)
            if line.strip() == "END:VCARD":
                count += 1
                if count % contacts_per_file == 0:
                    vcf_entries.append(current_entry)
                    current_entry = []
        if current_entry:
            vcf_entries.append(current_entry)
        
        for i, entry in enumerate(vcf_entries):
            with BytesIO() as vcf_file:
                vcf_file.write("\n".join(entry).encode())
                vcf_file.name = f"{file_name} PART {i+1}.vcf"
                vcf_file.seek(0)
                bot.send_document(chat_id, vcf_file)
        
        bot.reply_to(message, f"File VCF telah dipartisi menjadi {len(vcf_entries)} bagian dengan {contacts_per_file} kontak per file dan dikirimkan.")
    except ValueError:
        bot.reply_to(message, "Format jumlah kontak salah. Silakan masukkan angka yang valid.")
    except Exception as e:
        bot.reply_to(message, f"Terjadi kesalahan saat memproses file: {e}")

bot.polling()
