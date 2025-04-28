import sounddevice as sd
from scipy.io.wavfile import write
import assemblyai as aai
import os
from dotenv import load_dotenv

load_dotenv()
# === 1. Record Audio ===
def record_audio(filename="audio.wav", duration=5, fs=16000):
    print(f"🎙️ Recording for {duration} seconds...")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()
    write(filename, fs, recording)
    print("✅ Recording saved as:", filename)

# === 2. Transcribe with AssemblyAI ===
def transcribe_audio(file_path):
    aai.settings.api_key =os.getenv("ASSEMBLY_API_KEY") # Replace with your actual key

    if not os.path.exists(file_path):
        raise FileNotFoundError("Audio file not found")

    config = aai.TranscriptionConfig(
        speech_model=aai.SpeechModel.nano,     # ✅ Use the nano model
        language_code="en"                    
    )

    transcriber = aai.Transcriber(config=config)
    transcript = transcriber.transcribe(file_path)

    if transcript.status == "error":
        raise RuntimeError(f"Transcription failed: {transcript.error}")
    
    print("\n📝 Transcribed Arabic Text:")
    print(transcript.text)
    return transcript.text

# === 3. Run the flow ===
if __name__ == "__main__":
    record_audio(duration=7)  # Record 7 seconds
    transcribe_audio("audio.wav")
