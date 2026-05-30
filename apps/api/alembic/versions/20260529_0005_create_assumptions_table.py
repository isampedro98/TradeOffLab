"""create assumptions table

Revision ID: 20260529_0005
Revises: 20260529_0004
Create Date: 2026-05-29 10:55:00

"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260529_0005"
down_revision: str | None = "20260529_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("assumptions"):
        return

    op.create_table(
        "assumptions",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("decision_id", sa.String(length=255), nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column(
            "confidence",
            sa.Enum("low", "medium", "high", name="assumptionconfidence", native_enum=False),
            nullable=False,
        ),
        sa.Column("impact_if_false", sa.Text(), nullable=False),
        sa.Column("validation_method", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["decision_id"], ["decisions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_assumptions_decision_id", "assumptions", ["decision_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("assumptions"):
        return

    indexes = {index["name"] for index in inspector.get_indexes("assumptions")}
    if "ix_assumptions_decision_id" in indexes:
        op.drop_index("ix_assumptions_decision_id", table_name="assumptions")

    op.drop_table("assumptions")
