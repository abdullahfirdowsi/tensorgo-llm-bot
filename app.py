import streamlit as st
import speech_recognition as sr
import google.generativeai as gen_ai
import os
from dotenv import load_dotenv
from gtts import gTTS
from io import BytesIO
import pygame
import tempfile

# Load environment variables
load_dotenv()

# Custom CSS for enhancing design
def add_custom_css():
    st.markdown("""
        <style>
            .chat-container {
                padding: 10px;
                border-radius: 5px;
                background-color: #f0f0f0;
                margin-bottom: 10px;
            }
            .user-message {
                background-color: #007bff;
                color: white;
                padding: 8px;
                border-radius: 10px;
                text-align: left;
            }
            .bot-message {
                background-color: #e5e5e5;
                color: black;
                padding: 8px;
                border-radius: 10px;
                text-align: left;
            }
            .chat-history-btn {
                position: absolute;
                top: 10px;
                right: 10px;
            }
        </style>
    """, unsafe_allow_html=True)

# Add custom design enhancements
add_custom_css()

# Initialize recognizer
recognizer = sr.Recognizer()

# Configure Google Gemini API
GOOGLE_API_KEY = 'AIzaSyAhYPPra6fcIa96tkTTYgez5QWY0ydVzb0'

if not GOOGLE_API_KEY:
    st.error("GOOGLE_API_KEY environment variable not set.")
else:
    try:
        gen_ai.configure(api_key=GOOGLE_API_KEY)
        model = gen_ai.GenerativeModel('gemini-pro')
    except Exception as e:
        st.error(f"Error configuring Google Gemini API: {e}")

# Function to convert speech to text
def speech_to_text(audio_data):
    try:
        text = recognizer.recognize_google(audio_data)
        return text
    except sr.UnknownValueError:
        return "Sorry, I did not understand that. Try again recording."
    except sr.RequestError:
        return "Sorry, there seems to be a network issue."

# Function to get response from Gemini
def get_gemini_response(prompt):
    if prompt == "Sorry, I did not understand that. Try again recording." or prompt == "Sorry, there seems to be a network issue.":
        return "Please, Speak clearly !!"
    else:
        text_prompt = "Give a response in a single line for the following prompt without emojis and symbols (give only text as output): "
        user_prompt = text_prompt + prompt
        
        # Initialize chat session if not already present
        if "chat_session" not in st.session_state:
            st.session_state.chat_session = model.start_chat(history=[])

        # Send the user's message to Gemini-Pro and get the response
        chat_session = st.session_state.chat_session
        gemini_response = chat_session.send_message(user_prompt)
        return gemini_response.text.strip()

# Function to convert text to speech and play it using pygame
def speak_text_with_pygame(text):
    # Convert text to speech
    tts = gTTS(text=text, lang='en')
    
    # Create a temporary file for the audio
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
        audio_file = temp_file.name
        tts.write_to_fp(temp_file)

    # Initialize pygame mixer and play the audio
    pygame.mixer.init()
    pygame.mixer.music.load(audio_file)
    pygame.mixer.music.play()

    # Wait until the audio is done playing
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    
    pygame.mixer.music.stop()  # Ensure music playback stops
    pygame.mixer.music.unload()  # Unload the music
    os.remove(audio_file)  # Remove the temporary audio file after playback

# Initialize session state for chat history and its visibility
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "show_chat_history" not in st.session_state:
    st.session_state.show_chat_history = False

# Streamlit UI
st.title("Speech-to-Speech LLM Bot")

# Toggle button to show/hide chat history
if st.button("Show/Hide Chat History"):
    st.session_state.show_chat_history = not st.session_state.show_chat_history

# Display chat history if the toggle is on
if st.session_state.show_chat_history:
    if st.session_state.chat_history:
        pass
    else:
        st.subheader("Chat History")
        st.write("No conversation yet.")

# Placeholder for the "Listening..." message
status_placeholder = st.empty()

# Audio capture button
if st.button("Start Recording"):
    recording = True
    status_placeholder.write("Listening...")

    # Capture audio via microphone
    with sr.Microphone() as source:
        audio = recognizer.listen(source)
        user_input = speech_to_text(audio)
        st.write(f"You said: {user_input}")
    
    # Clear the "Listening..." message
    status_placeholder.empty()

    # If there's input, process it
    if user_input:
        # Add user input to chat history
        st.session_state.chat_history.append(f"You: {user_input}")

        # Get the response from Gemini
        response = get_gemini_response(user_input)
        st.write(f"Bot: {response}")

        # Add bot response to chat history
        st.session_state.chat_history.append(f"Bot: {response}")

        # Convert bot response to speech and play it using pygame
        speak_text_with_pygame(response)

# Refresh chat history display if the toggle is on
if st.session_state.show_chat_history and st.session_state.chat_history:
    st.subheader("Chat History")
    for entry in st.session_state.chat_history:
        st.write(entry)
