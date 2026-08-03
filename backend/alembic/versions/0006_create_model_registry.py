"""Alembic migration: create model_registry table
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0006_create_model_registry"
down_revision = "0005_create_notifications"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "model_registry",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("model_name", sa.String(length=256), nullable=False),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("framework", sa.String(length=64), nullable=True),
        sa.Column("accuracy", sa.Float(), nullable=True),
        sa.Column("precision", sa.Float(), nullable=True),
        sa.Column("recall", sa.Float(), nullable=True),
        sa.Column("f1_score", sa.Float(), nullable=True),
        sa.Column("weights_path", sa.String(length=1024), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text('false')),
    )


def downgrade():
    op.drop_table("model_registry")
