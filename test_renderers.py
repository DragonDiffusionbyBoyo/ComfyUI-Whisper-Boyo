#!/usr/bin/env python3
"""
Test script for subtitle renderers
Usage: python test_renderers.py [video_path]
"""

import sys
import os
from pathlib import Path

# Mock alignment data for testing
TEST_ALIGNMENT = [
    {"start": 0.5, "end": 2.0, "value": "Hello World"},
    {"start": 2.5, "end": 4.5, "value": "Testing subtitle rendering"},
    {"start": 5.0, "end": 7.0, "value": "With Dragon Diffusion enhancements"},
]

TEST_STYLE_CONFIG = {
    'font_family': 'Arial.ttf',
    'font_path': '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',  # Fallback
    'font_size': 80,
    'font_color': 'white',
    'stroke_width': 3,
    'stroke_color': 'black',
    'animation_style': 'fade',
    'animation_duration': 0.3,
    'position_preset': 'bottom_center',
    'x_position': 0,
    'y_position': 100,
}

def test_ffmpeg_renderer(video_path):
    """Test FFmpeg renderer."""
    print("\n🎬 Testing FFmpeg Renderer...")
    print("-" * 50)
    
    try:
        from renderers.ffmpeg_renderer import FFmpegRenderer
        
        renderer = FFmpegRenderer()
        output_path = str(Path(video_path).with_name('test_ffmpeg_output.mp4'))
        
        result = renderer.render(
            video_path=video_path,
            alignment=TEST_ALIGNMENT,
            style_config=TEST_STYLE_CONFIG,
            output_path=output_path,
            fps=24.0
        )
        
        print(f"✅ FFmpeg renderer SUCCESS")
        print(f"   Output: {result['output_path']}")
        print(f"   Subtitles: {result['subtitle_count']}")
        print(f"   Status: {result['status']}")
        
        return True
        
    except Exception as e:
        print(f"❌ FFmpeg renderer FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_pillow_renderer(video_path):
    """Test Pillow renderer."""
    print("\n🎨 Testing Pillow Renderer...")
    print("-" * 50)
    
    try:
        from renderers.pillow_renderer import PillowRenderer
        
        renderer = PillowRenderer()
        output_path = str(Path(video_path).with_name('test_pillow_output.mp4'))
        
        result = renderer.render(
            video_path=video_path,
            alignment=TEST_ALIGNMENT,
            style_config=TEST_STYLE_CONFIG,
            output_path=output_path,
            fps=24.0
        )
        
        print(f"✅ Pillow renderer SUCCESS")
        print(f"   Output: {result['output_path']}")
        print(f"   Subtitles: {result['subtitle_count']}")
        print(f"   Frames: {result['frames_processed']}")
        print(f"   Status: {result['status']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Pillow renderer FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def check_dependencies():
    """Check required dependencies."""
    print("\n🔍 Checking Dependencies...")
    print("-" * 50)
    
    deps = {
        'PIL': 'Pillow',
        'cv2': 'opencv-python',
        'numpy': 'numpy',
        'subprocess': 'built-in',
    }
    
    missing = []
    for module, package in deps.items():
        try:
            __import__(module)
            print(f"✅ {module} ({package})")
        except ImportError:
            print(f"❌ {module} ({package}) - MISSING")
            missing.append(package)
    
    # Check FFmpeg
    try:
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            print(f"✅ FFmpeg: {version}")
        else:
            print(f"❌ FFmpeg: Not working")
            missing.append('ffmpeg (system package)')
    except FileNotFoundError:
        print(f"❌ FFmpeg: Not installed")
        missing.append('ffmpeg (system package)')
    
    if missing:
        print(f"\n⚠️  Missing dependencies: {', '.join(missing)}")
        print("\nInstall with:")
        print("  pip install opencv-python pillow numpy")
        print("  System: apt install ffmpeg (Ubuntu) or brew install ffmpeg (Mac)")
        return False
    
    print("\n✅ All dependencies satisfied")
    return True

def main():
    print("=" * 60)
    print("Dragon Diffusion Subtitle Renderer Test Suite")
    print("=" * 60)
    
    # Check dependencies first
    if not check_dependencies():
        sys.exit(1)
    
    # Get video path
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
    else:
        video_path = input("\nEnter path to test video file: ").strip()
    
    if not os.path.exists(video_path):
        print(f"\n❌ Video file not found: {video_path}")
        sys.exit(1)
    
    print(f"\n📹 Test video: {video_path}")
    
    # Test renderers
    ffmpeg_ok = test_ffmpeg_renderer(video_path)
    pillow_ok = test_pillow_renderer(video_path)
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"FFmpeg Renderer: {'✅ PASS' if ffmpeg_ok else '❌ FAIL'}")
    print(f"Pillow Renderer: {'✅ PASS' if pillow_ok else '❌ FAIL'}")
    
    if ffmpeg_ok and pillow_ok:
        print("\n🎉 All tests passed! Ready for production.")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Check errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
