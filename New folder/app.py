import streamlit as st
import random
import string
from datetime import datetime
import smtplib
from email.mime.text import MIMEText

# --- Page Setup ---
st.set_page_config(page_title="Custom Password Generator", layout="centered")
st.title("🔐 Custom Password Generator")

st.write("Choose how many characters of each type you want in your password:")

# --- User Inputs ---
purpose = st.text_input("Where will this password be used? (e.g., Instagram, Work Email)")
email = st.text_input("Enter your email address (optional)")

num_uppercase = st.slider("Uppercase Letters (A-Z)", min_value=0, max_value=10, value=3)
num_lowercase = st.slider("Lowercase Letters (a-z)", min_value=0, max_value=10, value=3)
num_numbers = st.slider("Numbers (0-9)", min_value=0, max_value=10, value=2)
num_symbols = st.slider("Symbols (!@#$%)", min_value=0, max_value=10, value=2)

# --- Password Generator Function ---
def generate_custom_password(upper, lower, numbers, symbols):
    password_chars = []
    password_chars += random.choices(string.ascii_uppercase, k=upper)
    password_chars += random.choices(string.ascii_lowercase, k=lower)
    password_chars += random.choices(string.digits, k=numbers)
    password_chars += random.choices(string.punctuation, k=symbols)
    random.shuffle(password_chars)
    return ''.join(password_chars)

# --- Save to TXT ---
def save_password_to_file(password, purpose):
    with open("generated_passwords.txt", "a") as file:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file.write(f"[{timestamp}] ({purpose}) {password}\n")

# --- Send Email ---
def send_email(recipient_email, password, purpose):
    try:
        sender_email = st.secrets["email"]["address"]
        app_password = st.secrets["email"]["app_password"]

        msg = MIMEText(f"🔐 Your password for *{purpose}* is:\n\n{password}")
        msg['Subject'] = f'Password for {purpose}'
        msg['From'] = sender_email
        msg['To'] = recipient_email

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, app_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
        return True
    except Exception as e:
        st.error(f"Error sending email: {e}")
        return False

# --- Button Action ---
if st.button("Generate Password"):
    total_length = num_uppercase + num_lowercase + num_numbers + num_symbols
    if total_length == 0:
        st.warning("Please choose at least one character.")
    elif not purpose:
        st.warning("Please specify where the password will be used.")
    else:
        password = generate_custom_password(num_uppercase, num_lowercase, num_numbers, num_symbols)
        save_password_to_file(password, purpose)

        if email:
            if send_email(email, password, purpose):
                st.success(f"✅ Password for *{purpose}* generated, saved, and emailed to {email}")
            else:
                st.error("❌ Could not send the email. Check email or app password.")
        else:
            st.success(f"✅ Password for *{purpose}* generated and saved. No email sent.")

        st.text_input("Your Generated Password:", value=password, type="default", disabled=False)
