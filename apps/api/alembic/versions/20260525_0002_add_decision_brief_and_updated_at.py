"""add decision brief and updated at to decisions

Revision ID: 20260525_0002
Revises: 20260525_0001
Create Date: 2026-05-25 21:35:00

"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260525_0002"
down_revision: str | None = "20260525_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("decisions"):
        return

    columns = {column["name"] for column in inspector.get_columns("decisions")}

    if "decision_brief" not in columns:
        op.add_column(
            "decisions",
            sa.Column("decision_brief", sa.String(length=500), nullable=True),
        )
        op.execute(
            sa.text(
                """
                UPDATE decisions
                SET decision_brief = LEFT(COALESCE(question, title), 500)
                WHERE decision_brief IS NULL
                """
            )
        )
        op.alter_column("decisions", "decision_brief", nullable=False)

    if "updated_at" not in columns:
        op.add_column(
            "decisions",
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.execute(
            sa.text(
                """
                UPDATE decisions
                SET updated_at = created_at
                WHERE updated_at IS NULL
                """
            )
        )
        op.alter_column("decisions", "updated_at", nullable=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("decisions"):
        return

    columns = {column["name"] for column in inspector.get_columns("decisions")}

    if "updated_at" in columns:
        op.drop_column("decisions", "updated_at")

    if "decision_brief" in columns:
        op.drop_column("decisions", "decision_brief")
