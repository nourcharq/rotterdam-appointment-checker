
import os
import sys
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

URL = "https://concern.ir.rotterdam.nl/afspraak/maken/product/indienen-naturalisatieverzoek"


def send_telegram(message):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    response = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data={"chat_id": chat_id, "text": message},
        timeout=20,
    )
    response.raise_for_status()
    print("Telegram notification sent!")


options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1365,900")

driver = None

try:
    print("Opening Rotterdam appointment website...")
    driver = webdriver.Chrome(options=options)
    driver.get(URL)

    wait = WebDriverWait(driver, 25)
    button = wait.until(
        EC.element_to_be_clickable((By.NAME, "verder"))
    )
    button.click()

    print("Checking appointment availability...")

    wait.until(
        lambda d: (
            "alert-warning" in d.page_source
            or "list-group-item-action" in d.page_source
        )
    )

    soup = BeautifulSoup(driver.page_source, "html.parser")

    available = []
    for button in soup.select("button.list-group-item-action"):
        if button.has_attr("disabled"):
            continue

        location = button.find("h3")
        date_time = button.find("p")

        if location and date_time:
            available.append(
                f"{location.get_text(' ', strip=True)}: "
                f"{date_time.get_text(' ', strip=True)}"
            )

    if available:
        message = (
            "ROTTERDAM NATURALISATION APPOINTMENTS FOUND!\n\n"
            + "\n".join(available)
            + f"\n\nBook here: {URL}"
            + f"\nChecked: {datetime.now().isoformat(timespec='seconds')}"
        )
        print(message)
        send_telegram(message)

    elif soup.select_one("div.alert-warning"):
        print("No appointments available.")

    else:
        print("Unable to confirm appointment availability.")
        sys.exit(1)

except Exception as error:
    print(f"Checker failed: {type(error).__name__}: {error}")
    sys.exit(1)

finally:
    if driver:
        driver.quit()
