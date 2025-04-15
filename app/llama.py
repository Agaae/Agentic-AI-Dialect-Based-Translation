# First, keep the LLama recommender function from earlier:
from openai import OpenAI
from dotenv import load_dotenv
import os
load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key= os.getenv("OPENROUTER_API_KEY"),  # replace this
)

import time
import streamlit as st

# Initialize conversation log
conversation_log = []

# Define the function to get recommendations from Llama
def get_lama_recommendations(conversation_log: list[str]) -> str:
    prompt = f"""
    You are a travel assistant located in Egypt, specifically in Cairo. Based on the following conversation, suggest:
    - Interesting places to visit nearby, if the conversation involves a street name, then talk about the history of that street and nearby places around it.
    - Articles or cultural facts related to what’s being discussed, whether it's a place or food
    - Local recommendations if the conversation is about (food, landmarks, tips), 
    try to make it kind of short

    Conversation:
    {chr(10).join(conversation_log)}
    """.strip()

    try:
        # Call the Llama model to get a response
        response = client.chat.completions.create(
            model="meta-llama/llama-4-maverick:free",
            messages=[{
                "role": "user",
                "content": [{
                    "type": "text",
                    "text": prompt
                }]
            }]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ Error generating recommendations: {e}"

print(get_lama_recommendations(conversation_log))