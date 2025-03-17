import os
import sys
import requests
import argparse
import time
import wave
import struct
import math

# Check if required packages are installed, if not install them
try:
    from pydub import AudioSegment
except ImportError:
    print("Installing required packages...")
    os.system('pip install pydub')
    try:
        from pydub import AudioSegment
    except ImportError:
        print("Failed to install pydub. OGG format support may be limited.")

# Your Deepgram API key
DEEPGRAM_API_KEY = "c525b7d253f4406b401793b6628ab20e04cd2a8f"

def transcribe_file(file_path):
    """Transcribe an audio file using Deepgram API"""
    print(f"Transcribing file: {file_path}")
    start_time = time.time()
    
    try:
        url = "https://api.deepgram.com/v1/listen"
        
        # Format the API authorization header
        headers = {
            "Authorization": f"Token {DEEPGRAM_API_KEY}"
        }
        
        # Print partial key for verification (first 5 and last 5 characters)
        print(f"Using API key: {DEEPGRAM_API_KEY[:5]}...{DEEPGRAM_API_KEY[-5:]}")
        
        params = {
            "model": "nova-2",
            "smart_format": "true",
            "punctuate": "true"
        }
        
        # Try Method 1: Direct binary upload
        try:
            with open(file_path, "rb") as audio:
                # Get file size and print
                audio.seek(0, os.SEEK_END)
                file_size = audio.tell()
                audio.seek(0)
                print(f"Uploading file of size: {file_size/1024:.2f} KB")
                
                # Read the file content
                audio_data = audio.read()
                
                # Set the correct content type based on file extension
                content_type = "audio/wav"
                if file_path.lower().endswith(".mp3"):
                    content_type = "audio/mpeg"
                elif file_path.lower().endswith(".flac"):
                    content_type = "audio/flac"
                elif file_path.lower().endswith(".ogg"):
                    content_type = "audio/ogg"
                    
                direct_headers = headers.copy()
                direct_headers["Content-Type"] = content_type
                print(f"Attempt 1: Using direct binary upload with content type: {content_type}")
                
                # Direct method sending binary data
                response = requests.post(url, headers=direct_headers, params=params, data=audio_data)
                
                if response.status_code == 200:
                    print("Direct binary upload successful!")
                    data = response.json()
                    elapsed_time = time.time() - start_time
                    print(f"Transcription completed in {elapsed_time:.2f} seconds.")
                    return data["results"]["channels"][0]["alternatives"][0]["transcript"]
                else:
                    print(f"Direct upload failed with status {response.status_code}: {response.text}")
                    print("Trying fallback method...")
        except Exception as e:
            print(f"Error with direct upload: {str(e)}")
            print("Trying fallback method...")
        
        # Try Method 2: Multipart form upload
        try:
            print("Attempt 2: Using multipart form upload")
            with open(file_path, "rb") as audio:
                files = {"audio": (os.path.basename(file_path), audio, "audio/wav")}
                multipart_headers = headers.copy()  # No Content-Type, let requests set it
                
                response = requests.post(url, headers=multipart_headers, params=params, files=files)
                
                print(f"Response status code: {response.status_code}")
                
                if response.status_code == 200:
                    print("Multipart form upload successful!")
                    data = response.json()
                    elapsed_time = time.time() - start_time
                    print(f"Transcription completed in {elapsed_time:.2f} seconds.")
                    return data["results"]["channels"][0]["alternatives"][0]["transcript"]
                else:
                    print(f"Multipart upload failed with status {response.status_code}: {response.text}")
        except Exception as e:
            print(f"Error with multipart upload: {str(e)}")
        
        print("All upload methods failed.")
        return None
    
    except Exception as e:
        print(f"Error during transcription: {str(e)}")
        return None

def download_sample_audio():
    """Download a sample audio file for testing"""
    # List of sample audio URLs to try
    urls = [
        "https://github.com/mozilla/DeepSpeech/raw/master/data/smoke_test/smoke_test.wav",
        "https://github.com/mozilla/DeepSpeech/raw/master/data/ldc93s1/LDC93S1.wav",
        "https://github.com/sbconstantin/machine-learning/raw/master/sound-classifier/data/sample1.wav"
    ]
    
    output_file = "sample_audio.wav"
    
    for url in urls:
        try:
            print(f"Downloading sample audio from {url}...")
            response = requests.get(url, stream=True, timeout=10)  # Add 10 second timeout
            
            if response.status_code == 200:
                with open(output_file, 'wb') as f:
                    f.write(response.content)
                print(f"Sample audio downloaded to {output_file}")
                return output_file
            else:
                print(f"Failed to download sample audio: {response.status_code}")
        except Exception as e:
            print(f"Error downloading from {url}: {str(e)}")
    
    print("\nAll download attempts failed. Please provide your own audio file using:")
    print("python deepgram_test_simple.py -f path/to/your/audio.wav")
    return None

def create_test_audio(format='wav'):
    """Create a simple test audio file with a sine wave
    
    Args:
        format (str): Audio format to create - 'wav' or 'ogg'
    """
    print(f"Creating a test audio file in {format.upper()} format...")
    
    # Base filename without extension
    base_filename = "test_audio"
    output_file = f"{base_filename}.{format}"
    
    try:
        # Parameters for the WAV file
        duration = 3  # seconds
        sample_rate = 16000  # Hz
        frequency = 440  # A4 note frequency
        
        # Always create WAV first (we'll convert to OGG if needed)
        wav_file = f"{base_filename}.wav"
        
        # Create a sine wave
        samples = []
        for i in range(int(duration * sample_rate)):
            sample = int(32767 * math.sin(2 * math.pi * frequency * i / sample_rate))
            samples.append(sample)
        
        # Write the WAV file
        with wave.open(wav_file, 'w') as wf:
            wf.setparams((1, 2, sample_rate, 0, 'NONE', 'not compressed'))
            for sample in samples:
                wf.writeframes(struct.pack('h', sample))
        
        # If OGG format is requested, convert the WAV to OGG
        if format.lower() == 'ogg':
            try:
                audio = AudioSegment.from_wav(wav_file)
                audio.export(output_file, format="ogg")
                os.remove(wav_file)  # Remove the temporary WAV file
            except Exception as e:
                print(f"Error converting to OGG format: {str(e)}")
                print("Falling back to WAV format.")
                output_file = wav_file
        
        print(f"Created test audio file: {output_file}")
        return output_file
    
    except Exception as e:
        print(f"Error creating test audio: {str(e)}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Simple Deepgram Transcription Tool")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-f", "--file", help="Path to audio file for transcription")
    group.add_argument("-d", "--download", action="store_true", help="Download and transcribe a sample audio file")
    group.add_argument("-c", "--create", action="store_true", help="Create a test audio file locally")
    
    # Add format option
    parser.add_argument("--format", choices=["wav", "ogg"], default="wav", 
                      help="Audio format to use when creating test file (default: wav)")
    
    args = parser.parse_args()
    
    if args.file:
        if not os.path.exists(args.file):
            print(f"Error: File {args.file} not found.")
            return
        transcript = transcribe_file(args.file)
        if transcript:
            print("\nTranscription:")
            print("="*50)
            print(transcript)
            print("="*50)
    
    elif args.download:
        file_path = download_sample_audio()
        if file_path and os.path.exists(file_path):
            transcript = transcribe_file(file_path)
            if transcript:
                print("\nTranscription:")
                print("="*50)
                print(transcript)
                print("="*50)
    elif args.create:
        file_path = create_test_audio(format=args.format)
        if file_path and os.path.exists(file_path):
            transcript = transcribe_file(file_path)
            if transcript:
                print("\nTranscription:")
                print("="*50)
                print(transcript)
                print("="*50)

if __name__ == "__main__":
    print("Simple Deepgram Transcription Tool")
    print("-"*50)
    
    if len(sys.argv) == 1:
        print("Usage examples:")
        print("  Transcribe an audio file:")
        print("    python deepgram_test_simple.py -f path/to/audio.mp3")
        print("\n  Download and transcribe a sample audio file:")
        print("    python deepgram_test_simple.py -d")
        print("\n  Create a test audio file:")
        print("    python deepgram_test_simple.py -c")
        print("\n  Create a test audio file in OGG format:")
        print("    python deepgram_test_simple.py -c --format ogg")
        print("\nFor more options, use: python deepgram_test_simple.py -h")
    else:
        main() 