# app.py
import streamlit as st
import requests
import os

API_BASE = "http://localhost:8000"

st.title("AI Customer Support — Demo")

if "session_id" not in st.session_state:
    try:
        r = requests.post(f"{API_BASE}/session/start", timeout=5)
        r.raise_for_status()
        response_data = r.json()
        if "session_id" in response_data:
            st.session_state.session_id = response_data["session_id"]
        else:
            st.error(f"API Error: Unexpected response format. Response: {response_data}")
            st.stop()
    except requests.exceptions.ConnectionError:
        st.error(f"Connection Error: Cannot connect to API at {API_BASE}. Make sure the API server is running on port 8000.")
        st.stop()
    except requests.exceptions.Timeout:
        st.error("Timeout: API request took too long to respond.")
        st.stop()
    except Exception as e:
        st.error(f"Error starting session: {str(e)}")
        st.stop()

sid = st.session_state.session_id

st.header("Text chat")
user = st.text_input("Your message")
if st.button("Send text"):
    if not user.strip():
        st.warning("Please enter a message")
    else:
        try:
            r = requests.post(f"{API_BASE}/session/{sid}/message", json={"text": user}, timeout=30)
            r.raise_for_status()
            response_data = r.json()
            if "reply" in response_data:
                st.text_area("Assistant", value=response_data["reply"], height=200)
            else:
                st.error(f"API Error: Unexpected response format. Response: {response_data}")
        except requests.exceptions.Timeout:
            st.error("Request timed out. The API took too long to respond.")
        except Exception as e:
            st.error(f"Error sending message: {str(e)}")

st.header("Voice chat (upload)")
audio_file = st.file_uploader("Upload audio (wav/m4a)", type=["wav","m4a","mp3"])
if audio_file is not None:
    try:
        files = {"file": (audio_file.name, audio_file.getvalue(), audio_file.type)}
        r = requests.post(f"{API_BASE}/session/{sid}/audio", files=files, timeout=60)
        r.raise_for_status()
        response_data = r.json()
        if "transcript" in response_data and "reply" in response_data:
            st.write("Transcript:", response_data["transcript"])
            st.write("Reply:", response_data["reply"])
            wav_path = response_data.get("wav")
            if wav_path and os.path.exists(wav_path):
                st.audio(wav_path)
        else:
            st.error(f"API Error: Unexpected response format. Response: {response_data}")
    except requests.exceptions.Timeout:
        st.error("Request timed out. The API took too long to respond.")
    except Exception as e:
        st.error(f"Error processing audio: {str(e)}")