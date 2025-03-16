from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import time
from plyer import notification

# Facebook Credentials
USERNAME = "giulia02.cor@gmail.com"
PASSWORD = "Aisedra"

# Set up Selenium
options = webdriver.ChromeOptions()
#options.add_argument("--headless")  # Run in the background
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def login():
    driver.get("https://www.facebook.com/")
    time.sleep(3)
    
    # Enter username
    username_box = driver.find_element(By.ID, "email")
    username_box.send_keys(USERNAME)
    
    # Enter password
    password_box = driver.find_element(By.ID, "pass")
    password_box.send_keys(PASSWORD)
    password_box.send_keys(Keys.RETURN)

    time.sleep(5)

def check_messages():
    driver.get("https://www.facebook.com/marketplace/inbox")
    time.sleep(5)
    
    # Get all unread message elements
    unread_messages = driver.find_elements(By.XPATH, "//div[contains(@aria-label, 'Unread message')]")
    
    if unread_messages:
        notification.notify(
            title="New Facebook Marketplace Message!",
            message=f"You have {len(unread_messages)} new message(s).",
            timeout=5
        )

login()
while True:
    check_messages()
    time.sleep(60)  # Check every minute
