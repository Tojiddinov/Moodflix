import pandas as pd

# Load the CSV file
df = pd.read_csv("main_data.csv")

# Define mood mapping based on genres
mood_mapping = {
    "Action": "excited",
    "Drama": "melancholic",
    "Comedy": "joyful",
    "Horror": "anxious",
    "Sci-Fi": "curious",
    "Thriller": "alert",
    "Romance": "content",
    "Adventure": "intrigued",
    "Fantasy": "relaxed"
}

# Function to assign mood based on genre
def assign_mood(genre):
    for key, mood in mood_mapping.items():
        if key in genre:
            return mood
    return "neutral"  # Default mood if genre is not found

# Apply the function to create the "mood" column
df["mood"] = df["genres"].astype(str).apply(assign_mood)

# Save the updated CSV file
df.to_csv("main_data_updated.csv", index=False)

print("Mood column added successfully!")
