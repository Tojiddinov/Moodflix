# MoodFlix Project Structure

```
moodflix/
├── app/                      # Application package
│   ├── __init__.py           # Initialize app
│   ├── api/                  # API endpoints
│   │   ├── __init__.py
│   │   ├── routes.py         # API routes
│   │   └── models.py         # API models/schemas
│   ├── core/                 # Core functionality
│   │   ├── __init__.py
│   │   ├── config.py         # Configuration
│   │   ├── security.py       # Security utilities
│   │   └── logging.py        # Logging configuration
│   ├── services/             # Business logic
│   │   ├── __init__.py
│   │   ├── movie_service.py  # Movie recommendation logic
│   │   ├── speech_service.py # Speech recognition/synthesis
│   │   └── mood_service.py   # Mood analysis
│   ├── models/               # Data models
│   │   ├── __init__.py
│   │   ├── movie.py          # Movie model
│   │   └── user.py           # User model
│   ├── static/               # Static files (CSS, JS, images)
│   └── templates/            # HTML templates
├── scripts/                  # Utility scripts
│   └── db_setup.py           # Database setup script
├── tests/                    # Test suite
│   ├── __init__.py
│   ├── test_api.py           # API tests
│   └── test_services.py      # Service tests
├── .env.example              # Example environment variables
├── .gitignore                # Git ignore file
├── Dockerfile                # Docker configuration
├── docker-compose.yml        # Docker Compose configuration
├── requirements.txt          # Project dependencies
└── README.md                 # Project documentation
```
