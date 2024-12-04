import pytest
from unittest.mock import patch, MagicMock
from services.audio_service import AudioService, AUDIO_PATHS


@pytest.fixture
def mock_mixer():
    """Fixture to patch pygame mixer"""
    with patch('services.audio_service.mixer') as mock_mixer:
        yield mock_mixer


def test_audio_service_initialization(mock_mixer):
    """Test that AudioService correctly initializes mixer"""
    audio_service = AudioService()
    mock_mixer.init.assert_called_once()


def test_load_sounds(mock_mixer):
    """Test that _load_sounds method loads all sounds from AUDIO_PATHS"""
    # Create a mock Sound object that can be compared
    mock_sound = MagicMock()
    mock_mixer.Sound.return_value = mock_sound

    # Create AudioService which will call _load_sounds
    audio_service = AudioService()

    # Verify mixer.Sound was called for each path
    assert len(audio_service.sounds) == len(AUDIO_PATHS)

    # Check that each sound in AUDIO_PATHS was loaded
    for name, path in AUDIO_PATHS.items():
        assert name in audio_service.sounds
        mock_mixer.Sound.assert_any_call(path)


def test_play_sound_existing(mock_mixer):
    """Test playing an existing sound"""
    # Create a mock Sound object
    mock_sound = MagicMock()
    mock_mixer.Sound.return_value = mock_sound

    # Create AudioService
    audio_service = AudioService()
    sound_name = 'play'

    # Play the sound
    audio_service.play_sound(sound_name)

    # Verify the specific sound was played
    audio_service.sounds[sound_name].play.assert_called_once()


def test_play_sound_nonexistent(mock_mixer):
    """Test playing a non-existent sound does not raise an error"""
    # Create AudioService
    audio_service = AudioService()

    # Attempt to play non-existent sound
    audio_service.play_sound('nonexistent_sound')
    # Should not raise any exceptions


@pytest.mark.parametrize("sound_name", list(AUDIO_PATHS.keys()))
def test_all_sounds_playable(mock_mixer, sound_name):
    """Verify that all sounds in AUDIO_PATHS can be played without error"""
    # Create a mock Sound object
    mock_sound = MagicMock()
    mock_mixer.Sound.return_value = mock_sound

    # Create AudioService
    audio_service = AudioService()

    try:
        audio_service.play_sound(sound_name)
    except Exception as e:
        pytest.fail(f"Sound {sound_name} could not be played: {e}")