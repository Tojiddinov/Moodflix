$(function() {
  const apiKey = '74e9324ddf26ffda8ad02ea8bf8e6853';

  // Button will be disabled until input field is filled
  const source = document.getElementById('autoComplete');
  source.addEventListener('input', function (e) {
    $('.movie-button').attr('disabled', e.target.value === '');
  });

  // Trigger search when the button is clicked
  $('.movie-button').on('click', function () {
    const title = $('.movie').val();
    if (title === '') {
      showError('Please enter a movie title.');
    } else {
      loadDetails(apiKey, title);
    }
  });
});

// Fetch basic movie details using TMDb API
function loadDetails(apiKey, title) {
  toggleLoader(true);
  $.ajax({
    type: 'GET',
    url: `https://api.themoviedb.org/3/search/movie?api_key=${apiKey}&query=${title}`,
    success: function (response) {
      if (!response.results.length) {
        showError('No results found for the given title.');
      } else {
        const movie = response.results[0];
        getMovieRecommendations(movie.original_title, movie.id, apiKey);
      }
    },
    error: function () {
      showError('Failed to fetch movie details.');
    },
    complete: function () {
      toggleLoader(false);
    },
  });
}

// Fetch movie recommendations from the backend
function getMovieRecommendations(title, movieId, apiKey) {
  toggleLoader(true);
  $.ajax({
    type: 'POST',
    url: '/similarity',
    data: { name: title },
    success: function (recommendations) {
      if (!recommendations || recommendations.includes('Sorry')) {
        showError(recommendations);
      } else {
        const recs = recommendations.split('---');
        getMovieDetails(movieId, recs, title, apiKey);
      }
    },
    error: function () {
      showError('Failed to fetch recommendations.');
    },
    complete: function () {
      toggleLoader(false);
    },
  });
}

// Fetch detailed information about the movie
function getMovieDetails(movieId, recommendations, title, apiKey) {
  toggleLoader(true);
  $.ajax({
    type: 'GET',
    url: `https://api.themoviedb.org/3/movie/${movieId}?api_key=${apiKey}`,
    success: function (details) {
      displayDetails(details, recommendations, title, apiKey, movieId);
    },
    error: function () {
      showError('Failed to fetch movie details.');
    },
    complete: function () {
      toggleLoader(false);
    },
  });
}

// Display movie details and send data to the backend for rendering
function displayDetails(details, recommendations, title, apiKey, movieId) {
  const posterUrl = `https://image.tmdb.org/t/p/original${details.poster_path}`;
  const genres = details.genres.map((genre) => genre.name).join(', ');
  const runtime = formatRuntime(details.runtime);
  const recPosters = fetchRecommendationPosters(recommendations, apiKey);
  const movieCast = fetchMovieCast(movieId, apiKey);

  const payload = {
    title: details.original_title,
    imdb_id: details.imdb_id,
    poster: posterUrl,
    genres,
    overview: details.overview,
    rating: details.vote_average,
    vote_count: details.vote_count.toLocaleString(),
    release_date: new Date(details.release_date).toDateString(),
    runtime,
    status: details.status,
    rec_movies: JSON.stringify(recommendations),
    rec_posters: JSON.stringify(recPosters),
    cast_ids: JSON.stringify(movieCast.cast_ids),
    cast_names: JSON.stringify(movieCast.cast_names),
    cast_chars: JSON.stringify(movieCast.cast_chars),
    cast_profiles: JSON.stringify(movieCast.cast_profiles),
  };

  $.ajax({
    type: 'POST',
    url: '/recommend',
    data: payload,
    success: function (response) {
      $('.results').html(response);
      $('#autoComplete').val('');
      $(window).scrollTop(0);
    },
    complete: function () {
      toggleLoader(false);
    },
  });
}

// Fetch posters for recommended movies
function fetchRecommendationPosters(recommendations, apiKey) {
  const posters = [];
  recommendations.forEach((rec) => {
    $.ajax({
      type: 'GET',
      url: `https://api.themoviedb.org/3/search/movie?api_key=${apiKey}&query=${rec}`,
      async: false,
      success: function (data) {
        if (data.results.length) {
          posters.push(`https://image.tmdb.org/t/p/original${data.results[0].poster_path}`);
        }
      },
    });
  });
  return posters;
}

// Fetch cast details for the movie
function fetchMovieCast(movieId, apiKey) {
  const cast = { cast_ids: [], cast_names: [], cast_chars: [], cast_profiles: [] };
  $.ajax({
    type: 'GET',
    url: `https://api.themoviedb.org/3/movie/${movieId}/credits?api_key=${apiKey}`,
    async: false,
    success: function (data) {
      const topCast = data.cast.slice(0, 10);
      topCast.forEach((member) => {
        cast.cast_ids.push(member.id);
        cast.cast_names.push(member.name);
        cast.cast_chars.push(member.character);
        cast.cast_profiles.push(`https://image.tmdb.org/t/p/original${member.profile_path}`);
      });
    },
  });
  return cast;
}

// Helper function to format runtime
function formatRuntime(runtime) {
  const hours = Math.floor(runtime / 60);
  const minutes = runtime % 60;
  return `${hours} hour(s) ${minutes} minute(s)`;
}

// Show or hide loader
function toggleLoader(show) {
  $('#loader').toggle(show);
}

// Display error messages
function showError(message) {
  $('.fail').text(message).show();
  $('.results').hide();
}
