import pandas as pd
from scrape_schedules import scrape_team_schedules
from scrape_venues import join_schedule_with_venues
from generate_descriptions import generate_descriptions
from add_necassary_columns import finalize_game_info_df

from save_sep_files import generate_team_sheets_from_schedule


def main():
    schedule_df = scrape_team_schedules()
    combined_df = join_schedule_with_venues(schedule_df)
    description_df = generate_descriptions(combined_df)
    final_df = finalize_game_info_df(description_df)

    # Step 1: Save one Excel file with all teams as separate sheets
    by_team_path = "/app/static/mlb_final_draft_by_team.xlsx"
    with pd.ExcelWriter(by_team_path, engine="openpyxl") as writer:
        teams = final_df["Name"].str.extract(r'^(.*?) vs')[0].dropna().unique()
        for team in teams:
            team_df = final_df[final_df["Name"].str.startswith(team)]
            safe_name = team[:31]
            team_df.to_excel(writer, sheet_name=safe_name, index=False)
    print(f"✅ Multi-sheet schedule saved to: {by_team_path}")

    # Step 2: Generate Dynamics-ready Excel file per team
    template_path = "/app/data/dynamics_submission.xlsx"
    output_dir = "/app/static/dynamics_team_exports"
    generate_team_sheets_from_schedule(
        xlsx_path=by_team_path,
        template_path=template_path,
        output_dir=output_dir
    )


if __name__ == "__main__":
    main()
