import speech_recognition as sr
import pyaudio
import wave
import threading

class SpeechToText:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.recording = False
        self.frames = []
        self.audio_filename = "recorded_audio.wav"
        self.p = pyaudio.PyAudio()


    def record_audio(self):
        self.frames = []
        self.recording = True
        self.stream = self.p.open(format=pyaudio.paInt16,
                                channels=1,
                                rate=44100,
                                input=True,
                                frames_per_buffer=1024)
        while self.recording:
            data = self.stream.read(1024)
            self.frames.append(data)
        self.stream.close()

    def stop_recording(self):
        self.recording = False

    def save_audio(self):
        with wave.open(self.audio_filename, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
            wf.setframerate(44100)
            wf.writeframes(b''.join(self.frames))

    def transcribe_audio(self):
        text = ""
        with sr.AudioFile(self.audio_filename) as source:
            audio = self.recognizer.record(source)
        try:
            text = self.recognizer.recognize_google(audio)
            success = True
        except sr.UnknownValueError:
            success = False
            print("Google Speech Recognition could not understand audio")
        except sr.RequestError as e:
            success = False
            print(f"Could not request results from Google Speech Recognition service; {e}")

        return success, text

    def button_press(self):
        self.record_thread = threading.Thread(target=self.record_audio)
        self.record_thread.start()

    def button_release(self):
        self.stop_recording()
        self.record_thread.join()
        self.save_audio()
        return self.transcribe_audio()

if __name__ == "__main__":
    stt = SpeechToText()
    
    print("Press Enter to start recording, release Enter to stop recording and transcribe.")
    input("Press Enter to start...")
    stt.button_press()
    input("Press Enter to stop...")
    stt.button_release()
