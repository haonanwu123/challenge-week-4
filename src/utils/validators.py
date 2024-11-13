# Input validation functions
import streamlit as st
import re
from services.groq_service import validate_topic


def get_valid_custom_topic():
    """Get and validate topic input from user"""
    topic = st.text_input("Enter your quiz topic:")

    if topic:
        # Basic preprocessing
        topic = topic.strip()

        # Basic client-side validation
        if len(topic) < 2:
            st.error("Topic must be at least 2 characters long.")
            return None

        if re.match(r'^[0-9\W]+$', topic):  # Only numbers or special characters
            st.error("Topic cannot be just numbers or special characters.")
            return None

        is_valid, message = validate_topic(topic)

        if is_valid:
            return topic
        else:
            st.error(message)
            return None