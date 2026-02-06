from .apply_whisper import ApplyWhisperNode
from .add_subtitles_to_frames import AddSubtitlesToFramesNode
from .add_subtitles_to_background import AddSubtitlesToBackgroundNode
from .resize_cropped_subtitles import ResizeCroppedSubtitlesNode
from .save_srt import SaveSRTNode

# Boyo's enhanced backend processing node
from .add_subtitles_backend import AddSubtitlesBackendNode

NODE_CLASS_MAPPINGS = { 
    # Original nodes
    "Apply Whisper" : ApplyWhisperNode,
    "Add Subtitles To Frames": AddSubtitlesToFramesNode,
    "Add Subtitles To Background": AddSubtitlesToBackgroundNode,
    "Resize Cropped Subtitles": ResizeCroppedSubtitlesNode,
    "Save SRT": SaveSRTNode,
    
    # Enhanced backend node
    "Add Subtitles Backend": AddSubtitlesBackendNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
     # Original nodes
     "Apply Whisper" : "Apply Whisper", 
     "Add Subtitles To Frames": "Add Subtitles To Frames",
     "Add Subtitles To Background": "Add Subtitles To Background",
     "Resize Cropped Subtitles": "Resize Cropped Subtitles",
     "Save SRT": "Save SRT",
     
     # Enhanced node
     "Add Subtitles Backend": "Add Subtitles (Backend Mode)",
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
