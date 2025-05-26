# RERA Odisha Project Scraper

A robust web scraper for extracting project information from the RERA (Real Estate Regulatory Authority) Odisha website. This tool automatically collects project details including basic information and promoter details from registered real estate projects.

## 🚀 Features

- **Automated Data Extraction**: Scrapes project details from RERA Odisha website
- **Comprehensive Information**: Extracts both basic project info and promoter details
- **Excel Export**: Saves data to Excel format for easy analysis
- **Robust Error Handling**: Multiple fallback strategies for reliable scraping
- **Detailed Logging**: Comprehensive logs for debugging and monitoring
- **Flexible Configuration**: Customizable number of projects and browser settings

## 📋 Data Fields Extracted

### Basic Project Information
- RERA Registration Number
- Project Name
- Project Type
- Project Status

### Promoter Details
- Promoter/Company Name
- Registered Office Address
- GST Number
- Additional company information

## 🛠️ Prerequisites

### Required Software
- **Python 3.7+**
- **Google Chrome Browser**
- **ChromeDriver** (compatible with your Chrome version)

### Python Dependencies
```bash
pip install selenium pandas openpyxl
```

### ChromeDriver Setup
1. Check your Chrome version: `chrome://version/`
2. Download matching ChromeDriver from [ChromeDriver Downloads](https://chromedriver.chromium.org/)
3. Add ChromeDriver to your system PATH or place in project directory

## 📦 Installation

1. **Clone or download the project files**
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Ensure ChromeDriver is accessible**

### Requirements.txt
```txt
selenium>=4.0.0
pandas>=1.3.0
openpyxl>=3.0.0
```

## 🚀 Usage

### Basic Usage
```bash
python main.py
```

### Configuration Options

You can modify the configuration in the `main()` function:

```python
# Configuration
MAX_PROJECTS = 6        # Number of projects to scrape
HEADLESS = False        # Set to True for background execution
```

### Advanced Usage

```python
from main import RERAProjectScraper

# Initialize scraper
scraper = RERAProjectScraper(
    headless=True,      # Run in background
    max_projects=10     # Scrape 10 projects
)

# Run scraping
scraper.scrape_projects()

# Save results
scraper.save_to_excel("custom_filename.xlsx")
scraper.display_results()
```

## 📊 Output

### Console Output
- Real-time scraping progress
- Project details display
- Success/failure notifications
- Detailed error information

### Excel File
- Automatically generated with timestamp
- Format: `rera_projects_YYYYMMDD_HHMMSS.xlsx`
- Contains all scraped data in tabular format

### Log File
- Detailed execution logs
- Format: `rera_scraper_YYYYMMDD_HHMMSS.log`
- Useful for debugging and monitoring

## 🔧 Configuration Options

### Browser Settings
```python
# Headless mode (background execution)
scraper = RERAProjectScraper(headless=True)

# Custom Chrome options
options = Options()
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-notifications")
```

### Scraping Parameters
```python
# Maximum projects to scrape
MAX_PROJECTS = 6

# Timeout settings (in RERAProjectScraper class)
self.wait = WebDriverWait(self.driver, 20)  # 20 seconds timeout
```

## 🐛 Troubleshooting

### Common Issues

#### 1. ChromeDriver Not Found
```
Error: 'chromedriver' executable needs to be in PATH
```
**Solution**: Download ChromeDriver and add to PATH or project directory

#### 2. Chrome Version Mismatch
```
Error: This version of ChromeDriver only supports Chrome version X
```
**Solution**: Download ChromeDriver version matching your Chrome browser

#### 3. No Projects Found
```
No project buttons found on the page
```
**Solution**: 
- Check internet connection
- Verify website is accessible
- Check log file for detailed error information

#### 4. Timeout Errors
```
TimeoutException: Message:
```
**Solution**: 
- Increase timeout values in code
- Check internet connection speed
- Run with `headless=False` to see browser behavior

### Debugging Steps

1. **Check the log file** for detailed error information
2. **Run with headless=False** to see browser actions
3. **Verify website accessibility** manually
4. **Check ChromeDriver compatibility**

## 📁 Project Structure

```
rera-scraper/
│
├── main.py                 # Main scraper script
├── README.md              # This file
├── requirements.txt       # Python dependencies
│
├── logs/                  # Generated log files
│   └── rera_scraper_*.log
│
└── output/               # Generated Excel files
    └── rera_projects_*.xlsx
```

## 🔍 How It Works

### Scraping Process
1. **Initialize Chrome browser** with optimized settings
2. **Navigate to RERA project list** page
3. **Detect project buttons** using multiple strategies
4. **For each project**:
   - Click project link
   - Extract basic project information
   - Navigate to promoter details tab
   - Extract promoter information
   - Navigate back to project list
5. **Save data** to Excel file
6. **Generate logs** for monitoring

### Robust Detection Strategies
- **Multiple CSS selectors** for finding elements
- **XPath fallback methods** for complex layouts
- **JavaScript click methods** when standard clicks fail
- **Content verification** to ensure data quality

## ⚡ Performance Tips

### Optimize Speed
- Use `headless=True` for faster execution
- Reduce `max_projects` for testing
- Close other browser instances

### Reliability
- Monitor log files for issues
- Run during off-peak hours
- Use stable internet connection

## 🔒 Best Practices

### Responsible Scraping
- **Respect website terms of service**
- **Don't overload the server** - built-in delays included
- **Use for legitimate research purposes only**

### Data Handling
- **Verify extracted data** before using
- **Backup important results**
- **Handle sensitive information appropriately**

## 📝 Logging

### Log Levels
- **INFO**: General progress information
- **DEBUG**: Detailed operation steps
- **WARNING**: Non-critical issues
- **ERROR**: Failures and exceptions

### Log Contents
- Timestamp for each operation
- Success/failure status
- Detailed error messages
- Page state information

## 🤝 Contributing

To improve this scraper:

1. **Test with different configurations**
2. **Report issues** with detailed logs
3. **Suggest enhancements** for better reliability
4. **Share successful configurations**

## ⚠️ Disclaimer

This tool is for educational and research purposes. Users are responsible for:
- Complying with website terms of service
- Respecting rate limits and server resources
- Using data ethically and legally
- Following applicable data protection regulations

## 📞 Support

For issues or questions:
1. Check the **troubleshooting section** above
2. Review **log files** for detailed error information
3. Verify all **prerequisites** are met
4. Test with **reduced project count** first

## 🔄 Version History

### v2.0 (Enhanced Version)
- Multiple element detection strategies
- Improved error handling and logging
- Better page load detection
- Enhanced promoter tab navigation
- Robust click mechanisms
- Detailed debugging information

### v1.0 (Original Version)
- Basic project information extraction
- Simple promoter details scraping
- Excel export functionality
- Basic error handling
