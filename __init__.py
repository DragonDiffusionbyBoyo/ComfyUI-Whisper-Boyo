from .apply_whisper import ApplyWhisperNode
from .add_subtitles_to_frames import AddSubtitlesToFramesNode
from .add_subtitles_to_background import AddSubtitlesToBackgroundNode
from .resize_cropped_subtitles import ResizeCroppedSubtitlesNode
from .save_srt import SaveSRTNode

# Boyo's enhanced nodes
from .add_subtitles_backend import AddSubtitlesBackendNode
from .add_subtitles_lite import AddSubtitlesLiteNode

NODE_CLASS_MAPPINGS = { 
    # Original nodes
    "Apply Whisper" : ApplyWhisperNode,
    "Add Subtitles To Frames": AddSubtitlesToFramesNode,
    "Add Subtitles To Background": AddSubtitlesToBackgroundNode,
    "Resize Cropped Subtitles": ResizeCroppedSubtitlesNode,
    "Save SRT": SaveSRTNode,
    
    # Boyo's enhanced nodes - prefixed for easy discovery
    "BoyoSubtitlesBackend": AddSubtitlesBackendNode,
    "BoyoSubtitlesLite": AddSubtitlesLiteNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
     # Original nodes
     "Apply Whisper" : "Apply Whisper", 
     "Add Subtitles To Frames": "Add Subtitles To Frames",
     "Add Subtitles To Background": "Add Subtitles To Background",
     "Resize Cropped Subtitles": "Resize Cropped Subtitles",
     "Save SRT": "Save SRT",
     
     # Boyo's nodes - clear labeling
     "BoyoSubtitlesBackend": "Boyo Subtitles (Backend)",
     "BoyoSubtitlesLite": "Boyo Subtitles (Lite)",
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
