from TTS.api import TTS
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException

def synthesize_cloned_speech(
    text,
    speaker_wav,
    output_file="output.wav"
):
    """
    Generates speech in the cloned voice of a target speaker with automatic language detection.
    
    Args:
        text (str): Text to be converted to speech.
        speaker_wav (str): Path to the reference audio file (6-second clip).
        output_file (str): Path to save the generated audio file.
    
    Returns:
        str: Path to the generated audio file.
    """

    # Detect language from the input text
    try:
        language = detect(text)

    except LangDetectException:
        print("Error: Unable to detect language from text. Defaulting to 'en'.")
        language = "en"


    # Load the XTTS model
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=True) # fix this later for pc that has no gpu

    # Generate speech and save to file
    tts.tts_to_file(
        text=text,
        speaker_wav=speaker_wav,
        language=language,
        file_path=output_file
    )

    return output_file


# # Example Usage
# if __name__ == "__main__":
#     # Text to convert
#     with open('check.txt','r') as f:
#         text = f.read()

#     # Path to the reference speaker audio
#     speaker_audio_path = "testfull.wav"

#     # Output file path
#     output_audio_path = "cloned_speech.wav"

#     # Generate speech
#     a = synthesize_cloned_speech(
#         text=text,
#         speaker_wav=speaker_audio_path,
#         output_file=output_audio_path)
    
#     print(a) # is a sring of file path to the vid

