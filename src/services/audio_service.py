# Audio handling functions
from pygame import mixer
from src.config import AUDIO_PATHS


class AudioService:
    def __init__(self):
        mixer.init()
        self.sounds = {}
        self._load_sounds()


    def _load_sounds(self):
        """Load all sound files into memory"""
        for name, path in AUDIO_PATHS.items():
            self.sounds[name] = mixer.Sound(path)


    def play_sound(self, sound_name: str):
        """Play a sound by its name"""
        if sound_name in self.sounds:
            self.sounds[sound_name].play()


# Create a singleton instance
audio = AudioService()