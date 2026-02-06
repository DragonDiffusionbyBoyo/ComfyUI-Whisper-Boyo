import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import subprocess
import tempfile
import os
from .base_renderer import BaseRenderer

class PillowRenderer(BaseRenderer):
    """
    Pillow-based frame-by-frame subtitle renderer with STREAMING processing.
    
    Memory efficient:
    - Processes one frame at a time
    - Writes frames immediately
    - Never accumulates frames in memory
    - Can handle videos of any length
    
    Perfect for:
    - Long videos (hours)
    - High resolution
    - Complex animations
    - Limited RAM systems
    """
    
    def render(self, video_path, alignment, style_config, output_path, fps):
        """
        Render subtitles frame-by-frame using streaming processing.
        Memory usage: ~1 frame (constant, regardless of video length)
        """
        self.validate_inputs(video_path, alignment, style_config, output_path)
        
        # Open input video
        cap = cv2.VideoCapture(video_path)
        
        # Get video properties
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Prepare font
        font = ImageFont.truetype(style_config['font_path'], style_config['font_size'])
        
        # Create temporary file for video without audio
        temp_video = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        temp_video_path = temp_video.name
        temp_video.close()
        
        # Open video writer - STREAM frames directly
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(
            temp_video_path,
            fourcc,
            fps,
            (frame_width, frame_height)
        )
        
        frame_idx = 0
        
        print(f"Processing {total_frames} frames...")
        
        # STREAMING: Read → Process → Write → Discard
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Progress indicator
            if frame_idx % 100 == 0:
                progress = (frame_idx / total_frames) * 100
                print(f"Progress: {frame_idx}/{total_frames} ({progress:.1f}%)")
            
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_frame = Image.fromarray(frame_rgb)
            
            # Get current time
            current_time = frame_idx / fps
            
            # Find active subtitle(s)
            active_subtitles = self._get_active_subtitles(alignment, current_time)
            
            # Draw subtitles
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
            
            # Convert back to BGR for cv2
            frame_bgr = cv2.cvtColor(np.array(pil_frame), cv2.COLOR_RGB2BGR)
            
            # WRITE IMMEDIATELY - never accumulate
            out.write(frame_bgr)
            
            frame_idx += 1
            
            # Frame is now discarded, memory freed
        
        # Cleanup
        cap.release()
        out.release()
        
        print(f"Processed {frame_idx} frames")
        print(f"Merging audio...")
        
        # Merge audio from original video
        self._merge_audio(video_path, temp_video_path, output_path)
        
        # Clean up temp file
        os.unlink(temp_video_path)
        
        return {
            'status': 'success',
            'output_path': output_path,
            'subtitle_count': len(alignment),
            'frames_processed': frame_idx,
            'renderer': 'pillow'
        }
    
    def _merge_audio(self, input_video, processed_video, output_path):
        """
        Merge audio from original video with processed video.
        """
        try:
            cmd = [
                'ffmpeg',
                '-y',
                '-i', processed_video,  # Video with subtitles
                '-i', input_video,       # Original video with audio
                '-c:v', 'copy',          # Copy video (already encoded)
                '-c:a', 'aac',           # Encode audio to AAC
                '-map', '0:v:0',         # Video from first input
                '-map', '1:a:0?',        # Audio from second input (? means optional)
                '-shortest',             # Match shortest stream
                output_path
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            # If audio merge fails, just copy video without audio
            print(f"Warning: Audio merge failed, output will have no audio")
            import shutil
            shutil.copy(processed_video, output_path)
    
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
        Draw subtitles on frame with effects.
        """
        draw = ImageDraw.Draw(frame)
        
        for subtitle in subtitles:
            text = subtitle['value']
            
            # Calculate animation progress
            progress = self._calculate_animation_progress(
                subtitle, current_time, style_config
            )
            
            # Calculate position
            x, y = self._calculate_position(
                text, font, draw, style_config, 
                frame_width, frame_height, progress
            )
            
            # Apply animation effects
            current_font = font
            if style_config.get('animation_style') == 'zoom':
                # Scale font size
                scaled_size = int(style_config['font_size'] * progress)
                current_font = ImageFont.truetype(
                    style_config['font_path'], 
                    max(10, scaled_size)
                )
            
            # Calculate alpha for fade
            alpha = self._calculate_alpha(subtitle, current_time, style_config)
            
            # Draw stroke
            if style_config.get('stroke_width', 0) > 0:
                self._draw_text_stroke(
                    draw, x, y, text, current_font,
                    style_config['stroke_width'],
                    style_config['stroke_color'],
                    alpha
                )
            
            # Draw main text
            color = self._apply_alpha(style_config['font_color'], alpha)
            draw.text((x, y), text, fill=color, font=current_font)
        
        return frame
    
    def _calculate_animation_progress(self, subtitle, current_time, style_config):
        """Calculate 0-1 progress through animation."""
        duration = style_config.get('animation_duration', 0.3)
        elapsed = current_time - subtitle['start']
        
        if elapsed < duration:
            return elapsed / duration
        return 1.0
    
    def _calculate_alpha(self, subtitle, current_time, style_config):
        """Calculate alpha/opacity for fade effects."""
        animation = style_config.get('animation_style', 'none')
        
        if animation != 'fade':
            return 1.0
        
        duration = style_config.get('animation_duration', 0.3)
        
        # Fade in
        if current_time - subtitle['start'] < duration:
            return (current_time - subtitle['start']) / duration
        
        # Fade out
        if subtitle['end'] - current_time < duration:
            return (subtitle['end'] - current_time) / duration
        
        return 1.0
    
    def _calculate_position(self, text, font, draw, style_config, 
                           frame_width, frame_height, progress):
        """Calculate text position with animation offset."""
        preset = style_config.get('position_preset', 'bottom_center')
        
        # Get text dimensions
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        # Base position
        if preset == 'bottom_center':
            x = (frame_width - text_width) // 2
            y = frame_height - style_config.get('y_position', 100)
        elif preset == 'top_center':
            x = (frame_width - text_width) // 2
            y = style_config.get('y_position', 100)
        elif preset == 'center':
            x = (frame_width - text_width) // 2
            y = (frame_height - text_height) // 2
        else:  # custom
            x = style_config.get('x_position', 0)
            y = style_config.get('y_position', 100)
        
        # Apply animation offset
        animation = style_config.get('animation_style', 'none')
        
        if animation == 'slide_up' and progress < 1.0:
            y += int(50 * (1 - progress))
        elif animation == 'slide_down' and progress < 1.0:
            y -= int(50 * (1 - progress))
        
        return x, y
    
    def _draw_text_stroke(self, draw, x, y, text, font, width, color, alpha):
        """Draw text outline/stroke."""
        stroke_color = self._apply_alpha(color, alpha)
        
        for offset_x in range(-width, width + 1):
            for offset_y in range(-width, width + 1):
                if offset_x != 0 or offset_y != 0:
                    draw.text(
                        (x + offset_x, y + offset_y),
                        text,
                        fill=stroke_color,
                        font=font
                    )
    
    def _apply_alpha(self, color, alpha):
        """Apply alpha to color string."""
        # For now, just return the color
        # Full alpha support would require RGBA mode
        return color
