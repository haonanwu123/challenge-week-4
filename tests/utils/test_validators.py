import pytest
import streamlit as st
from unittest.mock import patch
from utils.validators import get_valid_custom_topic


@pytest.fixture
def mock_text_input(monkeypatch):
    """Fixture to mock streamlit's text_input"""

    def _mock_text_input(label, value=''):
        return value

    monkeypatch.setattr(st, 'text_input', _mock_text_input)


@pytest.fixture
def mock_st_error(monkeypatch):
    """Fixture to mock streamlit's error method"""
    errors = []

    def _mock_error(message):
        errors.append(message)

    monkeypatch.setattr(st, 'error', _mock_error)
    return errors


def test_topic_validation(mock_text_input, mock_st_error):
    """Comprehensive test cases for topic validation"""
    test_cases = [
        # (input, expected_result, expected_error)
        ('Python Programming', 'Python Programming', None),
        ('  Machine Learning  ', 'Machine Learning', None),
        ('A', None, 'Topic must be at least 2 characters long'),
        ('123', None, 'Topic cannot be just numbers or special characters'),
        ('!!!', None, 'Topic cannot be just numbers or special characters'),
    ]

    for input_topic, expected_result, expected_error in test_cases:
        # Reset mocks for each test case
        mock_st_error.clear()

        with patch('streamlit.text_input', return_value=input_topic):
            result = get_valid_custom_topic()

            assert result == expected_result

            if expected_error:
                assert len(mock_st_error) > 0
                assert expected_error in mock_st_error[0]
            else:
                assert len(mock_st_error) == 0


def test_server_validation_failure(mock_text_input, mock_st_error):
    """Test topic that fails server-side validation"""
    with patch('streamlit.text_input', return_value='Although'):
        result = get_valid_custom_topic()
        assert result is None
        assert len(mock_st_error) > 0
        assert "Please enter a real topic" in mock_st_error[0]