import os
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import logging
from dotenv import load_dotenv

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

def scrape_team_schedules(max_retries=5):
    print("Starting team schedules scraping.")

    # Define your team codes
    team_codes = [
        "dbacks", "braves", "orioles", "redsox", "cubs", "whitesox",
        "reds", "guardians", "rockies", "tigers", "astros", "royals",
        "angels", "dodgers", "marlins", "brewers", "twins", "mets",
        "yankees", "athletics", "phillies", "pirates", "padres", "giants",
        "mariners", "cardinals", "rays", "rangers", "bluejays", "nationals"
    ]

    driver = init_driver()
    game_data = []

    # Loop over each team code and scrape the schedule
    for team_code in team_codes:
        url = f"https://www.mlb.com/{team_code}/schedule/2025/fullseason"
        print(f"Processing team: {team_code} at URL: {url}")
        print(team_code)

        retry_count = 0
        while retry_count < max_retries:
            driver.get(url)
            time.sleep(4)  # Adjust sleep as needed for page load

            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")
            
            # Attempt to locate the parent container
            div_element = soup.find("div", class_="list-mode")
            if not div_element:
                print(f"Team {team_code}: No 'list-mode' div found.")
                retry_count += 1
                print(f"Retrying ({retry_count}/{max_retries})...")
                continue

            all_blocks = soup.find_all("div", class_="list-mode-table-wrapper")
            print(f"Team {team_code}: Found {len(all_blocks)} game blocks.")
            print(len(all_blocks))
            if len(all_blocks) < 162:
                print(f"Team {team_code}: Found {len(all_blocks)} games, expected 163. Retrying...")
                retry_count += 1
                print(f"Retrying ({retry_count}/{max_retries})...")
                continue

            # Process each game block
            for i, block in enumerate(all_blocks, start=1):
                matchup = block.get("data-tracking-matchup-with-date")
                if not matchup:
                    print(f"Team {team_code} Block {i}: No matchup attribute found, skipping.")
                    continue

                if " vs " not in matchup or "@" in matchup:
                    print(f"Team {team_code} Block {i}: Skipping due to format.")
                    continue

                teams_part = matchup.split(" on ")[0]
                teams = teams_part.split(" vs ")

                date_tag = block.find("div", class_="month-date")
                weekday_tag = block.find("div", class_="weekday")
                time_tag = block.find("div", class_="primary-time")

                game_date = date_tag.get_text(strip=True) if date_tag else None
                day_of_week = weekday_tag.get_text(strip=True) if weekday_tag else None
                game_time = time_tag.get_text(strip=True) if time_tag else None

                promo_text = block.get("data-tracking-featured-promotion", None)

                if len(teams) == 2:
                    home_team = teams[0].strip()
                    away_team = teams[1].strip()
                    print(f"Team {team_code} Block {i}: Home: {home_team}, Away: {away_team}")
                    game_data.append({
                        "Home Team": home_team,
                        "Away Team": away_team,
                        "Game Date": game_date,
                        "Day": day_of_week,
                        "Game Time": game_time,
                        "Promo": promo_text,
                    })
                else:
                    print(f"Team {team_code} Block {i}: Unexpected team format: {matchup}")

            # If we've successfully scraped 81 games, break out of the retry loop
            print(f"Successfully scraped 162 games for team {team_code}.")
            break

        if retry_count == max_retries:
            print(f"Failed to scrape 181 games for team {team_code} after {max_retries} attempts.")


    # Create a DataFrame from the collected data
    df = pd.DataFrame(game_data)

    # Map abbreviated team codes to full names (adjust mapping as needed)
    team_mapping = {
        'AZ': 'Arizona Diamondbacks',
        'BAL': 'Baltimore Orioles',
        'BOS': 'Boston Red Sox',
        'CWS': 'Chicago White Sox',
        'CIN': 'Cincinnati Reds',
        'CLE': 'Cleveland Guardians',
        'COL': 'Colorado Rockies',
        'DET': 'Detroit Tigers',
        'HOU': 'Houston Astros',
        'KC': 'Kansas City Royals',
        'LAA': 'Los Angeles Angels',
        'LAD': 'Los Angeles Dodgers',
        'MIA': 'Miami Marlins',
        'MIL': 'Milwaukee Brewers',
        'NYM': 'New York Mets',
        'NYY': 'New York Yankees',
        'ATH': 'Athletics',
        'PHI': 'Philadelphia Phillies',
        'PIT': 'Pittsburgh Pirates',
        'SD': 'San Diego Padres',
        'SF': 'San Francisco Giants',
        'SEA': 'Seattle Mariners',
        'STL': 'St. Louis Cardinals',
        'TEX': 'Texas Rangers',
        'TOR': 'Toronto Blue Jays',
        'WSH': 'Washington Nationals',
        'MIN': 'Minnesota Twins',
        'CHC': 'Chicago Cubs',
        'TB': 'Tampa Bay Rays',
        'ATL': 'Atlanta Braves'
    }

    df['Home Team'] = df['Home Team'].map(team_mapping)
    df['Away Team'] = df['Away Team'].map(team_mapping)
    df["Name"] = df["Home Team"] + " vs. " + df["Away Team"]

    print("Completed team schedules scraping.")
    driver.quit()
    return df
