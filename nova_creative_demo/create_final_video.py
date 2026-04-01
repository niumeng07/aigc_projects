import cv2
import numpy as np
import os
from pathlib import Path
from moviepy.video.io.VideoFileClip import VideoFileClip
import logging
from datetime import datetime
from utils.image_gen import BedrockImageGenerator
import utils.file_utils as file_utils

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

def split_video_to_frames(video_path, output_folder):
    # Create output folder if it doesn't exist
    Path(output_folder).mkdir(parents=True, exist_ok=True)

    # Read the video
    cap = cv2.VideoCapture(video_path)
    frame_count = 0
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        # Save frame
        output_path = os.path.join(output_folder, f'frame_{frame_count:04d}.jpg')
        cv2.imwrite(output_path, frame)
        frame_count += 1
        
    cap.release()
    return frame_count

def overlay_product_simple(background, product_img):
    # Convert background to RGBA if needed
    if background.shape[2] == 3:
        background = cv2.cvtColor(background, cv2.COLOR_BGR2BGRA)
    
    # Extract the alpha channel
    alpha = product_img[:, :, 3] / 255.0
    
    # Blend the images using alpha channel
    for c in range(3):  # BGR channels
        background[:, :, c] = background[:, :, c] * (1 - alpha) + product_img[:, :, c] * alpha
    
    return background

def create_video_with_overlay(frames_folder, product_path, output_path, fps=24):
    # Read the product image (with alpha channel)
    product = cv2.imread(product_path, cv2.IMREAD_UNCHANGED)
    if product is None:
        raise ValueError("Could not load product image")
    
    # Get the first frame to determine video size
    first_frame = cv2.imread(os.path.join(frames_folder, sorted(os.listdir(frames_folder))[0]))
    height, width = first_frame.shape[:2]
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    # Process each frame
    for frame_file in sorted(os.listdir(frames_folder)):
        if frame_file.endswith(('.jpg', '.png')):
            # Read frame
            frame_path = os.path.join(frames_folder, frame_file)
            frame = cv2.imread(frame_path)
            
            # Overlay product
            frame_with_overlay = overlay_product_simple(frame, product)
            
            # Convert back to BGR for video writing
            if frame_with_overlay.shape[2] == 4:
                frame_with_overlay = cv2.cvtColor(frame_with_overlay, cv2.COLOR_BGRA2BGR)
            
            # Write frame
            out.write(frame_with_overlay)
    
    out.release()


def convert_to_h264(input_file, output_file):
    clip = VideoFileClip(input_file)
    clip.write_videofile(output_file, 
                        codec='libx264',
                        fps=24,
                        preset='medium',
                        bitrate='4000k')
    clip.close()


if __name__ == "__main__":
    # Example usage
    # Input paths
    
    first_image_base64 = file_utils.image_to_base64('output/bk-replacement-2025-04-17_13-34-16/image_1.png') 
    video_path = 'output/2025-04-17_13-48-42_472ir34ufi7e/472ir34ufi7e.mp4'

    # Configure the inference parameters.
    inference_params = {
        "taskType": "BACKGROUND_REMOVAL",
        "backgroundRemovalParams": {
            "image": first_image_base64,
        },
    }

    # Define an output directory with a unique name.
    generation_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_directory_bk_removal = f"output/bk-removal-{generation_id}"

    # Create the generator.
    generator = BedrockImageGenerator(
        output_directory=output_directory_bk_removal
    )

    # Generate the image(s).
    response_background_removal = generator.generate_images(inference_params)

    if "images" in response_background_removal:
        # Save and display each image
        images = file_utils.save_base64_images(response_background_removal["images"], output_directory_bk_removal, "image")
            
    product_path = output_directory_bk_removal + '/image_1.png'
    frames_folder = f'output/final_videos/{generation_id}/temp_frames'
    output_path = f'output/final_videos/{generation_id}/output_video_overlay.mp4'
            
    # Convert base64 image to png
    # response_background_removal["images"][0]

    # 1. Split video into frames
    print("Splitting video into frames...")
    frame_count = split_video_to_frames(video_path, frames_folder)

    # 2 & 3. Overlay product and create new video
    print("Creating video with overlay...")
    create_video_with_overlay(frames_folder, product_path, output_path)

    # Clean up temporary frames
    print("Cleaning up...")
    for frame_file in os.listdir(frames_folder):
        os.remove(os.path.join(frames_folder, frame_file))
    os.rmdir(frames_folder)

    output_path_h264 = f'output/final_videos/{generation_id}/output_video_overlay_h264.mp4'
    convert_to_h264(output_path, output_path_h264)
    print("Process completed!")
