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


WNBA_TEAM_MAP = {
    "Atlanta": "Atlanta Dream", "Chicago": "Chicago Sky", "Connecticut": "Connecticut Sun",
    "Dallas": "Dallas Wings", "Indiana": "Indiana Fever", "Las Vegas": "Las Vegas Aces",
    "Los Angeles": "Los Angeles Sparks", "Minnesota": "Minnesota Lynx", "New York": "New York Liberty",
    "Phoenix": "Phoenix Mercury", "Seattle": "Seattle Storm", "Washington": "Washington Mystics",
    "Golden State": "Golden State Valkyries"
}

TEAM_TZ_MAP = {
    "Atlanta Dream": "America/New_York", "Chicago Sky": "America/Chicago",
    "Connecticut Sun": "America/New_York", "Dallas Wings": "America/Chicago",
    "Indiana Fever": "America/Indiana/Indianapolis", "Las Vegas Aces": "America/Los_Angeles",
    "Los Angeles Sparks": "America/Los_Angeles", "Minnesota Lynx": "America/Chicago",
    "New York Liberty": "America/New_York", "Phoenix Mercury": "America/Phoenix",
    "Seattle Storm": "America/Los_Angeles", "Washington Mystics": "America/New_York",
    "Golden State Valkyries": "America/Los_Angeles"
}

ARENAS = {
    "Atlanta Dream": "Gateway Center Arena", "Chicago Sky": "Wintrust Arena",
    "Connecticut Sun": "Mohegan Sun Arena", "Dallas Wings": "College Park Center",
    "Indiana Fever": "Gainbridge Fieldhouse", "Las Vegas Aces": "Michelob Ultra Arena",
    "Los Angeles Sparks": "Crypto.com Arena", "Minnesota Lynx": "Target Center",
    "New York Liberty": "Barclays Center", "Phoenix Mercury": "Footprint Center",
    "Seattle Storm": "Climate Pledge Arena", "Washington Mystics": "Entertainment and Sports Arena",
    "Golden State Valkyries": "Chase Center"
}


# --- Web Driver Setup ---
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


# --- Scraping Function ---
def scrape_wnba_schedule(driver, start_date, end_date):
    delta = timedelta(days=7)
    current = start_date
    results = []

    while current <= end_date:
        date_str = current.strftime("%Y%m%d")
        url = f"https://www.espn.com/wnba/schedule/_/date/{date_str}"
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


# --- Enrichment Logic ---
def enrich_game_data(games):
    local_tz = get_localzone()

    for g in games:
        g["home_team"] = WNBA_TEAM_MAP.get(g["home_team"], g["home_team"])
        g["away_team"] = WNBA_TEAM_MAP.get(g["away_team"], g["away_team"])
        g["Venue"] = ARENAS.get(g["home_team"], "")
        g["Name"] = f"{g['home_team']} vs. {g['away_team']}"
        g["Description"] = "WNBA: xxx tickets available for the game."

        if g["time"] == "TBD":
            g["Start Date"] = pd.NaT
        else:
            try:
                dt_local = datetime.strptime(f"{g['date']} {g['time']}", "%A, %B %d, %Y %I:%M %p")
                dt_local = dt_local.replace(tzinfo=local_tz)
                home_tz = pytz.timezone(TEAM_TZ_MAP.get(g['home_team'], "UTC"))
                g["Start Date"] = dt_local.astimezone(home_tz).replace(tzinfo=None)
            except:
                g["Start Date"] = pd.NaT
    return games


# --- Finalize DataFrame ---
def finalize_dataframe(games):
    df = pd.DataFrame(games)
    df["End Date"] = df["Start Date"] + pd.Timedelta(hours=3)
    df["Display Start Date"] = pd.Timestamp.today().date()
    df["Display End Date"] = df["Start Date"].apply(lambda d: d if pd.isna(d) or d.weekday() < 5 else d - pd.DateOffset(days=d.weekday() - 4)).dt.date

    new_cols = {
        "Multiple Dates or Times": "No", "Event Category": "Sports", "Age Range": "All", "Owner": "Coates, Anita",
        "Fulfillment Method": "Manual", "Fulfillment Type": "", "Fulfillment Date": "",
        "Enforce Quantity Limit": "No", "Maximum Tickets": "", "Split Groups": "", "Volunteer Event": "",
        "Volunteers Assigned": "", "Ticket Delivery Method": "", "Ticket Instructions": "",
        "Ticket Instruction Details": "", "Display On Web": "No", "Display Delivery Method": "No",
        "Allow Date Selection": "No", "Allow Time Selection": "No", "More Information Title": "",
        "More Information Url": "", "Web URL": "", "Address Line 1": "", "Address Line 2": "", "Address Line 3": "",
        "City": "", "State or Province": "", "Postal Code": "", "County": "", "Market": "", "Metro Area": "",
        "Country": "", "Contact Name": "", "Contact Email": "", "Contact Phone": "", "TFK Area": "",
        "TFK Market": "", "TFK Region": "", "Total Requested": "", "Total Distributed": "",
        "Total Donated": "", "Total Remaining": ""
    }
    df = df.assign(**new_cols)

    col_order = [
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
    return df[[col for col in col_order if col in df.columns]]


# --- Entry Point ---
def main():
    driver = init_driver()
    try:
        print("Scraping WNBA schedule...")
        raw_games = scrape_wnba_schedule(driver, datetime(2025, 5, 15), datetime(2025, 7, 31))
        enriched_games = enrich_game_data(raw_games)
        df = finalize_dataframe(enriched_games)

        by_team_path = "/app/static/wnba_final_draft_by_team.xlsx"
        with pd.ExcelWriter(by_team_path, engine="openpyxl") as writer:
            teams = df["Name"].str.extract(r'^(.*?) vs')[0].dropna().unique()
            for team in teams:
                team_df = df[df["Name"].str.startswith(team)]
                safe_name = team[:31]
                team_df.to_excel(writer, sheet_name=safe_name, index=False)
        print(f"✅ Multi-sheet WNBA schedule saved to: {by_team_path}")

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
