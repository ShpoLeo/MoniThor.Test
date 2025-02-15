import time
import os
import json
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from utils import get_url_status, certificate_checks
from logs import logger

with open('config.json', 'r') as f:
    config = json.load(f)

url = f"{config['host']}:{config['port']}/"
uu = config.get("uu", 1)  # Default to 1 is not provided/ uu = unique user

def create_driver():
    """Creates and returns a new Chrome WebDriver instance."""
    logger.info("Initializing Chrome WebDriver...")
    return webdriver.Chrome()

def is_alert_present(driver):
    """Checks if an alert is present in the browser."""
    try:
        WebDriverWait(driver, 5).until(EC.alert_is_present())
        return True
    except TimeoutException:
        return False

def alert_wait_and_click(driver):
    """Waits for an alert to appear, and clicks to accept it."""
    try:
        if is_alert_present(driver):
            alert = driver.switch_to.alert
            alert.accept()
            logger.info("Alert accepted.")
    except Exception as e:
        logger.error(f"Error handling alert: {e}")

def register(driver, username, password1, password2):
    """Registers a new user."""
    logger.info(f"Registering user: {username}")
    driver.get(f"{url}register")
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "username")))
    driver.find_element(By.ID, "username").send_keys(username)
    driver.find_element(By.ID, "password1").send_keys(password1)
    driver.find_element(By.ID, "password2").send_keys(password2)
    driver.find_element(By.CLASS_NAME, "register-submit").click()
    alert_wait_and_click(driver)

def login(driver, username, password):
    """Logs a user into the monitoring system."""
    logger.info(f"Logging in user: {username}")
    driver.get(f"{url}login")
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "username")))
    driver.find_element(By.ID, "username").send_keys(username)
    driver.find_element(By.ID, "password").send_keys(password)
    driver.find_element(By.CLASS_NAME, "login-submit").click()

def google_login_check(driver):
    driver.get(f"{url}login")
    try:
        # Wait for the page to load and check if the Google login button is present
        google_login_button = driver.find_element(By.LINK_TEXT, "Sign in with Google")
        logger.info("Google login button found.")
        # Click on the Google login button to initiate login flow
        google_login_button.click()
        logger.info("Clicked the Google login button.")

        # Wait for the Google login page to load (this may need to be adjusted based on the actual flow)
        time.sleep(2)  # Ideally, use WebDriverWait here instead of time.sleep

        # Once the Google login page is loaded, you can input the credentials (for example)
        # If there's an email input field:
        email_input = driver.find_element(By.ID, "identifierId")
        email_input.send_keys("shpolyanskiil@gmail.com")  # Replace with actual email
        time.sleep(5)
        driver.find_element(By.ID, "identifierNext").click()
        time.sleep(10)
        email_input.send_keys(Keys.RETURN)
        time.sleep(50)
        logger.info("Entered email and submitted.")

        # Wait for the password input field (wait until it becomes visible)
        time.sleep(10)
        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys("LeonGmailPass24")  # Replace with actual password
        password_input.send_keys(Keys.RETURN)
        logger.info("Entered password and submitted.")
        driver.get(f"{url}dashboard")

    except Exception as e:
        logger.error(f"An error occurred during Google login process: {e}")

def single_upload(driver, domain):
    """Uploads a single domain for verification."""
    logger.info(f"Uploading single domain: {domain}")
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "single")))
    driver.find_element(By.ID, "single").send_keys(domain)
    driver.find_element(By.CLASS_NAME, "single-submit").click()
    alert_wait_and_click(driver)
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "resultsBody")))

def bulk_upload(driver):
    """Uploads a list of domains in bulk."""
    logger.info("Uploading domains in bulk...")
    driver.get(f"{url}dashboard")
    file_path = os.path.abspath('../testdata/Domains_for_upload.txt')
    driver.find_element(By.ID, "bulk").send_keys(file_path)
    driver.find_element(By.CLASS_NAME, "bulk-submit").click()
    alert_wait_and_click(driver)
    alert_wait_and_click(driver)

def remove_one_domain(driver):
    """Removes the first domain from a list of domains on the web page."""
    try:
        list_group = driver.find_element("id", "domains")
        # Find all list items (domains) within the list
        list_items = list_group.find_elements("class name", "list-group-item")
        
        if list_items:
            first_item = list_items[0]
            
            # Extract the domain name (just for informational purposes)
            domain_name = first_item.text.split("\n")[0]
            logger.info(f"Found domain: {domain_name}")
            
            # Find the close button for the first domain item
            close_button = first_item.find_element("class name", "close")
            close_button.click()  # Click the close button to remove the domain
            logger.info(f"Clicked the close button for domain: {domain_name}")
            
            # Assuming `alert_wait_and_click(driver)` handles any confirmation alert
            alert_wait_and_click(driver)  # Handle the confirmation or alert
            logger.info(f"Handled the confirmation alert for domain: {domain_name}")
            
            # Wait for a moment to allow the DOM to update after the deletion
            time.sleep(1)
            logger.debug("Waiting for the DOM to update after deletion.")

        else:
            logger.warning("No domains found to delete.")
   
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")

def verify_results(driver, domains=None):
    """Verifies the results table for domain status and certificate validity."""
    logger.info("Verifying domain results...")
    driver.get(f"{url}results")
    table_body = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "resultsBody")))
    rows = table_body.find_elements(By.TAG_NAME, "tr")
    for row in rows:
        cells = row.find_elements(By.TAG_NAME, "td")
        # Skip rows that don't have the expected number of cells
        if len(cells) < 4:
            continue
        domain = cells[0].text
        status = cells[1].text
        expiration_date = cells[2].text
        issuer = cells[3].text

        # Validate domain status
        try:
            status_validation = get_url_status(domain)
            if status_validation not in ['OK', 'FAILED']:
                logger.error(f"Invalid status for domain {domain}: {status_validation}")
                continue
        except Exception as e:
            logger.error(f"Error validating status for domain {domain}: {e}")
            continue

        # Validate certificate details
        try:
            cert = certificate_checks(domain)
            if expiration_date != cert[0] or issuer != cert[1]:
                logger.error(f"Certificate mismatch for domain {domain}. Expected expiration date: {cert[0]}, issuer: {cert[1]}, but got expiration date: {expiration_date}, issuer: {issuer}.")
                continue
        except Exception as e:
            logger.error(f"Error checking certificate for domain {domain}: {e}")
            continue

        # If all checks pass, log success
        logger.info(f"Domain {domain} passed all checks.")

def perform_user_actions(user_index):
    """Performs a series of actions: register, login, upload, and verify."""
    logger.info(f"Performing actions for user {user_index}...")
    driver = create_driver()
    try:
        start_time = time.time()
        
        username = f"tester{user_index}"
        password = "tester"

        # Register and login the user
        register(driver, username, password, password)
        login(driver, username, password)

        # google_login_check(driver)

        # Perform single domain upload and verify results
        single_upload(driver, config['single-domain'])
        verify_results(driver, config['single-domain'])
        
        # Perform bulk upload 
        bulk_upload(driver)

        # Wait for bulk to finish
        time.sleep(15)

        # Verify results
        # verify_results(driver)

        remove_one_domain(driver)

        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"User {username} completed the actions in {duration:.2f} seconds.")
        return username, duration
    except Exception as e:
        logger.error(f"Error for user {user_index}: {e}")
        return None, None
    finally:
        driver.quit()

if __name__ == "__main__":
    results = []
    with ThreadPoolExecutor(max_workers=uu) as executor:
        futures = [executor.submit(perform_user_actions, i) for i in range(uu)]

        for future in futures:
            try:
                result = future.result()
                if result and result[0]:  # Only append valid results
                    results.append(result)
            except Exception as e:
                logger.error(f"Error during execution: {e}")

    # Print the results for all users
    logger.info("\n--- Test Results ---")
    for username, duration in results:
        logger.info(f"{username}: {duration:.2f} seconds")
