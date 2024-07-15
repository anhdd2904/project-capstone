from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship

db = SQLAlchemy()



artist_shows = db.Table('artist_shows',
    db.Column('artist_id', db.Integer, db.ForeignKey('artist.id'), primary_key=True),
    db.Column('show_id', db.Integer, db.ForeignKey('shows.id'), primary_key=True)
)
class Venue(db.Model):
    __tablename__ = 'venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(500))
    website_link = db.Column(db.String(500))
    look_talent = db.Column(db.String(100))
    seek_des = db.Column(db.String(500))


    #shows = relationship("shows", backref='venue', lazy=True)

    def __init__(self, name, city, state, address, phone, image_link, facebook_link, website_link, look_talent, seek_des):
        self.name = name
        self.city = city
        self.state = state
        self.address = address
        self.phone = phone
        self.image_link = image_link
        self.facebook_link = facebook_link
        self.website_link = website_link
        self.look_talent = look_talent
        self.seek_des = seek_des

class Artist(db.Model):
    __tablename__ = 'artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    shows = db.relationship('Show', secondary=artist_shows)

class Show(db.Model):
    __tablename__ = 'shows'
    id = db.Column(db.Integer, primary_key = True)
    time = db.Column(db.DateTime, nullable=False)
    #venue_id = db.Column(db.Integer, db.ForeignKey("venue.id"), nullable=False)
    artists = db.relationship("Artist", secondary=artist_shows,  lazy=True)

    #__table_args__ = (db.UniqueConstraint('venue_id', 'time', name='unique_venue_time'),)


