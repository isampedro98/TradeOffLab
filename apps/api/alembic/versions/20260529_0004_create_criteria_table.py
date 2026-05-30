"""create criteria table

Revision ID: 20260529_0004
Revises: 20260525_0003
Create Date: 2026-05-29 10:30:00

"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260529_0004"
down_revision: str | None = "20260525_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("criteria"):
        return

    op.create_table(
        "criteria",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("decision_id", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column(
            "measurement_type",
            sa.Enum(
                "qualitative",
                "numeric",
                "boolean",
                "ordinal",
                name="criterionmeasurementtype",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["decision_id"], ["decisions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_criteria_decision_id", "criteria", ["decision_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("criteria"):
        return

    indexes = {index["name"] for index in inspector.get_indexes("criteria")}
    if "ix_criteria_decision_id" in indexes:
        op.drop_index("ix_criteria_decision_id", table_name="criteria")

    op.drop_table("criteria")
