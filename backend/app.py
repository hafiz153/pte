from flask import Flask, request, jsonify, render_template, send_from_directory
from pymongo import MongoClient
import google.generativeai as genai
import os
import logging
import re
import pyttsx3

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

genai.configure(api_key="AIzaSyC19YT51luISDbtL8mesSxBym2B6xGo2ao")

app = Flask(__name__)
client = MongoClient('mongodb://localhost:27017/') # Assuming MongoDB is running locally
db = client.pte_project

# Initialize the TTS engine
engine = pyttsx3.init()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_sentence/<int:sentence_id>', methods=['GET'])
def get_sentence(sentence_id):
    sentence_data = db.pte_sentences.find_one({"id": str(sentence_id)})
    if sentence_data:
        return jsonify({"id": sentence_data["id"], "text": sentence_data["text"]})
    else:
        return jsonify({"error": "Sentence not found"}), 404

@app.route('/score', methods=['POST'])
def score():
    audio_file = request.files['audio']
    sentence = request.form['sentence']

    if not audio_file or audio_file.filename == '':
        transcribed_text = ""
        logging.warning("No audio file provided.")
    else:
        # Save the audio file temporarily
        audio_file_path = "temp_audio.wav"
        audio_file.save(audio_file_path)

        try:
            # Create a GenerativeModel instance for audio processing
            audio_model = genai.GenerativeModel('gemini-2.5-flash')
            audio_file_part = genai.upload_file(audio_file_path)
            transcription_response = audio_model.generate_content([audio_file_part, "Transcribe this audio."])
            transcribed_text = transcription_response.text
            logging.info(f"Transcribed text: {transcribed_text}")
        except Exception as e:
            logging.error(f"Error during audio transcription: {e}")
            transcribed_text = "" # Default to empty string on transcription error

    ai_score = "Error: Could not get AI score."
    gemini_score = 0

    try:
        # Use Gemini Pro for scoring
        scoring_model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"""You are an AI assistant that scores the similarity between a target sentence and a transcribed speech.
        The scoring should follow Pearson PTE guidelines, focusing on content, pronunciation, and oral fluency.

        Here are the scoring criteria:
        Content:
        - Errors = replacements, omissions and insertions only.
        - Hesitations, filled or unfilled pauses, leading or trailing material are ignored in the scoring of content.
        - 3: All words in the response from the prompt in the correct sequence.
        - 2: At least 50% of words in the response from the prompt in the correct sequence.
        - 1: Less than 50% of words in the response from the prompt in the correct sequence.
        - 0: Almost nothing from the prompt in the response.

        Pronunciation:
        - 5: Highly proficient
        - 4: Advanced
        - 3: Good
        - 2: Intermediate
        - 1: Intrusive
        - 0: Non-English (See detailed criteria on pages 41–42)

        Oral fluency:
        - 5: Highly proficient
        - 4: Advanced
        - 3: Good
        - 2: Intermediate
        - 1: Limited
        - 0: Disfluent

        Target sentence: "{sentence}"
        Transcribed speech: "{transcribed_text}"
        Provide an overall score from 1 to 5, where 5 is a perfect match and 1 is no similarity.
        Additionally, provide individual scores for content, pronunciation, and fluency, each from 0 to 5.
        Format your response as a JSON object with the following keys:
        "overall_score": <overall_score>,
        "content": <content_score>,
        "pronunciation": <pronunciation_score>,
        "fluency": <fluency_score>,
        "explanation": "<brief explanation highlighting areas of strength and weakness based on PTE guidelines, formatted as a bulleted list using asterisks>"
        """
        response = scoring_model.generate_content(prompt)

        ai_score = response.text.strip()

        try:
            # Remove markdown code block if present
            if ai_score.startswith('```json') and ai_score.endswith('```'):
                ai_score = ai_score[len('```json'):-len('```')].strip()

            # Parse the JSON response
            import json
            json_response = json.loads(ai_score)
            gemini_score = json_response.get("overall_score", 0)

        except json.JSONDecodeError:
            logging.warning(f"Could not parse JSON from Gemini response: {ai_score}")
            gemini_score = 0 # Default score if parsing fails
            json_response = {"overall_score": 0, "content": 0, "pronunciation": 0, "fluency": 0, "explanation": "Error: Could not parse AI response."}
        except Exception as e:
            logging.warning(f"Error processing Gemini JSON response: {e}")
            gemini_score = 0 # Default score if parsing fails
            json_response = {"overall_score": 0, "content": 0, "pronunciation": 0, "fluency": 0, "explanation": f"Error processing AI response: {e}"}

    except Exception as e:
        logging.error(f"Error during Gemini API call or scoring: {e}")
        gemini_score = 0
        json_response = {"overall_score": 0, "content": 0, "pronunciation": 0, "fluency": 0, "explanation": f"Error during Gemini API call or scoring: {e}"}

    finally:
        # Clean up the temporary audio file
        if os.path.exists(audio_file_path):
            os.remove(audio_file_path)

    # Save to MongoDB
    db.scores.insert_one({'sentence': sentence, 'score': gemini_score, 'ai_response': json_response})

    return jsonify({'score': gemini_score, 'ai_response': json_response})

@app.route('/generate_audio/<int:sentence_id>', methods=['GET'])
def generate_audio(sentence_id):
    sentence_data = db.pte_sentences.find_one({"id": str(sentence_id)})
    if sentence_data:
        sentence_text = sentence_data['text']
        audio_file_path = f"./static/audio/sentence_{sentence_id}.mp3"

        # Ensure the directory exists
        os.makedirs(os.path.dirname(audio_file_path), exist_ok=True)

        logging.info(f"Attempting to generate audio for sentence ID: {sentence_id}")
        # Temporarily bypass pyttsx3 for debugging
        # engine.save_to_file(sentence_text, audio_file_path)
        # engine.runAndWait()
        # logging.info(f"Audio file saved to: {audio_file_path}")

        # Create a dummy audio file for testing
        with open(audio_file_path, "w") as f:
            f.write("dummy audio content")
        logging.info(f"Dummy audio file created at: {audio_file_path}")

        if os.path.exists(audio_file_path):
            return send_from_directory('static/audio', f'sentence_{sentence_id}.mp3')
        else:
            logging.error(f"Audio file not found after generation: {audio_file_path}")
            return jsonify({"error": "Audio file not found"}), 500
    else:
        return jsonify({"error": "Sentence not found"}), 404

@app.route('/add_sentences', methods=['POST'])
def add_sentences():
    sentences = request.json
    if not isinstance(sentences, list):
        return jsonify({"error": "Payload must be a list of sentences"}), 400

    try:
        db.pte_sentences.insert_many(sentences)
        return jsonify({"message": f"Successfully added {len(sentences)} sentences"}), 201
    except Exception as e:
        logging.error(f"Error adding sentences to MongoDB: {e}")
        return jsonify({"error": "Failed to add sentences", "details": str(e)}), 500

@app.route('/total_sentences', methods=['GET'])
def get_total_sentences():
    try:
        count = db.pte_sentences.count_documents({})
        return jsonify({"total_sentences": count}), 200
    except Exception as e:
        logging.error(f"Error getting total sentences from MongoDB: {e}")
        return jsonify({"error": "Failed to get total sentences", "details": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)