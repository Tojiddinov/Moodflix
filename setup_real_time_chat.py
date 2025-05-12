import os
import shutil

def setup_real_time_chat():
    """Set up the real-time chat template"""
    try:
        # Source and destination paths
        source_path = os.path.join(os.getcwd(), 'real_time_chat_template.html')
        dest_path = os.path.join(os.getcwd(), 'templates', 'real_time_chat.html')
        
        # Check if source file exists
        if not os.path.exists(source_path):
            print(f"Error: Source file {source_path} does not exist")
            return False
        
        # Create templates directory if it doesn't exist
        templates_dir = os.path.join(os.getcwd(), 'templates')
        if not os.path.exists(templates_dir):
            os.makedirs(templates_dir)
            print(f"Created templates directory: {templates_dir}")
        
        # Copy the file
        shutil.copy2(source_path, dest_path)
        print(f"Successfully copied template to: {dest_path}")
        
        return True
    
    except Exception as e:
        print(f"Error setting up real-time chat template: {str(e)}")
        return False

if __name__ == "__main__":
    print("Setting up MoodFlix Real-Time Voice Chat...")
    if setup_real_time_chat():
        print("Setup completed successfully!")
        print("You can now run 'python app_main.py' to start the application")
        print("Access the real-time chat interface at: http://localhost:5000/real_time_chat")
    else:
        print("Setup failed. Please check the error messages above.")
