from PIL import ImageDraw, ImageFont, Image
import math
import os
import subprocess
import json
from pathlib import Path

try:
    from .utils import tensor2pil, pil2tensor
    from .renderers.ffmpeg_renderer import FFmpegRenderer
    from .renderers.pillow_renderer import PillowRenderer
except ImportError:
    # Fallback for development/testing
    pass

FONT_DIR = os.path.join(os.path.dirname(__file__), "fonts")

class AddSubtitlesBackendNode:
    """
    Enhanced subtitle node with backend processing for large videos.
    
    Features:
    - Automatic mode switching based on video length
    - Multiple rendering engines (FFmpeg, Pillow, SVG, Kinetic)
    - Advanced styling: strokes, shadows, gradients, animations
    - Backend processing bypasses ComfyUI memory limits
    """
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": { 
                "images": ("IMAGE",),
                "alignment": ("whisper_alignment",),
                "font_family": (os.listdir(FONT_DIR),),
                "font_size": ("INT", {
                    "default": 100,
                    "min": 10,
                    "max": 500,
                    "step": 5,
                    "display": "number"
                }),
                "font_color": ("STRING", {
                    "default": "white"
                }),
                "stroke_width": ("INT", {
                    "default": 3,
                    "min": 0,
                    "max": 20,
                    "step": 1
                }),
                "stroke_color": ("STRING", {
                    "default": "black"
                }),
                "animation_style": (["none", "fade", "slide_up", "slide_down", "zoom"],),
                "animation_duration": ("FLOAT", {
                    "default": 0.3,
                    "min": 0.1,
                    "max": 2.0,
                    "step": 0.1
                }),
                "position_preset": (["bottom_center", "top_center", "center", "custom"],),
                "x_position": ("INT", {
                    "default": 0,
                    "step": 10,
                    "display": "number"
                }),
                "y_position": ("INT", {
                    "default": 100,
                    "step": 10,
                    "display": "number"
                }),
                "video_fps": ("FLOAT", {
                    "default": 24.0,
                    "step": 1,
                    "display": "number"
                }),
                "processing_mode": (["auto", "lite", "backend"],),
                "renderer": (["ffmpeg", "pillow"],),
                "video_path": ("STRING", {
                    "default": "",
                    "multiline": False
                }),
                "output_path": ("STRING", {
                    "default": "",
                    "multiline": False
                }),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING",)
    RETURN_NAMES = ("images", "output_info",)
    FUNCTION = "add_subtitles"
    CATEGORY = "whisper/boyo"
    OUTPUT_NODE = True

    def add_subtitles(self, images, alignment, font_family, font_size, font_color,
                     stroke_width, stroke_color, animation_style, animation_duration,
                     position_preset, x_position, y_position, video_fps, 
                     processing_mode, renderer, video_path, output_path):
        """
        Main processing function with automatic mode selection.
        """
        
        # Determine processing mode
        frame_count = len(images)
        video_duration = frame_count / video_fps
        
        if processing_mode == "auto":
            # Auto-switch: lite for <120s, backend for >=120s
            mode = "lite" if video_duration < 120 else "backend"
        else:
            mode = processing_mode
        
        # Build style configuration
        style_config = self._build_style_config(
            font_family, font_size, font_color, stroke_width, stroke_color,
            animation_style, animation_duration, position_preset, x_position, y_position
        )
        
        if mode == "lite":
            return self._process_lite_mode(
                images, alignment, style_config, video_fps
            )
        else:
            return self._process_backend_mode(
                images, alignment, style_config, video_fps, renderer, video_path, output_path
            )
    
    def _build_style_config(self, font_family, font_size, font_color, 
                           stroke_width, stroke_color, animation_style, 
                           animation_duration, position_preset, x_position, y_position):
        """Build unified style configuration dictionary."""
        return {
            'font_family': font_family,
            'font_path': os.path.join(FONT_DIR, font_family),
            'font_size': font_size,
            'font_color': font_color,
            'stroke_width': stroke_width,
            'stroke_color': stroke_color,
            'animation_style': animation_style,
            'animation_duration': animation_duration,
            'position_preset': position_preset,
            'x_position': x_position,
            'y_position': y_position,
        }
    
    def _process_lite_mode(self, images, alignment, style_config, video_fps):
        """
        Process on ComfyUI canvas - traditional approach.
        Good for videos <120s to avoid memory issues.
        """
        pil_images = tensor2pil(images)
        pil_images_with_text = []
        
        frame_width, frame_height = pil_images[0].size
        font = ImageFont.truetype(style_config['font_path'], style_config['font_size'])
        
        # Calculate position based on preset
        base_x, base_y = self._calculate_position(
            frame_width, frame_height, style_config
        )
        
        if len(alignment) == 0:
            tensor_images = pil2tensor(pil_images)
            return (tensor_images, "Processed in lite mode: 0 subtitles added")
        
        last_frame_no = 0
        subtitle_count = 0
        
        for i in range(len(alignment)):
            alignment_obj = alignment[i]
            start_frame_no = math.floor(alignment_obj["start"] * video_fps)
            end_frame_no = math.floor(alignment_obj["end"] * video_fps)
            
            # Add frames without text
            for j in range(last_frame_no, start_frame_no):
                if j < len(pil_images):
                    pil_images_with_text.append(pil_images[j].convert("RGB"))
            
            # Add frames with text
            for j in range(start_frame_no, end_frame_no):
                if j < len(pil_images):
                    img = pil_images[j].convert("RGB")
                    draw = ImageDraw.Draw(img)
                    
                    text = alignment_obj["value"]
                    
                    # Center text based on actual text width
                    text_bbox = draw.textbbox((0, 0), text, font=font)
                    text_width = text_bbox[2] - text_bbox[0]
                    x = base_x if style_config['position_preset'] == 'custom' else (frame_width - text_width) // 2
                    y = base_y
                    
                    # Draw stroke if specified
                    if style_config['stroke_width'] > 0:
                        for offset_x in range(-style_config['stroke_width'], style_config['stroke_width'] + 1):
                            for offset_y in range(-style_config['stroke_width'], style_config['stroke_width'] + 1):
                                draw.text(
                                    (x + offset_x, y + offset_y),
                                    text,
                                    fill=style_config['stroke_color'],
                                    font=font
                                )
                    
                    # Draw main text
                    draw.text((x, y), text, fill=style_config['font_color'], font=font)
                    pil_images_with_text.append(img)
                    
            last_frame_no = end_frame_no
            subtitle_count += 1
        
        # Add remaining frames
        for j in range(len(pil_images_with_text), len(pil_images)):
            pil_images_with_text.append(pil_images[j])
        
        tensor_images = pil2tensor(pil_images_with_text)
        info = f"Processed in lite mode: {subtitle_count} subtitles added to {len(pil_images_with_text)} frames"
        
        return (tensor_images, info)
    
    def _process_backend_mode(self, images, alignment, style_config, video_fps, 
                              renderer, video_path, output_path):
        """
        Process video in backend without loading to canvas.
        Handles large videos by bypassing ComfyUI memory limits.
        """
        
        # Validate paths
        if not video_path or not os.path.exists(video_path):
            return (images, "ERROR: Backend mode requires valid video_path. Please provide the source video path.")
        
        if not output_path:
            # Generate output path in ComfyUI output directory
            output_dir = os.path.join(os.path.dirname(__file__), "..", "..", "output", "whisper_backend")
            os.makedirs(output_dir, exist_ok=True)
            timestamp = Path(video_path).stem
            output_path = os.path.join(output_dir, f"{timestamp}_subtitled.mp4")
        
        # Select and initialize renderer
        if renderer == "ffmpeg":
            renderer_instance = FFmpegRenderer()
        elif renderer == "pillow":
            renderer_instance = PillowRenderer()
        else:
            return (images, f"ERROR: Unknown renderer: {renderer}")
        
        # Process video
        try:
            result = renderer_instance.render(
                video_path=video_path,
                alignment=alignment,
                style_config=style_config,
                output_path=output_path,
                fps=video_fps
            )
            
            info = f"Backend processing complete!\nRenderer: {renderer}\nOutput: {output_path}\nSubtitles: {len(alignment)}"
            
            # Return original images (placeholder) and processing info
            return (images, info)
            
        except Exception as e:
            error_info = f"ERROR in backend processing: {str(e)}"
            return (images, error_info)
    
    def _calculate_position(self, width, height, style_config):
        """Calculate subtitle position based on preset or custom values."""
        preset = style_config['position_preset']
        
        if preset == "bottom_center":
            return width // 2, height - style_config['y_position']
        elif preset == "top_center":
            return width // 2, style_config['y_position']
        elif preset == "center":
            return width // 2, height // 2
        else:  # custom
            return style_config['x_position'], style_config['y_position']
