"""initial

Revision ID: 0001_initial
Revises: 
Create Date: 2026-07-20 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=200), nullable=False),
        sa.Column('password_hash', sa.String(length=200), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=True, server_default='1200'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )
    op.create_table(
        'games',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('white_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('black_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('fen', sa.String(length=1000), nullable=True, server_default='startpos'),
        sa.Column('pgn', sa.Text(), nullable=True, server_default=''),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('time_control', sa.String(length=50), nullable=True),
        sa.Column('ai', sa.String(length=5), nullable=True),
        sa.Column('ai_side', sa.String(length=10), nullable=True),
        sa.Column('ai_difficulty', sa.String(length=20), nullable=True, server_default='medium'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )
    op.create_table(
        'moves',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('game_id', sa.Integer(), sa.ForeignKey('games.id'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('uci', sa.String(length=16), nullable=False),
        sa.Column('san', sa.String(length=64), nullable=True),
        sa.Column('turn_number', sa.Integer(), nullable=False),
        sa.Column('clock_white_ms', sa.Integer(), nullable=True),
        sa.Column('clock_black_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

def downgrade():
    op.drop_table('moves')
    op.drop_table('games')
    op.drop_table('users')