import os
import streamlit as st
from dotenv import load_dotenv
import sqlite3
from openai import OpenAI
import time
from tenacity import retry, stop_after_attempt, wait_exponential
from thefuzz import fuzz

from speech import record_audio, transcribe_audio  # For fuzzy string matching
st.set_page_config(
    page_title="Translation",
    
)


from Gemini import detect_language, get_translation, store_translation, translate_text
from ocr import extract_text_from_image, extract_text_from_image_eng
from llama import get_lama_recommendations



# st.markdown(
#     """
#     <style>
#     body {
#         background-color: white;
#         color: black;
#     }
#     .stApp {
#         background-color: white;
#         color: black;
#     }
#     h1 {
#         color: black;
#         text-align: center;
#     }
    
#     label[for*="streamlit"] {
#     color: white;
# }
#     </style>
#     """,
#     unsafe_allow_html=True
# )


if "continue_conversation" not in st.session_state:
    st.session_state.continue_conversation = False
if "conversation_log" not in st.session_state:
    st.session_state.conversation_log = []
if "previous_recommendations" not in st.session_state:
    st.session_state.previous_recommendations = None
if "translated" not in st.session_state:
    st.session_state.translated = False
if "user_input" not in st.session_state:
    st.session_state.user_input = ""


st.title("Translator")
st.sidebar.success("Select a page above.")



uploaded_image = st.file_uploader("Upload an image for text extraction", type=["png", "jpg", "jpeg"])
if uploaded_image:
            # Option to choose language of text in the image
            language_choice = st.radio("Select the language in the image:", ("English", "Arabic"))

            # Wait for user confirmation
            if st.button("Confirm Language"):
                with st.spinner("Extracting text from image..."):
                    if language_choice == "English":
                        extracted_text  = extract_text_from_image_eng(uploaded_image)
                    else:
                        extracted_text  = extract_text_from_image(uploaded_image)
                    st.session_state.user_input = extracted_text  # 🛠️ Save extracted text
                    st.success("Text extracted and ready for translation!")

if uploaded_image is not None:
    st.image(uploaded_image, caption="Uploaded Image", use_container_width=True)

if st.button("Record Audio"):
    record_audio()  # Record the user's voice

            # After recording, transcribe the audio
    st.spinner("Transcribing audio...")  # Optional spinner while transcribing
    transcribed_text = transcribe_audio("audio.wav")
    st.write("DEBUG: transcribed_text =", transcribed_text)  # 👈 DEBUG
    st.session_state.user_input = transcribed_text  # This should update the session state
    st.rerun()



user_input = st.text_area("Enter text to translate:", height=100, value=st.session_state.user_input, key="unique_key_1")
st.session_state.user_input = user_input

if st.button("Translate"):
    if not st.session_state.user_input.strip():
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
                llama_recommendations = get_lama_recommendations(translation,st.session_state.conversation_log)
                st.session_state.conversation_log = [
                    f"User: {user_input}",
                    f"Llama: {llama_recommendations}"
    ]

                if llama_recommendations:
                    st.subheader("Recommendations:")
                    st.write(llama_recommendations)
                    st.session_state.conversation_log.append(f"Llama: {llama_recommendations}")
                    st.session_state.translated = True
                else:
                    st.info("No Llama recommendations found.")

                # Option to continue the conversation with Llama about the recommendations
                    # Transition to a new section where the user can ask follow-up questions

            except Exception as e:
                st.error(f"Translation failed: {str(e)}")



if st.button("Continue Conversation"):
    st.session_state.continue_conversation = True
    st.session_state.user_input = user_input  # Store user input for continuity
    # Store Llama's response
    st.switch_page("pages/mainpage.py")


