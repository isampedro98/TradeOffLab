"""create decisions table

Revision ID: 20260525_0001
Revises:
Create Date: 2026-05-25 20:45:00

"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260525_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("decisions"):
        return

    op.create_table(
        "decisions",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("context", sa.Text(), nullable=False),
        sa.Column(
            "type",
            sa.Enum(
                "erp_adoption",
                "architecture",
                "cloud_provider",
                "build_vs_buy",
                "procurement_automation",
                "software_stack",
                "strategic_technical",
                name="decisiontype",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "draft",
                "in_review",
                "recommended",
                "archived",
                name="decisionstatus",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("decisions"):
        return

    op.drop_table("decisions")
