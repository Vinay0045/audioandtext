
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, send_file, send_from_directory
from werkzeug.utils import secure_filename
from google.cloud import speech, texttospeech
import os
from flask import flash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'vinayak_is_secret_key'
 
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'wav','txt'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_files():
    audio_files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.endswith('.wav')]
    transcripts = {}
    for audio_file in audio_files:
        text_file = audio_file.replace('.wav', '.txt')
        text_path = os.path.join(app.config['UPLOAD_FOLDER'], text_file)
        if os.path.exists(text_path):
            with open(text_path, 'r') as f:
                transcripts[audio_file] = f.read()
    return audio_files,transcripts

@app.route('/', methods=['GET', 'POST'])
def index():
    files, transcripts = get_files()
    return render_template('index.html', files=files,transcripts=transcripts)

@app.route('/upload', methods=['POST'])
def upload_audio():
    if 'audio_data' not in request.files:
        return redirect(request.url)

    file = request.files['audio_data']
    if file.filename == '':
        return redirect(request.url)

    def transcribe_audio(file_path):
        client = speech.SpeechClient()

        with open(file_path, 'rb') as audio_file:
            content = audio_file.read()

        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            language_code="en-US",
            model="latest_long",
            enable_word_confidence=True,
            enable_word_time_offsets=True,
        )

        # Perform the transcription
        response = client.recognize(config=config, audio=audio)

        transcript = ''
        for result in response.results:
            transcript += result.alternatives[0].transcript + '\n'

        return transcript

    if file and allowed_file(file.filename):
        filename = datetime.now().strftime("%Y%m%d-%I%M%S%p") + '.wav'
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Transcribe the audio file
        transcript = transcribe_audio(file_path)

        # Save the transcript as a .txt file
        transcript_filename = filename.replace('.wav', '.txt')
        transcript_path = os.path.join(app.config['UPLOAD_FOLDER'], transcript_filename)
        with open(transcript_path, 'w') as transcript_file:
            transcript_file.write(transcript)

        return render_template('index.html', transcript=transcript, audio_file_url=url_for('uploaded_file', filename=filename))

    return redirect('/')


@app.route('/upload/<filename>')
def get_file(filename):
    return send_file(filename)

@app.route('/upload_audio', methods=['POST'])
def get_text():
    return redirect('/')

tts_folder = 'path_tts_folder'
if not os.path.exists(tts_folder):
    os.makedirs(tts_folder)
app.config['TTS_FOLDER'] = tts_folder
    
@app.route('/upload_text', methods=['POST'])
def upload_text():
    text = request.form['text']
    print(text)
    client = texttospeech.TextToSpeechClient()

    if text:
        # Call Google Cloud Text-to-Speech API
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

        # Pass the generated audio file's filename to the template
        audio_file_url = url_for('uploaded_file', filename=output_filename)

        return render_template('index.html', audio_file_url=audio_file_url)  # Render the template with the audio file URL
    return redirect('/')  # In case text is empty

@app.route('/script.js',methods=['GET'])
def scripts_js():
    return send_file('./script.js')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['TTS_FOLDER'], filename)

@app.route('/uploads_ats/<filename>')
def uploaded_file_att(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)



if __name__ == '__main__':
    app.run(debug=True)


