# extract audio from mp4 to wav

from moviepy.video.io.VideoFileClip import VideoFileClip
import os

def extract_audio_from_video(video_path, output_audio_file):
    """
    Extracts audio from a video file and saves it as a .wav file using moviepy.
    
    Args:
        video_path (str): Path to the input video file (.mp4).
        output_audio_file (str): Path to save the extracted audio (.wav).
    
    Returns:
        str: Path to the extracted audio file, or None if an error occurs.
    """
    if not os.path.exists(video_path):
        print(f"Error: Video file not found: {video_path}")
        return None

    try:
        # Load the video file
        video = VideoFileClip(video_path)

        # Write the audio to a .wav file
        video.audio.write_audiofile(output_audio_file, codec="pcm_s16le")
        print(f"Audio extracted and saved to {output_audio_file}")

        return output_audio_file
    
    except Exception as e:
        print(f"Error during audio extraction: {e}")
        return None


# # Example Usage
# if __name__ == "__main__":
#     # Input video file path
#     video_file_path = "testfull.mp4"

#     # Output audio file path
#     output_audio_path = "testfull.wav"

#     # Extract audio
#     result = extract_audio_from_video(video_file_path, output_audio_path)
#     if result:
#         print(f"Audio successfully processed: {result}")
#     else:
#         print("Failed to process audio.")
