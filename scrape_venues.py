import os
import time
import pandas as pd

def join_schedule_with_venues(schedule_df):
    """
    Joins the schedule DataFrame with venue information for each team.
    
    Parameters:
        schedule_df (pd.DataFrame): DataFrame containing the schedule data with a column 'Home Team'
        
    Returns:
        pd.DataFrame: Merged DataFrame containing schedule and venue details,
                      with the park name stored in the 'Venue' column.
    """
    # Dictionary mapping full team names to their stadium names.
    venues_dict = {
        'Arizona Diamondbacks': 'Chase Field',
        'Baltimore Orioles': 'Oriole Park at Camden Yards',
        'Boston Red Sox': 'Fenway Park',
        'Chicago White Sox': 'Guaranteed Rate Field',
        'Cincinnati Reds': 'Great American Ball Park',
        'Cleveland Guardians': 'Progressive Field',
        'Colorado Rockies': 'Coors Field',
        'Detroit Tigers': 'Comerica Park',
        'Houston Astros': 'Minute Maid Park',
        'Kansas City Royals': 'Kauffman Stadium',
        'Los Angeles Angels': 'Angel Stadium',
        'Los Angeles Dodgers': 'Dodger Stadium',
        'Miami Marlins': 'LoanDepot Park',
        'Milwaukee Brewers': 'American Family Field',
        'New York Mets': 'Citi Field',
        'New York Yankees': 'Yankee Stadium',
        'Athletics': 'Oakland Coliseum',
        'Philadelphia Phillies': 'Citizens Bank Park',
        'Pittsburgh Pirates': 'PNC Park',
        'San Diego Padres': 'Petco Park',
        'San Francisco Giants': 'Oracle Park',
        'Seattle Mariners': 'T-Mobile Park',
        'St. Louis Cardinals': 'Busch Stadium',
        'Texas Rangers': 'Globe Life Field',
        'Toronto Blue Jays': 'Rogers Centre',
        'Washington Nationals': 'Nationals Park',
        'Minnesota Twins': 'Target Field',
        'Chicago Cubs': 'Wrigley Field',
        'Tampa Bay Rays': 'Tropicana Field',
        'Atlanta Braves': 'Truist Park'
    }

    # Convert the dictionary to a DataFrame with proper column names.
    venues_df = pd.DataFrame(list(venues_dict.items()), columns=['Team Name', 'Venue'])
    
    # Merge the schedule DataFrame with the venues DataFrame.
    merged_df = pd.merge(schedule_df, venues_df, how='left', left_on='Home Team', right_on='Team Name')
    
    # Create a combined game name from Home Team and Away Team.
    merged_df["Name"] = merged_df["Home Team"] + " vs. " + merged_df["Away Team"]
    
    # Remove the redundant 'Team Name' column.
    merged_df.drop(columns=["Team Name"], inplace=True)
    
    return merged_df
