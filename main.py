from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd
import time
import logging
from datetime import datetime
import traceback

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'rera_scraper_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RERAProjectScraper:
    def __init__(self, headless=False, max_projects=6):
        """
        Initialize the RERA Project Scraper
        
        Args:
            headless (bool): Run browser in headless mode
            max_projects (int): Maximum number of projects to scrape
        """
        self.max_projects = max_projects
        self.projects_data = []
        
        # Setup Chrome options
        self.options = Options()
        if headless:
            self.options.add_argument("--headless")
        self.options.add_argument("--start-maximized")
        self.options.add_argument("--disable-blink-features=AutomationControlled")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-gpu")
        self.options.add_argument("--window-size=1920,1080")
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.options.add_experimental_option('useAutomationExtension', False)
        
        # Add user agent to avoid detection
        self.options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self.driver = None
        self.wait = None
    
    def setup_driver(self):
        """Initialize the Chrome driver and WebDriverWait"""
        try:
            self.driver = webdriver.Chrome(options=self.options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.wait = WebDriverWait(self.driver, 20)  # Increased timeout
            logger.info("Chrome driver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Chrome driver: {e}")
            raise
    
    def debug_page_content(self, description=""):
        """Debug helper to log current page state"""
        try:
            current_url = self.driver.current_url
            page_title = self.driver.title
            page_source_length = len(self.driver.page_source)
            
            logger.info(f"=== DEBUG PAGE STATE {description} ===")
            logger.info(f"Current URL: {current_url}")
            logger.info(f"Page Title: {page_title}")
            logger.info(f"Page Source Length: {page_source_length} characters")
            
            # Check for common elements
            buttons = self.driver.find_elements(By.CSS_SELECTOR, "a.btn.btn-primary")
            logger.info(f"Found {len(buttons)} primary buttons")
            
            # Check for other button selectors
            alt_buttons = self.driver.find_elements(By.CSS_SELECTOR, "a.btn")
            logger.info(f"Found {len(alt_buttons)} buttons with .btn class")
            
            # Check for any links
            all_links = self.driver.find_elements(By.TAG_NAME, "a")
            logger.info(f"Found {len(all_links)} total links")
            
            # Get visible text sample
            try:
                body_text = self.driver.find_element(By.TAG_NAME, "body").text
                first_500_chars = body_text[:500].replace('\n', ' ').strip()
                logger.info(f"First 500 chars of body text: {first_500_chars}")
            except:
                logger.warning("Could not get body text")
            
            logger.info("=== END DEBUG ===")
            
        except Exception as e:
            logger.error(f"Error in debug_page_content: {e}")
    
    def wait_for_page_load(self, timeout=20):
        """Wait for page to fully load"""
        try:
            # Wait for document ready state
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            logger.info("Page loaded (document ready)")
            
            # Additional wait for any AJAX content
            time.sleep(3)
            return True
            
        except TimeoutException:
            logger.warning("Page load timeout - continuing anyway")
            return False
        except Exception as e:
            logger.error(f"Error waiting for page load: {e}")
            return False
    
    def find_project_buttons(self):
        """Find project buttons using multiple strategies"""
        try:
            # Strategy 1: Original selector
            buttons = self.driver.find_elements(By.CSS_SELECTOR, "a.btn.btn-primary")
            if buttons:
                logger.info(f"Strategy 1: Found {len(buttons)} buttons with 'a.btn.btn-primary'")
                return buttons
            
            # Strategy 2: Alternative button selectors
            selectors = [
                "a.btn-primary",
                ".btn-primary",
                "a[href*='project']",
                "a[href*='detail']",
                "button.btn-primary",
                ".project-item a",
                ".project-card a",
                "a.btn"
            ]
            
            for i, selector in enumerate(selectors, 2):
                buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if buttons:
                    logger.info(f"Strategy {i}: Found {len(buttons)} buttons with '{selector}'")
                    return buttons
            
            # Strategy: Look for any clickable elements with project-related text
            all_links = self.driver.find_elements(By.TAG_NAME, "a")
            project_links = []
            for link in all_links:
                try:
                    link_text = link.text.strip().lower()
                    href = link.get_attribute('href') or ''
                    
                    if any(word in link_text for word in ['view', 'detail', 'more']) or \
                       any(word in href.lower() for word in ['project', 'detail']):
                        project_links.append(link)
                except:
                    continue
            
            if project_links:
                logger.info(f"Strategy (fallback): Found {len(project_links)} potential project links")
                return project_links[:self.max_projects]  # Limit to max_projects
            
            logger.error("No project buttons found with any strategy")
            return []
            
        except Exception as e:
            logger.error(f"Error finding project buttons: {e}")
            return []
    
    def get_label_strong_field(self, label_text, timeout=5):
        """
        Extract value from label-strong field structure
        Enhanced with better error handling and multiple strategies
        """
        try:
            time.sleep(0.5)
            
            # Strategy 1: Original approach with details-project divs
            blocks = self.driver.find_elements(By.CSS_SELECTOR, "div.details-project")
            logger.debug(f"Found {len(blocks)} detail blocks while searching for '{label_text}'")
            
            for block in blocks:
                try:
                    label = block.find_element(By.TAG_NAME, "label")
                    if label_text.strip().lower() in label.text.strip().lower():
                        
                        # Handle GST No PDF links
                        if "gst" in label_text.lower():
                            try:
                                link = block.find_element(By.CSS_SELECTOR, "a[href*='fileId']")
                                href = link.get_attribute("href")
                                if href and "fileId=" in href:
                                    file_id = href.split("fileId=")[-1]
                                    logger.debug(f"Found '{label_text}' as PDF document link: {file_id}")
                                    return f"PDF Document (ID: {file_id})"
                            except NoSuchElementException:
                                pass
                        
                        # Try strong tag
                        try:
                            strong = block.find_element(By.TAG_NAME, "strong")
                            value = strong.text.strip()
                            if value:
                                logger.debug(f"Found '{label_text}' in <strong>: {value}")
                                return value
                        except NoSuchElementException:
                            pass
                        
                        # Try getting text from entire block
                        block_text = block.text.strip()
                        label_text_clean = label.text.strip()
                        
                        if block_text.startswith(label_text_clean):
                            value = block_text[len(label_text_clean):].strip()
                            value = value.lstrip(': \n\t').strip()
                            if value:
                                logger.debug(f"Found '{label_text}' in block text: {value}")
                                return value
                        
                        return "N/A"
                        
                except NoSuchElementException:
                    continue
            
            # Strategy 2: Look for the field anywhere on the page
            try:
                # Try to find by partial text match
                xpath_selectors = [
                    f"//text()[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{label_text.lower()}')]/following::text()[1]",
                    f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{label_text.lower()}')]/following-sibling::*[1]",
                    f"//*[contains(text(), '{label_text}')]/following-sibling::*[1]"
                ]
                
                for xpath in xpath_selectors:
                    try:
                        elements = self.driver.find_elements(By.XPATH, xpath)
                        for element in elements:
                            text = element.text.strip() if hasattr(element, 'text') else str(element).strip()
                            if text and len(text) > 0:
                                logger.debug(f"Found '{label_text}' via XPath: {text}")
                                return text
                    except:
                        continue
                        
            except Exception as e:
                logger.debug(f"XPath strategy failed for '{label_text}': {e}")
            
            logger.warning(f"Field '{label_text}' not found")
            return "N/A"
            
        except Exception as e:
            logger.error(f"Error extracting field '{label_text}': {e}")
            return f"Error: {e}"
    
    def click_promoter_tab(self):
        """Enhanced promoter tab click with better detection"""
        try:
            logger.info("Attempting to click Promoter Details tab...")
            time.sleep(2)
            
            # Multiple strategies to find and click promoter tab
            strategies = [
                # XPath strategies
                ("xpath", "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'promoter')]"),
                ("xpath", "//a[contains(text(),'Promoter')]"),
                ("xpath", "//li//a[contains(text(),'Promoter')]"),
                ("xpath", "//*[@role='tab' and contains(text(),'Promoter')]"),
                
                # CSS strategies
                ("css", "a[href*='promoter']"),
                ("css", ".nav-link[href*='promoter']"),
                ("css", ".tab-link[href*='promoter']"),
                ("css", "[data-toggle='tab'][href*='promoter']"),
            ]
            
            tab_clicked = False
            
            for strategy_type, selector in strategies:
                try:
                    if strategy_type == "xpath":
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    logger.debug(f"Found {len(elements)} elements with {strategy_type} selector: {selector}")
                    
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            try:
                                logger.info(f"Attempting to click element with text: '{element.text.strip()}'")
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                                time.sleep(1)
                                
                                # Try regular click first
                                try:
                                    element.click()
                                except:
                                    # Fallback to JavaScript click
                                    self.driver.execute_script("arguments[0].click();", element)
                                
                                tab_clicked = True
                                logger.info("✅ Promoter tab clicked successfully")
                                break
                            except Exception as e:
                                logger.debug(f"Failed to click element: {e}")
                                continue
                    
                    if tab_clicked:
                        break
                        
                except Exception as e:
                    logger.debug(f"Strategy {strategy_type} with selector '{selector}' failed: {e}")
                    continue
            
            if not tab_clicked:
                logger.warning("Could not find promoter tab, trying to extract promoter info from current page")
                return True  # Continue anyway, might be on a single-page layout
            
            # Wait for content to load after clicking
            logger.info("Waiting for promoter content to load...")
            max_wait = 8
            for attempt in range(max_wait):
                time.sleep(1)
                
                # Test if promoter fields are now available
                test_fields = ["Company Name", "Promoter Name", "GST", "Address"]
                found_content = False
                
                for field in test_fields:
                    result = self.get_label_strong_field(field)
                    if result not in ["N/A", ""] and not result.startswith("Error:"):
                        logger.info(f"✅ Promoter content loaded - found {field}: {result[:30]}...")
                        found_content = True
                        break
                
                if found_content:
                    return True
                
                logger.debug(f"Attempt {attempt + 1}/{max_wait}: Waiting for promoter content...")
            
            logger.warning("Promoter tab clicked but content may not have loaded")
            return True
                
        except Exception as e:
            logger.error(f"Error in click_promoter_tab: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def scrape_project_details(self, project_index):
        """Enhanced project detail scraping with better error handling"""
        try:
            # Find project buttons
            buttons = self.find_project_buttons()
            
            if not buttons:
                logger.error("No project buttons found")
                return None
            
            if project_index >= len(buttons):
                logger.warning(f"Project index {project_index} exceeds available projects ({len(buttons)})")
                return None
            
            # Click on project
            logger.info(f"Scraping project {project_index + 1}/{min(len(buttons), self.max_projects)}")
            button = buttons[project_index]
            
            try:
                # Scroll to button and click
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                time.sleep(1)
                
                # Try regular click first
                try:
                    button.click()
                except:
                    # Fallback to JavaScript click
                    self.driver.execute_script("arguments[0].click();", button)
                
                logger.info("✅ Project button clicked")
                
            except Exception as e:
                logger.error(f"Failed to click project button: {e}")
                return None
            
            # Wait for detail page to load
            if not self.wait_for_page_load():
                logger.warning("Page load timeout, but continuing...")
            
            # Debug the loaded page
            self.debug_page_content(f"after clicking project {project_index + 1}")
            
            # Wait for detail content
            try:
                # Try to wait for detail content with multiple selectors
                detail_selectors = [
                    "div.details-project",
                    ".project-details",
                    ".detail-content",
                    "[class*='detail']",
                    ".container"
                ]
                
                content_loaded = False
                for selector in detail_selectors:
                    try:
                        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                        logger.info(f"Detail content loaded (selector: {selector})")
                        content_loaded = True
                        break
                    except TimeoutException:
                        continue
                
                if not content_loaded:
                    logger.warning("Could not detect detail content loading, continuing anyway...")
                
            except Exception as e:
                logger.warning(f"Error waiting for detail content: {e}")
            
            time.sleep(2)  # Additional wait
            
            # Extract basic project details
            logger.info("Extracting basic project details...")
            rera_no = self.get_label_strong_field("RERA Regd. No")
            project_name = self.get_label_strong_field("Project Name")
            project_type = self.get_label_strong_field("Project Type")
            project_status = self.get_label_strong_field("Project Status")
            
            logger.info(f"Basic details - RERA: {rera_no}, Name: {project_name}, Type: {project_type}, Status: {project_status}")
            
            # Extract promoter details
            logger.info("Extracting promoter details...")
            promoter_name = "N/A"
            promoter_address = "N/A"
            gst_no = "N/A"
            
            if self.click_promoter_tab():
                # Try multiple field variations
                promoter_fields = [
                    ("Promoter Name", ["Company Name", "Promoter Name", "Developer Name", "Builder Name"]),
                    ("Promoter Address", ["Registered Office Address", "Address", "Office Address", "Registered Address"]),
                    ("GST No", ["GST No", "GST", "GST Number", "GSTIN"])
                ]
                
                results = {"Promoter Name": "N/A", "Promoter Address": "N/A", "GST No": "N/A"}
                
                for result_key, field_variations in promoter_fields:
                    for field in field_variations:
                        value = self.get_label_strong_field(field)
                        if value not in ["N/A", ""] and not value.startswith("Error:"):
                            results[result_key] = value
                            logger.info(f"Found {result_key} via '{field}': {value[:50]}...")
                            break
                
                promoter_name = results["Promoter Name"]
                promoter_address = results["Promoter Address"]
                gst_no = results["GST No"]
            
            # Compile project data
            project_data = {
                "RERA Regd. No": rera_no,
                "Project Name": project_name,
                "Project Type": project_type,
                "Project Status": project_status,
                "Promoter Name": promoter_name,
                "Promoter Address": promoter_address,
                "GST No": gst_no,
                "Scraped At": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            logger.info(f"✅ Successfully scraped project: {project_name}")
            return project_data
            
        except Exception as e:
            logger.error(f"Error scraping project {project_index + 1}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    def navigate_back_to_list(self):
        """Enhanced navigation back to project list"""
        try:
            logger.info("Navigating back to project list...")
            
            # Try browser back button
            self.driver.back()
            
            # Wait for list to load
            if self.wait_for_page_load():
                # Verify we're back on the list page
                buttons = self.find_project_buttons()
                if buttons:
                    logger.info(f"✅ Successfully navigated back - found {len(buttons)} project buttons")
                    return True
            
            logger.warning("Back navigation may not have worked properly")
            return False
            
        except Exception as e:
            logger.error(f"Error navigating back to project list: {e}")
            return False
    
    def scrape_projects(self):
        """Enhanced main scraping method"""
        try:
            self.setup_driver()
            
            # Navigate to RERA project list
            logger.info("Navigating to RERA Odisha project list...")
            self.driver.get("https://rera.odisha.gov.in/projects/project-list")
            
            # Wait for page to load
            if not self.wait_for_page_load():
                logger.error("Failed to load main page")
                return
            
            # Debug initial page state
            self.debug_page_content("initial page load")
            
            # Find project buttons
            buttons = self.find_project_buttons()
            if not buttons:
                logger.error("No project buttons found on the page")
                return
            
            total_projects = len(buttons)
            projects_to_scrape = min(self.max_projects, total_projects)
            
            logger.info(f"Found {total_projects} projects. Scraping first {projects_to_scrape} projects...")
            
            # Scrape projects
            for i in range(projects_to_scrape):
                logger.info(f"\n{'='*60}")
                logger.info(f"SCRAPING PROJECT {i + 1}/{projects_to_scrape}")
                logger.info(f"{'='*60}")
                
                project_data = self.scrape_project_details(i)
                
                if project_data:
                    self.projects_data.append(project_data)
                    logger.info(f"✅ Project {i + 1} scraped successfully")
                else:
                    logger.warning(f"❌ Failed to scrape project {i + 1}")
                
                # Navigate back (except for last project)
                if i < projects_to_scrape - 1:
                    if not self.navigate_back_to_list():
                        logger.error("Failed to navigate back to project list. Stopping scraping.")
                        break
                    time.sleep(2)  # Extra wait between projects
            
            logger.info(f"\n🎉 Scraping completed! Successfully scraped {len(self.projects_data)}/{projects_to_scrape} projects.")
            
        except Exception as e:
            logger.error(f"Critical error during scraping: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                    logger.info("Browser closed")
                except:
                    pass
    
    def save_to_excel(self, filename=None):
        """Save scraped data to Excel file"""
        if not self.projects_data:
            logger.warning("No data to save")
            return
        
        if filename is None:
            filename = f"rera_projects_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        try:
            df = pd.DataFrame(self.projects_data)
            df.to_excel(filename, index=False, engine='openpyxl')
            logger.info(f"Data saved to {filename}")
            print(f"\n✅ Data successfully saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving to Excel: {e}")
    
    def display_results(self):
        """Display scraped results in console"""
        if not self.projects_data:
            print("No data to display")
            return
        
        print(f"\n{'='*80}")
        print(f"SCRAPED RERA PROJECT DATA ({len(self.projects_data)} projects)")
        print(f"{'='*80}")
        
        for i, project in enumerate(self.projects_data, 1):
            print(f"\n🏢 Project {i}")
            print("-" * 50)
            for key, value in project.items():
                if key != "Scraped At":
                    print(f"{key:.<25} {value}")
            print(f"Scraped At: {project.get('Scraped At', 'N/A')}")

def main():
    """Main execution function"""
    print("🚀 Starting Enhanced RERA Odisha Project Scraper...")
    print("📋 Scraping first 6 projects with enhanced error handling...")
    
    # Configuration
    MAX_PROJECTS = 6
    HEADLESS = False  # Set to True to run browser in background
    
    # Create and run scraper
    scraper = RERAProjectScraper(headless=HEADLESS, max_projects=MAX_PROJECTS)
    scraper.scrape_projects()
    
    # Display and save results
    if scraper.projects_data:
        scraper.display_results()
        scraper.save_to_excel()
        print(f"\n✅ Successfully scraped {len(scraper.projects_data)}/6 projects!")
        print("📊 Data saved to Excel file and displayed above.")
    else:
        print("\n❌ No projects were scraped. Check the log file for detailed error information.")
        print("💡 The enhanced version provides detailed debugging - check the log file for clues about what went wrong.")

if __name__ == "__main__":
    main()