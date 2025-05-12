"""
Simplified WebSocket service for real-time chat communication
"""
import json
import time
import threading
from flask import Flask, request
from flask_socketio import SocketIO, emit, join_room, leave_room

# Global SocketIO instance to be used across the application
socketio = None
active_sessions = {}

def create_socketio():
    """Create a SocketIO instance without attaching it to an app yet
    
    Returns:
        SocketIO: The created SocketIO instance
    """
    return SocketIO(cors_allowed_origins="*", async_mode='threading')

def init_socketio(app, socket_instance=None):
    """Initialize the SocketIO instance with the Flask app
    
    Args:
        app: The Flask application instance
        socket_instance: Optional existing SocketIO instance
    
    Returns:
        SocketIO: The initialized SocketIO instance
    """
    global socketio
    
    if socket_instance:
        socketio = socket_instance
        socketio.init_app(app)
    else:
        socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
    
    # Register event handlers
    register_handlers(socketio)
    
    return socketio

def register_handlers(socketio_instance):
    """Register all WebSocket event handlers
    
    Args:
        socketio_instance: The SocketIO instance
    """
    @socketio_instance.on('connect')
    def handle_connect():
        """Handle client connection"""
        print(f"Client connected: {request.sid}")
        emit('connection_response', {'status': 'connected', 'message': 'Connected to MovieBuddyAI'})

    @socketio_instance.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        print(f"Client disconnected: {request.sid}")
        # Clean up any user session if necessary
        for session_id, data in active_sessions.items():
            if data.get('socket_id') == request.sid:
                active_sessions[session_id]['connected'] = False
                break

    @socketio_instance.on('join_session')
    def handle_join_session(data):
        """Handle client joining a session
        
        Args:
            data (dict): Contains session_id and user information
        """
        session_id = data.get('session_id')
        if not session_id:
            emit('error', {'message': 'No session ID provided'})
            return
            
        # Create or update session data
        if session_id not in active_sessions:
            active_sessions[session_id] = {
                'socket_id': request.sid,
                'connected': True,
                'last_activity': time.time(),
                'user_info': data.get('user_info', {})
            }
        else:
            active_sessions[session_id]['socket_id'] = request.sid
            active_sessions[session_id]['connected'] = True
            active_sessions[session_id]['last_activity'] = time.time()
            
        # Join the room for this session
        join_room(session_id)
        emit('session_joined', {'session_id': session_id, 'status': 'active'}, room=session_id)
        
    @socketio_instance.on('leave_session')
    def handle_leave_session(data):
        """Handle client leaving a session
        
        Args:
            data (dict): Contains session_id
        """
        session_id = data.get('session_id')
        if not session_id:
            return
            
        # Update session status
        if session_id in active_sessions:
            active_sessions[session_id]['connected'] = False
            
        # Leave the room
        leave_room(session_id)
        
    @socketio_instance.on('chat_message')
    def handle_chat_message(data):
        """Handle new chat messages from client
        
        Args:
            data (dict): Contains session_id, message content, and type
        """
        session_id = data.get('session_id')
        if not session_id:
            emit('error', {'message': 'No session ID provided'})
            return
            
        message = data.get('message', '')
        message_type = data.get('type', 'text')  # text, voice, etc.
        
        # Update session activity
        if session_id in active_sessions:
            active_sessions[session_id]['last_activity'] = time.time()
        
        # Emit typing indicator to the client
        emit('typing_indicator', {'status': 'typing'}, room=session_id)
        
        # Process message in a separate thread to not block
        threading.Thread(target=process_message, 
                        args=(session_id, message, message_type)).start()

def process_message(session_id, message, message_type):
    """Process an incoming message and emit response
    
    Args:
        session_id (str): The session ID
        message (str): The message content
        message_type (str): The type of message (text, voice)
    """
    from voice_movie_recommender import VoiceMovieRecommender
    
    # Access global voice recommender or create new instance
    from main import voice_recommender
    
    try:
        # Process the message
        if message_type == 'text':
            result = voice_recommender.handle_web_request("text_input", {
                "text": message,
                "session_id": session_id,
                "source": "websocket"
            })
        elif message_type == 'voice':
            # Voice data should already be saved to a temp file by the client handler
            result = voice_recommender.handle_web_request("voice_input", {
                "file_path": message,  # This should be a path to the saved audio file
                "session_id": session_id,
                "source": "websocket"
            })
        
        # Send the response back through WebSocket
        if result.get('success'):
            # Send typing indicator (animated)
            socketio.emit('typing_indicator', {'status': 'active'}, room=session_id)
            
            # Convert recommendations to a sendable format
            recommendations = result.get('recommendations', [])
            
            # Send the response in chunks for a more natural conversation feel
            response = result.get('response', '')
            if response:
                # Send chunks of the response to simulate typing
                chunks = split_response_into_chunks(response)
                
                for i, chunk in enumerate(chunks):
                    # Small delay between chunks to simulate typing
                    time.sleep(0.5)
                    
                    # Is this the final chunk?
                    is_final = (i == len(chunks) - 1)
                    
                    socketio.emit('chat_response', {
                        'content': chunk,
                        'is_final': is_final,
                        'recommendations': recommendations if is_final else [],
                        'transcript': result.get('transcript', '') if is_final else None
                    }, room=session_id)
                
            # Send end of typing
            socketio.emit('typing_indicator', {'status': 'inactive'}, room=session_id)
            
        else:
            # Send error
            socketio.emit('error', {
                'message': result.get('error', 'An error occurred processing your request')
            }, room=session_id)
    
    except Exception as e:
        # Handle exceptions
        socketio.emit('error', {
            'message': f"An error occurred: {str(e)}"
        }, room=session_id)

def split_response_into_chunks(response, max_chunk_size=100):
    """Split a response into chunks for streaming
    
    Args:
        response (str): The full response text
        max_chunk_size (int): Maximum size of each chunk
        
    Returns:
        list: List of response chunks
    """
    # Split by sentences for more natural breaks
    import re
    sentences = re.split(r'(?<=[.!?])\s+', response)
    
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        # If adding this sentence would exceed max size, save current chunk and start new one
        if len(current_chunk) + len(sentence) > max_chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = sentence
        else:
            if current_chunk:
                current_chunk += " " + sentence
            else:
                current_chunk = sentence
    
    # Add the last chunk if not empty
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks
