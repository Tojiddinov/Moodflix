"""
Movie model for MoodFlix application.
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class Movie:
    """Movie data model."""
    
    title: str
    year: Optional[int] = None
    genres: List[str] = field(default_factory=list)
    plot: str = ""
    poster: str = ""
    actors: List[str] = field(default_factory=list)
    directors: List[str] = field(default_factory=list)
    mood: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Movie object to dictionary.
        
        Returns:
            Dictionary representation of the Movie
        """
        return {
            'title': self.title,
            'year': self.year,
            'genres': self.genres,
            'plot': self.plot,
            'poster': self.poster,
            'actors': self.actors,
            'directors': self.directors,
            'mood': self.mood
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Movie':
        """
        Create Movie object from dictionary.
        
        Args:
            data: Dictionary containing movie data
            
        Returns:
            Movie object
        """
        return cls(
            title=data.get('title', 'Unknown Title'),
            year=data.get('year'),
            genres=data.get('genres', []),
            plot=data.get('plot', ''),
            poster=data.get('poster', ''),
            actors=data.get('actors', []),
            directors=data.get('directors', []),
            mood=data.get('mood')
        )
