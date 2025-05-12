import os
import time
import json
import threading
import queue
from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit
from voice_movie_recommender import VoiceMovieRecommender

# Initialize the voice recommender
voice_recommender = VoiceMovieRecommender()

# Queue for processing voice requests
request_queue = queue.Queue()
response_queue = queue.Queue()

def process_voice_request_worker():
    """Worker thread to process voice requests in the background"""
    while True:
        try:
            # Get request from queue
            request_data = request_queue.get()
            if request_data is None:  # Sentinel value to stop the thread
                break
                
            session_id = request_data.get('session_id')
            user_input = request_data.get('text')
            audio_path = request_data.get('audio_path')
            
            # Process the request based on input type
            if audio_path and os.path.exists(audio_path):
                # Process audio file
                result = voice_recommender.handle_web_request('process_input', {
                    'file_path': audio_path,
                    'source': 'real_time_chat'
                })
                # Clean up temporary file
                try:
                    if os.path.exists(audio_path):
                        os.unlink(audio_path)
                except Exception as e:
                    print(f"Error removing temporary file: {e}")
            elif user_input:
                # Process text input
                result = voice_recommender.handle_web_request('process_input', {
                    'text': user_input,
                    'source': 'real_time_chat'
                })
            else:
                result = {
                    'success': False,
                    'error': 'No valid input provided'
                }
            
            # Add response to the response queue with session ID
            response_queue.put({
                'session_id': session_id,
                'response': result
            })
            
            # Mark task as done
            request_queue.task_done()
            
        except Exception as e:
            print(f"Error in voice request worker: {e}")
            # Mark task as done even if there was an error
            request_queue.task_done()

def create_app(existing_app=None):
    """Create or configure the Flask app with real-time voice chat functionality"""
    if existing_app:
        app = existing_app
    else:
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'your-secret-key-here'
        
    # Initialize SocketIO
    socketio = SocketIO(app, cors_allowed_origins="*")
    
    # Start the worker thread
    worker_thread = threading.Thread(target=process_voice_request_worker)
    worker_thread.daemon = True
    worker_thread.start()
    
    @app.route('/real_time_chat')
    def real_time_chat():
        """Render the real-time chat interface"""
        return render_template('real_time_chat.html')
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        session_id = request.sid
        print(f"Client connected: {session_id}")
        emit('connection_response', {'status': 'connected', 'session_id': session_id})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        print(f"Client disconnected: {request.sid}")
    
    @socketio.on('voice_message')
    def handle_voice_message(data):
        """Handle incoming voice messages"""
        session_id = request.sid
        audio_data = data.get('audio')
        
        if not audio_data:
            emit('error', {'message': 'No audio data received'})
            return
            
        # Save audio data to temporary file
        import tempfile
        import base64
        
        try:
            # Decode base64 audio data
            audio_bytes = base64.b64decode(audio_data.split(',')[1])
            
            # Save to temporary file
            temp_dir = tempfile.mkdtemp()
            temp_path = os.path.join(temp_dir, f'recording_{session_id}.wav')
            
            with open(temp_path, 'wb') as f:
                f.write(audio_bytes)
                
            # Add to request queue
            request_queue.put({
                'session_id': session_id,
                'audio_path': temp_path
            })
            
            # Acknowledge receipt
            emit('processing', {'status': 'processing'})
            
        except Exception as e:
            emit('error', {'message': f'Error processing audio: {str(e)}'})
    
    @socketio.on('text_message')
    def handle_text_message(data):
        """Handle incoming text messages"""
        session_id = request.sid
        text = data.get('text', '').strip()
        
        if not text:
            emit('error', {'message': 'Empty message'})
            return
            
        # Add to request queue
        request_queue.put({
            'session_id': session_id,
            'text': text
        })
        
        # Acknowledge receipt
        emit('processing', {'status': 'processing'})
    
    def check_responses():
        """Check for responses and send them to clients"""
        while not response_queue.empty():
            try:
                response_data = response_queue.get_nowait()
                session_id = response_data.get('session_id')
                response = response_data.get('response')
                
                if session_id:
                    socketio.emit('response', response, room=session_id)
                
                response_queue.task_done()
            except queue.Empty:
                break
    
    # Set up background task to check for responses
    @socketio.on_namespace
    def background_thread():
        """Background thread to check for responses"""
        while True:
            socketio.sleep(0.1)  # Short sleep to prevent CPU hogging
            check_responses()
    
    # API endpoint for voice processing
    @app.route('/api/real_time_voice', methods=['POST'])
    def real_time_voice():
        """API endpoint for voice processing"""
        try:
            if 'audio_data' not in request.files:
                return jsonify({
                    'success': False,
                    'error': 'No audio file received'
                }), 400
                
            audio_file = request.files['audio_data']
            if not audio_file:
                return jsonify({
                    'success': False,
                    'error': 'Empty audio file'
                }), 400
                
            # Save audio file temporarily
            import tempfile
            temp_dir = tempfile.mkdtemp()
            temp_path = os.path.join(temp_dir, 'recording.wav')
            audio_file.save(temp_path)
            
            # Process immediately for API requests
            result = voice_recommender.handle_web_request('process_input', {
                'file_path': temp_path,
                'source': 'api'
            })
            
            # Clean up temporary file
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                if os.path.exists(temp_dir):
                    os.rmdir(temp_dir)
            except Exception as e:
                print(f"Error removing temporary files: {e}")
            
            return jsonify(result)
            
        except Exception as e:
            print(f"Error in real_time_voice API: {str(e)}")
            return jsonify({
                'success': False,
                'error': f"An error occurred: {str(e)}"
            }), 500
    
    # API endpoint for text processing
    @app.route('/api/real_time_text', methods=['POST'])
    def real_time_text():
        """API endpoint for text processing"""
        try:
            data = request.get_json()
            if not data or 'text' not in data:
                return jsonify({
                    'success': False,
                    'error': 'No text received'
                }), 400
                
            text = data.get('text', '').strip()
            if not text:
                return jsonify({
                    'success': False,
                    'error': 'Empty message'
                }), 400
                
            # Process immediately for API requests
            result = voice_recommender.handle_web_request('process_input', {
                'text': text,
                'source': 'api'
            })
            
            return jsonify(result)
            
        except Exception as e:
            print(f"Error in real_time_text API: {str(e)}")
            return jsonify({
                'success': False,
                'error': f"An error occurred: {str(e)}"
            }), 500
    
    return app, socketio

if __name__ == '__main__':
    app, socketio = create_app()
    # Run the app with SocketIO
    socketio.run(app, debug=True)
