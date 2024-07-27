#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, flash, redirect, url_for
from flask_migrate import Migrate
from flask_moment import Moment
import logging
from logging import Formatter, FileHandler
from sqlalchemy import select, text, func
from forms import *
from model import db, Venue, Show, Artist, artist_shows
from flask import jsonify

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
migrate = Migrate(app, db)
db.init_app(app)


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    if isinstance(value, datetime):
        date = value
    else:
        date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


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
    # TODO: replace with real venues data.
    #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
    data = []
    raw_data = db.session.scalars(select(Venue).order_by(Venue.id)).all()
    for i in raw_data:
        venue = {
            "id": i.id,
            "name": i.name,
        }
        found = False
        for city_data in data:
            if city_data["city"] == i.city:
                city_data["venues"].append(venue)
                found = True
                break
        if not found:
            new_city = {
                "city": i.city,
                "state": i.state,
                "venues": [venue]
            }
            data.append(new_city)
    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    try:
        input_sel = request.form.get("search_term")
        upcoming_shows_subquery = (
            db.session.query(
                Show.venue_id,
                func.count(Show.id).label('num_upcoming_shows')
            )
            .filter(Show.time > func.current_date())
            .group_by(Show.venue_id)
        ).subquery()

        query = (
            db.session.query(
                Venue.name,
                Venue.id,
                func.coalesce(upcoming_shows_subquery.c.num_upcoming_shows, 0).label('num_upcoming_shows'),
                func.count().over().label('total_count')
            )
            .outerjoin(upcoming_shows_subquery, Venue.id == upcoming_shows_subquery.c.venue_id)
            .filter(func.lower(Venue.name).like(func.lower(f'%{input_sel}%')))
            .group_by(Venue.name, Venue.id, upcoming_shows_subquery.c.num_upcoming_shows)
        )
        result = query.all()
        data_list = []
        count_result = 0
        # format data
        for i in result:
            count_result = i["total_count"]
            data = {
                "id": i["id"],
                "name": i["name"],
                "num_upcoming_shows": i["num_upcoming_shows"]
            }
            data_list.append(data)
        response = {
            "count": count_result,
            "data": data_list
        }
        return render_template('pages/search_venues.html', results=response,
                               search_term=request.form.get('search_term', ''))
    except:
        print("error")


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id

    #data = Venue.query.get(venue_id)

    query = (
        db.session.query(
            Venue,
            Show.time,
            Artist.id.label('artist_id'),
            Artist.name.label('artist_name'),
            Artist.image_link.label('artist_image_link')
        )
        .outerjoin(Show, Venue.id == Show.venue_id)
        .outerjoin(artist_shows, Show.id == artist_shows.c.show_id)
        .outerjoin(Artist, artist_shows.c.artist_id == Artist.id)
        .filter(Venue.id == venue_id)
    )

    results = query.all()
    upcoming_shows = []
    past_shows = []
    data = {}
    for venue, show_time,artist_id, artist_name, artist_image_link in results:
        if venue_id == venue.id or 0 == venue.id:
            data = {
                "id": venue.id,
                "name": venue.name,
                "genres": venue.genres,
                "address": venue.address,
                "city": venue.city,
                "state": venue.state,
                "phone": venue.phone,
                "website": venue.website_link,
                "facebook_link": venue.facebook_link,
                "seeking_talent": venue.look_talent,
                "image_link": venue.image_link
            }
        artist_item = {
            "artist_id": artist_id,
            "artist_name": artist_name,
            "artist_image_link": artist_image_link,
            "start_time": show_time
        }
        if show_time > datetime.now():
            upcoming_shows.append(artist_item)
        else:
           past_shows.append(artist_item)
        data["upcoming_shows"] = upcoming_shows
        data["past_shows"] = past_shows
        data["upcoming_shows_count"] = len(upcoming_shows)
        data["past_shows_count"] = len(past_shows)
    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------
@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    try:
        name = request.form.get("name")
        city = request.form.get("city")
        state = request.form.get("state")
        address = request.form.get("address")
        phone = request.form.get("phone")
        image_link = request.form.get("image_link")
        facebook_link = request.form.get("facebook_link")
        website_link = request.form.get("website_link")
        look_talent = request.form.get("seeking_talent")
        seek_des = request.form.get("seeking_description")
        genres = request.form.get("genres")
        venues = Venue(name, city, state, address, phone, image_link, facebook_link, website_link, look_talent,
                       seek_des, genres)
        db.session.add(venues)
        db.session.commit()
        # TODO: modify data to be the data object returned from db insertion
        # on successful db insert, flash success
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except:
        # TODO: on unsuccessful db insert, flash an error instead.
        flash('An error occurred. Venue ' + request.form.get("name") + ' could not be listed.')
    return render_template('pages/home.html')


@app.route('/venues/delete/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    try:
        venue_to_delete = db.session.query(Venue).get(venue_id)
        db.session.delete(venue_to_delete)
        db.session.commit()
        return jsonify({'message': 'Venue deleted successfully'}), 200
    except:
        return jsonify({'message': 'Failed to delete venue because have a show of this venue'}), 500


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    # TODO: replace with real data returned from querying the database
    data = db.session.scalars(select(Artist).order_by(Artist.id)).all()
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".

    try:
        input_sel = request.form.get("search_term")
        sql = text("""
              SELECT artist.name, 
                     artist.id,
                    (
                        SELECT COUNT(*)  as total_shows
                          FROM artist_shows join shows on artist_shows.show_id = shows.id
                         WHERE 1=1 
						   AND artist_shows.artist_id = artist.id
						   AND shows."time" > CURRENT_DATE ) as num_upcoming_shows,
                      COUNT(*) OVER () AS total_count
                 FROM artist
                WHERE 1=1 
                  AND LOWER(artist.name) LIKE LOWER(:search_term)
             GROUP BY artist.name, 
                      artist.id
                """)
        result = db.session.execute(sql, {'search_term': f'%{input_sel}%'}).fetchall()
        data_list = []
        count_result = 0
        # format data
        for i in result:
            count_result = i["total_count"]
            data = {
                "id": i["id"],
                "name": i["name"],
                "num_upcoming_shows": i["num_upcoming_shows"]
            }
            data_list.append(data)
        response = {
            "count": count_result,
            "data": data_list
        }
        return render_template('pages/search_artists.html', results=response,
                               search_term=request.form.get('search_term', ''))
    except:
        return jsonify({'message': 'Failed to search artist'}), 500


def show_artist_by_id(artist_id):
    query = (
        db.session.query(
            Artist,
            Show.venue_id,
            Show.time,
            Venue.name.label('venue_name'),
            Venue.image_link.label('venue_image_link')
        )
        .outerjoin(artist_shows, Artist.id == artist_shows.c.artist_id)
        .outerjoin(Show, artist_shows.c.show_id == Show.id)
        .outerjoin(Venue, Show.venue_id == Venue.id)
        .filter(Artist.id == artist_id)
    )
    result = query.all()
    upcoming_shows = []
    past_shows = []
    data = {}
    for artist, venue_id, show_time, venue_name, venue_image_link in result:
        if artist_id == artist.id:
            data = {
                "id": artist.id,
                "name": artist.name,
                "genres": artist.genres,
                "city": artist.city,
                "state": artist.state,
                "phone": artist.phone,
                "seek_des": artist.seek_des,
                "seeking_venue": artist.seeking_venue,
                "image_link": artist.image_link,
                "website_link": artist.website_link,
                "facebook_link": artist.facebook_link,
                "past_shows": [],
                "upcoming_shows": [],
                "past_shows_count": 0,
                "upcoming_shows_count": 0,
            }
        if venue_id is not None:
            show = {
                "venue_id": venue_id,
                "venue_name": venue_name,
                "venue_image_link": venue_image_link,
                "start_time": show_time
            }
            if show_time > datetime.now():
                upcoming_shows.append(show)
            else:
                past_shows.append(show)

        data["upcoming_shows"] = upcoming_shows
        data["past_shows"] = past_shows
        data["upcoming_shows_count"] = len(upcoming_shows)
        data["past_shows_count"] = len(past_shows)

    return data
@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    # TODO: replace with real artist data from the artist table, using artist_id
    data = show_artist_by_id(artist_id)

    return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    data = show_artist_by_id(artist_id)
    if data["id"] == None:
        return jsonify({"error": "Artist not found"}), 404

    seeking_venue = True if data["seeking_venue"] == "y" else False
    artist = {
        "id": data["id"],
        "name": data["name"],
        "genres": data["genres"],
        "city": data["city"],
        "state": data["state"],
        "phone": data["phone"],
        "website_link": data["website_link"],
        "facebook_link":data["facebook_link"],
        "seeking_venue": seeking_venue,
        "seeking_description":data["seek_des"],
        "image_link": data["image_link"]
    }
    # TODO: populate form with fields from artist with ID <artist_id>
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    artist = Artist.query.get(artist_id)
    if not artist:
        return jsonify({"error": "Artist not found"}), 404

    artist.name = request.form.get("name")
    artist.city = request.form.get("city")
    artist.state = request.form.get("state")
    artist.address = request.form.get("address")
    artist.phone = request.form.get("phone")
    artist.image_link = request.form.get("image_link")
    artist.facebook_link = request.form.get("facebook_link")
    artist.website_link = request.form.get("website_link")
    artist.seek_des = request.form.get("seeking_description")
    artist.genres = request.form.get("genres")
    artist.seeking_venue = request.form.get("seeking_venue")

    db.session.commit()
    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    data = Venue.query.get(venue_id)
    if data.id is None:
        return jsonify({"error": "Venue not found"}), 404

    look_talent = True if data.look_talent == "y" else False
    venue = {
        "id": data.id,
        "name": data.name,
        "address": data.address,
        "city": data.city,
        "state": data.state,
        "phone": data.phone,
        "website_link": data.website_link,
        "facebook_link": data.facebook_link,
        "seeking_talent": look_talent,
        "seeking_description": data.seek_des,
        "image_link": data.image_link,
        "genres":data.genres

    }
    # TODO: populate form with values from venue with ID <venue_id>
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes

    venue = Venue.query.get(venue_id)
    if not venue:
        return jsonify({"error": "Venue not found"}), 404

    venue.name = request.form.get("name")
    venue.city = request.form.get("city")
    venue.state = request.form.get("state")
    venue.address = request.form.get("address")
    venue.phone = request.form.get("phone")
    venue.image_link = request.form.get("image_link")
    venue.facebook_link = request.form.get("facebook_link")
    venue.website_link = request.form.get("website_link")
    venue.seek_des = request.form.get("seeking_description")
    venue.look_talent = request.form.get("seeking_talent")
    venue.genres = request.form.get("genres")

    db.session.commit()
    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    try:
        name = request.form.get("name")
        city = request.form.get("city")
        state = request.form.get("state")
        address = request.form.get("address")
        phone = request.form.get("phone")
        image_link = request.form.get("image_link")
        facebook_link = request.form.get("facebook_link")
        website_link = request.form.get("website_link")
        seek_des = request.form.get("seeking_description")
        genres = request.form.get("genres")
        seeking_venue = request.form.get("seeking_venue")
        artist = Artist(name, city, state, address, phone, image_link, facebook_link, website_link, seeking_venue, seek_des, genres)
        db.session.add(artist)
        db.session.commit()
        # TODO: modify data to be the data object returned from db insertion
        # on successful db insert, flash success
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except:
        # TODO: on unsuccessful db insert, flash an error instead.
        flash('An error occurred. Artist ' + request.form.get("name") + ' could not be listed.')
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    query = (
        db.session.query(
            Show,
            Venue.name.label('venue_name'),
            Artist.id.label('artist_id'),
            Artist.name.label('artist_name'),
            Artist.image_link.label('artist_image_link')
        )
        .outerjoin(Venue, Show.venue_id == Venue.id)
        .outerjoin(artist_shows, Show.id == artist_shows.c.show_id)
        .outerjoin(Artist, Artist.id == artist_shows.c.artist_id)
    )
    result = query.all()

    data = []
    for show, venue_name, artist_id, artist_name, artist_image_link in result:
        data_item = {
            "venue_id": show.venue_id,
            "venue_name": venue_name,
            "artist_id": artist_id,
            "artist_name": artist_name,
            "artist_image_link": artist_image_link,
            "start_time": show.time
        }
        data.append(data_item)
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead
    try:
        artist_id = request.form.get("artist_id")
        venue_id = request.form.get("venue_id")
        time = request.form.get("start_time")
        artist = Artist.query.get(artist_id)
        venue = Venue.query.get(venue_id)
        if artist is None:
            flash('An error occurred. Artist ' + request.form.get("name") + ' not found.')
            return render_template('pages/home.html')
        if venue is None:
            flash('An error occurred. Venue ' + request.form.get("name") + ' not found.')
            return render_template('pages/home.html')
        show = Show(venue_id, artist_id, time)
        db.session.add(show)
        db.session.commit()
        artist_show_entry = artist_shows.insert().values(artist_id=artist_id, show_id=show.id)
        db.session.execute(artist_show_entry)

        # Commit the session to save changes to artist_shows
        db.session.commit()


        # on successful db insert, flash success
        flash('Show was successfully listed!')
        # TODO: on unsuccessful db insert, flash an error instead.
        # e.g., flash('An error occurred. Show could not be listed.')
        # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
        return render_template('pages/home.html')
    except:
        flash('An error occurred. Show could not be listed.')
        return render_template('pages/home.html')
    finally:
        db.session.close()



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
