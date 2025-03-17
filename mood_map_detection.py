import cv2
import pandas as pd
from deepface import DeepFace


def detect_emotion():
    cap = cv2.VideoCapture(0)
    print("Capturing image... Look at the camera")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture image")
            break

        cv2.imshow("Press 'q' to capture", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    try:
        analysis = DeepFace.analyze(frame, actions=['emotion'])
        return analysis[0]['dominant_emotion']
    except Exception as e:
        print(f"Error detecting emotion: {e}")
        return None


def recommend_movies_by_mood(detected_emotion, df):
    mood_map = {
        "happy": ["happy", "excited"],
        "sad": ["sad", "melancholy"],
        "angry": ["angry", "furious"],
        "surprise": ["surprise", "shocked"],
        "fear": ["fear", "scared"],
        "neutral": ["neutral", "calm"],
        "confused": ["confused", "uncertain"]
    }

    moods = mood_map.get(detected_emotion, [])
    if not moods:
        return ["No recommendations found for this mood."]

    filtered_movies = df[df["mood"].isin(moods)]
    if filtered_movies.empty:
        return ["No recommendations found for this mood."]

    return filtered_movies["movie_title"].sample(min(5, len(filtered_movies))).tolist()


if __name__ == "__main__":
    df = pd.read_csv("main_data_updated.csv")  # Ensure this file exists with the correct structure
    detected_emotion = detect_emotion()
    if detected_emotion:
        print(f"Detected Emotion: {detected_emotion}")
        recommendations = recommend_movies_by_mood(detected_emotion, df)
        print(f"Recommended Movies: {recommendations}")
    else:
        print("Could not detect emotion. Try again.")
