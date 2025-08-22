import audio_extractor 
import speech_to_text
import text_translation
from utils.audio_reattached import process_video_with_dub

"""
    The function lang_convert() is used to convert the language name to its respective language code.
"""
def lang_convert(language_name):
    if language_name.lower() == "english":
        return "en"
    elif language_name.lower() == "spanish":
        return "es"
    elif language_name.lower() == "french":
        return "fr"
    elif language_name.lower() == "german":
        return "de"
    elif language_name.lower() == "italian":
        return "it"
    elif language_name.lower() == "portuguese":
        return "pt"
    elif language_name.lower() == "polish":
        return "pl"
    elif language_name.lower() == "turkish":
        return "tr"
    elif language_name.lower() == "russian":
        return "ru"
    elif language_name.lower() == "dutch":
        return "nl"
    elif language_name.lower() == "czech":
        return "cs"
    elif language_name.lower() == "arabic":
        return "ar"
    elif language_name.lower() == "chinese":
        return "zh-cn"
    elif language_name.lower() == "japanese":
        return "ja"
    elif language_name.lower() == "hungarian":
        return "hu"
    elif language_name.lower() == "korean":
        return "ko"
    elif language_name.lower() == "hindi":
        return "hi"
    else:
        return "Unknown code"

def convert(video_path, language_name):
    """
        Extract the audio from the video file.
    """
    input_audio_file = audio_extractor.extract_audio_from_video(video_path, "a.wav")  # Correcte_filed this line by removing the second argument
    output_json_file = "transcript.json"  # output json file

    # Write the text to that JSON file
    speech_to_text.transcribe_audio(input_file=input_audio_file, output_file=output_json_file)

    # Convert the language name to the respective language code
    language_code = lang_convert(language_name)

    # Overwrite the JSON file with the translated text
    text_translation.translate(file_path=output_json_file, target_language=language_code)

    # Convert json file to speech and reattach to mp4 file
    process_video_with_dub(
        timing_json=output_json_file, 
        speaker_wav=input_audio_file, 
        video_file=video_path, 
        output_dir="audio_clips", 
        final_audio_path="final_audio.wav", 
        output_video_file="output_video.mp4"
    )


    
# # Example run

# convert("pitch.mov", "spanish")
