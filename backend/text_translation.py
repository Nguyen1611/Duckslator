import json
from googletrans import Translator

def translate(file_path, target_language):
    """
    Translates the content of a JSON file into a target language.
    
    Args:
        file_path (str): Path to the JSON file to be translated.
        target_language (str): Language code to translate the content to (e.g., "en" for English).

    Returns:
        file_path (str): Path to the translated file.
        Output: Overwrite old file path with translated text.
    """
    translator = Translator()

    # Read the content of the file
    try:
        with open(file_path, "r") as file:
            contents = json.load(file)
            print("Original Content:", contents)

            # Loop through the list of dictionaries and translate each sentence
            for content in contents:
                sentence = content.get("sentence")  # Ensure there's a "sentence" key
                if sentence:
                    try:
                        # Translate the sentence
                        result = translator.translate(text=sentence, dest=target_language)
                        content["sentence"] = result.text
                    except Exception as e:
                        print(f"Error during translation of sentence '{sentence}': {e}")
                        continue  # Skip this item and move to the next

            # Write the updated content back to the file
            with open(file_path, "w") as file:
                json.dump(contents, file, indent=4)
            print(f"Translation successful. File saved to {file_path}")
            return file_path

    except FileNotFoundError:
        print("Error: The file does not exist.")
        return None
    
    except PermissionError:
        print("Error: You do not have permission to access this file.")
        return None
    
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


# # Example Usage
# if __name__ == "__main__":
#     # Example: {"sentence": str, "start": float, "end": float}
#     translate("transcript.json", "ru")  # Replace with the actual file path and target language
