"""
Test Virtual Fence Position
Quick script to visualize the fence position on different sample videos
"""

import cv2
import sys
import os

# Configuration
RESIZE_WIDTH = 640
FENCE_HEIGHT_RATIO = 0.5  # Same as in detect_track_fence.py

def test_video(video_path):
    """Test and visualize fence position on a video"""
    print(f"\n{'='*60}")
    print(f"Testing: {os.path.basename(video_path)}")
    print(f"{'='*60}")
    
    # Open video
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"[ERROR] Could not open: {video_path}")
        return
    
    # Get properties
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    orig_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    orig_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"Original size: {orig_width}x{orig_height}")
    print(f"FPS: {fps:.2f}")
    print(f"Total frames: {total_frames}")
    print(f"Duration: {total_frames/fps:.2f} seconds")
    
    # Read first frame
    ret, frame = cap.read()
    if not ret:
        print("[ERROR] Could not read first frame")
        cap.release()
        return
    
    # Resize
    h, w = frame.shape[:2]
    scale = RESIZE_WIDTH / w
    new_height = int(h * scale)
    frame = cv2.resize(frame, (RESIZE_WIDTH, new_height))
    
    # Calculate fence position
    fence_y = int(new_height * FENCE_HEIGHT_RATIO)
    
    print(f"Resized: {RESIZE_WIDTH}x{new_height}")
    print(f"Fence at Y={fence_y} ({FENCE_HEIGHT_RATIO*100:.0f}% of frame height)")
    
    # Draw fence on frame
    line_start = (0, fence_y)
    line_end = (RESIZE_WIDTH, fence_y)
    
    cv2.line(frame, line_start, line_end, (0, 0, 255), 2)
    cv2.putText(
        frame,
        f"VIRTUAL FENCE (y={fence_y})",
        (5, fence_y - 8),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 0, 255),
        2
    )
    
    # Add info text
    cv2.putText(
        frame,
        f"Video: {os.path.basename(video_path)}",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0),
        2
    )
    cv2.putText(
        frame,
        f"Size: {RESIZE_WIDTH}x{new_height} | Fence: y={fence_y}",
        (10, 60),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 255, 0),
        2
    )
    
    # Show frame
    window_name = f"Fence Position Test - {os.path.basename(video_path)}"
    cv2.imshow(window_name, frame)
    
    print(f"\nPress any key to continue to next video...")
    print(f"(Close window or press 'q' to quit)")
    
    key = cv2.waitKey(0)
    
    cap.release()
    cv2.destroyWindow(window_name)
    
    return key != ord('q')

def main():
    # Get base directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sample_dir = os.path.join(base_dir, "..", "sample_videos")
    
    # Find all MP4 files
    videos = []
    if os.path.exists(sample_dir):
        videos = [
            os.path.join(sample_dir, f) 
            for f in os.listdir(sample_dir) 
            if f.endswith('.mp4')
        ]
        videos.sort()
    
    if not videos:
        print("[ERROR] No video files found in sample_videos/")
        return
    
    print(f"\nFound {len(videos)} video(s):")
    for i, v in enumerate(videos, 1):
        print(f"  {i}. {os.path.basename(v)}")
    
    # Test each video
    for video_path in videos:
        if not test_video(video_path):
            print("\n[INFO] Testing stopped by user")
            break
    
    cv2.destroyAllWindows()
    print("\n[INFO] Testing complete!")

if __name__ == "__main__":
    main()
