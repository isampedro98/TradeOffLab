"""create options table

Revision ID: 20260525_0003
Revises: 20260525_0002
Create Date: 2026-05-25 22:05:00

"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260525_0003"
down_revision: str | None = "20260525_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("options"):
        return

    op.create_table(
        "options",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("decision_id", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["decision_id"], ["decisions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_options_decision_id", "options", ["decision_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("options"):
        return

    indexes = {index["name"] for index in inspector.get_indexes("options")}
    if "ix_options_decision_id" in indexes:
        op.drop_index("ix_options_decision_id", table_name="options")

    op.drop_table("options")
