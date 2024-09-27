import langdetect
import os
import requests
import logging
import json

logging.basicConfig(level=logging.INFO)

def read_text_file(file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def detect_language(text: str) -> str:
    try:
        return langdetect.detect(text)
    except langdetect.lang_detect_exception.LangDetectException:
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
                        # Only append the actual translation text
                        translation_text = response_data['response']
                        translation_parts.append(translation_text)
                    if response_data.get('done'):
                        break  # Exit when done
                except json.JSONDecodeError:
                    logging.error("JSON decoding failed")

        # Join the parts together and clean up the output
        full_translation = ''.join(translation_parts).strip()
        
        # If the translation still has unwanted structure, further refine it
        # This example assumes the translated text is enclosed in specific markers
        # Adjust based on the actual output structure if necessary
        return full_translation.replace('{"translation": "', '').replace('"}', '').strip()

    except requests.exceptions.RequestException as e:
        logging.error(f"Error during API call: {e}")
        return ""



def save_translated_text(file_path: str, translated_text: str):
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(translated_text)

def main():
    file_path = input("Enter the path to the text file: ")

    if not os.path.exists(file_path):
        logging.error(f"The file {file_path} does not exist.")
        return

    text = read_text_file(file_path)
    if not text.strip():
        logging.error("The file is empty or contains no valid content.")
        return

    lang = detect_language(text)
    translated_text = call_ollama_api(text, lang)

    if translated_text.strip():
        output_file_path = f"{file_path.rsplit('.', 1)[0]}_translated.txt"
        save_translated_text(output_file_path, translated_text)
        logging.info(f"Translation saved to {output_file_path}")
    else:
        logging.error("No translation was generated.")

if __name__ == "__main__":
    main()
