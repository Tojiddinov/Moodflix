# Moodflix - Movie Recommendation System with Sentiment Analysis

![Moodflix Logo](static/Untitled%20design%20(2).png)

Moodflix is an AI-powered movie recommendation platform that suggests movies based on your current mood. Using advanced sentiment analysis and machine learning algorithms, it provides personalized movie recommendations tailored to how you're feeling.

## Features

- **Mood-Based Recommendations**: Get movie suggestions based on how you're feeling (e.g., joyful, melancholy, inspired)
- **Search Functionality**: Find detailed information about specific movies
- **Trending Movies**: Discover what's popular right now
- **Movie Details**: View comprehensive information including cast, reviews, and similar movies
- **Responsive Design**: Optimized for all devices from mobile to desktop
- **Interactive UI**: Modern interface with animations and visual feedback

## Technologies Used

- **Frontend**: HTML5, CSS3, JavaScript, jQuery
- **CSS Framework**: Bootstrap 4
- **Icons**: Font Awesome
- **Autocomplete**: @tarekraafat/autocomplete.js
- **Backend**: Python with Flask framework
- **Machine Learning**: Sentiment analysis for mood-based recommendations
- **API Integration**: Movie database APIs for content

## Setup and Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/AJAX-Movie-Recommendation-System-with-Sentiment-Analysis.git
   cd AJAX-Movie-Recommendation-System-with-Sentiment-Analysis
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables (if necessary):
   ```
   export FLASK_APP=app.py
   export FLASK_ENV=development
   ```

5. Run the application:
   ```
   flask run
   ```

6. Open your browser and navigate to `http://localhost:5000`

## Usage

### Search for a Movie
Enter a movie title in the search box on the homepage and click "Search" to view details about that specific movie.

### Get Mood-Based Recommendations
Click on any mood button (like "Joy 🌟", "Melancholy 🌧️", etc.) to receive movie recommendations tailored to that mood.

### Explore Trending Movies
Scroll down to see what movies are currently trending and click on any movie poster to see more details.

## Project Structure

```
├── app.py                  # Main Flask application
├── static/                 # Static assets
│   ├── images/             # Image files
│   ├── style.css           # Additional CSS styles
│   └── recommend.js        # JavaScript for recommendations
├── templates/              # HTML templates
│   ├── home.html           # Homepage template
│   ├── movie_details.html  # Movie details page
│   └── recommend.html      # Recommendations page
├── models/                 # Machine learning models
├── requirements.txt        # Project dependencies
└── README.md               # Project documentation
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Acknowledgments

- Movie data provided by [TMDb](https://www.themoviedb.org/) or similar APIs
- Inspired by modern streaming platforms and recommendation systems
- Special thanks to all contributors who helped in building this project

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

Made with ❤️ by Moodflix Team


