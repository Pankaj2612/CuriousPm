# AI Voice Replacement for Video

This project provides a proof of concept (PoC) for replacing the audio of a video with AI-generated voice using Python. The application utilizes various AI models to transcribe, correct, and synthesize audio, ensuring a seamless and improved audio experience.

## Features

- **Upload Video:** Users can upload a video file with audio that may contain filler words and grammatical mistakes.
- **Audio Transcription:** The audio is transcribed using the `whisper_timestamp` library.
- **Text Correction:** The transcribed text is corrected using the GPT-4o model via Azure OpenAI.
- **AI-Generated Voice:** The corrected transcription is converted back to audio using `gTTS`.
- **Audio Replacement:** The new audio is synchronized and replaces the original audio in the video.

## Requirements

- Python 3.x
- Libraries:
  - `flask`
  - `moviepy`
  - `pydub`
  - `google-cloud-speech`
  - `gTTS`
  - `openai`
  - `whisper-timestamp`

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/AI-Voice-Replacement-for-Video.git
   cd AI-Voice-Replacement-for-Video

Video Demo -> https://drive.google.com/file/d/19o-32pXnRt10gYNePKIOde4b-vdVUo4C/view?usp=drive_link
