# Moodflix: Voice-Activated Movie Recommendation System
## Final Project Presentation

---

### Slide 1: Title Slide

**Moodflix: Voice-Activated Movie Recommendation System**

**Group Members:**
- Student Name 1
- Student Name 2

**Supervisor:** Dr. [Supervisor Name]

---

### Slide 2: Introduction & Problem Statement

**Problem:**
- Most movie recommendation systems rely solely on text input or past viewing history
- Voice-based preferences are underutilized despite being more natural and expressive
- Capturing mood and emotional state is challenging but crucial for personalized recommendations

**Importance:**
- Voice interfaces are becoming ubiquitous (smart speakers, virtual assistants)
- Emotional context significantly enhances recommendation quality
- Creates a more accessible and natural user experience

---

### Slide 3: Objectives

**Primary Objectives:**
- Create a voice-activated movie recommendation system
- Implement advanced sentiment analysis for mood detection
- Develop accurate preference extraction from natural language
- Design an intuitive, responsive user interface
- Integrate with comprehensive movie databases

---

### Slide 4: Project Scope

**In Scope:**
- Voice input processing and transcription
- Natural language preference extraction
- Sentiment analysis for mood detection
- Multi-factor movie recommendations
- Web-based responsive user interface

**Out of Scope:**
- Mobile app development
- Integration with streaming platforms
- Multi-language support (future enhancement)
- Voice authentication

---

### Slide 5: Methodology

**Approach:**
- Agile development methodology with iterative improvements
- User-centered design process
- Test-driven development for core algorithms
- Continuous integration workflow
- Regular usability testing and feedback incorporation

**System Architecture:**
- Frontend: HTML5, CSS3, JavaScript, Bootstrap
- Backend: Python with Flask framework
- API Integration: Deepgram for speech-to-text
- Database: Structured movie metadata with sentiment mappings

---

### Slide 6: Technologies Used

**Key Technologies:**
- **Deepgram API**: State-of-the-art speech recognition
- **Flask**: Python web framework for backend services
- **Bootstrap**: Responsive frontend framework
- **AJAX**: Asynchronous JavaScript for dynamic content
- **scikit-learn**: Machine learning for sentiment analysis
- **pandas/numpy**: Data processing and analysis
- **TMDb API**: Movie metadata and information

---

### Slide 7: Implementation Progress - Voice Recognition

**Completed Components:**
- **Speech-to-Text Integration**: Successfully implemented Deepgram API
- **Audio Recording Interface**: Browser-based voice capture system
- **Voice Preference Extraction**: Algorithm for detecting genres, actors, era preferences

**Demo Screenshot:** [Include screenshot of voice input interface]

---

### Slide 8: Implementation Progress - Recommendation Engine

**Completed Components:**
- **Preference Matching Algorithm**: Scores and ranks movies based on extracted preferences
- **Multi-factor Recommendation**: Considers genres, mood, actors, directors, and era
- **Database Integration**: Connected to comprehensive movie dataset

**Code Implementation:**
```python
def recommend_movies(self, limit=5):
    """Recommend movies based on user preferences"""
    # Score each movie based on matching preferences
    scored_movies = []
    for movie in self.movie_database:
        score = 0
        
        # Score for matching genres
        if self.user_preferences["genres"]:
            for genre in self.user_preferences["genres"]:
                if genre in movie["genres"]:
                    score += 3
        
        # [Additional scoring logic...]
        
    # Sort and return top recommendations
    scored_movies.sort(key=lambda x: x[1], reverse=True)
    return [movie for movie, score in scored_movies[:limit]]
```

---

### Slide 9: Implementation Progress - UI Development

**Completed Components:**
- **Responsive Web Interface**: Works on desktop and mobile devices
- **Real-time Results Display**: Dynamic updates of recommendations
- **Interactive Elements**: Voice recording button, movie cards, filtering options

**Demo Screenshot:** [Include screenshot of recommendation results]

---

### Slide 10: Implementation Progress - Testing Framework

**Completed Components:**
- **Unit Testing Framework**: Tests for core recommendation functions
- **Preference Extraction Tests**: Verification of natural language parsing
- **Integration Tests**: End-to-end system testing with sample voice inputs

**Sample Test Results:**
```
test_preference_extraction_genres ✓
test_preference_extraction_actors ✓
test_preference_extraction_era ✓
test_preference_extraction_mood ✓
test_movie_recommendation ✓
test_multiple_preference_extraction ✓
```

---

### Slide 11: Challenges Faced

**Technical Challenges:**
- **Speech Recognition Accuracy**: Addressed by implementing Deepgram API and fine-tuning
- **Natural Language Parsing**: Created custom regex patterns and keyword detection
- **Mood Detection from Text**: Developed sentiment mapping and keyword associations
- **Database Limitations**: Enhanced movie metadata with additional mood and theme tags

**Other Challenges:**
- **Performance Optimization**: Improved database query efficiency
- **Browser Compatibility**: Addressed audio API inconsistencies across browsers

---

### Slide 12: Individual Contributions

**Team Member 1:**
- Voice recognition integration
- Natural language processing algorithms
- Preference extraction engine
- Unit test development

**Team Member 2:**
- User interface design and implementation
- Database setup and management
- Movie recommendation algorithms
- Documentation and presentation

---

### Slide 13: Supervisor Meetings & Feedback

**Meeting 1 (Date):**
- Suggested improving preference extraction accuracy
- Recommended integrating with professional speech-to-text API
- Advised on project scope and prioritization

**Meeting 2 (Date):**
- Provided feedback on UI design and usability
- Suggested additional test cases for recommendation engine
- Recommended more comprehensive error handling

**Meeting 3 (Date):**
- Reviewed implementation progress and system architecture
- Suggested optimization for recommendation algorithm
- Provided guidance on final presentation structure

---

### Slide 14: Remaining Work & Next Steps

**Remaining Tasks:**
- Enhanced error handling and edge cases
- Optimization of recommendation algorithms
- User experience refinements
- Additional testing and performance optimization

**Timeline:**
- Week 1-2: Complete error handling and optimization
- Week 3: Finalize user interface refinements
- Week 4: Comprehensive testing and bug fixes
- Week 5: Final documentation and project submission

---

### Slide 15: Conclusion

**Key Achievements:**
- Successfully implemented voice-activated movie recommendation system
- Developed accurate preference extraction from natural language
- Created intuitive user interface with dynamic recommendations
- Built comprehensive testing framework ensuring reliability

**Project Readiness:**
- Core functionality is complete and functional
- Remaining tasks are primarily refinements and optimizations
- On track for successful final submission
- System demonstrates innovative approach to movie recommendations

---

### Thank You!

**Questions?**

**GitHub Repository:** [github.com/Tojiddinov/Moodflix](https://github.com/Tojiddinov/Moodflix)

**Demo Available Upon Request** 