import os
import streamlit as st
from dotenv import load_dotenv
import sqlite3
from openai import OpenAI
import time
from tenacity import retry, stop_after_attempt, wait_exponential
from thefuzz import fuzz  # For fuzzy string matching
from ocr import extract_text_from_image, extract_text_from_image_eng
from llama import get_lama_recommendations

# st.markdown("""
#     <style>
#     /* Page background and font */
#     html, body, .stApp {
#         background-color: #ffffff;
#         color: #000000;
#         font-family: 'Segoe UI', sans-serif;
#     }

#     /* Text input area (main and extracted) */
#     textarea, .stTextArea textarea {
#         background-color: #ffffff !important;
#         color: #000000 !important;
#         border: 2px solid #000000 !important;
#         border-radius: 8px !important;
#         padding: 10px !important;
#         font-size: 16px !important;
#     }
    
    
    

#     /* File uploader */
#     .stFileUploader {
#         background-color: #ffffff !important;
#         border: 2px dashed #000000 !important;
#         border-radius: 10px !important;
#         padding: 10px !important;
#     }

#     /* Radio buttons block */
#     .stRadio > div {
#         background-color: #ffffff !important;
#         border: 2px solid #ffffff !important;
#         border-radius: 10px !important;
#         padding: 15px !important;
#     }

# /* Style the text label of each radio button */
# label[data-baseweb="radio"] > div {
#     color: #000000 !important; /* Change to any visible color */
#     font-weight: 500; /* Optional: Make it bolder */
# }

#     /* Buttons */
#     .stButton button {
#         background-color: #ffffff;
#         color: #000000;
#         border: 2px solid #000000;
#         border-radius: 8px;
#         padding: 0.5em 1.5em;
#         font-weight: bold;
#         font-size: 16px;
#     }

#     .stButton button:hover {
#         background-color: #000000;
#         border-color: #ffffff;
#         color: #ffffff;
#     }

#     /* Translation output box */
#     .stMarkdown, .stWrite, .stSuccess, .stInfo, .stWarning, .stError {
#         border-radius: 8px;
#         padding: 12px;
#         background-color: #ffffff !important;
#         border: 2px solid #000000;
#     }

#     /* Translation caption */
#     .stCaption {
#         font-style: italic;
#         color: #000000;
#         margin-top: 0.5em;
#     }

#     /* Message boxes */
#     .stAlert {
#         border-radius: 8px;
#         padding: 1em;
#         font-weight: normal;
#         color: #FFFFFF;
#     }

   
#     </style>
# """, unsafe_allow_html=True)

# Configuration
MAX_RETRIES = 3
API_TIMEOUT = 30  # seconds
SIMILARITY_THRESHOLD = 80  # Minimum similarity score (0-100)

load_dotenv()
# Initialize OpenRouter client
def get_client():
    API_KEY = os.getenv("OPENROUTER_API_KEYS")
    print(API_KEY)
    if not API_KEY:
        st.error("OPENROUTER_API_KEY not found in environment variables")
        st.stop()
    
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=API_KEY,
    )

client = get_client()

# Maintain original table structure
def init_db():
    conn = sqlite3.connect("translations.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS translations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            input_text TEXT,
            translated_text TEXT,
            UNIQUE(input_text, translated_text)
        )
    """)
    conn.commit()
    conn.close()

# Retry decorator for API calls
@retry(stop=stop_after_attempt(MAX_RETRIES), wait=wait_exponential(multiplier=1, min=4, max=10))
def make_api_call(messages):
    try:
        # Make the API call
        response = client.chat.completions.create(
            model="google/gemini-2.5-pro-exp-03-25:free",
            messages=messages,
            timeout=API_TIMEOUT
        )
        
        # Debug: Print the full response for inspection
        print(f"Full API Response: {response}")
        
        # Ensure the response has the correct structure
        if not response.choices or len(response.choices) == 0:
            raise ValueError("Empty or malformed response from API")
        
        # Access the content correctly
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        st.error(f"API call failed: {str(e)}")
        print(f"Error occurred: {str(e)}")  # Debugging
        raise


def normalize_text(text):
    """Normalize text for better similarity comparison"""
    return text.lower().strip()

def detect_language(text):
    """Simple language detection"""
    if any(char in 'ءابتثجحخدذرزسشصضطظعغفقكلمنهوي' for char in text):
        return 'egyptian'
    return 'english'

def find_similar_translation(text, source_lang):
    """Find similar existing translations using fuzzy matching"""
    conn = sqlite3.connect("translations.db")
    cursor = conn.cursor()
    
    normalized_input = normalize_text(text)
    input_length = len(normalized_input)
    
    # Get all relevant translations based on language direction
    if source_lang == 'english':
        cursor.execute("SELECT input_text, translated_text FROM translations")
        compare_index = 0  # Compare against input_text
        return_index = 1   # Return translated_text
    else:
        cursor.execute("SELECT translated_text, input_text FROM translations")
        compare_index = 0  # Compare against translated_text
        return_index = 1   # Return input_text
    
    best_match = None
    highest_score = 0
    
    for row in cursor.fetchall():
        db_text = normalize_text(row[compare_index])
        # Skip texts with very different lengths
        if abs(len(db_text) - input_length) > (0.3 * input_length):
            continue
            
        score = fuzz.ratio(normalized_input, db_text)
        
        if score > highest_score and score >= SIMILARITY_THRESHOLD:
            highest_score = score
            best_match = row[return_index]
    
    conn.close()
    return best_match, highest_score

def get_translation(text, source_lang):
    """Try exact match first, then fuzzy match"""
    # First try exact match
    conn = sqlite3.connect("translations.db")
    cursor = conn.cursor()
    
    if source_lang == 'english':
        cursor.execute("SELECT translated_text FROM translations WHERE input_text = ?", (text,))
    else:
        cursor.execute("SELECT input_text FROM translations WHERE translated_text = ?", (text,))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return result[0], 100  # Return with 100% confidence
    
    # Fall back to fuzzy matching
    return find_similar_translation(text, source_lang)

def store_translation(input_text, translated_text):
    """Store translation with original structure"""
    conn = sqlite3.connect("translations.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO translations (input_text, translated_text)
        VALUES (?, ?)
    """, (input_text, translated_text))
    conn.commit()
    conn.close()

def translate_text(text, source_lang):
    system_prompt = (
        f"You are an expert translator between English and Egyptian Arabic. "
        f"Translate this {source_lang} text to {'english' if source_lang == 'egyptian' else 'egyptian'}. "
        "Provide only the translation, no additional commentary."
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": text}
    ]
    
    return make_api_call(messages)

# Initialize database
init_db()


# Initialize session state for conversation tracking
if "continue_conversation" not in st.session_state:
    st.session_state.continue_conversation = False
if "conversation_log" not in st.session_state:
    st.session_state.conversation_log = []

# Title for the app
st.title("Egyptian Arabic ↔ English Translator")

# If in conversation mode, show the chat interface
if st.session_state.continue_conversation:
    # Conversation interface
    st.title("Continue Conversation with Llama")

    previous_recommendations = st.session_state.get("previous_recommendations", "")

    if previous_recommendations:
        st.subheader("Previous Recommendations from Llama:")
        st.write(previous_recommendations)

    user_question = st.text_input("Ask Llama a follow-up question:")

    if user_question:
        # Add the new question to the conversation log and ask Llama
        st.session_state.conversation_log.append(f"User: {user_question}")
        llama_reply = get_lama_recommendations(st.session_state.conversation_log)
        st.write(f"Llama: {llama_reply}")
        st.session_state.conversation_log.append(f"Llama: {llama_reply}")

    # Option to return to the main translation section
    if st.button("Return to Translation"):
        # Return to translation section by setting continue_conversation to False
        st.session_state.continue_conversation = False
        st.experimental_rerun()  # Ensure the page re-runs and refreshes with the translation section

else:
    # Option to choose between text or image upload
    translation_method = st.radio("Choose Translation Method:", ("Text Input", "Upload Image"))

    # Normal Translation Flow
    if translation_method == "Text Input":
        user_input = st.text_area("Enter text to translate:", height=100)

        if st.button("Translate"):
            if not user_input.strip():
                st.warning("Please enter text to translate")
            else:
                with st.spinner("Translating..."):
                    try:
                        start_time = time.time()

                        # Detect language
                        source_lang = detect_language(user_input)

                        # Check cache with fuzzy matching
                        translation, confidence = get_translation(user_input, source_lang)

                        if not translation:
                            # Call API if no match found
                            translation = translate_text(user_input, source_lang)
                            confidence = 100  # New translations get 100% confidence

                            # Store in database
                            store_translation(
                                user_input if source_lang == 'english' else translation,
                                translation if source_lang == 'english' else user_input
                            )

                        st.success(f"Translation ({'Arabic → English' if source_lang == 'egyptian' else 'English → Arabic'}):")
                        st.write(translation)

                        if confidence < 100:
                            st.info(f"⚠️ Used similar match ({confidence}% confidence)")

                        st.caption(f"Translation took {time.time() - start_time:.2f} seconds")

                        # Fetch and display Llama recommendations based on the user input
                        llama_recommendations = get_lama_recommendations([user_input])
                        st.session_state.conversation_log.append(f"User: {user_input}")

                        if llama_recommendations:
                            st.subheader("Llama Recommendations:")
                            st.write(llama_recommendations)
                            st.session_state.conversation_log.append(f"Llama: {llama_recommendations}")
                        else:
                            st.info("No Llama recommendations found.")

                        # Option to continue the conversation with Llama about the recommendations
                        if st.button("Continue Conversation"):
                            # Transition to a new section where the user can ask follow-up questions
                            st.session_state.continue_conversation = True
                            st.session_state.previous_recommendations = llama_recommendations
                            st.experimental_rerun()  # Ensure the page re-runs and enters conversation mode

                    except Exception as e:
                        st.error(f"Translation failed: {str(e)}")

    elif translation_method == "Upload Image":
        uploaded_image = st.file_uploader("Upload an image for text extraction", type=["png", "jpg", "jpeg"])

        if uploaded_image:
            # Option to choose language of text in the image
            language_choice = st.radio("Select the language in the image:", ("English", "Arabic"))

            # Wait for user confirmation
            if st.button("Confirm Language"):
                with st.spinner("Extracting text from image..."):
                    try:
                        if language_choice == "English":
                            extracted_text = extract_text_from_image_eng(uploaded_image)
                        else:
                            extracted_text = extract_text_from_image(uploaded_image)

                        # Display extracted text
                        st.text_area("Extracted Text", extracted_text, height=200)

                        if extracted_text.strip():
                            start_time = time.time()

                            source_lang = detect_language(extracted_text)

                            # Check cache with fuzzy matching
                            translation, confidence = get_translation(extracted_text, source_lang)

                            if not translation:
                                translation = translate_text(extracted_text, source_lang)
                                confidence = 100

                                store_translation(
                                    extracted_text if source_lang == 'english' else translation,
                                    translation if source_lang == 'english' else extracted_text
                                )

                            st.success(f"Translation ({'Arabic → English' if source_lang == 'egyptian' else 'English → Arabic'}):")
                            st.write(translation)

                            if confidence < 100:
                                st.info(f"⚠️ Used similar match ({confidence}% confidence)")

                            st.caption(f"Translation took {time.time() - start_time:.2f} seconds")

                            # Fetch and display Llama recommendations
                            llama_recommendations = get_lama_recommendations([extracted_text])
                            st.session_state.conversation_log.append(f"User: {extracted_text}")

                            if llama_recommendations:
                                st.subheader("Llama Recommendations:")
                                st.write(llama_recommendations)
                                st.session_state.conversation_log.append(f"Llama: {llama_recommendations}")
                            else:
                                st.info("No Llama recommendations found.")

                            # Option to continue the conversation with Llama about the recommendations
                            if st.button("Continue Conversation"):
                                # Transition to a new section where the user can ask follow-up questions
                                st.session_state.continue_conversation = True
                                st.session_state.previous_recommendations = llama_recommendations
                                st.experimental_rerun()  # Ensure the page re-runs and enters conversation mode

                        else:
                            st.warning("No text found in the image.")

                    except Exception as e:
                        st.error(f"Error during text extraction: {str(e)}")
