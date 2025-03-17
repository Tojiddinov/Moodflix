import os
import sys
import tempfile
import argparse
import time
import json
from pathlib import Path

# Check if required packages are installed, if not install them
try:
    import requests
    from pydub import AudioSegment
    from pydub.playback import play
except ImportError:
    print("Installing required packages...")
    os.system('pip install requests pydub')
    import requests
    from pydub import AudioSegment
    from pydub.playback import play

# Install a specific version of the Deepgram SDK known to work
try:
    from deepgram import DeepgramClient, PrerecordedOptions, FileSource
except ImportError:
    print("Installing Deepgram SDK...")
    os.system('pip install -U "deepgram-sdk==2.11.0"')
    from deepgram import DeepgramClient, PrerecordedOptions, FileSource

# Set your Deepgram API key here
# Get a free API key at https://console.deepgram.com/signup
DEEPGRAM_API_KEY = "c525b7d253f4406b401793b6628ab20e04cd2a8f"  # Insert your API key between the quotes

# Alternatively, set it as an environment variable and uncomment these lines:
# import os
# os.environ["DEEPGRAM_API_KEY"] = "your-api-key-here"  # Or set this in your system environment
# DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

# API key format should look like: "sk_abcdef123456789..."

def check_api_key():
    """Check if the Deepgram API key is set"""
    if not DEEPGRAM_API_KEY:
        print("Error: Deepgram API key not found. Please set it in the script or as an environment variable DEEPGRAM_API_KEY.")
        print("You can get an API key from https://console.deepgram.com/signup")
        sys.exit(1)

def simple_transcribe(file_path):
    """Basic transcription using the Deepgram API directly with requests"""
    print(f"Transcribing file: {file_path}")
    start_time = time.time()
    
    try:
        # This is a simplified approach that doesn't use the SDK
        url = "https://api.deepgram.com/v1/listen"
        
        # Try with the Authorization header formatted differently
        headers = {
            "Authorization": f"Token {DEEPGRAM_API_KEY}",
            "Content-Type": "audio/wav"
        }
        
        print(f"Using API key: {DEEPGRAM_API_KEY[:5]}...{DEEPGRAM_API_KEY[-5:]}")
        print(f"Authorization header: {headers['Authorization']}")
        
        params = {
            "model": "nova-2",
            "smart_format": "true",
            "punctuate": "true",
            "language": "en"
        }
        
        with open(file_path, "rb") as audio:
            response = requests.post(url, headers=headers, params=params, data=audio)
        
        if response.status_code != 200:
            print(f"Error: API returned status {response.status_code}")
            print(response.text)
            return None
        
        data = response.json()
        elapsed_time = time.time() - start_time
        print(f"Transcription completed in {elapsed_time:.2f} seconds.")
        
        transcript = data["results"]["channels"][0]["alternatives"][0]["transcript"]
        confidence = data["results"]["channels"][0]["alternatives"][0]["confidence"]
        print(f"Confidence: {confidence:.2f}")
        
        return transcript
        
    except Exception as e:
        print(f"Error during transcription: {str(e)}")
        return None

def transcribe_audio_file(file_path):
    """Transcribe an audio file using Deepgram API"""
    check_api_key()
    
    try:
        # First try with the SDK
        print(f"Transcribing file using Deepgram SDK: {file_path}")
        start_time = time.time()
        
        deepgram = DeepgramClient(DEEPGRAM_API_KEY)
        
        with open(file_path, "rb") as audio:
            source = FileSource(audio)
            
            options = PrerecordedOptions(
                model="nova-2",
                smart_format=True,
                language="en",
                punctuate=True
            )
            
            response = deepgram.listen.prerecorded.v("1").transcribe_file(source, options)
            
        elapsed_time = time.time() - start_time
        print(f"Transcription completed in {elapsed_time:.2f} seconds.")
        
        transcript = response.results.channels[0].alternatives[0].transcript
        confidence = response.results.channels[0].alternatives[0].confidence
        print(f"Confidence: {confidence:.2f}")
        
        return transcript
        
    except Exception as e:
        print(f"SDK Error: {str(e)}")
        print("Falling back to direct API request method...")
        return simple_transcribe(file_path)

def transcribe_from_microphone(duration=5):
    """Record audio from microphone and transcribe it"""
    try:
        import sounddevice as sd
        import scipy.io.wavfile as wav
    except ImportError:
        print("Installing required packages for microphone recording...")
        os.system('pip install sounddevice scipy')
        import sounddevice as sd
        import scipy.io.wavfile as wav
    
    check_api_key()
    
    print(f"Recording for {duration} seconds... Speak now!")
    
    # Record audio
    fs = 16000  # Sample rate
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()  # Wait until recording is finished
    
    # Save recording to temporary file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
        temp_filename = temp_file.name
        wav.write(temp_filename, fs, recording)
    
    print("Recording finished. Transcribing...")
    
    # Transcribe the temporary file
    transcript = transcribe_audio_file(temp_filename)
    
    # Clean up the temporary file
    os.unlink(temp_filename)
    
    return transcript

def download_sample_audio():
    """Download a sample audio file for testing"""
    url = "https://dpgr.am/sample.wav"  # This is Deepgram's current sample URL
    output_file = "sample_audio.wav"
    
    print(f"Downloading sample audio from {url}...")
    response = requests.get(url, stream=True)
    
    if response.status_code == 200:
        with open(output_file, 'wb') as f:
            f.write(response.content)
        print(f"Sample audio downloaded to {output_file}")
        return output_file
    else:
        print(f"Failed to download sample audio: {response.status_code}")
        return None

def transcribe_with_features(file_path):
    """Transcribe audio file with additional Deepgram features - fallback to simpler API if needed"""
    check_api_key()
    
    print(f"Analyzing file with enhanced features: {file_path}")
    start_time = time.time()
    
    try:
        # First try with SDK
        deepgram = DeepgramClient(DEEPGRAM_API_KEY)
        
        with open(file_path, "rb") as audio:
            source = FileSource(audio)
            
            options = PrerecordedOptions(
                model="nova-2",
                smart_format=True,
                language="en",
                punctuate=True,
                summarize=True,
                detect_topics=True,
                sentiment=True
            )
            
            response = deepgram.listen.prerecorded.v("1").transcribe_file(source, options)
            
        elapsed_time = time.time() - start_time
        print(f"Analysis completed in {elapsed_time:.2f} seconds.")
        
        # Print the formatted response
        print("\nEnhanced Transcription Results:")
        print("="*50)
        print(f"Transcript: {response.results.channels[0].alternatives[0].transcript}")
        print(f"Confidence: {response.results.channels[0].alternatives[0].confidence:.2f}")
        
        # Print additional features if available
        if hasattr(response.results, 'summary') and response.results.summary:
            print(f"\nSummary: {response.results.summary.short}")
        
        if hasattr(response.results, 'topics') and response.results.topics:
            print("\nDetected Topics:")
            for topic in response.results.topics:
                print(f"- {topic}")
        
        if hasattr(response.results.channels[0].alternatives[0], 'sentiment') and response.results.channels[0].alternatives[0].sentiment:
            print("\nSentiment Analysis:")
            sentiment = response.results.channels[0].alternatives[0].sentiment
            print(f"Overall: {sentiment.overall}")
            print(f"Positive: {sentiment.positive}")
            print(f"Neutral: {sentiment.neutral}")
            print(f"Negative: {sentiment.negative}")
            
        return response.results.channels[0].alternatives[0].transcript
    
    except Exception as e:
        print(f"SDK Error in enhanced transcription: {str(e)}")
        print("Falling back to basic transcription...")
        return simple_transcribe(file_path)

def simple_enhanced_transcribe(file_path):
    """Enhanced transcription using direct API calls (fallback method)"""
    print(f"Attempting enhanced transcription via direct API...")
    start_time = time.time()
    
    try:
        url = "https://api.deepgram.com/v1/listen"
        
        headers = {
            "Authorization": f"Token {DEEPGRAM_API_KEY}",
            "Content-Type": "audio/wav"
        }
        
        params = {
            "model": "nova-2",
            "smart_format": "true",
            "punctuate": "true",
            "language": "en",
            "summarize": "true",
            "detect_topics": "true",
            "sentiment": "true"
        }
        
        with open(file_path, "rb") as audio:
            response = requests.post(url, headers=headers, params=params, data=audio)
        
        if response.status_code != 200:
            print(f"Error: API returned status {response.status_code}")
            print(response.text)
            return None
        
        data = response.json()
        elapsed_time = time.time() - start_time
        print(f"Enhanced transcription completed in {elapsed_time:.2f} seconds.")
        
        # Print the basic transcript
        transcript = data["results"]["channels"][0]["alternatives"][0]["transcript"]
        confidence = data["results"]["channels"][0]["alternatives"][0]["confidence"]
        
        print("\nEnhanced Transcription Results:")
        print("="*50)
        print(f"Transcript: {transcript}")
        print(f"Confidence: {confidence:.2f}")
        
        # Print additional features if available
        if "summary" in data["results"]:
            print(f"\nSummary: {data['results']['summary']['short']}")
        
        if "topics" in data["results"]:
            print("\nDetected Topics:")
            for topic in data["results"]["topics"]:
                print(f"- {topic}")
                
        if "sentiment" in data["results"]["channels"][0]["alternatives"][0]:
            sentiment = data["results"]["channels"][0]["alternatives"][0]["sentiment"]
            print("\nSentiment Analysis:")
            print(f"Overall: {sentiment['overall']}")
            print(f"Positive: {sentiment['positive']}")
            print(f"Neutral: {sentiment['neutral']}")
            print(f"Negative: {sentiment['negative']}")
        
        return transcript
        
    except Exception as e:
        print(f"Error during enhanced transcription: {str(e)}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Deepgram Speech Recognition Test Tool")
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-f", "--file", help="Path to audio file for transcription")
    group.add_argument("-m", "--mic", type=int, help="Record from microphone for N seconds")
    group.add_argument("-d", "--download", action="store_true", help="Download and transcribe a sample audio file")
    group.add_argument("-a", "--analyze", help="Analyze audio file with additional features (topics, sentiment, etc.)")
    group.add_argument("-s", "--simple", help="Use direct API method instead of SDK for transcription")
    
    args = parser.parse_args()
    
    if args.file:
        if not os.path.exists(args.file):
            print(f"Error: File {args.file} not found.")
            return
        transcript = transcribe_audio_file(args.file)
        if transcript:
            print("\nTranscription:")
            print("="*50)
            print(transcript)
            print("="*50)
    
    elif args.mic:
        transcript = transcribe_from_microphone(duration=args.mic)
        if transcript:
            print("\nTranscription:")
            print("="*50)
            print(transcript)
            print("="*50)
    
    elif args.download:
        file_path = download_sample_audio()
        if file_path:
            transcript = transcribe_audio_file(file_path)
            if transcript:
                print("\nTranscription:")
                print("="*50)
                print(transcript)
                print("="*50)
    
    elif args.analyze:
        if not os.path.exists(args.analyze):
            print(f"Error: File {args.analyze} not found.")
            return
        
        # Try with SDK first, then fall back to simple method if needed
        try:
            transcript = transcribe_with_features(args.analyze)
        except Exception as e:
            print(f"Error using SDK: {str(e)}")
            print("Falling back to direct API method...")
            transcript = simple_enhanced_transcribe(args.analyze)
            
    elif args.simple:
        if not os.path.exists(args.simple):
            print(f"Error: File {args.simple} not found.")
            return
        transcript = simple_transcribe(args.simple)
        if transcript:
            print("\nTranscription (Direct API):")
            print("="*50)
            print(transcript)
            print("="*50)

if __name__ == "__main__":
    print("Deepgram Speech Recognition Test Tool")
    print("-"*50)
    
    if len(sys.argv) == 1:
        print("Usage examples:")
        print("  Transcribe an audio file:")
        print("    python deepgram_test.py -f path/to/audio.mp3")
        print("\n  Record from microphone for 5 seconds and transcribe:")
        print("    python deepgram_test.py -m 5")
        print("\n  Download and transcribe a sample audio file:")
        print("    python deepgram_test.py -d")
        print("\n  Analyze audio with additional features (topics, sentiment, etc.):")
        print("    python deepgram_test.py -a path/to/audio.mp3")
        print("\n  Use direct API method (bypassing SDK):")
        print("    python deepgram_test.py -s path/to/audio.mp3")
        print("\nFor more options, use: python deepgram_test.py -h")
    else:
        main() 