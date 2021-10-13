import sqlalchemy as sa
from sqlalchemy.engine import create_engine

# define table objects
metadata_obj = sa.MetaData()

def get_connection():
        engine = create_engine('sqlite:///dfs.db')
        return engine.connect()

player = sa.Table(
        'player', metadata_obj,
        sa.Column('sid', sa.Integer, primary_key=True),
        sa.Column('player_id', sa.Integer, nullable=False, unique=False),
        sa.Column('first_name', sa.String),
        sa.Column('last_name', sa.String)
)

slate = sa.Table(
        'slate', metadata_obj,
        sa.Column('sid', sa.Integer, primary_key=True),
        sa.Column('slate_id', sa.String, nullable=False, unique=True),
        sa.Column('slate_draftgroup_id', sa.Integer, nullable=False, unique=True),
        sa.Column('start_date', sa.DateTime),
        sa.Column('end_date', sa.DateTime),
        sa.Column('sport', sa.Integer),
        sa.Column('slate_type', sa.Integer),
)

contest = sa.Table(
        'contest', metadata_obj,
        sa.Column('sid', sa.Integer, primary_key=True),
        sa.Column('contest_id', sa.BigInteger, nullable=False, unique=True),
        sa.Column('name', sa.String),
        sa.Column('start_date', sa.DateTime),
        sa.Column('max_entries_per_user', sa.Integer),
        sa.Column('max_entries', sa.Integer),
        sa.Column('total_entries', sa.Integer),
        sa.Column('slate_fk', sa.String, sa.ForeignKey('slate.slate_id'), nullable=False,)
)

draftgroup = sa.Table(
        'draftgroup', metadata_obj,
        sa.Column('sid', sa.Integer, primary_key=True),
        sa.Column('salary', sa.Numeric),
        sa.Column('draftable_id', sa.BigInteger, unique=True),
        sa.Column('average_fantasy_points', sa.Numeric),
        sa.Column('projected_fantasy_points', sa.Numeric),
        sa.Column('slate_draftgroup_fk', sa.Integer, sa.ForeignKey('contest.contest_id'), nullable=True),
        sa.Column('player_fk', sa.Integer, sa.ForeignKey('player.player_id')),
)