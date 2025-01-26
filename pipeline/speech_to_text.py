import whisper
import json

def transcribe_audio(input_file, output_file):
    # Load the Whisper model
    model = whisper.load_model("base")

    # Transcribe the audio file
    result = model.transcribe(input_file)

    #create a list to store segment data
    segments_data = []

    # Iterate through the segments and print timestamps
    for segment in result['segments']:
        segment_info = {
            "start": segment['start'],
            "end": segment['end'],
            "sentence": segment['text'].strip()
        }
        segments_data.append(segment_info)

    with open(output_file, "w") as f:
        json.dump(segments_data, f, indent=4)
        
    return output_file

# transcribe_audio('testfull.mp4','test.json')