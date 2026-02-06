# ComfyUI Whisper - Dragon Diffusion Enhanced Edition

Enhanced fork of ComfyUI-Whisper with professional subtitle rendering and backend processing for large videos.

**Original:** [yuvraj108c/ComfyUI-Whisper](https://github.com/yuvraj108c/ComfyUI-Whisper)  
**Enhanced by:** Dragon Diffusion UK Ltd

## 🚀 What's New in This Fork

### Backend Processing Mode
- **Bypass ComfyUI Memory Limits**: Process videos of any length without loading to canvas
- **Automatic Mode Selection**: Videos <120s use lite mode, ≥120s auto-switch to backend
- **Manual Override**: Force lite or backend mode as needed

### Advanced Subtitle Styling
- **Multiple Rendering Engines**: FFmpeg (fast) or Pillow (flexible)
- **Text Strokes/Outlines**: Configurable width and colour
- **Shadow Effects**: Optional drop shadows for better readability
- **Animation Styles**: Fade, slide up/down, zoom effects
- **Position Presets**: Bottom center, top center, center, or custom positioning
- **Custom Fonts**: Full TrueType font support

### Professional Quality Output
- **FFmpeg Integration**: Hardware-accelerated encoding, professional codecs
- **Configurable Quality**: CRF control, preset selection
- **Audio Preservation**: Audio streams copied without re-encoding

## Installation

### Via ComfyUI Manager (Recommended)
Install from custom node list (search for "Whisper Boyo" or "Dragon Diffusion")

### Manual Installation
```bash
cd ComfyUI/custom_nodes/
git clone https://github.com/DragonDiffusionbyBoyo/ComfyUI-Whisper-Boyo.git
cd ComfyUI-Whisper-Boyo
pip install -r requirements.txt
```

## Usage

### New: Backend Processing Node

The **"Add Subtitles (Backend Mode)"** node adds all original features plus:

#### Required Inputs
- `images`: Image tensor (from video load)
- `alignment`: Whisper alignment data
- `font_family`: Font selection from fonts directory
- `font_size`: Size in pixels (10-500)
- `font_color`: Text colour (name or hex)
- `video_fps`: Frames per second
- `processing_mode`: `auto`, `lite`, or `backend`
- `renderer`: `ffmpeg` or `pillow`

#### Optional Inputs (Advanced Styling)
- `video_path`: **Required for backend mode** - path to source video file
- `output_path`: Custom output location (auto-generated if not specified)
- `stroke_width`: Outline thickness (0-20 pixels)
- `stroke_color`: Outline colour
- `animation_style`: `none`, `fade`, `slide_up`, `slide_down`, `zoom`
- `animation_duration`: Animation length in seconds (0.1-2.0)
- `position_preset`: `bottom_center`, `top_center`, `center`, `custom`
- `x_position`: Custom X coordinate
- `y_position`: Custom Y offset/coordinate

### Processing Modes

#### Auto Mode (Recommended)
```
Videos <120 seconds  → Lite mode (in-memory processing)
Videos ≥120 seconds  → Backend mode (file-based processing)
```

#### Lite Mode
- Traditional ComfyUI processing
- Results appear on canvas
- Good for short clips, quick iteration
- Memory limited

#### Backend Mode
- Headless processing
- No canvas memory limits
- Output saved to `/ComfyUI/output/whisper_backend/`
- Required: `video_path` parameter must be set
- Notification with output path returned

### Example Workflow

```
Load Video
    ↓
Apply Whisper (transcribe)
    ↓
Add Subtitles (Backend Mode)
    ├─ processing_mode: "auto"
    ├─ renderer: "ffmpeg"
    ├─ animation_style: "fade"
    ├─ stroke_width: 2
    ├─ stroke_color: "black"
    └─ video_path: "/path/to/source.mp4"
    ↓
Output: Subtitled video in output folder
```

## Rendering Engines

### FFmpeg Renderer (Recommended)
- **Fast**: Single-pass processing
- **Professional**: Hardware acceleration support
- **Effects**: Strokes, shadows, fades, slides, zoom
- **Limitations**: Complex per-frame animations limited

### Pillow Renderer
- **Flexible**: Full programmatic control per frame
- **Advanced**: Custom effects, gradients, complex animations
- **Slower**: Frame-by-frame processing
- **Use when**: Need effects FFmpeg can't provide

## Architecture

```
ComfyUI Node (Configuration)
    ↓
Processing Mode Selection
    ├─→ Lite Mode (<120s or user-selected)
    │   └─→ Traditional PIL processing
    │       └─→ Results to canvas
    │
    └─→ Backend Mode (≥120s or user-selected)
        ├─→ Extract parameters
        ├─→ Select renderer (FFmpeg/Pillow)
        ├─→ Process video file directly
        └─→ Output to folder
            └─→ Notification with path
```

## Original Features (Preserved)

All original nodes remain functional:
- **Apply Whisper**: Audio transcription
- **Add Subtitles To Frames**: Basic subtitle overlay
- **Add Subtitles To Background**: Word cloud style
- **Resize Cropped Subtitles**: Subtitle resizing
- **Save SRT**: Export SRT subtitle files

## Requirements

```
whisper
torch
torchvision
opencv-python
pillow
numpy
ffmpeg (system package)
```

## Performance Comparison

| Mode | Processing Speed | Memory Usage | Max Video Length |
|------|-----------------|--------------|------------------|
| Original (PIL) | Slow | High | ~120 seconds |
| Lite Mode | Moderate | High | ~120 seconds |
| Backend FFmpeg | **Very Fast** | **Low** | **Unlimited** |
| Backend Pillow | Moderate | Low | Unlimited |

## Roadmap

### Planned Features
- [ ] SVG-based kinetic typography renderer
- [ ] Pre-built animated font templates
- [ ] Gradient text fills
- [ ] Multiple subtitle tracks
- [ ] Batch processing multiple videos
- [ ] GPU-accelerated Pillow processing
- [ ] WebM/VP9 output support
- [ ] Real-time preview for backend mode

## Technical Details

### Backend Processing Flow
1. Node receives config + alignment from ComfyUI
2. Mode auto-selected based on video duration
3. Backend processor initialised with renderer
4. Video processed directly from file (no canvas load)
5. Output written to configured/auto-generated path
6. Notification returned to ComfyUI

### FFmpeg Command Structure
```bash
ffmpeg -i input.mp4 \
  -vf "drawtext=fontfile=font.ttf:text='word':fontsize=100:..." \
  -c:a copy \
  -c:v libx264 -preset medium -crf 23 \
  output.mp4
```

### Memory Optimisation
- Backend mode never loads full video into Python memory
- Frames processed in streaming fashion when using Pillow
- FFmpeg handles encoding in single pass

## Credits

- **Original Project**: [yuvraj108c/ComfyUI-Whisper](https://github.com/yuvraj108c/ComfyUI-Whisper)
- **Enhanced by**: Dragon Diffusion UK Ltd / Boyo
- **Based on**: 
  - [OpenAI Whisper](https://github.com/openai/whisper/)
  - [ComfyUI](https://github.com/comfyanonymous/ComfyUI)

## License

[Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)](https://creativecommons.org/licenses/by-nc-sa/4.0/)

## Support

Issues, feature requests, and contributions welcome at:
https://github.com/DragonDiffusionbyBoyo/ComfyUI-Whisper-Boyo/issues

---

**Dragon Diffusion UK Ltd** - Professional AI Solutions
