import os
import time
import pandas as pd
from datetime import datetime, timedelta
from dateutil.parser import parse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from tzlocal import get_localzone
import pytz
from save_sep_files import generate_team_sheets_from_schedule
# Constants


NBA_TEAM_MAP = {
    "Atlanta": "Atlanta Hawks", "Boston": "Boston Celtics", "Brooklyn": "Brooklyn Nets",
    "Charlotte": "Charlotte Hornets", "Chicago": "Chicago Bulls", "Cleveland": "Cleveland Cavaliers",
    "Dallas": "Dallas Mavericks", "Denver": "Denver Nuggets", "Detroit": "Detroit Pistons",
    "Golden State": "Golden State Warriors", "Houston": "Houston Rockets", "Indiana": "Indiana Pacers",
    "LA Clippers": "Los Angeles Clippers", "L.A. Lakers": "Los Angeles Lakers", "Memphis": "Memphis Grizzlies",
    "Miami": "Miami Heat", "Milwaukee": "Milwaukee Bucks", "Minnesota": "Minnesota Timberwolves",
    "New Orleans": "New Orleans Pelicans", "New York": "New York Knicks", "Oklahoma City": "Oklahoma City Thunder",
    "Orlando": "Orlando Magic", "Philadelphia": "Philadelphia 76ers", "Phoenix": "Phoenix Suns",
    "Portland": "Portland Trail Blazers", "Sacramento": "Sacramento Kings", "San Antonio": "San Antonio Spurs",
    "Toronto": "Toronto Raptors", "Utah": "Utah Jazz", "Washington": "Washington Wizards"
}

NBA_TIMEZONE_MAP = {
    "Atlanta Hawks": "America/New_York", "Boston Celtics": "America/New_York", "Brooklyn Nets": "America/New_York",
    "Charlotte Hornets": "America/New_York", "Chicago Bulls": "America/Chicago", "Cleveland Cavaliers": "America/New_York",
    "Dallas Mavericks": "America/Chicago", "Denver Nuggets": "America/Denver", "Detroit Pistons": "America/Detroit",
    "Golden State Warriors": "America/Los_Angeles", "Houston Rockets": "America/Chicago", "Indiana Pacers": "America/Indiana/Indianapolis",
    "Los Angeles Clippers": "America/Los_Angeles", "Los Angeles Lakers": "America/Los_Angeles", "Memphis Grizzlies": "America/Chicago",
    "Miami Heat": "America/New_York", "Milwaukee Bucks": "America/Chicago", "Minnesota Timberwolves": "America/Chicago",
    "New Orleans Pelicans": "America/Chicago", "New York Knicks": "America/New_York", "Oklahoma City Thunder": "America/Chicago",
    "Orlando Magic": "America/New_York", "Philadelphia 76ers": "America/New_York", "Phoenix Suns": "America/Phoenix",
    "Portland Trail Blazers": "America/Los_Angeles", "Sacramento Kings": "America/Los_Angeles", "San Antonio Spurs": "America/Chicago",
    "Toronto Raptors": "America/Toronto", "Utah Jazz": "America/Denver", "Washington Wizards": "America/New_York"
}

NBA_ARENAS = {
    "Atlanta Hawks": "State Farm Arena", "Boston Celtics": "TD Garden", "Brooklyn Nets": "Barclays Center",
    "Charlotte Hornets": "Spectrum Center", "Chicago Bulls": "United Center", "Cleveland Cavaliers": "Rocket Mortgage FieldHouse",
    "Dallas Mavericks": "American Airlines Center", "Denver Nuggets": "Ball Arena", "Detroit Pistons": "Little Caesars Arena",
    "Golden State Warriors": "Chase Center", "Houston Rockets": "Toyota Center", "Indiana Pacers": "Gainbridge Fieldhouse",
    "Los Angeles Clippers": "Crypto.com Arena", "Los Angeles Lakers": "Crypto.com Arena", "Memphis Grizzlies": "FedExForum",
    "Miami Heat": "Kaseya Center", "Milwaukee Bucks": "Fiserv Forum", "Minnesota Timberwolves": "Target Center",
    "New Orleans Pelicans": "Smoothie King Center", "New York Knicks": "Madison Square Garden", "Oklahoma City Thunder": "Paycom Center",
    "Orlando Magic": "Amway Center", "Philadelphia 76ers": "Wells Fargo Center", "Phoenix Suns": "Footprint Center",
    "Portland Trail Blazers": "Moda Center", "Sacramento Kings": "Golden 1 Center", "San Antonio Spurs": "Frost Bank Center",
    "Toronto Raptors": "Scotiabank Arena", "Utah Jazz": "Delta Center", "Washington Wizards": "Capital One Arena"
}



CHROME_BINARY = "/usr/bin/chromium-browser"
CHROMEDRIVER_PATH = "/usr/bin/chromedriver"
SELENIUM_REMOTE_URL = "http://localhost:4444/wd/hub"

def init_driver(mode=None):
    """
    Initialize Selenium Chrome WebDriver based on environment.

    mode: 'docker', 'local', or None for auto-detect.
    """

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Auto-detect if no mode is specified
    if mode is None:
        in_docker = os.path.exists("/.dockerenv") or os.getenv("IN_DOCKER") == "1"
        mode = "docker" if in_docker else "local"

    if mode == "docker":
        print("🔧 Using remote Selenium driver (Docker mode)")
        return webdriver.Remote(
            command_executor=SELENIUM_REMOTE_URL,
            options=options
        )
    elif mode == "local":
        print("🔧 Using local ChromeDriver (Local mode)")
        options.binary_location = CHROME_BINARY
        return webdriver.Chrome(service=Service(CHROMEDRIVER_PATH), options=options)
    else:
        raise ValueError(f"Unknown mode '{mode}': must be 'docker', 'local', or None")


def scrape_nba_schedule(driver, start_date, end_date):
    delta = timedelta(days=7)
    current = start_date
    results = []

    while current <= end_date:
        date_str = current.strftime("%Y%m%d")
        url = f"https://www.espn.com/nba/schedule/_/date/{date_str}"
        driver.get(url)
        time.sleep(1)
        try:
            titles = driver.find_elements(By.CLASS_NAME, "Table__Title")
            tables = driver.find_elements(By.CLASS_NAME, "Table__TBODY")
            for title, table in zip(titles, tables):
                for row in table.find_elements(By.TAG_NAME, "tr"):
                    cols = row.find_elements(By.TAG_NAME, "td")
                    if len(cols) >= 3:
                        results.append({
                            "date": title.text.strip(),
                            "home_team": cols[1].text.replace("@", "").strip(),
                            "away_team": cols[0].text.strip(),
                            "time": cols[2].text.strip()
                        })
        except Exception as e:
            print(f"Error on {date_str}: {e}")
        current += delta

    return results


def enrich_nba_data(games):
    local_tz = get_localzone()
    for g in games:
        g["home_team"] = NBA_TEAM_MAP.get(g["home_team"], g["home_team"])
        g["away_team"] = NBA_TEAM_MAP.get(g["away_team"], g["away_team"])
        g["Venue"] = NBA_ARENAS.get(g["home_team"], "")
        g["Name"] = f"{g['home_team']} vs. {g['away_team']}"
        g["Description"] = "NBA: xxx tickets available for the game."

        if g["time"] == "TBD":
            g["Start Date"] = pd.NaT
        else:
            try:
                dt_local = datetime.strptime(f"{g['date']} {g['time']}", "%A, %B %d, %Y %I:%M %p").replace(tzinfo=local_tz)
                home_tz = pytz.timezone(NBA_TIMEZONE_MAP.get(g['home_team'], "UTC"))
                g["Start Date"] = dt_local.astimezone(home_tz).replace(tzinfo=None)
            except:
                g["Start Date"] = pd.NaT
    return games


def finalize_dataframe(games):
    df = pd.DataFrame(games)
    df["End Date"] = df["Start Date"] + pd.Timedelta(hours=3)
    df["Display Start Date"] = pd.Timestamp.today().normalize()
    df["Display End Date"] = df["Start Date"].apply(
        lambda d: d if pd.isna(d) or d.weekday() < 5 else d - pd.DateOffset(days=d.weekday() - 4)
    ).dt.date

    static_cols = {
        "Multiple Dates or Times": "No", "Event Category": "Sports", "Age Range": "All",
        "Owner": "Coates, Anita", "Fulfillment Method": "Manual", "Fulfillment Type": "",
        "Fulfillment Date": "", "Enforce Quantity Limit": "No", "Maximum Tickets": "", "Split Groups": "",
        "Volunteer Event": "", "Volunteers Assigned": "", "Ticket Delivery Method": "", "Ticket Instructions": "",
        "Ticket Instruction Details": "", "Display On Web": "No", "Display Delivery Method": "No",
        "Allow Date Selection": "No", "Allow Time Selection": "No", "More Information Title": "",
        "More Information Url": "", "Web URL": "", "Address Line 1": "", "Address Line 2": "", "Address Line 3": "",
        "City": "", "State or Province": "", "Postal Code": "", "County": "", "Market": "", "Metro Area": "",
        "Country": "", "Contact Name": "", "Contact Email": "", "Contact Phone": "", "TFK Area": "",
        "TFK Market": "", "TFK Region": "", "Total Requested": "", "Total Distributed": "",
        "Total Donated": "", "Total Remaining": ""
    }

    df = df.assign(**static_cols)

    final_cols = [
        'Name', 'Description', 'Start Date', 'End Date', 'Multiple Dates or Times', 'Event Category', 'Age Range',
        'Owner', 'Fulfillment Method', 'Fulfillment Type', 'Fulfillment Date', 'Enforce Quantity Limit',
        'Maximum Tickets', 'Split Groups', 'Volunteer Event', 'Volunteers Assigned', 'Ticket Delivery Method',
        'Ticket Instructions', 'Ticket Instruction Details', 'Display On Web', 'Display Delivery Method',
        'Allow Date Selection', 'Allow Time Selection', 'Display Start Date', 'Display End Date',
        'More Information Title', 'More Information Url', 'Web URL', 'Venue', 'Address Line 1', 'Address Line 2',
        'Address Line 3', 'City', 'State or Province', 'Postal Code', 'County', 'Market', 'Metro Area', 'Country',
        'Contact Name', 'Contact Email', 'Contact Phone', 'TFK Area', 'TFK Market', 'TFK Region',
        'Total Requested', 'Total Distributed', 'Total Donated', 'Total Remaining'
    ]
    return df[[col for col in final_cols if col in df.columns]]


def main():
    driver = init_driver()
    try:
        print("Scraping NBA schedule...")
        raw = scrape_nba_schedule(driver, datetime(2025, 5, 15), datetime(2025, 5, 15))
        print("Enriching NBA schedule...")
        enriched = enrich_nba_data(raw)
        print("Finalizing NBA schedule...")
        df = finalize_dataframe(enriched)

        by_team_path = "/app/static/nba_final_draft_by_team.xlsx"
        with pd.ExcelWriter(by_team_path, engine="openpyxl") as writer:
            teams = df["Name"].str.extract(r'^(.*?) vs')[0].dropna().unique()
            for team in teams:
                team_df = df[df["Name"].str.startswith(team)]
                safe_name = team[:31]
                team_df.to_excel(writer, sheet_name=safe_name, index=False)
        print(f"✅ Multi-sheet NBA schedule saved to: {by_team_path}")

        # Step 2: Save separate Dynamics-style Excel file for each team
        template_path = "/app/data/dynamics_submission.xlsx"
        output_dir = "/app/static/dynamics_team_exports"
        generate_team_sheets_from_schedule(
            xlsx_path=by_team_path,
            template_path=template_path,
            output_dir=output_dir
        )
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
