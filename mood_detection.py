import cv2
import numpy as np
from deepface import DeepFace
from collections import deque
import random

# Initialize webcam
cap = cv2.VideoCapture(0)

# Choose the best backend for face detection
DETECTION_BACKENDS = ["opencv", "mtcnn", "mediapipe"]
BACKEND = "opencv"  # Default backend

# Moving average filter to stabilize emotion detection
emotion_buffer = deque(maxlen=10)
confidence_threshold = 0.7  # Minimum confidence level for emotion detection

# Predefined movie recommendations based on emotions
MOVIE_RECOMMENDATIONS = {
    "happy": ["The Pursuit of Happyness", "Forrest Gump", "Inside Out", "The Grand Budapest Hotel"],
    "sad": ["Schindler's List", "The Green Mile", "Atonement", "Manchester by the Sea"],
    "neutral": ["Inception", "Interstellar", "The Matrix", "Blade Runner 2049"],
    "angry": ["Gladiator", "Mad Max: Fury Road", "John Wick", "Django Unchained"],
    "fear": ["The Conjuring", "A Quiet Place", "It", "Hereditary"],
    "surprise": ["Fight Club", "The Sixth Sense", "The Prestige", "Gone Girl"],
    "disgust": ["Se7en", "American Psycho", "Joker", "Requiem for a Dream"]
}

while True:
    # Capture frame from webcam
    ret, frame = cap.read()
    if not ret:
        print("Failed to capture image.")
        break

    # Save frame as a temporary image
    img_path = "static/dep.jpg"
    cv2.imwrite(img_path, frame)

    try:
        # Analyze the emotion
        analysis = DeepFace.analyze(img_path, actions=['emotion'], enforce_detection=False, detector_backend=BACKEND)
        emotion = analysis[0]['dominant_emotion']
        confidence = analysis[0]['emotion'][emotion]

        # Filter emotions based on confidence threshold
        if confidence >= confidence_threshold:
            emotion_buffer.append(emotion)

        # Determine stable mood from buffer
        if len(emotion_buffer) == emotion_buffer.maxlen:
            stable_emotion = max(set(emotion_buffer), key=emotion_buffer.count)

            # Recommend movies based on stable mood
            recommended_movies = MOVIE_RECOMMENDATIONS.get(stable_emotion, [])
            if recommended_movies:
                recommended_movie = random.choice(recommended_movies)
                print(f"Detected Emotion: {stable_emotion} (Confidence: {confidence:.2f})")
                print(f"Recommended Movie: {recommended_movie}")

        # Display detected emotion on the frame
        cv2.putText(frame, f"Emotion: {stable_emotion}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow('Mood Detection', frame)

    except Exception as e:
        print(f"Error detecting emotion: {e}")

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()
