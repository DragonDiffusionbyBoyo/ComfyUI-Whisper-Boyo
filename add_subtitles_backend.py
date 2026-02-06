import os
import subprocess
import json

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

try:
    from .renderers.pillow_renderer import PillowRenderer
except ImportError:
    pass

FONT_DIR = os.path.join(os.path.dirname(__file__), "fonts")

def get_backend_videos():
    """Scan the backend input folder and return list of video files."""
    comfyui_root = os.path.join(os.path.dirname(__file__), "..", "..")
    input_folder = os.path.join(comfyui_root, "input", "backend")
    
    # Create folder if it doesn't exist
    os.makedirs(input_folder, exist_ok=True)
    
    # Get all video files
    video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.webm', '.flv', '.wmv']
    videos = []
    
    try:
        for filename in os.listdir(input_folder):
            if os.path.isfile(os.path.join(input_folder, filename)):
                ext = os.path.splitext(filename)[1].lower()
                if ext in video_extensions:
                    videos.append(filename)
    except:
        pass
    
    # Return list or placeholder if empty
    return videos if videos else ["no_videos_found.mp4"]

class AddSubtitlesBackendNode:
    """
    Boyo's Standalone Backend Subtitle Node
    
    Complete one-stop solution:
    1. Load video from /input/backend/ folder
    2. Transcribe with Whisper
    3. Render subtitles with Pillow (frame-by-frame, handles any length)
    4. Output to /output/processedsubs/ folder
    
    No canvas involvement - everything processed off-screen.
    Uses Pillow renderer for reliability and quality.
    """
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": { 
                "video_filename": (get_backend_videos(),),
                "whisper_model": (["tiny", "base", "small", "medium", "large-v3"],),
                "font_family": (os.listdir(FONT_DIR),),
                "font_size": ("INT", {
                    "default": 100,
                    "min": 10,
                    "max": 500,
                    "step": 5,
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
                }),
                "y_position": ("INT", {
                    "default": 100,
                    "step": 10,
                }),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("status",)
    FUNCTION = "process_video"
    CATEGORY = "whisper/boyo"
    OUTPUT_NODE = True

    def process_video(self, video_filename, whisper_model, font_family, font_size, 
                     font_color, stroke_width, stroke_color, animation_style, 
                     animation_duration, position_preset, x_position, y_position):
        """
        Complete standalone processing pipeline using Pillow renderer.
        """
        
        if not WHISPER_AVAILABLE:
            return ("❌ ERROR: Whisper not installed. Run: pip install openai-whisper",)
        
        if video_filename == "no_videos_found.mp4":
            comfyui_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            input_folder = os.path.join(comfyui_root, "input", "backend")
            return (f"❌ ERROR: No videos found\n\n📁 Place videos in: {input_folder}\n\nSupported: .mp4, .mov, .avi, .mkv, .webm",)
        
        # Set up paths - use absolute paths
        comfyui_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        input_folder = os.path.join(comfyui_root, "input", "backend")
        output_folder = os.path.join(comfyui_root, "output", "processedsubs")
        
        # Create output folder
        os.makedirs(output_folder, exist_ok=True)
        
        # Full paths
        video_path = os.path.abspath(os.path.join(input_folder, video_filename))
        
        if not os.path.exists(video_path):
            return (f"❌ ERROR: Video not found: {video_path}",)
        
        # Generate output path
        output_filename = f"{os.path.splitext(video_filename)[0]}_subtitled.mp4"
        output_path = os.path.abspath(os.path.join(output_folder, output_filename))
        
        try:
            # Step 1: Transcribe with Whisper
            status = f"🎙️  Transcribing with Whisper ({whisper_model})...\n"
            print(status)
            
            model = whisper.load_model(whisper_model)
            result = model.transcribe(video_path, word_timestamps=True)
            
            # Extract word-level alignment
            alignment = []
            for segment in result['segments']:
                if 'words' in segment:
                    for word in segment['words']:
                        alignment.append({
                            'start': word['start'],
                            'end': word['end'],
                            'value': word['word'].strip()
                        })
            
            status += f"✅ Transcribed {len(alignment)} words\n\n"
            print(f"Transcribed {len(alignment)} words")
            
            # Get video FPS
            fps = self._get_video_fps(video_path)
            
            # Step 2: Build style config
            style_config = {
                'font_family': font_family,
                'font_path': os.path.abspath(os.path.join(FONT_DIR, font_family)),
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
            
            # Step 3: Render subtitles with Pillow
            status += f"🎨 Rendering with Pillow renderer (frame-by-frame)...\n"
            print(f"Rendering with Pillow...")
            
            renderer_instance = PillowRenderer()
            
            render_result = renderer_instance.render(
                video_path=video_path,
                alignment=alignment,
                style_config=style_config,
                output_path=output_path,
                fps=fps
            )
            
            status += f"✅ Rendering complete!\n\n"
            status += f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            status += f"📁 Output: {output_path}\n"
            status += f"📊 Subtitles: {len(alignment)} words\n"
            status += f"🎬 Frames: {render_result.get('frames_processed', 'N/A')}\n"
            status += f"⏱️  Model: {whisper_model}\n"
            status += f"🎥 FPS: {fps:.2f}\n"
            status += f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            
            print("Processing complete!")
            return (status,)
            
        except Exception as e:
            import traceback
            error_msg = f"❌ ERROR: {str(e)}\n\n{traceback.format_exc()}"
            print(error_msg)
            return (error_msg,)
    
    def _get_video_fps(self, video_path):
        """Get video FPS using ffprobe."""
        try:
            cmd = [
                'ffprobe', '-v', 'error',
                '-select_streams', 'v:0',
                '-show_entries', 'stream=r_frame_rate',
                '-of', 'json',
                video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            fps_str = data['streams'][0]['r_frame_rate']
            num, den = map(int, fps_str.split('/'))
            return num / den
        except:
            return 24.0  # Default fallback
