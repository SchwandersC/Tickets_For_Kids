from dotenv import load_dotenv
import os
from openai import OpenAI
import pandas as pd
import openai
import backoff
import time
from collections import deque
load_dotenv() 
client = OpenAI()



def generate_descriptions(game_df):
    previous_descriptions = deque(maxlen=10)  # adjust window as needed


    # Exponential backoff to handle rate limits
    @backoff.on_exception(backoff.expo, openai.RateLimitError, max_time=60, max_tries=6)
    def completions_with_backoff(**kwargs):
        return client.chat.completions.create(**kwargs)

    # Define a function to generate descriptions using GPT-4o-mini
    def chat_generate_description(row):
        print(f"Processing row index: {row.name}")   
        recent_examples = "\n".join(f"- {desc}" for desc in previous_descriptions)
        context = f"""
        You are generating descriptions for tickets that have been donated.
        Avoid repeating common words and phrases in these recent descriptions:
        {recent_examples if recent_examples else '- None yet!'}
        """

        prompt = f"""
        Generate a short description. It should exactly word for word begin with --- MLB: xxx tickets available for the game. LEAVE THE xxx IN!
        Then write a short and sweet description and dont be cringy. That doesn't mention family and friends. Do not mention exact time.
        Limit it to 1 short sentence!
        If there is a promo available please write a kid friendly description for it within that 1 sentence. Do not refer to anything as 'our events' or 'our tickets'. It is 'the tickets' or 'the event'
        Do not refer to promo sponsors in your description
        Do not refer to "your purchase" or anything along those lines.
        If its a light hearted event, include a pun

        - **Promo:** {row['Promo'] if pd.notna(row['Promo']) else 'No promo available'}
        - **Time:** {row['Game Time']}
        
        """

        try:
            response = completions_with_backoff(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )

            description = response.choices[0].message.content.strip()
            previous_descriptions.append(description)
            return description
        
        except Exception as e:
            print(f"Error for game {row['Home Team']} vs {row['Away Team']}: {e}")
            return "Description unavailable"

    # Apply the function to each row while handling rate limits
    game_df["Description"] = game_df.apply(chat_generate_description, axis=1)

    # Save the updated DataFrame
    return game_df


