import requests
from bs4 import BeautifulSoup
import time
import smtplib
from email.mime.text import MIMEText
from plyer import notification
import json
import re

# Selenium (ONLY for Flipkart)
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

# ================= CONFIG ================= #

EMAIL = "sparshmaheshwari003@gmail.com"
APP_PASSWORD = "crbwattqulectkyq"

CHECK_INTERVAL = 60 * 20

# ========================================== #

def load_products():
    try:
        with open("products.json", "r") as f:
            return json.load(f)
    except:
        return []

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9"
}

# -------- EMAIL -------- #
def send_email(msg):
    try:
        message = MIMEText(msg)
        message["Subject"] = "🔥 Price Drop Alert"
        message["From"] = EMAIL
        message["To"] = EMAIL

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL, APP_PASSWORD)
            server.send_message(message)

        print("📩 Email sent!")

    except Exception as e:
        print("Email error:", e)

# -------- PRICE PER GRAM -------- #
def price_per_gram(price, total_weight, protein_percentage):
    try:
        total_protein = total_weight * (protein_percentage / 100)
        return round(price / total_protein, 2)
    except:
        return None

# -------- NOTIFICATION -------- #
def notify(msg):
    notification.notify(
        title="Price Alert 🚀",
        message=msg,
        timeout=10
    )

# -------- SCRAPERS -------- #

def amazon_price(soup):
    try:
        price = soup.select_one("span.a-offscreen")
        if price:
            return float(price.text.replace("₹", "").replace(",", ""))
    except:
        return None
def muscleblaze_price(soup):
    try:
        price = soup.select_one(".offer-price")
        if price:
            return float(price.text.replace("₹", "").replace(",", ""))
    except:
        return None
def asitis_price(soup):
    try:
        price_div = soup.select_one(".price__current")
        if price_div:
            match = re.search(r"[\d,]+\.\d+", price_div.text)
            if match:
                return float(match.group().replace(",", ""))
    except:
        return None
def avvatar_price(soup):
    try:
        price = soup.select_one(".new-price")
        if price:
            return float(price.text.replace("₹", "").replace(",", ""))
    except:
        return None
def naturaltein_price(soup):
    try:
        price = soup.select_one(".price-item--sale.price-item--last") \
             or soup.select_one(".price-item--sale")
        if price:
            return float(price.text.replace("₹", "").replace(",", ""))
    except:
        return None

# -------- FLIPKART (FIXED) -------- #

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def flipkart_price(url):
    driver = None
    try:
        options = Options()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")

        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )

        driver.get(url)

        wait = WebDriverWait(driver, 10)

        # ❗ Close login popup if appears
        try:
            close_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'✕')]")))
            close_btn.click()
        except:
            pass

        # ✅ WAIT FOR PRICE ELEMENT (THIS IS KEY)
        price_element = wait.until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'_30jeq3')]"))
        )

        price_text = price_element.text
        print("RAW PRICE:", price_text)

        price = float(price_text.replace("₹", "").replace(",", "").strip())

        print("✅ FLIPKART PRICE:", price)

        return price

    except Exception as e:
        print("❌ FLIPKART ERROR:", e)
        return None

    finally:
        if driver:
            driver.quit()
# -------- FETCH -------- #

def get_price(url):
    try:
        print("\nURL CHECK:", url)

        if "flipkart" in url:
            print("➡ FLIPKART (SELENIUM)")
            return flipkart_price(url)

        # rest use requests (FAST)
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, "lxml")

        if "amazon" in url:
            return amazon_price(soup)

        elif "muscleblaze" in url:
            return muscleblaze_price(soup)

        elif "asitisnutrition" in url:
            return asitis_price(soup)

        elif "avvatar" in url:
            return avvatar_price(soup)

        elif "naturaltein" in url:
            return naturaltein_price(soup)

        else:
            print("❌ NO SCRAPER")
            return None

    except Exception as e:
        print("Request error:", e)
        return None

# -------- TRACKER -------- #

def track_prices():
    alerted = set()

    while True:
        print("\n🔍 Checking prices...\n")

        products = load_products()

        for product in products:
            price = get_price(product["url"])

            if price is not None:
                print(f"{product['name']} → ₹{price}")

                if price <= product["target_price"] and product["url"] not in alerted:

                    ppg = price_per_gram(
                        price,
                        product.get("total_weight"),
                        product.get("protein_percentage")
                    )

                    msg = f"{product['name']} ₹{price}"
                    if ppg:
                        msg += f" | ₹{ppg}/g"

                    notify(msg)
                    send_email(f"{msg}\n{product['url']}")

                    alerted.add(product["url"])

            else:
                print(f"❌ Failed: {product['name']}")

        print("\n😴 Sleeping...\n")
        time.sleep(CHECK_INTERVAL)