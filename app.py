import os
from gtts import gTTS
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_audioclips
import requests
import whisper_timestamped as whisper
import json
import openai
import shutil
from flask import Flask, jsonify, render_template, request
from prompt import system_prompt
from dotenv import load_dotenv
from pydub import AudioSegment

load_dotenv()

app = Flask(__name__)

azure_openai_key = os.getenv("AZURE_OPENAI_KEY")  #
azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
#  Replace with your actual endpoint URL


@app.route("/")
def homepage():
    return render_template("homepage.html")


@app.route("/video", methods=["POST"])
def process_video():
    if "file" in request.files:
        video = request.files["file"]
        if not (os.path.exists("uploads")):
            os.makedirs("uploads")
        video_path = os.path.join("uploads", video.filename)

        try:
            video.save(video_path)
            response = extract_audio_from_video(video_path)
            return response
        except Exception as e:

            return jsonify({"message": f"Error processing video: {str(e)}"}), 500
    else:

        return jsonify({"message": "No video received"}), 400


def extract_audio_from_video(video_dir):
    try:
        video = VideoFileClip(video_dir)
        if video.audio is not None:
            if not os.path.exists("audio_file"):
                os.mkdir("audio_file")
            audio_path = f"audio_file/output_audio.mp3"
            video.audio.write_audiofile(audio_path)
            video.close()
            # Proceed to the next step after audio extraction
            return extract_text_from_audio(audio_path)
        else:
            # Return a JSON response if there's no audio in the video
            return (
                jsonify({"message": "The video does not contain any audio stream."}),
                400,
            )
    except Exception as e:
        # Return a JSON response in case of an error
        return jsonify({"message": f"An error occurred: {e}"}), 500


def extract_text_from_audio(audio_dir):
    try:
        # Load and transcribe the audio
        audio = whisper.load_audio(audio_dir)
        model = whisper.load_model("tiny", device="cpu")
        result = model.transcribe(audio, language="en")

        text = json.dumps(result["text"], indent=2, ensure_ascii=False)
        segments = json.dumps(result["segments"], indent=2, ensure_ascii=False)
        segment_to_Arr = json.loads(segments)
        segments_obj = []

        for ob in segment_to_Arr:
            obj = {
                "ID": ob["id"],
                "Text": ob["text"],
                "Start": ob["start"],
                "End": ob["end"],
            }
            segments_obj.append(obj)

        full_textsegment = {"context": text, "segments": segments_obj}

        # Call AI response function and return result
        return get_response_from_AI(str(full_textsegment))

    except Exception as e:
        # Return a JSON response in case of an error
        return jsonify({"message": f"An error occurred during transcription: {e}"}), 500


def get_response_from_AI(text):
    try:
        # Setting up headers for the API request
        # Define the headers needed for the API request, including the API key for authentication.
        headers = {
            "Content-Type": "application/json",  # Specifies that we are sending JSON data
            "api-key": azure_openai_key,  # The API key for authentication
        }

        # Data to be sent to Azure OpenAI
        # Define the payload, which includes the message prompt and token limit.
        # **** This is where you can customize the message prompt and token limit. ****
        data = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": text,
                },
            ],  # The message we want the model to respond to
            # Limit the response length
        }

        # Making the POST request to the Azure OpenAI endpoint
        # Send the request to the Azure OpenAI endpoint using the defined headers and data.
        response = requests.post(f"{azure_openai_endpoint}", headers=headers, json=data)

        # Check if the request was successful
        # Handle the response, checking the status and displaying the result.
        if response.status_code == 200:
            result = response.json()  # Parse the JSON response
            full_result = result["choices"][0]["message"]["content"].strip()
            print(full_result)
            full_result = json.loads(full_result)
            print(full_result)
            return text_to_audio(full_result)
            # Display the response content from the AI
        else:
            # Handle errors if the request was not successful
            return print(
                f"Failed to connect or retrieve response: {response.status_code} - {response.text}"
            )
    except Exception as e:
        # Handle any exceptions that occur during the request
        print(f"Failed to connect or retrieve response: {str(e)}")


def text_to_audio(data):
    print(type(data))
    audio_segments = []

    for segment in data["segments"]:
        text = segment["Text"]
        start_time = segment["Start"]
        end_time = segment["End"]

        # Calculate duration in milliseconds
        duration_ms = (end_time - start_time) * 1000

        # Generate audio from text
        tts = gTTS(text=text, lang="en")
        if not os.path.exists("audio_segments"):
            os.mkdir("audio_segments")
        tts_file = f"audio_segments/segment_{segment['ID']}.mp3"
        tts.save(tts_file)

        # Load the audio file
        audio_segment = AudioSegment.from_mp3(tts_file)

        # Ensure audio segment matches the required duration
        if duration_ms > 0:
            if len(audio_segment) < duration_ms:
                # Pad with silence if shorter than required duration
                silence_duration = duration_ms - len(audio_segment)
                silence = AudioSegment.silent(duration=silence_duration)
                audio_segment += silence
            elif len(audio_segment) > duration_ms:
                # Trim if longer than required duration
                audio_segment = audio_segment[:duration_ms]

        audio_segments.append(audio_segment)

    audio_segment.export(tts_file, format="mp3")
    return append_audio(data["segments"])


def append_audio(segments):
    # Check if the uploads directory exists
    if not os.path.exists("uploads"):
        os.mkdir("uploads")

    if os.path.exists("uploads"):

        # List all files in the uploads directory
        video_files = [
            f for f in os.listdir("uploads") if f.endswith((".mp4", ".avi", ".mov"))
        ]

        # If there are no video files, return an error
        if not video_files:
            return print("No video files found in the uploads directory.")

        # Get the first video file (or modify this to suit your needs)
        video_filename = video_files[0]  # or handle multiple files as needed
        video_path = os.path.join("uploads", video_filename)

        video = VideoFileClip(video_path)  # Load the video using the found filename
    else:
        return print("Uploads directory does not exist.")

    audio_clips = []

    # Load each audio segment based on its ID and sync it to the correct position
    for segment in segments:
        audio_file_path = f"audio_segments/segment_{segment['ID']}.mp3"

        if not os.path.exists(audio_file_path):
            print(f"Audio file for segment {segment['ID']} not found.")
            continue

        try:
            audio_clip = AudioFileClip(audio_file_path)

            # Skip if the audio clip has zero duration
            if audio_clip.duration == 0:
                print(
                    f"Audio file segment {segment['ID']} is empty or has zero duration."
                )
                continue

            # Set its start and duration
            audio_clip = audio_clip.set_start(segment["Start"])
            audio_clips.append(audio_clip)

        except Exception as e:
            print(f"Error processing audio for segment {segment['ID']}: {str(e)}")
            continue

    # Ensure audio_clips is not empty before concatenating
    if not audio_clips:
        print("No valid audio clips found. Exiting.")
        return

    # Concatenate all the audio clips into a single track
    final_audio = concatenate_audioclips(audio_clips)

    # Set the final audio to the video
    final_video = video.set_audio(final_audio)

    # Save the output video with synced audio
    final_video.write_videofile(
        "static/output_video.mp4", codec="libx264", audio_codec="aac"
    )
    return render_template("transcription.html", video_path="static/output_video.mp4")



if __name__ == "__main__":
    app.run(debug=True)
