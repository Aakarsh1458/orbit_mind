"""Create conversation and orchestration tables

Revision ID: 002_orchestration_tables
Revises: 001_initial_tables
Create Date: 2026-09-10 12:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "002_orchestration_tables"
down_revision: Union[str, None] = "001_initial_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create conversations table
    op.create_table(
        "conversations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False, server_default="New Satellite Session"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
    )

    # 2. Create conversation_messages table
    op.create_table(
        "conversation_messages",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("conversation_id", sa.String(length=36), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("imagery_ids", sa.JSON(), nullable=True),
        sa.Column("task", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # 3. Create orchestration_runs table
    op.create_table(
        "orchestration_runs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("request_id", sa.String(length=36), nullable=False, index=True),
        sa.Column("conversation_id", sa.String(length=36), sa.ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("task", sa.String(length=50), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False, server_default="internal"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="completed"),
        sa.Column("duration_ms", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("fallback_used", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("errors", sa.JSON(), nullable=True),
        sa.Column("result_path", sa.String(length=1024), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # 4. Create orchestration_steps table
    op.create_table(
        "orchestration_steps",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("run_id", sa.String(length=36), sa.ForeignKey("orchestration_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("step_number", sa.Integer(), nullable=False),
        sa.Column("stage", sa.String(length=50), nullable=False),
        sa.Column("action", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="completed"),
        sa.Column("duration_ms", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("orchestration_steps")
    op.drop_table("orchestration_runs")
    op.drop_table("conversation_messages")
    op.drop_table("conversations")
