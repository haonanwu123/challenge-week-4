import pytest
from unittest.mock import Mock, patch
import plotly.graph_objects as go
import streamlit as st
from utils.spinning_wheel import SpinningWheel


# Fixture to mock Streamlit
@pytest.fixture
def mock_streamlit(monkeypatch):
    mock_empty = Mock()
    mock_empty.plotly_chart = Mock()
    monkeypatch.setattr(st, 'empty', lambda: mock_empty)
    return mock_empty


@pytest.mark.parametrize("num_topics", [3, 5, 6])
def test_initialize_wheel(mock_streamlit, num_topics):
    """Test initializing the wheel with different numbers of topics."""
    wheel = SpinningWheel()
    assert wheel.plot_placeholder is None

    # Call the method
    frames, final_angle = wheel.initialize_wheel(
        [f'Topic {i + 1}' for i in range(num_topics)],
        num_topics
    )

    # Assertions
    assert len(frames) == 100
    assert 1080 <= final_angle <= 2160

    # Verify Streamlit plotly_chart was called
    mock_streamlit.plotly_chart.assert_called_once()


def test_create_frames_and_plot():
    """Test the create_frames_and_plot method."""
    wheel = SpinningWheel()

    # Prepare test data
    values = ['Topic 1', 'Topic 2', 'Topic 3', 'Topic 4']
    num_segments = 4

    # Call the method
    fig, frames, max_rotation_angle = wheel.create_frames_and_plot(values, num_segments)

    # Assertions
    assert isinstance(fig, go.Figure)
    assert len(frames) == 100  # total_frames in the original method

    # Check the first and last frame
    assert isinstance(frames[0], go.Frame)
    assert isinstance(frames[-1], go.Frame)

    # Verify rotation angle is within expected range
    assert 1080 <= max_rotation_angle <= 2160


def test_add_pointer_to_figure():
    """Test adding a pointer to the figure."""
    wheel = SpinningWheel()

    # Create a basic figure
    fig = go.Figure()

    # Add pointer
    wheel.add_pointer_to_figure(fig)

    # Check annotations
    assert len(fig.layout.annotations) == 1
    annotation = fig.layout.annotations[0]

    # Verify annotation properties
    assert annotation.x == 0.5
    assert annotation.y == 1.03
    assert annotation.text == "▼"


def test_animate_spin():
    """Test the animate_spin method."""
    wheel = SpinningWheel()

    # Prepare test data
    topics = ['Topic 1', 'Topic 2', 'Topic 3', 'Topic 4']
    fig, frames, _ = wheel.create_frames_and_plot(topics, 4)

    # Mock the plot_placeholder and time.sleep
    with patch.object(wheel, 'plot_placeholder', Mock()) as mock_placeholder, \
            patch('time.sleep', Mock()) as mock_sleep:
        # Call animate_spin
        wheel.animate_spin(frames)

        # Verify plotly_chart was called for each frame
        assert mock_placeholder.plotly_chart.call_count == len(frames)

        # Verify time.sleep was called for each frame
        assert mock_sleep.call_count == len(frames)