import requests
from bs4 import BeautifulSoup
from datetime import datetime
import csv
import os
import smtplib
from email.mime.text import MIMEText
import re

# CONFIG: List your products here
PRODUCTS = [
    {
        "name": "LEGO Audi RS Q e-tron",
        "url": "https://www.emag.ro/legor-technic-audi-rs-q-e-tron-42160-914-piese-5702017425207/pd/DVFWNWMBM/",
        "threshold": 519.99,
    },
    {
        "name": "LEGO Chevrolet Corvette",
        "url": "https://www.emag.ro/legor-technic-chevrolet-corvette-stingray-42205-732-piese-5702017816289/pd/DBB9X6YBM/",
        "threshold": 199.99,
    }
]

CSV_FILE = "emag_price_history.csv"
HEADERS = {"User-Agent": "Mozilla/5.0"}

# Email config
EMAIL_FROM = "liviumarius912000@gmail.com"
EMAIL_TO = "liviumarius912000@gmail.com"
EMAIL_PASSWORD = "lmdi olxb mrgv ygvt "  # Use environment variables for security in production
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

def fetch_price(product_url):
    try:
        response = requests.get(product_url, headers=HEADERS, timeout=10)
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
        cleaned_price = re.sub(r"[^\d.]", "", full_price)
        return float(cleaned_price) if cleaned_price else None
    except Exception as e:
        print(f"Error fetching price: {e}")
        return None

def read_last_price(product_name, csv_file=CSV_FILE):
    if not os.path.exists(csv_file):
        return None
    with open(csv_file, newline="", encoding="utf-8") as csvfile:
        rows = list(csv.reader(csvfile))
        if len(rows) < 2:
            return None
        # Filter rows for the product and get last price
        product_rows = [row for row in rows[1:] if row[1] == product_name]
        if not product_rows:
            return None
        return float(product_rows[-1][2])

def save_price(product_name, price, alert_sent, threshold, csv_file=CSV_FILE):
    file_exists = os.path.isfile(csv_file)
    with open(csv_file, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            writer.writerow(["Timestamp", "Product", "Price (RON)", "Threshold (RON)", "Alert Sent"])
        writer.writerow([datetime.now().isoformat(), product_name, price, threshold, alert_sent])

def send_email_notification(product_name, current_price, product_url, threshold):
    subject = f"eMAG Price Alert 🚨 - {product_name}"
    body = (
        f"The price for *{product_name}* dropped below {threshold} RON!\n"
        f"Current price: {current_price} RON\n"
        f"Link: {product_url}"
    )
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
        print(f"📧 Email sent for {product_name}")
    except Exception as e:
        print(f"Failed to send email for {product_name}: {e}")

def main():
    for product in PRODUCTS:
        name = product["name"]
        url = product["url"]
        threshold = product["threshold"]

        print(f"\n🔍 Checking price for: {name}")
        current_price = fetch_price(url)
        if current_price is None:
            print("Price not found.")
            continue

        alert_sent = "No"
        last_price = read_last_price(name)

        if current_price < threshold:
            send_email_notification(name, current_price, url, threshold)
            alert_sent = "Yes"

        save_price(name, current_price, alert_sent, threshold)
        print(f"Price saved: {current_price} RON | Threshold: {threshold} RON | Alert Sent: {alert_sent}")

if __name__ == "__main__":
    main()
