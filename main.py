from datetime import datetime

from flask import Flask, flash, render_template, request, redirect, url_for, send_file, send_from_directory
from werkzeug.utils import secure_filename

import os

app = Flask(__name__)
app.secret_key = 'vinayak_is_secret_key'

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'wav','txt'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_files():
    files = []
    for filename in os.listdir(UPLOAD_FOLDER):
        if allowed_file(filename):
            files.append(filename)
    files.sort(reverse=True)
    return files

@app.route('/')
def index():
    # Get uploaded files
    files = get_files()

    # Get generated TTS files
    tts_folder = 'tts'
    os.makedirs(tts_folder, exist_ok=True)
    tts_files = [file for file in os.listdir(tts_folder) if file.endswith('.mp3')]

    return render_template('index.html', files=files, tts_files=tts_files)

@app.route('/upload', methods=['POST'])
def upload_audio():
    if 'audio_data' not in request.files:
        flash('No audio data')
        return redirect(request.url)
    file = request.files['audio_data']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file:
        filename = datetime.now().strftime("%Y%m%d-%I%M%S%p") + '.wav'
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Example for speech-to-text API call
        transcript_path = os.path.join(app.config['UPLOAD_FOLDER'], filename.replace('.wav', '.txt'))
        try:
            from google.cloud import speech
            client = speech.SpeechClient()
            with open(file_path, "rb") as audio_file:
                content = audio_file.read()
            audio = speech.RecognitionAudio(content=content)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code="en-US",
            )
            response = client.recognize(config=config, audio=audio)
            transcript = "\n".join(result.alternatives[0].transcript for result in response.results)
            with open(transcript_path, 'w') as f:
                f.write(transcript)
        except Exception as e:
            flash(f"Error processing speech-to-text: {str(e)}")
            return redirect('/')

    return redirect('/')

@app.route('/upload/<filename>')
def get_file(filename):
    return send_file(filename)
@app.route('/upload_text', methods=['POST'])
def upload_text():
    from google.cloud import texttospeech
    import os

    # Get the input text from the frontend
    text = request.form.get('text', '').strip()
    if not text:
        flash("No text provided. Please enter some text to convert.")
        print("Error: No text input received.")
        return redirect('/')

    try:
        # Initialize Google Cloud TTS client
        print("Initializing Google Cloud Text-to-Speech client...")
        client = texttospeech.TextToSpeechClient()

        # Set up the input text for synthesis
        print(f"Received text for conversion: {text}")
        synthesis_input = texttospeech.SynthesisInput(text=text)

        # Configure the voice parameters
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL,
        )

        # Set audio encoding to MP3
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
        )

        # Make the API call
        print("Sending request to Google Cloud TTS API...")
        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        # Check if the response contains audio content
        if not response.audio_content:
            flash("The TTS API returned no audio content.")
            print("Error: No audio content in the response.")
            return redirect('/')

        # Save the audio content to a file
        tts_folder = 'tts'
        os.makedirs(tts_folder, exist_ok=True)  # Ensure the folder exists
        output_filename = os.path.join(tts_folder, f"{datetime.now().strftime('%Y%m%d-%H%M%S')}.mp3")
        print(f"Saving audio file to: {output_filename}")
        with open(output_filename, "wb") as out:
            out.write(response.audio_content)

        flash("Text successfully converted to speech!")
        print("Audio file successfully created.")
    except Exception as e:
        flash(f"Error during text-to-speech conversion: {str(e)}")
        print(f"Exception occurred: {e}")
        return redirect('/')

    return redirect('/')



@app.route('/tts/<filename>')
def serve_tts_file(filename):
    # Serve files from the TTS folder
    return send_from_directory('tts', filename)



@app.route('/tts/<filename>')
def tts_file(filename):
    return send_from_directory('tts', filename)

@app.route('/script.js', methods=['GET'])
def scripts_js():
    return send_file('./script.js')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)