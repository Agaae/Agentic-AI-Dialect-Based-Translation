import streamlit as st
from llama import get_lama_recommendations

# Title of the page
st.title("AI Guide")

# Initialize the session state if not already done
if "conversation_log" not in st.session_state:
    st.session_state.conversation_log = []

# Display previous conversations (User's input and Llama's responses)
if st.session_state.conversation_log:
    for message in st.session_state.conversation_log:
        st.write(message)

# User input
# Initialize user_input session state if it's not already initialized
if 'user_input' not in st.session_state:
    st.session_state.user_input = ""  # Initialize empty input field

# Display text input field (initially empty)
# Display text input field (initially empty)
# Replace this:
# user_input = st.text_area("Enter text for Llama to respond:", height=100, value=st.session_state.user_input, key="unique_key_2")

# With this:
user_input = st.chat_input("Enter your message...")

if user_input:
    # Get Llama's response
    llama_response = get_lama_recommendations(user_input, st.session_state.conversation_log)

    # Update the conversation log
    st.session_state.conversation_log.append(f"User: {user_input}")
    st.session_state.conversation_log.append(f"Llama: {llama_response}")

    # Clear input automatically (chat_input resets automatically)
    st.rerun()


# Button to clear conversation log
if st.button("Clear Conversation"):
    st.session_state.conversation_log = []
    st.write("Conversation cleared!")

# Button to return to translation page
if st.button("Return to Translation"):
    st.switch_page("interface.py")
