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
        
        for idx, word in enumerate(alignment):
            start_time = word['start']
            end_time = word['end']
            text = self._escape_text(word['value'])
            
            # Build drawtext filter for this subtitle
            filter_parts = [
                f"drawtext=fontfile='{style_config['font_path']}'",
                f"text='{text}'",
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
            filter_parts.append(animation_filter)
            
            # Enable only during subtitle timeframe
            filter_parts.append(f"enable='between(t,{start_time},{end_time})'")
            
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
            
            alpha = (
                f"alpha='if(lt(t,{fade_in_end}),"
                f"(t-{start_time})/{duration},"
                f"if(gt(t,{fade_out_start}),"
                f"({end_time}-t)/{duration},1))'"
            )
            return alpha
        
        elif animation == 'slide_up':
            # Start below final position, slide up
            slide_distance = 50
            y_expr = (
                f"y='if(lt(t,{start_time + duration}),"
                f"y+{slide_distance}*(1-(t-{start_time})/{duration}),y)'"
            )
            return y_expr
        
        elif animation == 'slide_down':
            # Start above final position, slide down
            slide_distance = 50
            y_expr = (
                f"y='if(lt(t,{start_time + duration}),"
                f"y-{slide_distance}*(1-(t-{start_time})/{duration}),y)'"
            )
            return y_expr
        
        elif animation == 'zoom':
            # Start small, zoom to full size
            zoom_expr = (
                f"fontsize='if(lt(t,{start_time + duration}),"
                f"{style_config['font_size']}*(t-{start_time})/{duration},"
                f"{style_config['font_size']})'"
            )
            return zoom_expr
        
        else:  # none
            return "alpha=1"
    
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
        """
        # FFmpeg drawtext requires escaping: : [ ] ' \
        text = text.replace("\\", "\\\\")
        text = text.replace(":", "\\:")
        text = text.replace("'", "\\'")
        text = text.replace("[", "\\[")
        text = text.replace("]", "\\]")
        return text
    
    def _build_ffmpeg_command(self, video_path, filters, output_path):
        """
        Build complete FFmpeg command.
        """
        cmd = [
            'ffmpeg',
            '-y',  # Overwrite output file
            '-i', video_path,
            '-vf', filters,
            '-c:a', 'copy',  # Copy audio without re-encoding
            '-c:v', 'libx264',  # Video codec
            '-preset', 'medium',  # Encoding speed/quality balance
            '-crf', '23',  # Quality (lower = better, 18-28 is reasonable)
            output_path
        ]
        return cmd
