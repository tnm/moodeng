class MoodengError(Exception):
    """Base exception for all moodeng errors"""
    pass

class ConfigurationError(MoodengError):
    """Raised when there's an error in configuration"""
    pass

class AlerterError(MoodengError):
    """Raised when there's an error with an alerter"""
    pass

class VideoError(MoodengError):
    """Raised when there's an error with video processing"""
    pass

class ModelError(MoodengError):
    """Raised when there's an error with the ML model"""
    pass