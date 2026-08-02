"""Alembic migration: create stage_predictions table
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0002_create_stage_predictions"
down_revision = "0001_create_users_roles"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "stage_predictions",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("analysis_id", sa.Integer(), sa.ForeignKey("analysis_results.id", ondelete="CASCADE"), nullable=False),
        sa.Column("stage", sa.String(length=32), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("contributing_factors", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    )


def downgrade():
    op.drop_table("stage_predictions")
