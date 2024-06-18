import base64
import re
import time
from dataclasses import dataclass
from io import BytesIO
from typing import Literal, Optional

import streamlit as st
from googletrans import Translator
from gtts import gTTS
from streamlit_extras.stylable_container import stylable_container


### METHODS & DATACLASSES ###

@dataclass
class Message:
    """
    Class for keeping track of a chat message.
    """
    origin: Literal["human", "ai"]
    message: str
    context: str = ""
    confidence: str = ""
    avatar: Optional[str] = None
    image: str = None
    out_of_scope: bool = False


def initialize_session_state():
    """
    Initialization of the chatbot session state.
    This method is only loaded once on the application start.
    """
    try:
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "token_count" not in st.session_state:
            st.session_state.token_count = 0
        if "conversation" not in st.session_state:
            @st.cache_resource(ttl=3600 * 24, show_spinner=False)  # Reload the model at least every 24 hours
            def load_llm():
                import app.chatbot as cb
                st.session_state.conversation = cb.ChatBot()
                st.session_state.conversation.setup("intfloat-qa",
                                                    "marco/em_german_mistral_v01-coherent",
                                                    "intfloat/multilingual-e5-large",
                                                    "cross-encoder/msmarco-MiniLM-L6-en-de-v1", "intfloat-website")
                return st.session_state.conversation
            st.session_state.conversation = load_llm()
        if 'audio_visible' not in st.session_state:
            st.session_state.audio_visible = False
        if 'audio_bytes' not in st.session_state:
            st.session_state.audio_bytes = None
    except Exception as _:
        st.error(f"An unknown error occurred. Please reload the page and try again.", icon="❗")


def clear_chat():
    """
    Callback for "Clear Chat" button.
    """
    st.session_state.messages = []
    st.session_state.audio_visible = False
    st.session_state.audio_bytes = None


def detect_language(text: str):
    """
    Detects the language of a written text.
    :param text: user query as string
    :return: detected language as string
    """
    translator = Translator()
    return translator.detect(text).lang


def preprocess_text(text: str):
    """
    Searches for urls and adds a prefix.
    This is needed because of the preprocessing of the speech output.
    :param text: chatbot answer as string
    :return: the given text with replacements
    """
    url_pattern = r'http[s]?://(?:[azAZ]|[0-9]|[$@.&+]|[!*\\(\\),]|(?:%[09afAF][09afAF]))+'
    urls = re.findall(url_pattern, text)

    for url in urls:
        text = text.replace(url, f"link to {url}")

    return text


def text_to_speech(text: str, lang: str):
    """
    Main method to convert text into speech
    :param text: chatbot answer as string
    :param lang: language as string, usually "en" or "de"
    :return: BytesIO object that contains the gTTS speech translation
    """
    text = preprocess_text(text)

    audio_buffer = BytesIO()
    tts = gTTS(text=text, lang=lang, slow=False)
    tts.write_to_fp(audio_buffer)
    audio_buffer.seek(0)

    return audio_buffer


def extract_image_urls(text: str):
    """
    Extracts the image urls for displaying them directly.
    :param text: chatbot answer as string
    :return:
    """
    pattern = r"(https?:\/\/.*\.(?:png|jpg|webp))"
    image_urls = re.findall(pattern, text)
    local_pattern = r"\./backend\/rasa\/actions\/images\/[^ \n]+"
    image_urls.extend(re.findall(local_pattern, text))
    return image_urls


def generate_messages():
    """
    Generates the old chat messages.
    """
    for message in st.session_state.messages:
        if not message.out_of_scope:
            with st.chat_message(message.origin, avatar=message.avatar):
                st.markdown(message.message)
                if message.image:
                    st.image(message.image, use_column_width=True)


def get_base64_image(image_path: str):
    with open(image_path, "rb") as file:
        contents = file.read()
        data_url = base64.b64encode(contents).decode("utf-8")
    return data_url


def load_css():
    """
    Load CSS styles.
    """
    with open("static/styles.css", "r") as f:
        style_css = f.read()
        css = "<style>{}</style>".format(style_css)
        st.markdown(css, unsafe_allow_html=True)

### PAGE CONFIGURATION ###

st.set_page_config(
    page_title="THA Chatbot",
    page_icon="static/logo_icon.png",
)

user_avatar_path = "static/user_icon.png"
ai_avatar_path = "static/tha_logo.png"
tha_logo = "static/tha_logo.png"
tha_logo_base64 = get_base64_image(tha_logo)

load_css()

with st.container():
    st.markdown(f"""
    <div class="container-fluid fixed-header">
        <div class="row align-items-center">
            <div class="col-5">
                <h1><strong>THA Chatbot</strong></h1>
            </div>
            <div class="col-1 text-right">
                <img src="data:image/png;base64,{tha_logo_base64}" alt="THA Logo">
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with stylable_container(key="clear_button", css_styles=""):  # workaroung to style the button   
    st.button("Clear Chat", key="clear_button", on_click=clear_chat) 

st.markdown(
    """
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">
    <script src="https://code.jquery.com/jquery-3.2.1.slim.min.js" integrity="sha384-KJ3o2DKtIkvYIK3UENzmM7KCkRr/rE9/Qpg6aAZGJwFDMVNA/GpGFF93hXpG5KkN" crossorigin="anonymous"></script>
    <script src="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/js/bootstrap.min.js" integrity="sha384-JZR6Spejh4U02d8jOt6vLEHfe/JQGiRRSQQxSfFWpi1MquVdAyjUar5+76PVCmYl" crossorigin="anonymous"></script>
    
    <div class="sticky-footer-container">
        <div class="col-12">
            <div class="alert infobox" style="color: grey;">
                <p>AI-generated content may contain errors or inaccuracies. Always verify the information independently. </p>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


### MAIN APPLICATION ###

initialize_session_state()

generate_messages()

if prompt := st.chat_input("Hey, I'm here to help you. Please type in your question."):
    with st.chat_message("human", avatar=user_avatar_path):
        st.write(prompt)

    with st.spinner("Thinking..."):
        # try:
        # Get the last two messages (= 1 question and answer pair) to use as history for generating new answers
        chat_history = st.session_state.messages[-2:]
        full_response, relevant_docs, reranked_docs, confidence = st.session_state.conversation.run(prompt,
                                                                                                    chat_history)
        image_urls = extract_image_urls(full_response)
        llm_image = ""
        for url in image_urls:
            llm_image = url
            full_response = full_response.replace(url, "")

        st.session_state.messages.append(
            Message(origin="human", message=prompt,
                    avatar=user_avatar_path,
                    out_of_scope=True if relevant_docs and relevant_docs[0] == "none" else False))
        st.session_state.messages.append(
            Message(origin="ai", message=full_response,
                    avatar=ai_avatar_path, image=llm_image,
                    out_of_scope=True if relevant_docs and relevant_docs[0] == "none" else False,
                    context=reranked_docs, confidence=confidence)
        )

        print(confidence)

        with st.chat_message("ai", avatar=ai_avatar_path):
            typing_placeholder = st.empty()
            typing_accumulator = ""
            for char in full_response:
                typing_accumulator += char
                typing_placeholder.markdown(typing_accumulator)
                time.sleep(0.003)

            if llm_image != "":
                st.image(llm_image, use_column_width=True)

            detected_lang = detect_language(typing_accumulator)
            audio_fp = text_to_speech(typing_accumulator, detected_lang)

            if relevant_docs and relevant_docs[0] == "none":
                if detected_lang == "en":
                    st.warning(
                        'No suitable information could be found for your question, so the answer may not be correct. Please ask another question or try to be more specific.',
                        icon="⚠️")
                else:
                    st.warning(
                        'Zu deiner Frage konnten keine passenden Informationen gefunden werden, weshalb die gegebene Antwort möglicherweise nicht korrekt ist. Bitte stelle eine andere Frage oder versuche sie genauer zu formulieren.',
                        icon="⚠️")

            st.session_state.audio_bytes = audio_fp.read()
        # except Exception as e:
        #    st.error(f"An unknown error occurred. Please reload the page and try again.", icon="❗")

try:
    if st.session_state and st.session_state.audio_bytes:
        if st.button('🔊'):
            st.session_state.audio_visible = not st.session_state.audio_visible
            if st.session_state.audio_visible:
                st.rerun()

    if st.session_state and st.session_state.audio_visible and st.session_state.audio_bytes:
        audio_data = st.session_state.audio_bytes
        audio_base64 = base64.b64encode(audio_data).decode()
        audio_html = f"""
        <audio id="custom-audio-player" controls autoplay class="audio_player_widget">
            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
        </audio>
        """
        st.markdown(audio_html, unsafe_allow_html=True)
except Exception as e:
    st.error(f"An unknown error occurred. Please reload the page and try again.", icon="❗")

