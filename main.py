from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_file, send_from_directory
from werkzeug.utils import secure_filename
from google.cloud import speech, texttospeech, language_v1
import os
from flask import flash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'vinayak_is_secret_key'
 
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'wav','txt'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

tts_folder = 'tts_files'
if not os.path.exists(tts_folder):
    os.makedirs(tts_folder)
app.config['TTS_FOLDER'] = tts_folder

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_files():
    audio_files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.endswith('.wav')]
    transcripts = {}
    for audio_file in audio_files:
        text_file = audio_file.replace('.wav', '.txt')
        text_path = os.path.join(app.config['UPLOAD_FOLDER'], text_file)
        if os.path.exists(text_path):
            with open(text_path, 'r') as f:
                transcripts[audio_file] = f.read()
    return audio_files, transcripts
def analyze_sentiment(text):
    client = language_v1.LanguageServiceClient()
    document = language_v1.Document(content=text, type_=language_v1.Document.Type.PLAIN_TEXT)
    sentiment = client.analyze_sentiment(request={'document': document}).document_sentiment

    # Convert Sentiment Score to Words
    if sentiment.score > 0.25:
        sentiment_label = "Positive"
    elif sentiment.score < -0.25:
        sentiment_label = "Negative"
    else:
        sentiment_label = "Neutral"

    return f"Sentiment: {sentiment_label} "


@app.route('/uploaded_audio/<filename>')
def uploaded_audio(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
def get_tts_files():
    """Retrieves all generated TTS files from the TTS folder."""
    return [f for f in os.listdir(app.config['TTS_FOLDER']) if f.endswith('.mp3')]

@app.route('/', methods=['GET', 'POST'])
def index():
    files, transcripts = get_files()
    tts_files = get_tts_files()  # Fetch all stored TTS files
    return render_template('index.html', files=files, transcripts=transcripts, tts_files=tts_files)

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
        response = client.recognize(config=config, audio=audio)
        transcript = ''
        for result in response.results:
            transcript += result.alternatives[0].transcript + '\n'
        return transcript

    if file and allowed_file(file.filename):
        filename = datetime.now().strftime("%Y%m%d-%I%M%S%p") + '.wav'
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        transcript = transcribe_audio(file_path)
        sentiment_result = analyze_sentiment(transcript)

        transcript_filename = filename.replace('.wav', '.txt')
        transcript_path = os.path.join(app.config['UPLOAD_FOLDER'], transcript_filename)
        with open(transcript_path, 'w') as transcript_file:
            transcript_file.write(transcript + '\n\nSentiment Analysis:\n' + sentiment_result)

        return render_template('index.html', transcript=transcript, sentiment=sentiment_result, audio_file_url=url_for('uploaded_audio', filename=filename))

    return redirect('/')



@app.route('/upload/<filename>')
def get_file(filename):
    return send_file(filename)
@app.route('/serve_tts_file/<filename>')
def serve_tts_file(filename):
    return send_from_directory(app.config['TTS_FOLDER'], filename)

@app.route('/upload_audio', methods=['POST'])
def get_text():
    return redirect('/')


if not os.path.exists(tts_folder):
    os.makedirs(tts_folder)
app.config['TTS_FOLDER'] = tts_folder
    
@app.route('/upload_text', methods=['POST'])
def upload_text():
    text = request.form['text'].strip()
    
    if not text:
        flash("No text provided. Please enter some text to convert.")
        return redirect('/')
    
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

    # Generate filenames
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    audio_filename = f"{timestamp}.mp3"
    text_filename = f"{timestamp}.txt"
    
    audio_path = os.path.join(app.config['TTS_FOLDER'], audio_filename)
    text_path = os.path.join(app.config['TTS_FOLDER'], text_filename)

    # Save the audio file
    with open(audio_path, 'wb') as out:
        out.write(response.audio_content)

    # Save the text input as a .txt file
    with open(text_path, 'w', encoding="utf-8") as text_file:
        text_file.write(text)

    flash("Text successfully converted to speech and saved!")
    
    tts_files = get_tts_files()  # Fetch all stored TTS files
    return render_template('index.html', tts_files=tts_files, transcript=text)



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

