from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0008_create_report_reviews"
down_revision = "0007_create_visualizations"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "report_reviews",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("report_id", sa.Integer(), sa.ForeignKey("reports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("doctor_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default='pending'),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("stage_review", sa.String(length=64), nullable=True),
        sa.Column("risk_review", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    )


def downgrade():
    op.drop_table("report_reviews")
