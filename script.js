
const recordButton = document.getElementById('record');
const stopButton = document.getElementById('stop');
const audioElement = document.getElementById('audio');
const uploadForm = document.getElementById('uploadForm');
const audioDataInput = document.getElementById('audioData');
const timerDisplay = document.getElementById('timer');

let mediaRecorder;
let audioChunks = [];
let timerInterval;

function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
}

function startTimer() {
    let elapsedSeconds = 0;
    timerInterval = setInterval(() => {
        elapsedSeconds++;
        timerDisplay.textContent = formatTime(elapsedSeconds);
    }, 1000);
}

function stopTimer() {
    clearInterval(timerInterval);
    timerDisplay.textContent = '00:00';
}

recordButton.addEventListener('click', () => {
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            // Check for a compatible mimeType and set it for mediaRecorder
            const mimeType = 'audio/webm'; // Or 'audio/ogg'
            const options = { mimeType: mimeType };

            try {
                mediaRecorder = new MediaRecorder(stream, options);
            } catch (err) {
                console.error('Error accessing MediaRecorder:', err);
                return;
            }

            mediaRecorder.start();
            audioChunks = [];
            startTimer();

            mediaRecorder.ondataavailable = e => {
                audioChunks.push(e.data);
            };

            mediaRecorder.onstop = () => {
                const audioBlob = new Blob(audioChunks, { type: mimeType });
                const audioUrl = URL.createObjectURL(audioBlob);
                audioElement.src = audioUrl;
                audioElement.style.display = 'block';
                audioDataInput.value = audioBlob;

                // Handle file upload
                const formData = new FormData();
                formData.append('audio_data', audioBlob, 'recorded_audio.webm'); // or .ogg

                fetch('/upload', {
                    method: 'POST',
                    body: formData
                })
                    .then(response => response.text())
                    .then(data => {
                        console.log('Upload success:', data);
                        location.reload();
                    })
                    .catch(error => console.error('Upload failed:', error));
            };
        })
        .catch(error => {
            console.error('Microphone access denied:', error);
        });

        
    recordButton.disabled = true;
    stopButton.disabled = false;
});
stopButton.addEventListener('click', () => {
    mediaRecorder.stop();
    stopTimer();
    recordButton.disabled = false;
    stopButton.disabled = true;
});

// Initially disable stop button
stopButton.disabled = true;
