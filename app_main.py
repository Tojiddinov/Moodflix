"""
Main entry point for the MoodFlix application.
"""
from app import create_app
from real_time_voice_chat import create_app as create_socketio_app

# Create the Flask application
app = create_app()

# Integrate the real-time voice chat with the main app
app, socketio = create_socketio_app(app)

if __name__ == '__main__':
    # Run the app with SocketIO instead of the regular Flask server
    print("Starting MoodFlix application...")
    print(f"Visit http://localhost:5000 to access the application")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
