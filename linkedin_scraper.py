"""
LinkedIn Job Scraper - Main scraper class for login and job search functionality
"""
import time
import os
from urllib.parse import quote
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv


class LinkedInScraper:
    """Scraper class for LinkedIn job search"""
    
    LINKEDIN_LOGIN_URL = "https://www.linkedin.com/login"
    LINKEDIN_JOBS_BASE_URL = "https://www.linkedin.com/jobs/search/"
    
    def __init__(self, headless=False, job_title="software developer", time_seconds=3600):
        """
        Initialize the scraper with Chrome WebDriver
        
        Args:
            headless: Run browser without GUI
            job_title: Job title/keywords to search (e.g., "software developer", "data engineer")
            time_seconds: Time filter in seconds (3600 = 1 hour, 86400 = 24 hours)
        """
        load_dotenv()
        
        self.email = os.getenv("LINKEDIN_EMAIL")
        self.password = os.getenv("LINKEDIN_PASSWORD")
        self.job_title = job_title
        self.time_seconds = time_seconds
        
        if not self.email or not self.password:
            raise ValueError("LINKEDIN_EMAIL and LINKEDIN_PASSWORD must be set in .env file")
        
        # Setup Chrome options
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        
        # Initialize WebDriver
        try:
            # Try using webdriver-manager
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        except Exception as e:
            print(f"WebDriver Manager failed: {e}")
            print("Trying default Chrome installation...")
            # Fallback to system Chrome
            self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 20)
        
    def login(self):
        """Login to LinkedIn with credentials from .env"""
        print(f"Navigating to LinkedIn login page...")
        self.driver.get(self.LINKEDIN_LOGIN_URL)
        time.sleep(2)
        
        try:
            # Enter email
            print(f"Entering email: {self.email}")
            email_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            email_field.clear()
            email_field.send_keys(self.email)
            time.sleep(1)
            
            # Enter password
            print("Entering password...")
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(self.password)
            time.sleep(1)
            
            # Click login button
            print("Clicking login button...")
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()
            
            # Wait for login to complete
            time.sleep(5)
            
            # Check if login was successful
            if "feed" in self.driver.current_url or "checkpoint" in self.driver.current_url:
                print("Login successful!")
                return True
            elif "challenge" in self.driver.current_url:
                print("Security challenge detected. Please complete the verification manually.")
                input("Press Enter after completing the verification...")
                return True
            else:
                print(f"Current URL: {self.driver.current_url}")
                # Check for error messages
                try:
                    error = self.driver.find_element(By.CSS_SELECTOR, ".form__label--error, #error-for-username, #error-for-password")
                    print(f"Login error: {error.text}")
                    return False
                except:
                    print("Login may have succeeded, continuing...")
                    return True
                    
        except Exception as e:
            print(f"Login failed with error: {e}")
            return False
    
    def _build_jobs_url(self):
        """Build the LinkedIn jobs URL with dynamic parameters"""
        encoded_title = quote(self.job_title)
        return f"{self.LINKEDIN_JOBS_BASE_URL}?f_TPR=r{self.time_seconds}&keywords={encoded_title}"
    
    def search_jobs(self):
        """Navigate to the job search page with filters applied"""
        jobs_url = self._build_jobs_url()
        print(f"Searching for: '{self.job_title}' (last {self.time_seconds} seconds)")
        print(f"URL: {jobs_url}")
        self.driver.get(jobs_url)
        time.sleep(3)
        
        # Wait for job listings to load
        try:
            self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".jobs-search-results-list, .scaffold-layout__list"))
            )
            print("Job search page loaded successfully!")
            return True
        except Exception as e:
            print(f"Failed to load job search page: {e}")
            return False
    
    def scroll_job_list(self):
        """Scroll through the job list to load all jobs"""
        print("Scrolling to load all jobs...")
        
        try:
            # Find the jobs list container
            jobs_container = self.driver.find_element(By.CSS_SELECTOR, ".jobs-search-results-list, .scaffold-layout__list")
            
            last_height = 0
            scroll_attempts = 0
            max_attempts = 10
            
            while scroll_attempts < max_attempts:
                # Scroll down the jobs container
                self.driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollHeight", 
                    jobs_container
                )
                time.sleep(2)
                
                new_height = self.driver.execute_script(
                    "return arguments[0].scrollHeight", 
                    jobs_container
                )
                
                if new_height == last_height:
                    break
                    
                last_height = new_height
                scroll_attempts += 1
                
            print(f"Finished scrolling after {scroll_attempts} attempts")
            
        except Exception as e:
            print(f"Error during scrolling: {e}")
    
    def get_job_listings(self):
        """Get all job listings from the current page"""
        jobs = []
        seen_job_ids = set()
        skipped_duplicates = 0
        skipped_no_id = 0
        
        try:
            # Find all job cards using multiple selectors
            job_cards = self.driver.find_elements(
                By.CSS_SELECTOR, 
                ".job-card-container, .jobs-search-results__list-item, li[data-occludable-job-id], .scaffold-layout__list-item"
            )
            
            print(f"Found {len(job_cards)} job cards")
            
            for card in job_cards:
                try:
                    job_data = self._extract_job_from_card(card)
                    if not job_data:
                        skipped_no_id += 1
                        continue
                    if job_data['job_id'] in seen_job_ids:
                        skipped_duplicates += 1
                        continue
                    # Include jobs even with unknown titles
                    seen_job_ids.add(job_data['job_id'])
                    jobs.append(job_data)
                except Exception as e:
                    print(f"Error extracting job from card: {e}")
                    continue
            
            print(f"  - Valid jobs: {len(jobs)}")
            print(f"  - Skipped duplicates: {skipped_duplicates}")
            print(f"  - Skipped (no ID): {skipped_no_id}")
                    
        except Exception as e:
            print(f"Error getting job listings: {e}")
            
        return jobs
    
    def _extract_job_from_card(self, card):
        """Extract job data from a job card element"""
        job_data = {}
        
        try:
            # Get job ID - try multiple attributes
            job_id = card.get_attribute("data-job-id")
            if not job_id:
                job_id = card.get_attribute("data-occludable-job-id")
            if not job_id:
                # Try to find it from a child element
                try:
                    job_id_elem = card.find_element(By.CSS_SELECTOR, "[data-job-id], [data-occludable-job-id]")
                    job_id = job_id_elem.get_attribute("data-job-id") or job_id_elem.get_attribute("data-occludable-job-id")
                except:
                    pass
            if not job_id:
                # Try to extract from link
                try:
                    link = card.find_element(By.CSS_SELECTOR, "a[href*='/jobs/view/']")
                    href = link.get_attribute("href")
                    job_id = href.split("/jobs/view/")[1].split("/")[0].split("?")[0]
                except:
                    return None
            
            if not job_id:
                return None
                
            job_data["job_id"] = job_id
            job_data["link"] = f"https://www.linkedin.com/jobs/view/{job_id}"
            
            # Get job title - try multiple selectors (ordered by specificity)
            title_selectors = [
                ".job-card-list__title strong",
                ".job-card-list__title",
                ".artdeco-entity-lockup__title strong",
                ".artdeco-entity-lockup__title",
                "a.job-card-list__title--link strong",
                ".job-card-container__link strong",
                ".jobs-unified-top-card__job-title",
                "h3 a",
                "h3",
                "a[href*='/jobs/view/']",
                "strong",
            ]
            
            job_title = "Unknown"
            for selector in title_selectors:
                try:
                    title_elem = card.find_element(By.CSS_SELECTOR, selector)
                    text = title_elem.text.strip()
                    # Filter out non-title text (company names, locations, etc.)
                    if text and len(text) > 2 and len(text) < 150:
                        # Skip if it looks like a location or company badge
                        if not any(x in text.lower() for x in ['ago', 'promoted', 'easy apply', 'applicants']):
                            job_title = text.split('\n')[0].strip()  # Take first line only
                            break
                except:
                    continue
            
            job_data["job_title"] = job_title
            
            # Required years will be extracted from job description later
            job_data["required_years"] = "Not specified"
            
            return job_data
            
        except Exception as e:
            print(f"Error in _extract_job_from_card: {e}")
            return None
    
    def get_job_details(self, job_id):
        """Click on a job and extract detailed information including years of experience"""
        try:
            # Try multiple ways to find and click the job card
            job_card = None
            selectors = [
                f"[data-job-id='{job_id}']",
                f"[data-occludable-job-id='{job_id}']",
                f"a[href*='/jobs/view/{job_id}']",
            ]
            
            for selector in selectors:
                try:
                    job_card = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except:
                    continue
            
            if job_card:
                job_card.click()
                time.sleep(2)
            else:
                # Navigate directly to the job page
                self.driver.get(f"https://www.linkedin.com/jobs/view/{job_id}")
                time.sleep(3)
            
            # Wait for job details to load
            self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".jobs-description, .job-view-layout, .jobs-unified-top-card"))
            )
            
            # Get job description
            description = ""
            desc_selectors = [
                ".jobs-description__content",
                ".jobs-box__html-content",
                ".jobs-description",
                "#job-details",
            ]
            
            for selector in desc_selectors:
                try:
                    description_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    description = description_elem.text
                    if description:
                        break
                except:
                    continue
            
            return description
                
        except Exception as e:
            print(f"Error getting job details for {job_id}: {e}")
            return ""
    
    def get_job_title_from_page(self):
        """Extract job title from the currently open job page"""
        title_selectors = [
            ".jobs-unified-top-card__job-title",
            ".job-details-jobs-unified-top-card__job-title",
            "h1.t-24",
            "h1",
        ]
        
        for selector in title_selectors:
            try:
                title_elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                title = title_elem.text.strip()
                if title and len(title) > 2:
                    return title
            except:
                continue
        
        return None
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            print("Browser closed.")


# Test function
def test_login():
    """Test the login functionality"""
    scraper = LinkedInScraper(headless=False)
    try:
        success = scraper.login()
        if success:
            print("=== LOGIN TEST PASSED ===")
        else:
            print("=== LOGIN TEST FAILED ===")
        return success
    finally:
        input("Press Enter to close the browser...")
        scraper.close()


if __name__ == "__main__":
    test_login()

