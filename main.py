import langdetect
import os
import requests
import logging
import json
from langdetect.lang_detect_exception import LangDetectException

logging.basicConfig(level=logging.INFO)

def detect_language(text: str) -> str:
    try:
        return langdetect.detect(text)
    except LangDetectException:
        logging.warning("Language detection failed. Defaulting to English.")
        return 'en'

def generate_prompt(text: str, source_lang: str, target_lang: str = 'en') -> str:
    return f"Translate this {source_lang} text to {target_lang}: \"{text}\""

def call_ollama_api(text: str, source_lang: str) -> str:
    url = "http://localhost:11434/api/generate"
    model = "gemma2:2b"
    prompt = generate_prompt(text, source_lang)

    payload = {
        "model": model,
        "prompt": prompt,
        "format": "json",
        "options": {
            "temperature": 0.5
        }
    }
    
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(url, json=payload, headers=headers, stream=True)
        response.raise_for_status()

        translation_parts = []
        
        for line in response.iter_lines():
            if line:
                line_data = line.decode('utf-8')
                logging.info(f"Raw line data: {line_data}")
                try:
                    response_data = json.loads(line_data)
                    if 'response' in response_data:
                        translation_text = response_data['response']
                        translation_parts.append(translation_text)
                    if response_data.get('done'):
                        break
                except json.JSONDecodeError:
                    logging.error("JSON decoding failed for line: {}".format(line_data))

        return ''.join(translation_parts).strip()

    except requests.exceptions.RequestException as e:
        logging.error(f"Error during API call: {e}")
        return ""

def save_translated_text(file_path: str, translated_text: str):
    with open(file_path, 'a', encoding='utf-8') as f:  # Append mode
        f.write(translated_text + "\n")  # Add newline for each line

def main():
    input_file_path = input("Enter the path to the text file: ")

    if not os.path.exists(input_file_path):
        logging.error(f"The file {input_file_path} does not exist.")
        return

    output_file_path = f"{input_file_path.rsplit('.', 1)[0]}_translated.txt"

    with open(input_file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()  # Remove leading/trailing whitespace
            if not line:
                continue  # Skip empty lines

            lang = detect_language(line)
            translated_text = call_ollama_api(line, lang)

            if translated_text.strip():
                save_translated_text(output_file_path, translated_text)
                logging.info(f"Translated line saved: {translated_text}")
            else:
                logging.error("No translation was generated for the line.")

if __name__ == "__main__":
    main()
