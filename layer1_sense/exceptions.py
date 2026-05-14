class PRISMSenseError(Exception):
    """Base exception for PRISM SENSE module"""
    pass

class FaceNotDetectedError(PRISMSenseError):
    """Raised when MediaPipe fails to detect a face in the frame"""
    pass

class InsufficientDataError(PRISMSenseError):
    """Raised when the input video/audio is shorter than the required minimum duration"""
    pass

class AudioQualityError(PRISMSenseError):
    """Raised when background noise or signal quality is too poor for analysis"""
    pass

class ModelNotLoadedError(PRISMSenseError):
    """Raised when an inference call is made before models are initialized"""
    pass

class ConfigurationError(PRISMSenseError):
    """Raised when the config file is missing or contains invalid values"""
    pass
