from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, send_file, send_from_directory
from werkzeug.utils import secure_filename
from google.cloud import speech, texttospeech
import os
from flask import flash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'vinayak_is_secret_key'
 
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'wav'}
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
            print(filename)
    files.sort(reverse=True)
    return files

@app.route('/', methods=['GET', 'POST'])
def index():
    files = get_files()
    return render_template('index.html', files=files)

@app.route('/', methods=['GET', 'POST'])
def upload_audio():
    if request.method == 'POST':
        # Check if audio_data is present in the request
        if 'audio_data' not in request.files:
            return "No audio data provided", 400  # Return error response

        file = request.files['audio_data']
        if file.filename == '':
            return "No file selected", 400  # Return error response

        if file:
            # Save the file with a timestamp-based name
            filename = datetime.now().strftime("%Y%m%d-%I%M%S%p") + '.wav'
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Use Google Cloud Speech-to-Text API
            client = speech.SpeechClient()
            with open(file_path, 'rb') as audio_file:
                audio_content = audio_file.read()

            audio = speech.RecognitionAudio(content=audio_content)
            config=speech.RecognitionConfig(
            # encoding=speech.RecognitionConfig.AudioEncoding.MP3,
            # sample_rate_hertz=24000,
            language_code="en-US",
            model="latest_long",
            audio_channel_count=1,
            enable_word_confidence=True,
            enable_word_time_offsets=True,
            )

            response = client.recognize(config=config, audio=audio)

            if response.results:
                transcript = response.results[0].alternatives[0].transcript
                transcript_path = os.path.splitext(file_path)[0] + '.txt'
                with open(transcript_path, 'w') as f:
                    f.write(transcript)

            return "Audio uploaded and processed successfully", 200  # Success response

    # For GET request, render the index page
    files = get_files()
    return render_template('index.html', files=files)


@app.route('/upload/<filename>')
def get_file(filename):
    return send_file(filename)

tts_folder = 'path/to/your/tts_folder'
if not os.path.exists(tts_folder):
    os.makedirs(tts_folder)
app.config['TTS_FOLDER'] = tts_folder
    
@app.route('/upload_text', methods=['POST'])
def upload_text():
    text = request.form['text']
    print(text)
    client = texttospeech.TextToSpeechClient()
    print("Credentials are working correctly!")
    #
    #
    # Modify this block to call the stext to speech API
    # Save the output as a audio file in the 'tts' directory 
    # Display the audio files at the bottom and allow the user to listen to them
    #
    if text:
        # Call Google Cloud Text-to-Speech API
        client = texttospeech.TextToSpeechClient()

        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL,
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
        )

        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config,
        )

        output_filename = datetime.now().strftime("%Y%m%d-%I%M%S%p") + '.mp3'
        output_path = os.path.join(app.config['TTS_FOLDER'], output_filename)

        with open(output_path, 'wb') as out:
            out.write(response.audio_content)

    return redirect('/') #success

@app.route('/script.js',methods=['GET'])
def scripts_js():
    return send_file('./script.js')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)




if __name__ == '__main__':
    app.run(debug=True)