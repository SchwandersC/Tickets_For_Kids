import pandas as pd

def finalize_game_info_df(game_info: pd.DataFrame) -> pd.DataFrame:
    """
    Finalizes the game info DataFrame by adding new columns, formatting date/time fields,
    and calculating additional values.

    Parameters:
        game_info (pd.DataFrame): Input DataFrame with game info (including 'Game Date' and 'Game Time').

    Returns:
        pd.DataFrame: Finalized DataFrame with all additional columns and formatted values.
    """
    print("Starting finalization of game info DataFrame.")
    
    # Define new columns and their default values
    new_columns = {
        "Multiple Dates or Times": "No", "Event Category": "Sports", "Age Range": "All", 
        "Owner": "Coates, Anita", "Fulfillment Method": "Manual", "Fulfillment Type": "",
        "Fulfillment Date": "", "Enforce Quantity Limit": "No", "Maximum Tickets": "", 
        "Split Groups": "", "Volunteer Event": "", "Volunteers Assigned": "", "Ticket Delivery Method": "",
        "Ticket Instructions": "", "Ticket Instruction Details": "", "Display On Web": "No", 
        "Display Delivery Method": "No", "Allow Date Selection": "No", "Allow Time Selection": "No", 
        "More Information Title": "", "More Information Url": "", "Web URL": "", "Address Line 1": "",
        "Address Line 2": "", "Address Line 3": "", "City": "", "State or Province": "", "Postal Code": "",
        "County": "", "Market": "", "Metro Area": "", "Country": "", "Contact Name": "", "Contact Email": "",
        "Contact Phone": "", "TFK Area": "", "TFK Market": "", "TFK Region": "", "Total Requested": "", 
        "Total Distributed": "", "Total Donated": "", "Total Remaining": ""
    }

    # Add new columns to the DataFrame
    game_info = game_info.assign(**new_columns)
    print("Added new columns with default values.")
    
    # Append the current year to 'Game Date'
    current_year = pd.Timestamp.now().year
    game_info['Game Date'] = game_info['Game Date'] + f", {current_year}"
    print("Appended current year to 'Game Date'.")
    
    # Clean 'Game Time' by extracting the time in the format "1:30 PM"
    game_info['Game Time'] = game_info['Game Time'].str.extract(r'(\d{1,2}:\d{2} [APap][Mm])')[0]
    print("Cleaned 'Game Time' column.")
    
    # Combine 'Game Date' and 'Game Time' to create a datetime for the event start
    try:
        game_info['Start Date'] = pd.to_datetime(game_info['Game Date'] + " " + game_info['Game Time'], format="%b %d, %Y %I:%M %p")
        print("Created 'Start Date' column.")
    except Exception as e:
        print("Error converting 'Game Date' and 'Game Time' into datetime format.", exc_info=True)
        raise e
    
    # Create 'End Date' by adding 3 hours to the start time
    game_info['End Date'] = game_info['Start Date'] + pd.Timedelta(hours=3)
    print("Created 'End Date' column.")
    
    # Create 'Display Start Date' as today's date (no time component)
    game_info["Display Start Date"] = pd.Timestamp.today().normalize()
    print("Created 'Display Start Date' column.")
    
    # Function to calculate 'Display End Date' based on game start day
    def get_display_end_date(start_date):
        return start_date if start_date.weekday() < 5 else start_date - pd.DateOffset(days=(start_date.weekday() - 4))
    
    game_info["Display End Date"] = game_info["Start Date"].apply(get_display_end_date)
    game_info["Display End Date"] = pd.to_datetime(game_info["Display End Date"], errors="coerce")
    game_info["Display End Date"] = game_info["Display End Date"].dt.date
    print("Created 'Display End Date' column.")
    
    # Rename 'Event Name' to 'Name' if it exists
    if "Event Name" in game_info.columns:
        game_info = game_info.rename(columns={"Event Name": "Name"})
        print("Renamed 'Event Name' to 'Name'.")
    
    # Define the desired column order
    desired_columns = [
        'Name', 'Description', 'Start Date', 'End Date', 'Multiple Dates or Times', 'Event Category', 'Age Range', 'Owner', 
        'Fulfillment Method', 'Fulfillment Type', 'Fulfillment Date', 'Enforce Quantity Limit', 'Maximum Tickets', 
        'Split Groups', 'Volunteer Event', 'Volunteers Assigned', 'Ticket Delivery Method', 'Ticket Instructions', 
        'Ticket Instruction Details', 'Display On Web', 'Display Delivery Method', 'Allow Date Selection', 
        'Allow Time Selection', 'Display Start Date', 'Display End Date', 'More Information Title', 'More Information Url', 
        'Web URL', 'Venue', 'Address Line 1', 'Address Line 2', 'Address Line 3', 'City', 'State or Province', 
        'Postal Code', 'County', 'Market', 'Metro Area', 'Country', 'Contact Name', 'Contact Email', 'Contact Phone', 
        'TFK Area', 'TFK Market', 'TFK Region', 'Total Requested', 'Total Distributed', 'Total Donated', 'Total Remaining'
    ]
    
    # Remove any columns not in the desired list
    game_info = game_info[[col for col in desired_columns if col in game_info.columns]]
    print("Removed columns that were not in the desired list.")
    
    # Reorder the columns based on the desired order
    game_info = game_info[desired_columns]
    print("Reordered DataFrame columns to match the desired order.")

    return game_info

