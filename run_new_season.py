import pandas as pd
from scrape_schedules import scrape_team_schedules
from scrape_venues import join_schedule_with_venues
from generate_descriptions import generate_descriptions
from add_necassary_columns import finalize_game_info_df

def main():
    schedule_df = scrape_team_schedules()
    combined_df = join_schedule_with_venues(schedule_df)
    description_df = generate_descriptions(combined_df)
    final_df = finalize_game_info_df(description_df)
    final_df.to_csv("/app/static/final_draft.csv", encoding="utf-8-sig", index=False)

if __name__ == "__main__":
    main()

