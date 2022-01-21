import sqlalchemy as sa
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# define table objects
Base = declarative_base()

engine = create_engine('sqlite:///dfs.db')
Session = sessionmaker(bind=engine)


def get_session():
    session = Session()
    return session


class Player(Base):
    __tablename__ = 'player'

    sid = sa.Column(sa.Integer, primary_key=True)
    player_id = sa.Column(sa.Integer, nullable=False, unique=True)
    name = sa.Column(sa.String)


class Slate(Base):
    __tablename__ = 'slate'

    sid = sa.Column(sa.Integer, primary_key=True)
    slate_id = sa.Column(sa.String, nullable=False, unique=True)
    start_date = sa.Column(sa.DateTime)
    end_date = sa.Column(sa.DateTime)
    sport = sa.Column(sa.Integer)
    slate_type = sa.Column(sa.Integer)
    slate_type_name = sa.Column(sa.String)


class Contest(Base):
    __tablename__ = 'contest'

    sid = sa.Column(sa.Integer, primary_key=True)
    contest_id = sa.Column(sa.String, nullable=False, unique=True)
    slate_fk = sa.Column(sa.String, sa.ForeignKey('slate.slate_id'), nullable=False)
    prize_pool = sa.Column(sa.Integer)
    max_entries = sa.Column(sa.Integer)
    max_entries_per_user = sa.Column(sa.Integer)
    entry_fee = sa.Column(sa.Integer)
    name = sa.Column(sa.String)


class PlayerOwnership(Base):
    __tablename__ = 'playerownership'

    sid = sa.Column(sa.Integer, primary_key=True)
    slate_player_id = sa.Column(sa.String, nullable=False)
    player_fk = sa.Column(sa.String, sa.ForeignKey('player.player_id'), nullable=False)
    contest_fk = sa.Column(sa.String, sa.ForeignKey('contest.contest_id'), nullable=False)
    salary = sa.Column(sa.Numeric)
    projected_fantasy_points = sa.Column(sa.Numeric)
    actual_fantasy_points = sa.Column(sa.Numeric)
    projected_ownership = sa.Column(sa.Numeric)
    actual_ownership = sa.Column(sa.Numeric)


class Entry(Base):
    __tablename__ = 'entry'

    sid = sa.Column(sa.Integer, primary_key=True)
    entry_id = sa.Column(sa.String, nullable=False)
    contest_fk = sa.Column(sa.String, sa.ForeignKey('contest.contest_id'), nullable=False)
    rank = sa.Column(sa.Integer, nullable=False)
    points = sa.Column(sa.Numeric)


class Lineup(Base):
    __tablename__ = 'lineup'

    sid = sa.Column(sa.Integer, primary_key=True)
    entry_fk = sa.Column(sa.String, sa.ForeignKey('entry.entry_id'), nullable=False)
    playerownership_fk = sa.Column(sa.String, sa.ForeignKey('playerownership.slate_player_id'), nullable=False)
