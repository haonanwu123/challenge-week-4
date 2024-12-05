import pytest
import streamlit as st
from unittest.mock import patch

# Import the SessionState class from your actual module
from models.session import SessionState


@pytest.fixture
def mock_streamlit_session():
    """Fixture to reset Streamlit session state before each test"""
    st.session_state.clear()
    yield st.session_state


@pytest.fixture
def mock_generate_functions():
    """Fixture to mock external generate functions"""
    with patch('models.session.generate_topics') as mock_topics, \
            patch('models.session.generate_questions') as mock_questions:
        mock_topics.return_value = ['Topic1', 'Topic2', 'Topic3']
        mock_questions.return_value = [
            {'question': 'Q1', 'options': ['A', 'B', 'C'], 'correct_answer': 'A'},
            {'question': 'Q2', 'options': ['X', 'Y', 'Z'], 'correct_answer': 'Y'}
        ]
        yield mock_topics, mock_questions


def test_initialize_sets_default_session_state(mock_streamlit_session, mock_generate_functions):
    """Test that initialize() sets all expected session state variables"""
    SessionState.initialize()

    # Check that all expected keys are set
    expected_keys = [
        'running', 'topic', 'num_topics', 'topics', 'custom_topic',
        'current_question_idx', 'user_answers', 'correctness',
        'explanations', 'is_sound_played', 'selected_options'
    ]

    for key in expected_keys:
        assert key in st.session_state, f"{key} not initialized"

    # Validate specific default values
    assert st.session_state.running is False
    assert st.session_state.topic is None
    assert st.session_state.custom_topic is False
    assert st.session_state.current_question_idx == 0
    assert len(st.session_state.user_answers) == 0
    assert len(st.session_state.correctness) == 0
    assert isinstance(st.session_state.num_topics, int)
    assert 3 <= st.session_state.num_topics <= 30


def test_initialize_uses_random_num_topics(mock_streamlit_session):
    """Test that num_topics is randomly selected from predefined segments"""
    valid_segments = [3, 4, 5, 6, 8, 9, 10, 12, 15, 18, 20, 24, 30]

    SessionState.initialize()

    assert st.session_state.num_topics in valid_segments


def test_start_game(mock_streamlit_session, mock_generate_functions):
    """Test start_game() method sets questions and start time"""
    # Simulate having a topic set
    st.session_state.topic = 'Test Topic'

    SessionState.start_game()

    assert 'questions' in st.session_state
    assert isinstance(st.session_state.questions, list)
    assert 'start_time' in st.session_state
    assert isinstance(st.session_state.start_time, float)


def test_reset(mock_streamlit_session):
    """Test reset() method clears all session state"""
    # Populate session state with some dummy data
    st.session_state.test_key = 'test_value'
    st.session_state.another_key = 123

    SessionState.reset()

    # Verify session state is completely cleared
    assert len(st.session_state.keys()) == 0


def test_initialize_handles_repeated_calls(mock_streamlit_session, mock_generate_functions):
    """Test that repeated calls to initialize() don't cause errors"""
    SessionState.initialize()
    first_num_topics = st.session_state.num_topics
    first_topics = st.session_state.topics

    # Call initialize again
    SessionState.initialize()

    # Verify state remains consistent
    assert st.session_state.num_topics == first_num_topics
    assert st.session_state.topics == first_topics