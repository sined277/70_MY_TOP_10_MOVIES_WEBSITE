from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests

# API key and URLs for The Movie DB API
MOVIE_DB_API_KEY = GET YOUR API KEY FROM themoviedb.org
MOVIE_DB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
MOVIE_DB_INFO_URL = "https://api.themoviedb.org/3/movie"
MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"

# Initialize Flask app and configure secret key
app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'

# Initialize Bootstrap for app
Bootstrap(app)

##CREATE DB
# Configure SQLAlchemy for app to create and connect to SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

##CREATE TABLE
# Define Movie class as a SQLAlchemy model for the database
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)

# Create the database and its tables
db.create_all()

# Define form for finding a movie
class FindMovieForm(FlaskForm):
    title = StringField("Movie Title", validators=[DataRequired()])
    submit = SubmitField("Add Movie")

# Define form for rating a movie
class RateMovieForm(FlaskForm):
    rating = StringField("Your Rating Out of 10 e.g. 7.5")
    review = StringField("Your Review")
    submit = SubmitField("Done")

# Define home page for app
@app.route("/")
def home():
    # Query all movies in the database and order them by rating
    all_movies = Movie.query.order_by(Movie.rating).all()

    # Calculate the ranking of each movie based on its position in the list
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i

    # Commit changes to the database
    db.session.commit()

    # Render the home page template and pass the list of movies as a parameter
    return render_template("index.html", movies=all_movies)

# Define page for adding a movie to the database
@app.route("/add", methods=["GET", "POST"])
def add_movie():
    # Create a form for finding a movie
    form = FindMovieForm()

    # If form has been submitted and is valid, query The Movie DB API for search results and render them as options
    if form.validate_on_submit():
        movie_title = form.title.data

        response = requests.get(MOVIE_DB_SEARCH_URL, params={"api_key": MOVIE_DB_API_KEY, "query": movie_title})
        data = response.json()["results"]
        return render_template("select.html", options=data)

    # Render the add movie page template with the form
    return render_template("add.html", form=form)

@app.route("/find")
def find_movie():
    # Get movie id from request args
    movie_api_id = request.args.get("id")
    if movie_api_id:
        # Construct url for movie api
        movie_api_url = f"{MOVIE_DB_INFO_URL}/{movie_api_id}"
        # Send request to the api
        response = requests.get(movie_api_url, params={"api_key": MOVIE_DB_API_KEY, "language": "en-US"})
        # Parse response to JSON format
        data = response.json()
        # Create a new Movie instance with data from the api
        new_movie = Movie(
            title=data["title"],
            year=data["release_date"].split("-")[0],
            img_url=f"{MOVIE_DB_IMAGE_URL}{data['poster_path']}",
            description=data["overview"]
        )
        # Add new movie to database and commit the change
        db.session.add(new_movie)
        db.session.commit()
        # Redirect user to rate the new movie
        return redirect(url_for("rate_movie", id=new_movie.id))


@app.route("/edit", methods=["GET", "POST"])
def rate_movie():
    # Create a new form instance for editing movie
    form = RateMovieForm()
    # Get movie id from request args
    movie_id = request.args.get("id")
    # Get the movie object by the id from database
    movie = Movie.query.get(movie_id)
    if form.validate_on_submit():
        # Update the rating and review of the movie object
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        db.session.commit()
        # Redirect user to home page after successful update
        return redirect(url_for('home'))
    # Render the edit page with movie and form
    return render_template("edit.html", movie=movie, form=form)


@app.route("/delete")
def delete_movie():
    # Get movie id from request args
    movie_id = request.args.get("id")
    # Get the movie object by the id from database
    movie = Movie.query.get(movie_id)
    # Delete the movie object from database
    db.session.delete(movie)
    db.session.commit()
    # Redirect user to home page after successful deletion
    return redirect(url_for("home"))


if __name__ == '__main__':
    # Start the application in debug mode
    app.run(debug=True)
