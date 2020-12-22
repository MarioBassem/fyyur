#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
from datetime import datetime
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
import sys
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
# moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.Column(db.String(500))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default=True)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship('Show', backref='venue', lazy='dynamic')

class Artist(db.Model):
    __tablename__ = 'artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(500))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(200))
    seeking_venue = db.Column(db.Boolean, default=True)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship('Show', backref='artist', lazy='dynamic')

class Show(db.Model):
  __tablename__ = 'show'

  id = db.Column(db.Integer, primary_key=True)
  venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'), nullable=False)
  artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), nullable=False)
  start_time = db.Column(db.DateTime, nullable=False)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  areas = Venue.query.with_entities(Venue.city, Venue.state).group_by('city', 'state').all()
  data = []
  for area in areas:
    venues_query = Venue.query.filter(Venue.city == area.city).all()
    venues_modified = []
    for venue in venues_query:
      venues_modified.append({
        'id': venue.id,
        'name': venue.name,
        'num_upcoming_shows': venue.shows.filter(Show.start_time > datetime.utcnow(), Venue.city == area.city).count()
      })

    data.append({
      'city': area.city,
      'state': area.state,
      'venues': venues_modified
    })

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form.get('search_term')
  venues = Venue.query.with_entities(Venue.id, Venue.name).filter(Venue.name.ilike('%' + search_term + '%')).all()
  response = {
    'count': len(venues),
    'data': venues
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue = Venue.query.filter(Venue.id==venue_id).first()
  upcoming_shows = venue.shows.filter(Show.start_time > datetime.utcnow()).all()
  past_shows = venue.shows.filter(Show.start_time <= datetime.utcnow()).all()
  data = {
    **venue.__dict__,  
    'upcoming_shows': [],
    'past_shows': [],
    'upcoming_shows_count': len(upcoming_shows),
    'past_shows_count': len(past_shows)
  }

  for upcoming_show in upcoming_shows:
    artist = Artist.query.filter(Artist.id == upcoming_show.artist_id).first()
    data['upcoming_shows'].append({
      'artist_id': artist.id,
      'artist_name': artist.name,
      'artist_image_link': artist.image_link,
      'start_time': upcoming_show.start_time
    })

  for past_show in past_shows:
    artist = Artist.query.filter(Artist.id == past_show.artist_id).first()
    data['past_shows'].append({
      'artist_id': artist.id,
      'artist_name': artist.name,
      'artist_image_link': artist.image_link,
      'start_time': past_show.start_time
    })

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  error = False
  try: 
    f = request.form
    new_venue = Venue(**f)
    new_venue.genres = ", ".join(f.getlist('genres'))
    db.session.add(new_venue)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if error:
    flash('Venue ' + request.form['name'] + ' was not successfully listed!')
  
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    venue = Venue.query.filter_by(Venue.id == venue_id).first()
    db.session.delete(venue)
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
  

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = Artist.query.with_entities(Artist.id, Artist.name).order_by('id').all()

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form.get('search_term')
  artists = Artist.query.filter(Artist.name.ilike('%' + search_term + '%')).all()

  f = lambda a : {
    'id': a.id,
    'name': a.name,
    'num_upcoming_shows': a.shows.filter(Show.start_time > datetime.utcnow()).count()
  }
  response = {
    'count': len(artists),
    'data': [f(a) for a in artists]
  }
  print(response)

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.filter_by(id=artist_id).first()
  upcoming_shows = artist.shows.filter(Show.start_time > datetime.utcnow()).all()
  past_shows = artist.shows.filter(Show.start_time <= datetime.utcnow()).all()
  data = {
    **artist.__dict__,
    'upcoming_shows': [],
    'past_shows': [],
    'upcoming_shows_count': len(upcoming_shows),
    'past_shows_count': len(past_shows)
  }
  for upcoming_show in upcoming_shows:
    venue = Venue.query.filter(Venue.id == upcoming_show.venue_id).first()
    data['upcoming_shows'].append({
      'venue_id': venue.id,
      'venue_name': venue.name,
      'venue_image_link': venue.image_link,
      'start_time': upcoming_show.start_time
    })

  for past_show in past_shows:
    venue = Venue.query.filter(Venue.id == past_show.venue_id).first()
    data['past_shows'].append({
      'venue_id': venue.id,
      'venue_name': venue.name,
      'venue_image_link': venue.image_link,
      'start_time': past_show.start_time
    })

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.filter(Artist.id == artist_id).first()
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  try:  
    f = request.form
    artist = Artist.query.filter(Artist.id == artist_id).first()
    for key in f.keys():
      if key == 'genres':
        setattr(artist, key, ', '.join(f.getlist('genres')))
      else:
        setattr(artist, key, f.get(key))

    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.filter(Venue.id == venue_id).first()
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  try:  
    f = request.form
    venue = Venue.query.filter(Venue.id == venue_id).first()
    for key in f.keys():
      if key == 'genres':
        setattr(venue, key, ', '.join(f.getlist('genres')))
      else:
        setattr(venue, key, f.get(key))

    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():

  error = False
  try: 
    f = request.form
    new_artist = Artist(**f)
    new_artist.genres = ', '.join(f.getlist('genres'))
    db.session.add(new_artist)
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('Artist ' + request.form['name'] + ' was not successfully listed!')

  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():

  shows = Show.query.order_by(Show.id).all()
  data = []
  for show in shows:
    artist = Artist.query.with_entities(Artist.name, Artist.image_link).filter(Artist.id == show.artist_id).first()
    venue = Venue.query.with_entities(Venue.name).filter(Venue.id == show.venue_id).first()

    data.append({
      **show.__dict__,
      'artist_name': artist.name,
      'artist_image_link': artist.image_link,
      'venue_name': venue.name
    })

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  error = False
  try: 
    f = request.form
    new_show = Show(**f)
    db.session.add(new_show)
    db.session.commit()
    flash('Show was successfully listed!')
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if error:
    flash('Show was not successfully listed!')
  
  return render_template('pages/home.html')
  

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
