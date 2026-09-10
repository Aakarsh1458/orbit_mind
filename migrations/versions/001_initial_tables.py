"""Initial migration creating imagery, analysis_jobs, and analysis_results tables

Revision ID: 001_initial_tables
Revises: 
Create Date: 2026-09-10 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001_initial_tables"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create imagery table
    op.create_table(
        "imagery",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("path", sa.String(length=1024), nullable=False),
        sa.Column("sensor", sa.String(length=100), nullable=True, server_default="Unknown"),
        sa.Column("acquisition_time", sa.DateTime(), nullable=True),
        sa.Column("crs", sa.String(length=100), nullable=False, server_default="EPSG:4326"),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column("bands", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("bounds", sa.JSON(), nullable=False),
        sa.Column("resolution", sa.JSON(), nullable=False),
        sa.Column("dtype", sa.String(length=50), nullable=False, server_default="uint8"),
        sa.Column("is_georeferenced", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("meta_info", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # 2. Create analysis_jobs table
    op.create_table(
        "analysis_jobs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("query", sa.Text(), nullable=True),
        sa.Column("analysis_type", sa.String(length=50), nullable=False),
        sa.Column("imagery_ids", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="queued"),
        sa.Column("progress", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )

    # 3. Create analysis_results table
    op.create_table(
        "analysis_results",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("job_id", sa.String(length=36), sa.ForeignKey("analysis_jobs.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("mode", sa.String(length=20), nullable=False, server_default="mock"),
        sa.Column("statistics", sa.JSON(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("execution_trace", sa.JSON(), nullable=False),
        sa.Column("result_path", sa.String(length=1024), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("analysis_results")
    op.drop_table("analysis_jobs")
    op.drop_table("imagery")
