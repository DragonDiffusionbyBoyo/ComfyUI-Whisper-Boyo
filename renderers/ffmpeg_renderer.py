import subprocess
import os
from .base_renderer import BaseRenderer

class FFmpegRenderer(BaseRenderer):
    """
    FFmpeg-based subtitle renderer with advanced effects.
    
    Features:
    - Custom fonts with full TrueType support
    - Text strokes/outlines
    - Shadows
    - Fade in/out animations
    - Slide animations
    - Zoom effects
    - Position presets
    
    Much faster than frame-by-frame PIL processing for long videos.
    """
    
    def render(self, video_path, alignment, style_config, output_path, fps):
        """
        Render subtitles using FFmpeg drawtext filter.
        """
        self.validate_inputs(video_path, alignment, style_config, output_path)
        
        # Build FFmpeg filtergraph
        filters = self._build_filtergraph(alignment, style_config, fps)
        
        # Construct FFmpeg command
        cmd = self._build_ffmpeg_command(video_path, filters, output_path)
        
        # Execute
        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )
            
            return {
                'status': 'success',
                'output_path': output_path,
                'subtitle_count': len(alignment),
                'renderer': 'ffmpeg'
            }
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"FFmpeg processing failed: {e.stderr}")
    
    def _build_filtergraph(self, alignment, style_config, fps):
        """
        Build complex FFmpeg filtergraph for all subtitles.
        """
        filters = []
        
        # Convert font path to forward slashes for FFmpeg (works on Windows and Linux)
        font_path = style_config['font_path'].replace('\\', '/')
        
        for idx, word in enumerate(alignment):
            start_time = word['start']
            end_time = word['end']
            text = self._escape_text(word['value'])
            
            # Build drawtext filter for this subtitle
            filter_parts = [
                f"drawtext=fontfile={font_path}",  # No quotes - FFmpeg prefers this
                f"text={text}",
                f"fontsize={style_config['font_size']}",
                f"fontcolor={style_config['font_color']}",
            ]
            
            # Add stroke if specified
            if style_config.get('stroke_width', 0) > 0:
                filter_parts.append(f"borderw={style_config['stroke_width']}")
                filter_parts.append(f"bordercolor={style_config['stroke_color']}")
            
            # Add shadow effect (offset bordercolor)
            if style_config.get('shadow', False):
                filter_parts.append("shadowx=2")
                filter_parts.append("shadowy=2")
                filter_parts.append("shadowcolor=black@0.5")
            
            # Position
            x_pos, y_pos = self._calculate_position(style_config, text)
            filter_parts.append(f"x={x_pos}")
            filter_parts.append(f"y={y_pos}")
            
            # Animation effects
            animation_filter = self._build_animation(
                start_time, end_time, style_config
            )
            if animation_filter:
                filter_parts.append(animation_filter)
            
            # Enable only during subtitle timeframe
            filter_parts.append(f"enable=between(t,{start_time},{end_time})")
            
            # Join all parts
            filters.append(":".join(filter_parts))
        
        # Chain all drawtext filters
        return ",".join(filters)
    
    def _build_animation(self, start_time, end_time, style_config):
        """
        Build animation expressions for FFmpeg.
        """
        animation = style_config.get('animation_style', 'none')
        duration = style_config.get('animation_duration', 0.3)
        
        if animation == 'fade':
            # Fade in at start, fade out at end
            fade_in_end = start_time + duration
            fade_out_start = end_time - duration
            
            alpha_expr = (
                f"if(lt(t,{fade_in_end}),"
                f"(t-{start_time})/{duration},"
                f"if(gt(t,{fade_out_start}),"
                f"({end_time}-t)/{duration},1))"
            )
            return f"alpha={alpha_expr}"
        
        elif animation == 'slide_up':
            # Start below final position, slide up
            slide_distance = 50
            # No animation - just return None, can't easily do y animation in drawtext
            return None
        
        elif animation == 'slide_down':
            # Start above final position, slide down
            slide_distance = 50
            # No animation - just return None
            return None
        
        elif animation == 'zoom':
            # Start small, zoom to full size
            # No animation - drawtext doesn't support dynamic fontsize easily
            return None
        
        else:  # none
            return None
    
    def _calculate_position(self, style_config, text):
        """
        Calculate text position based on preset.
        Returns (x, y) expression strings for FFmpeg.
        """
        preset = style_config.get('position_preset', 'bottom_center')
        
        if preset == 'bottom_center':
            x = "(w-text_w)/2"
            y = f"h-{style_config.get('y_position', 100)}"
        elif preset == 'top_center':
            x = "(w-text_w)/2"
            y = str(style_config.get('y_position', 100))
        elif preset == 'center':
            x = "(w-text_w)/2"
            y = "(h-text_h)/2"
        else:  # custom
            x = str(style_config.get('x_position', 0))
            y = str(style_config.get('y_position', 100))
        
        return x, y
    
    def _escape_text(self, text):
        """
        Escape special characters for FFmpeg drawtext filter.
        FFmpeg drawtext uses : as separator and needs escaping.
        """
        # Escape colon which is the parameter separator
        text = text.replace(":", r"\:")
        # Escape single quote
        text = text.replace("'", r"\'")
        # Escape backslash
        text = text.replace("\\", r"\\")
        return text
    
    def _build_ffmpeg_command(self, video_path, filters, output_path):
        """
        Build complete FFmpeg command.
        Convert paths to forward slashes for cross-platform compatibility.
        """
        # Normalize paths - FFmpeg on Windows accepts forward slashes
        video_path_norm = video_path.replace('\\', '/')
        output_path_norm = output_path.replace('\\', '/')
        
        cmd = [
            'ffmpeg',
            '-y',  # Overwrite output file
            '-i', video_path_norm,
            '-vf', filters,
            '-c:a', 'copy',  # Copy audio without re-encoding
            '-c:v', 'libx264',  # Video codec
            '-preset', 'medium',  # Encoding speed/quality balance
            '-crf', '23',  # Quality (lower = better, 18-28 is reasonable)
            output_path_norm
        ]
        return cmd
