#!/usr/bin/python3
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import csv
import os
import smtplib
from email.mime.text import MIMEText

# CONFIG
PRODUCT_URL = "https://www.emag.ro/legor-technic-audi-rs-q-e-tron-42160-914-piese-5702017425207/pd/DVFWNWMBM/"
CSV_FILE = "emag_price_history.csv"
HEADERS = {"User-Agent": "Mozilla/5.0"}

# Email config
EMAIL_FROM = "liviumarius912000@gmail.com"
EMAIL_TO = "liviumarius912000@gmail.com"
EMAIL_PASSWORD = "lmdi olxb mrgv ygvt "
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Alert threshold
PRICE_ALERT_THRESHOLD = 519.99  # RON

def fetch_price():
    response = requests.get(PRODUCT_URL, headers=HEADERS, timeout=10)
    soup = BeautifulSoup(response.text, 'html.parser')
    price_tag = soup.find("p", {"class": "product-new-price"})
    if not price_tag:
        return None

    main_price = ""
    decimal = ""
    for element in price_tag.children:
        if isinstance(element, str):
            main_price += element.strip()
        elif element.name == "sup":
            decimal = element.get_text(strip=True).replace(",", ".")
    full_price = f"{main_price}{decimal}".strip()
    return float(full_price) if full_price else None

def read_last_price():
    if not os.path.exists(CSV_FILE):
        return None
    with open(CSV_FILE, newline="", encoding="utf-8") as csvfile:
        rows = list(csv.reader(csvfile))
        if len(rows) < 2:
            return None
        return float(rows[-1][1])

def save_price(price, alert_sent):
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            writer.writerow(["Timestamp", "Price (RON)", "Alert Sent"])
        writer.writerow([datetime.now().isoformat(), price, alert_sent])

def send_email_notification(current_price):
    subject = "eMAG Price Alert 🚨"
    body = f"The price dropped below {PRICE_ALERT_THRESHOLD} RON!\nCurrent price: {current_price} RON\nLink: {PRODUCT_URL}"
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
        server.quit()
        print("📧 Email sent.")
    except Exception as e:
        print(f"Failed to send email: {e}")

def main():
    current_price = fetch_price()
    if current_price is None:
        print("Price not found.")
        return

    alert_sent = "No"
    if current_price < PRICE_ALERT_THRESHOLD:
        send_email_notification(current_price)
        alert_sent = "Yes"

    save_price(current_price, alert_sent)
    print(f"Price saved: {current_price} RON | Alert Sent: {alert_sent}")
    print(f"Threshold: {PRICE_ALERT_THRESHOLD} RON")
if __name__ == "__main__":
    main()
