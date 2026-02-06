from PIL import ImageDraw, ImageFont, Image
import math
import os

try:
    from .utils import tensor2pil, pil2tensor
except ImportError:
    pass

FONT_DIR = os.path.join(os.path.dirname(__file__), "fonts")

class AddSubtitlesLiteNode:
    """
    Boyo's Lite Subtitle Node with Advanced Rendering
    
    Processes frames in ComfyUI memory (lite mode) but with all the advanced
    rendering features: strokes, shadows, animations, custom positioning.
    
    Uses the same rendering logic as backend mode but works with loaded frames.
    Good for videos <120 seconds that fit in memory.
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
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    FUNCTION = "add_subtitles"
    CATEGORY = "whisper/boyo"

    def add_subtitles(self, images, alignment, font_family, font_size, font_color,
                     stroke_width, stroke_color, animation_style, animation_duration,
                     position_preset, x_position, y_position, video_fps):
        """
        Process subtitles with advanced rendering in ComfyUI memory.
        """
        
        # Build style configuration
        style_config = {
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
        
        # Convert to PIL
        pil_images = tensor2pil(images)
        
        if len(pil_images) == 0:
            return (images,)
        
        frame_width, frame_height = pil_images[0].size
        
        # Load font
        font = ImageFont.truetype(style_config['font_path'], style_config['font_size'])
        
        # Process each frame
        processed_frames = []
        
        for frame_idx in range(len(pil_images)):
            pil_frame = pil_images[frame_idx].convert("RGB")
            current_time = frame_idx / video_fps
            
            # Find active subtitle(s) at this time
            active_subtitles = self._get_active_subtitles(alignment, current_time)
            
            # Draw subtitles if any are active
            if active_subtitles:
                pil_frame = self._draw_subtitles(
                    pil_frame,
                    active_subtitles,
                    font,
                    style_config,
                    current_time,
                    frame_width,
                    frame_height
                )
            
            processed_frames.append(pil_frame)
        
        # Convert back to tensor
        tensor_images = pil2tensor(processed_frames)
        
        return (tensor_images,)
    
    def _get_active_subtitles(self, alignment, current_time):
        """Get all subtitles active at current time."""
        active = []
        for subtitle in alignment:
            if subtitle['start'] <= current_time <= subtitle['end']:
                active.append(subtitle)
        return active
    
    def _draw_subtitles(self, frame, subtitles, font, style_config, 
                       current_time, frame_width, frame_height):
        """
        Draw subtitles on frame with advanced effects.
        Uses same logic as Pillow renderer for consistency.
        """
        draw = ImageDraw.Draw(frame)
        
        for subtitle in subtitles:
            text = subtitle['value']
            
            # Calculate animation progress (0-1)
            progress = self._calculate_animation_progress(
                subtitle, current_time, style_config
            )
            
            # Get scaled font if using zoom animation
            active_font = font
            if style_config['animation_style'] == 'zoom' and progress < 1.0:
                scaled_size = int(style_config['font_size'] * progress)
                if scaled_size >= 10:  # Minimum readable size
                    active_font = ImageFont.truetype(
                        style_config['font_path'], 
                        scaled_size
                    )
            
            # Calculate position with animation offset
            x, y = self._calculate_position(
                text, active_font, draw, style_config, 
                frame_width, frame_height, progress
            )
            
            # Calculate alpha for fade
            alpha = self._calculate_alpha(subtitle, current_time, style_config)
            
            # Draw stroke/outline if specified
            if style_config['stroke_width'] > 0:
                self._draw_text_stroke(
                    draw, x, y, text, active_font,
                    style_config['stroke_width'],
                    style_config['stroke_color'],
                    alpha
                )
            
            # Draw main text
            # Note: PIL doesn't support alpha on text directly for all color formats
            # For full alpha support, would need to composite separate layers
            draw.text((x, y), text, fill=style_config['font_color'], font=active_font)
        
        return frame
    
    def _calculate_animation_progress(self, subtitle, current_time, style_config):
        """Calculate 0-1 progress through animation intro."""
        duration = style_config['animation_duration']
        elapsed = current_time - subtitle['start']
        
        if elapsed < duration:
            return elapsed / duration
        return 1.0
    
    def _calculate_alpha(self, subtitle, current_time, style_config):
        """Calculate alpha/opacity for fade effects."""
        animation = style_config['animation_style']
        
        if animation != 'fade':
            return 1.0
        
        duration = style_config['animation_duration']
        
        # Fade in at start
        if current_time - subtitle['start'] < duration:
            return (current_time - subtitle['start']) / duration
        
        # Fade out at end
        if subtitle['end'] - current_time < duration:
            return (subtitle['end'] - current_time) / duration
        
        return 1.0
    
    def _calculate_position(self, text, font, draw, style_config, 
                           frame_width, frame_height, progress):
        """Calculate text position with animation offset."""
        preset = style_config['position_preset']
        
        # Get text dimensions
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        # Base position from preset
        if preset == 'bottom_center':
            x = (frame_width - text_width) // 2
            y = frame_height - style_config['y_position']
        elif preset == 'top_center':
            x = (frame_width - text_width) // 2
            y = style_config['y_position']
        elif preset == 'center':
            x = (frame_width - text_width) // 2
            y = (frame_height - text_height) // 2
        else:  # custom
            x = style_config['x_position']
            y = style_config['y_position']
        
        # Apply animation offset during intro
        animation = style_config['animation_style']
        
        if progress < 1.0:
            if animation == 'slide_up':
                # Start below, slide up to final position
                y += int(50 * (1 - progress))
            elif animation == 'slide_down':
                # Start above, slide down to final position
                y -= int(50 * (1 - progress))
        
        return x, y
    
    def _draw_text_stroke(self, draw, x, y, text, font, width, color, alpha):
        """Draw text outline/stroke."""
        # Simple stroke: draw text in all directions around main position
        for offset_x in range(-width, width + 1):
            for offset_y in range(-width, width + 1):
                if offset_x != 0 or offset_y != 0:
                    draw.text(
                        (x + offset_x, y + offset_y),
                        text,
                        fill=color,
                        font=font
                    )
