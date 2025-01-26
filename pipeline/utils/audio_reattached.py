from utils.text_to_speech import synthesize_cloned_speech  # Import your TTS function
from pydub import AudioSegment
import os
import subprocess
import json


def load_timing_data(json_file):
    """
    Load timing data from a JSON file.
    
    Args:
        json_file (str): Path to the JSON file.
    
    Returns:
        list: A list of sentences with start and end times.
    """
    with open(json_file, "r") as file:
        data = json.load(file)
    return data


def synthesize_and_fit_audio(sentence, start, end, speaker_wav, output_dir):
    """
    Synthesize audio for a sentence and strictly fit it within the time frame 
    by trimming or padding as necessary.

    Args:
        sentence (str): The text to synthesize.
        start (float): Start time in seconds.
        end (float): End time in seconds.
        speaker_wav (str): Path to the reference speaker audio file.
        output_dir (str): Directory to save the audio file.

    Returns:
        str: Path to the generated audio file.
    """
    total_duration = end - start  # Total allowed duration in seconds
    output_path = os.path.join(output_dir, f"{start:.2f}_{end:.2f}.wav")

    # Synthesize audio
    temp_path = os.path.join(output_dir, "temp.wav")
    synthesize_cloned_speech(
        text=sentence,
        speaker_wav=speaker_wav,
        output_file=temp_path
    )

    # Load synthesized audio
    audio = AudioSegment.from_file(temp_path)
    audio_duration = len(audio) / 1000.0  # Duration in seconds

    # Trim or pad audio to strictly fit the allowed duration
    if audio_duration > total_duration:
        # Trim the audio if it's too long
        audio = audio[:int(total_duration * 1000)]
    elif audio_duration < total_duration:
        # Pad with silence if it's too short
        silence_duration = total_duration - audio_duration
        audio += AudioSegment.silent(duration=int(silence_duration * 1000))

    # Export and cleanup
    audio.export(output_path, format="wav")
    os.remove(temp_path)

    return output_path



def concatenate_audio_clips(audio_files, output_path):
    """
    Concatenate multiple audio files while strictly adhering to the specified durations,
    adjusting playback speed for clips that are too long.

    Args:
        audio_files (list): List of tuples (audio_path, start, end).
        output_path (str): Path to save the concatenated audio.

    Returns:
        None
    """
    full_audio = AudioSegment.silent(duration=0)  # Start with an empty audio segment

    for audio_path, start, end in audio_files:
        audio = AudioSegment.from_file(audio_path)

        # Ensure audio fits exactly within its designated time frame
        total_duration = (end - start) * 1000  # Convert seconds to milliseconds
        audio_duration = len(audio)

        if audio_duration > total_duration:
            # Speed up the audio if it's too long
            speed_factor = total_duration / audio_duration
            audio = audio._spawn(audio.raw_data, overrides={
                "frame_rate": int(audio.frame_rate * speed_factor)
            }).set_frame_rate(audio.frame_rate)
        elif audio_duration < total_duration:
            # Pad with silence if it's too short
            silence_duration = total_duration - audio_duration
            audio += AudioSegment.silent(duration=int(silence_duration))

        # Append the adjusted audio directly
        full_audio += audio

    # Export the final concatenated audio
    full_audio.export(output_path, format="wav")



def reattach_audio_to_video(video_file, audio_file, output_video_file):
    """
    Reattach audio to the video using FFmpeg.
    
    Args:
        video_file (str): Path to the original video file.
        audio_file (str): Path to the generated audio file.
        output_video_file (str): Path to save the final video file.
    
    Returns:
        None
    """
    command = [
        "ffmpeg",
        "-i", video_file,
        "-i", audio_file,
        "-map", "0:v:0",  # Use video stream from the original file
        "-map", "1:a:0",  # Use audio stream from the generated file
        "-c:v", "copy",   # Copy video without re-encoding
        "-c:a", "aac",    # Encode audio as AAC
        "-b:a", "192k",   # Set audio bitrate
        "-strict", "experimental",
        output_video_file
    ]
    subprocess.run(command, check=True)


# Main function that includes everything
def process_video_with_dub(timing_json, speaker_wav, video_file, output_dir, final_audio_path, output_video_file):
    """
    Process a video by generating a dubbed voice-over and reattaching it to the original video.

    Args:
        timing_json (str): Path to the JSON file with timing data.
        speaker_wav (str): Path to the reference speaker audio.
        video_file (str): Path to the original video file.
        output_dir (str): Directory to store intermediate audio files.
        final_audio_path (str): Path for the concatenated audio file.
        output_video_file (str): Path for the final video with voice-over.
    
    Returns:
        None
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Load timing data
    timing_data = load_timing_data(timing_json)

    # Generate and adjust audio for each sentence
    audio_files = []
    for item in timing_data:
        sentence = item["sentence"]
        start = item["start"]
        end = item["end"]
        audio_path = synthesize_and_fit_audio(
            sentence, start, end, speaker_wav, output_dir
        )
        audio_files.append((audio_path, start, end))

    # Concatenate all audio files
    concatenate_audio_clips(audio_files, final_audio_path)

    # Reattach audio to video
    reattach_audio_to_video(video_file, final_audio_path, output_video_file)

    print(f"Voice-over video saved to {output_video_file}")


# Uncomment and test the function below with appropriate file paths
# process_video_with_dub(
#     timing_json="../test.json", 
#     speaker_wav="../testfull.wav", 
#     video_file="../testfull.mp4", 
#     output_dir="audio_clips", 
#     final_audio_path="final_audio.wav", 
#     output_video_file="output_video.mp4"
# )
