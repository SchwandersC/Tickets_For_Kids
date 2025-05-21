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
CHROME_BINARY = "/usr/bin/chromium-browser"
CHROMEDRIVER_PATH = "/usr/bin/chromedriver"

# --- TEAM INFO ---
NHL_TEAM_MAP = {
    "Anaheim": "Anaheim Ducks", "Arizona": "Arizona Coyotes", "Boston": "Boston Bruins",
    "Buffalo": "Buffalo Sabres", "Calgary": "Calgary Flames", "Carolina": "Carolina Hurricanes",
    "Chicago": "Chicago Blackhawks", "Colorado": "Colorado Avalanche", "Columbus": "Columbus Blue Jackets",
    "Dallas": "Dallas Stars", "Detroit": "Detroit Red Wings", "Edmonton": "Edmonton Oilers",
    "Florida": "Florida Panthers", "Los Angeles": "Los Angeles Kings", "Minnesota": "Minnesota Wild",
    "Montreal": "Montreal Canadiens", "Nashville": "Nashville Predators", "New Jersey": "New Jersey Devils",
    "NY Islanders": "New York Islanders", "NY Rangers": "New York Rangers", "Ottawa": "Ottawa Senators",
    "Philadelphia": "Philadelphia Flyers", "Pittsburgh": "Pittsburgh Penguins", "San Jose": "San Jose Sharks",
    "Seattle": "Seattle Kraken", "St. Louis": "St. Louis Blues", "Tampa Bay": "Tampa Bay Lightning",
    "Toronto": "Toronto Maple Leafs", "Vancouver": "Vancouver Canucks", "Vegas": "Vegas Golden Knights",
    "Washington": "Washington Capitals", "Winnipeg": "Winnipeg Jets"
}

NHL_TIMEZONE_MAP = {
    "Anaheim Ducks": "America/Los_Angeles", "Arizona Coyotes": "America/Phoenix", "Boston Bruins": "America/New_York",
    "Buffalo Sabres": "America/New_York", "Calgary Flames": "America/Edmonton", "Carolina Hurricanes": "America/New_York",
    "Chicago Blackhawks": "America/Chicago", "Colorado Avalanche": "America/Denver", "Columbus Blue Jackets": "America/New_York",
    "Dallas Stars": "America/Chicago", "Detroit Red Wings": "America/Detroit", "Edmonton Oilers": "America/Edmonton",
    "Florida Panthers": "America/New_York", "Los Angeles Kings": "America/Los_Angeles", "Minnesota Wild": "America/Chicago",
    "Montreal Canadiens": "America/Toronto", "Nashville Predators": "America/Chicago", "New Jersey Devils": "America/New_York",
    "New York Islanders": "America/New_York", "New York Rangers": "America/New_York", "Ottawa Senators": "America/Toronto",
    "Philadelphia Flyers": "America/New_York", "Pittsburgh Penguins": "America/New_York", "San Jose Sharks": "America/Los_Angeles",
    "Seattle Kraken": "America/Los_Angeles", "St. Louis Blues": "America/Chicago", "Tampa Bay Lightning": "America/New_York",
    "Toronto Maple Leafs": "America/Toronto", "Vancouver Canucks": "America/Vancouver", "Vegas Golden Knights": "America/Los_Angeles",
    "Washington Capitals": "America/New_York", "Winnipeg Jets": "America/Winnipeg"
}

NHL_ARENAS = {
    "Anaheim Ducks": "Honda Center", "Arizona Coyotes": "Mullett Arena", "Boston Bruins": "TD Garden",
    "Buffalo Sabres": "KeyBank Center", "Calgary Flames": "Scotiabank Saddledome", "Carolina Hurricanes": "PNC Arena",
    "Chicago Blackhawks": "United Center", "Colorado Avalanche": "Ball Arena", "Columbus Blue Jackets": "Nationwide Arena",
    "Dallas Stars": "American Airlines Center", "Detroit Red Wings": "Little Caesars Arena", "Edmonton Oilers": "Rogers Place",
    "Florida Panthers": "Amerant Bank Arena", "Los Angeles Kings": "Crypto.com Arena", "Minnesota Wild": "Xcel Energy Center",
    "Montreal Canadiens": "Bell Centre", "Nashville Predators": "Bridgestone Arena", "New Jersey Devils": "Prudential Center",
    "New York Islanders": "UBS Arena", "New York Rangers": "Madison Square Garden", "Ottawa Senators": "Canadian Tire Centre",
    "Philadelphia Flyers": "Wells Fargo Center", "Pittsburgh Penguins": "PPG Paints Arena", "San Jose Sharks": "SAP Center",
    "Seattle Kraken": "Climate Pledge Arena", "St. Louis Blues": "Enterprise Center", "Tampa Bay Lightning": "Amalie Arena",
    "Toronto Maple Leafs": "Scotiabank Arena", "Vancouver Canucks": "Rogers Arena", "Vegas Golden Knights": "T-Mobile Arena",
    "Washington Capitals": "Capital One Arena", "Winnipeg Jets": "Canada Life Centre"
}


# --- Setup ---
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



def scrape_nhl_schedule(driver, start_date, end_date):
    delta = timedelta(days=7)
    current = start_date
    results = []

    while current <= end_date:
        date_str = current.strftime("%Y%m%d")
        url = f"https://www.espn.com/nhl/schedule/_/date/{date_str}"
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


def enrich_nhl_data(games):
    local_tz = get_localzone()
    for g in games:
        g["home_team"] = NHL_TEAM_MAP.get(g["home_team"], g["home_team"])
        g["away_team"] = NHL_TEAM_MAP.get(g["away_team"], g["away_team"])
        g["Venue"] = NHL_ARENAS.get(g["home_team"], "")
        g["Name"] = f"{g['home_team']} vs. {g['away_team']}"
        g["Description"] = "NHL: xxx tickets available for the game."

        if g["time"] == "TBD":
            g["Start Date"] = pd.NaT
        else:
            try:
                dt_local = datetime.strptime(f"{g['date']} {g['time']}", "%A, %B %d, %Y %I:%M %p").replace(tzinfo=local_tz)
                home_tz = pytz.timezone(NHL_TIMEZONE_MAP.get(g['home_team'], "UTC"))
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


# --- Run It ---
def main():
    driver = init_driver()
    try:
        print("Scraping NHL schedule...")
        raw = scrape_nhl_schedule(driver, datetime(2025, 5, 15), datetime(2025, 5, 15))
        enriched = enrich_nhl_data(raw)
        df = finalize_dataframe(enriched)
        
        by_team_path = "/app/static/nhl_final_draft_by_team.xlsx"
        with pd.ExcelWriter(by_team_path, engine="openpyxl") as writer:
            teams = df["Name"].str.extract(r'^(.*?) vs')[0].dropna().unique()
            for team in teams:
                team_df = df[df["Name"].str.startswith(team)]
                safe_name = team[:31]
                team_df.to_excel(writer, sheet_name=safe_name, index=False)
        print(f"✅ Multi-sheet NHL schedule saved to: {by_team_path}")

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
