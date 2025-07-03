#!/usr/bin/python3
import hashlib
import os
import shutil
import random
import string
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import gradio as gr


class PasswordManager:
    def __init__(self):
        self.path_to_database = "passwords.db"
        if not os.path.exists(self.path_to_database):
            self.create_default_db()
        with open(self.path_to_database, "rb") as db_handle:
            self.db_key_hash = db_handle.read(64).decode()
            self.ciphertext = db_handle.read()
        self.decryption_key = None
        self.content = ""
        self.records_count = 0

    def pad_db_key(self, password):
        return password + ("0" * (16 - (len(password) % 16))) if len(password) % 16 != 0 else password

    def create_default_db(self):
        default_pass = hashlib.sha256(self.pad_db_key("password123").encode()).hexdigest()
        with open(self.path_to_database, "wb") as db_handle:
            db_handle.write(default_pass.encode())
        print("Created new DB with default key 'password123'")

    def decrypt_db(self, key):
        self.decryption_key = self.pad_db_key(key)
        password_hash = hashlib.sha256(self.decryption_key.encode()).hexdigest()
        if password_hash != self.db_key_hash:
            return "❌ Invalid decryption key."
        if self.ciphertext.strip():
            aes_instance = AES.new(self.decryption_key.encode(), AES.MODE_CBC, self.decryption_key[:16].encode())
            self.content = unpad(aes_instance.decrypt(self.ciphertext), AES.block_size).decode("UTF-8")
            self.records_count = len(self.content.split("|"))
        else:
            self.content = ""
            self.records_count = 0
        return "✅ Decryption successful."

    def encrypt_and_save(self):
        with open(self.path_to_database, "wb") as db_handle:
            ciphertext = b""
            if self.records_count != 0 and self.content.strip():
                aes_instance = AES.new(self.decryption_key.encode(), AES.MODE_CBC, self.decryption_key[:16].encode())
                ciphertext = aes_instance.encrypt(pad(self.content.encode(), AES.block_size))
            db_handle.write(self.db_key_hash.encode() + ciphertext)

    def show_credentials(self):
        if self.records_count == 0 or not self.content.strip():
            return "No records."
        table = self.content.split("|")
        output = "ID | Username/Email | Password | Platform\n"
        output += "-" * 50 + "\n"
        for row in table:
            fields = row.split("-")
            output += f"{fields[0]} | {fields[1]} | {fields[2]} | {fields[3]}\n"
        return output

    def add_credentials(self, username, password, platform):
        new_id = 1 if self.records_count == 0 or not self.content.strip() else int(
            self.content.split("|")[-1].split("-")[0]) + 1
        new_record = f"{new_id}-{username}-{password}-{platform}"
        self.content = new_record if self.records_count == 0 or not self.content.strip() else self.content + "|" + new_record
        self.records_count += 1
        self.encrypt_and_save()
        return "✅ Record added."

    def edit_credentials(self, record_id, new_username, new_password):
        if self.records_count == 0 or not self.content.strip():
            return "❌ No records."
        records = self.content.split("|")
        updated = False
        for i, record in enumerate(records):
            fields = record.split("-")
            if int(fields[0]) == record_id:
                if new_username.strip():
                    fields[1] = new_username
                if new_password.strip():
                    fields[2] = new_password
                records[i] = "-".join(fields)
                updated = True
                break
        if not updated:
            return "❌ Record not found."
        self.content = "|".join(records)
        self.encrypt_and_save()
        return "✅ Record updated."

    def delete_credentials(self, record_id):
        if self.records_count == 0 or not self.content.strip():
            return "❌ No records."
        records = self.content.split("|")
        new_records = []
        found = False
        for record in records:
            fields = record.split("-")
            if int(fields[0]) == record_id:
                found = True
                continue
            new_records.append(record)
        if not found:
            return "❌ Record not found."
        self.content = "|".join(new_records)
        self.records_count -= 1
        self.encrypt_and_save()
        return "✅ Record deleted."

    def change_db_password(self, current_pass, new_pass):
        current_hash = hashlib.sha256(self.pad_db_key(current_pass).encode()).hexdigest()
        if current_hash != self.db_key_hash:
            return "❌ Current key incorrect."
        if len(new_pass) < 10:
            return "❌ New key must be at least 10 characters."
        new_padded = self.pad_db_key(new_pass)
        new_hash = hashlib.sha256(new_padded.encode()).hexdigest()
        self.db_key_hash = new_hash
        self.decryption_key = new_padded
        self.encrypt_and_save()
        return "✅ Key updated."

    def generate_password(self):
        return "".join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=16))

    def backup_database(self):
        backup_path = "./passwords.db.bak"
        shutil.copyfile(self.path_to_database, backup_path)
        return f"✅ Backup created: {backup_path}"

    def erase_database(self):
        self.content = ""
        self.records_count = 0
        self.encrypt_and_save()
        return "✅ Database erased."

    def send_password_to_email(self, record_id, to_email):
        if self.records_count == 0 or not self.content.strip():
            return "❌ No records."
        record = None
        for rec in self.content.split("|"):
            fields = rec.split("-")
            if int(fields[0]) == record_id:
                record = fields
                break
        if not record:
            return "❌ Record not found."

        sender_email = "python24122006@gmail.com"
        app_password = "pxahuzxdzywtukne"

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = f"Password for {record[3]}"
        body = f"Username/Email: {record[1]}\nPassword: {record[2]}\nPlatform: {record[3]}"
        msg.attach(MIMEText(body, 'plain'))
        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, app_password)
            server.sendmail(sender_email, to_email, msg.as_string())
            server.quit()
            return "✅ Email sent."
        except Exception as e:
            return f"❌ Failed: {e}"


pm = PasswordManager()


# Gradio UI Functions
def decrypt_ui(key):
    status = pm.decrypt_db(key)
    creds = pm.show_credentials()
    return status, creds


def add_ui(username, password, platform):
    status = pm.add_credentials(username, password, platform)
    creds = pm.show_credentials()
    return status, creds


def edit_ui(record_id, new_username, new_password):
    if record_id is None:
        return "❌ Please enter a valid ID.", pm.show_credentials()
    status = pm.edit_credentials(int(record_id), new_username, new_password)
    creds = pm.show_credentials()
    return status, creds


def delete_ui(record_id):
    if record_id is None:
        return "❌ Please enter a valid ID.", pm.show_credentials()
    status = pm.delete_credentials(int(record_id))
    creds = pm.show_credentials()
    return status, creds


def change_pass_ui(current_key, new_key):
    return pm.change_db_password(current_key, new_key)


def generate_pass_ui():
    return pm.generate_password()


def backup_ui():
    return pm.backup_database()


def erase_ui():
    status = pm.erase_database()
    creds = pm.show_credentials()
    return status, creds


def send_email_ui(record_id, to_email):
    if record_id is None:
        return "❌ Please enter a valid ID."
    return pm.send_password_to_email(int(record_id), to_email)


# Gradio Interface
with gr.Blocks() as demo:
    gr.Markdown("## 🔐 Password Manager — Gradio UI")

    with gr.Tab("Decrypt & Show"):
        key = gr.Textbox(label="Decryption Key", type="password")
        decrypt_button = gr.Button("Decrypt")
        decrypt_status = gr.Textbox(label="Status")
        creds_box = gr.Textbox(label="Credentials", lines=10)
        decrypt_button.click(decrypt_ui, inputs=key, outputs=[decrypt_status, creds_box])

    with gr.Tab("Add"):
        u = gr.Textbox(label="Username/Email")
        p = gr.Textbox(label="Password", type="password")
        plat = gr.Textbox(label="Platform")
        add_button = gr.Button("Add")
        add_status = gr.Textbox(label="Status")
        add_creds = gr.Textbox(label="Credentials", lines=10)
        add_button.click(add_ui, inputs=[u, p, plat], outputs=[add_status, add_creds])

    with gr.Tab("Edit"):
        eid = gr.Number(label="Record ID", precision=0)
        nu = gr.Textbox(label="New Username/Email (optional)")
        np = gr.Textbox(label="New Password (optional)", type="password")
        edit_button = gr.Button("Edit")
        edit_status = gr.Textbox(label="Status")
        edit_creds = gr.Textbox(label="Credentials", lines=10)
        edit_button.click(edit_ui, inputs=[eid, nu, np], outputs=[edit_status, edit_creds])

    with gr.Tab("Delete"):
        did = gr.Number(label="Record ID", precision=0)
        del_button = gr.Button("Delete")
        del_status = gr.Textbox(label="Status")
        del_creds = gr.Textbox(label="Credentials", lines=10)
        del_button.click(delete_ui, inputs=did, outputs=[del_status, del_creds])

    with gr.Tab("Change DB Password"):
        ck = gr.Textbox(label="Current Key", type="password")
        nk = gr.Textbox(label="New Key (min 10 chars)", type="password")
        change_button = gr.Button("Change")
        change_status = gr.Textbox(label="Status")
        change_button.click(change_pass_ui, inputs=[ck, nk], outputs=change_status)

    with gr.Tab("Generate Password"):
        gen_button = gr.Button("Generate")
        gen_output = gr.Textbox(label="Generated Password")
        gen_button.click(generate_pass_ui, outputs=gen_output)

    with gr.Tab("Backup"):
        backup_button = gr.Button("Backup Database")
        backup_status = gr.Textbox(label="Status")
        backup_button.click(backup_ui, outputs=backup_status)

    with gr.Tab("Erase"):
        erase_button = gr.Button("Erase Database")
        erase_status = gr.Textbox(label="Status")
        erase_creds = gr.Textbox(label="Credentials", lines=10)
        erase_button.click(erase_ui, outputs=[erase_status, erase_creds])

    with gr.Tab("Send Email"):
        seid = gr.Number(label="Record ID", precision=0)
        to_e = gr.Textbox(label="Recipient Email")
        send_button = gr.Button("Send Email")
        send_status = gr.Textbox(label="Status")
        send_button.click(send_email_ui, inputs=[seid, to_e], outputs=send_status)

demo.launch()
