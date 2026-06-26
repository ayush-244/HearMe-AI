import streamlit as st
import logging
from typing import Dict, List

from .api_client import APIClient, APIClientError
from .config import LANGUAGES

logger = logging.getLogger(__name__)


@st.cache_resource
def _get_api_client() -> APIClient:
    return APIClient()


def _init_session_state():
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "backend_online" not in st.session_state:
        st.session_state.backend_online = True
    if "error_message" not in st.session_state:
        st.session_state.error_message = None


def _check_backend_health(api: APIClient) -> bool:
    if not api.health():
        st.session_state.backend_online = False
        st.session_state.error_message = "Backend server is offline. Please start the backend and refresh."
    else:
        st.session_state.backend_online = True
        st.session_state.error_message = None
    return st.session_state.backend_online


def display_chat_history(history: List[Dict[str, str]]):
    for message in history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def run():
    _init_session_state()
    api = _get_api_client()

    st.title("Multilingual Sentiment-Aware Chatbot")

    _check_backend_health(api)
    backend_ok = st.session_state.backend_online

    with st.sidebar:
        st.header("Language Settings")
        language_options = ["auto"] + list(LANGUAGES.keys())
        selected_language = st.selectbox(
            "Choose Language (or detect automatically)",
            options=language_options,
            format_func=lambda x: "Detect Automatically"
            if x == "auto"
            else LANGUAGES.get(x, x),
        )

        if st.button("Clear Chat History"):
            st.session_state.chat_history = []
            st.rerun()

        log_sentiment = st.checkbox("Log Sentiment Analysis", value=False)

        if not backend_ok:
            st.error("Backend server is offline.\n\nStart the backend with:\n`uvicorn backend.app.main:app --reload`")
            if st.button("Retry Connection"):
                if _check_backend_health(api):
                    st.rerun()

    display_chat_history(st.session_state.chat_history)

    user_input = st.chat_input("Enter your message", disabled=not backend_ok)

    if user_input and backend_ok:
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.spinner("Analyzing message..."):
            try:
                chat_result = api.chat(
                    message=user_input,
                    language=selected_language,
                    history=st.session_state.chat_history,
                )
            except APIClientError as e:
                st.error(f"Request failed: {e}")
                st.stop()
            except Exception as e:
                logger.exception("Unexpected error during chat request")
                st.error("An unexpected error occurred. Please try again.")
                st.stop()

        reply = chat_result["reply"]
        sentiment = chat_result["sentiment"]
        confidence = chat_result["confidence"]
        detected_language = chat_result["detected_language"]
        language_name = chat_result["language_name"]

        if log_sentiment:
            try:
                api.send_feedback(
                    message_id=f"msg_{hash(user_input)}",
                    rating=3,
                    comment=f"Sentiment: {sentiment} ({confidence:.2%})",
                )
                st.success("Sentiment analysis logged successfully!")
            except APIClientError:
                logger.warning("Failed to log sentiment feedback")
                st.warning("Could not log sentiment analysis.")

        with st.expander("Message Analysis", expanded=False):
            st.write(f"Sentiment Detected: {sentiment}")
            st.write(f"Confidence: {confidence:.2%}")
            st.write(f"Language: {language_name}")

        try:
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            st.session_state.chat_history.append({"role": "assistant", "content": reply})
            if len(st.session_state.chat_history) > 20:
                st.session_state.chat_history = st.session_state.chat_history[-20:]

            with st.chat_message("assistant"):
                st.markdown(reply)

        except Exception as e:
            logger.exception("Failed to update chat display")
            st.error("An error occurred while rendering the response.")


if __name__ == "__main__":
    run()
