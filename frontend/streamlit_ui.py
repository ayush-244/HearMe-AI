import streamlit as st
import logging
from typing import Dict, List

from backend.app.config.settings import Settings
from backend.app.services.sentiment_service import SentimentService
from backend.app.services.language_service import LanguageService
from backend.app.services.prompt_service import PromptService
from backend.app.services.chat_service import ChatService
from backend.app.services.history_service import HistoryService
from backend.app.services.logging_service import LoggingService
from ai.sentiment.model import SentimentModel
from ai.language.detector import LanguageDetector
from langchain_groq import ChatGroq

logger = logging.getLogger(__name__)


@st.cache_resource
def _init_services():
    settings = Settings()

    sentiment_model = SentimentModel(settings.sentiment_model_name, settings.hf_token)
    sentiment_service = SentimentService(sentiment_model)

    language_detector = LanguageDetector()
    prompt_service = PromptService(settings.PROMPTS_DIR)
    language_service = LanguageService(language_detector, prompt_service.language_configs)

    llm = ChatGroq(
        groq_api_key=settings.groq_api_key,
        model_name=settings.llm_model_name,
    )
    chat_service = ChatService(llm, prompt_service)

    history_service = HistoryService(settings.max_history_messages)
    logging_service = LoggingService(settings.sentiment_log_file)

    return {
        "settings": settings,
        "sentiment": sentiment_service,
        "language": language_service,
        "prompt": prompt_service,
        "chat": chat_service,
        "history": history_service,
        "logging": logging_service,
    }


def _init_session_state():
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []


def display_chat_history(history: List[Dict[str, str]]):
    for message in history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


def run():
    _init_session_state()
    svc = _init_services()

    st.title("🌐 Multilingual Sentiment-Aware Chatbot")

    with st.sidebar:
        st.header("Language Settings")
        selected_language = st.selectbox(
            "Choose Language (or detect automatically)",
            options=["auto"] + list(svc["prompt"].language_configs.keys()),
            format_func=lambda x: "Detect Automatically"
            if x == "auto"
            else svc["prompt"].language_configs[x]["name"],
        )

        if st.button("Clear Chat History"):
            st.session_state.chat_history = []
            st.rerun()

        log_sentiment = st.checkbox("Log Sentiment Analysis", value=False)

    display_chat_history(st.session_state.chat_history)

    user_input = st.chat_input("Enter your message")

    if user_input:
        detected_lang = svc["language"].detect(user_input)
        language_to_use = detected_lang if selected_language == "auto" else selected_language

        if language_to_use not in svc["prompt"].language_configs:
            language_to_use = "en"

        sentiment, confidence = svc["sentiment"].analyze(user_input)

        if log_sentiment:
            svc["logging"].log_sentiment(user_input, sentiment, confidence)
            st.success("Sentiment analysis logged successfully!")

        with st.chat_message("user"):
            st.markdown(user_input)

        with st.expander("Message Analysis", expanded=False):
            st.write(f"🧠 Sentiment Detected: {sentiment}")
            st.write(f"🎯 Confidence: {confidence:.2%}")
            lang_name = svc["language"].get_language_name(language_to_use)
            st.write(f"🌍 Language: {lang_name}")

        try:
            sentiment_intro = svc["prompt"].select_intro(sentiment)

            bot_response = svc["chat"].generate_response(
                user_input=user_input,
                language=language_to_use,
                sentiment=sentiment,
                history=st.session_state.chat_history,
            )

            st.session_state.chat_history = svc["history"].add_message(
                st.session_state.chat_history, "user", user_input
            )
            st.session_state.chat_history = svc["history"].add_message(
                st.session_state.chat_history, "assistant", bot_response
            )

            with st.chat_message("assistant"):
                st.markdown(f"{sentiment_intro}\n\n{bot_response}")

        except Exception as e:
            st.error(f"An error occurred while generating response: {e}")


if __name__ == "__main__":
    run()
