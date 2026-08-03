"""Alembic migration: create visualizations table
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0007_create_visualizations"
down_revision = "0006_create_model_registry"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "visualizations",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("analysis_id", sa.Integer(), sa.ForeignKey("analysis_results.id", ondelete="CASCADE"), nullable=False),
        sa.Column("mesh_path", sa.String(length=1024), nullable=False),
        sa.Column("texture_path", sa.String(length=1024), nullable=True),
        sa.Column("metadata", sa.Text(), nullable=True),
        sa.Column("volume", sa.Float(), nullable=True),
        sa.Column("surface_area", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    )


def downgrade():
    op.drop_table("visualizations")
