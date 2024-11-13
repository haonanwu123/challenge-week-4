# Session state management
import streamlit as st
import random
import time
from src.services.groq_service import generate_questions, generate_topics

class SessionState:
    @staticmethod
    def initialize():
        """Initialize all session state variables"""
        if "running" not in st.session_state:
            st.session_state.running = False
        if "topic" not in st.session_state:
            st.session_state.topic = None
        if "num_topics" not in st.session_state:
            # Wheel properties
            num_segments = [3, 4, 5, 6, 8, 9, 10, 12, 15, 18, 20, 24, 30]
            st.session_state.num_topics = random.choice(num_segments)
        if "topics" not in st.session_state:
            st.session_state.topics = generate_topics(st.session_state.num_topics)
        if "custom_topic" not in st.session_state:
            st.session_state.custom_topic = False
        if "current_question_idx" not in st.session_state:
            st.session_state.current_question_idx = 0
        if "user_answers" not in st.session_state:
            st.session_state.user_answers = []
        if "correctness" not in st.session_state:
            st.session_state.correctness = []
        if "explanations" not in st.session_state:
            st.session_state.explanations = {}
        if "is_sound_played" not in st.session_state:
            st.session_state.is_sound_played = [False] * 5
        if "selected_options" not in st.session_state:
            st.session_state.selected_options = [None] * 5


    @staticmethod
    def start_game():
        if "questions" not in st.session_state:
            st.session_state.questions = generate_questions(st.session_state.topic)
            st.session_state.start_time = time.time()