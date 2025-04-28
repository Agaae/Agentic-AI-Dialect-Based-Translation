# First, keep the LLama recommender function from earlier:
from openai import OpenAI
from dotenv import load_dotenv
import os
load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key= os.getenv("OPENROUTER_LAMA_KEY"),  # replace this
)

import time
import streamlit as st

# Initialize conversation log
conversation_log = []

# Define the function to get recommendations from Llama
def get_lama_recommendations(new_input: str, conversation_log: list[str]) -> str:
    prompt = f"""
You are a travel assistant located in Cairo, Egypt. If the reply is in Arabic, translate it to English first, then do your search.

You ONLY reply if the input talks about a place, location, street, landmark, food, or Egyptian culture.

Rules:

If the input mentions a "street", "square", "area", "district", or landmark, check if it’s a known location. If it’s a local street, district, or a place named after an individual or event (e.g., Martyr Street), explain briefly about it and mention any nearby famous sites.

If the input mentions food or restaurants, suggest a local dish or a restaurant.

If the input mentions traffic, weather, or cultural events, give a short, direct answer.

Otherwise, DO NOT REPLY.

Always reply with only 2 sentences maximum. Be short, clear, and relevant to the input.
    Conversation:
     {chr(10).join(conversation_log)}
    
    New User Input:
    {new_input}
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
