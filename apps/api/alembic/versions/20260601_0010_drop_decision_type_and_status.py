"""drop decision type and status columns

Revision ID: 20260601_0010
Revises: 20260531_0009
Create Date: 2026-06-01 12:00:00

"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260601_0010"
down_revision: str | None = "20260531_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("decisions"):
        return

    columns = {column["name"] for column in inspector.get_columns("decisions")}
    if "type" in columns:
        op.drop_column("decisions", "type")
    if "status" in columns:
        op.drop_column("decisions", "status")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("decisions"):
        return

    columns = {column["name"] for column in inspector.get_columns("decisions")}
    if "type" not in columns:
        op.add_column(
            "decisions",
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
                server_default="software_stack",
            ),
        )
    if "status" not in columns:
        op.add_column(
            "decisions",
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
                server_default="draft",
            ),
        )
