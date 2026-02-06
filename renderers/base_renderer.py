from abc import ABC, abstractmethod

class BaseRenderer(ABC):
    """
    Abstract base class for subtitle renderers.
    
    All renderers must implement the render() method which processes
    a video file and adds subtitles based on alignment data.
    """
    
    @abstractmethod
    def render(self, video_path, alignment, style_config, output_path, fps):
        """
        Render subtitles onto video.
        
        Args:
            video_path (str): Path to input video file
            alignment (list): List of subtitle alignment objects with 'start', 'end', 'value'
            style_config (dict): Styling configuration (fonts, colors, positions, etc.)
            output_path (str): Path for output video
            fps (float): Frames per second of the video
            
        Returns:
            dict: Processing results with status and metadata
        """
        pass
    
    def validate_inputs(self, video_path, alignment, style_config, output_path):
        """Validate input parameters before processing."""
        import os
        
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        if not alignment or len(alignment) == 0:
            raise ValueError("Alignment data is empty")
        
        if not style_config:
            raise ValueError("Style configuration is required")
        
        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        return True
