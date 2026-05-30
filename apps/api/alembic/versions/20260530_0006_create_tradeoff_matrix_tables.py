"""create tradeoff matrix tables

Revision ID: 20260530_0006
Revises: 20260529_0005
Create Date: 2026-05-30 10:15:00

"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260530_0006"
down_revision: str | None = "20260529_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("tradeoff_matrices"):
        op.create_table(
            "tradeoff_matrices",
            sa.Column("id", sa.String(length=255), nullable=False),
            sa.Column("decision_id", sa.String(length=255), nullable=False),
            sa.Column("summary", sa.Text(), nullable=False),
            sa.Column("scoring_scale_label", sa.String(length=255), nullable=False),
            sa.Column("provider", sa.String(length=100), nullable=False),
            sa.Column("model", sa.String(length=255), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["decision_id"], ["decisions.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("decision_id"),
        )
        op.create_index(
            "ix_tradeoff_matrices_decision_id",
            "tradeoff_matrices",
            ["decision_id"],
            unique=True,
        )

    if not inspector.has_table("tradeoff_assessments"):
        op.create_table(
            "tradeoff_assessments",
            sa.Column("id", sa.String(length=255), nullable=False),
            sa.Column("matrix_id", sa.String(length=255), nullable=False),
            sa.Column("criterion_id", sa.String(length=255), nullable=False),
            sa.Column("option_id", sa.String(length=255), nullable=False),
            sa.Column("score", sa.Float(), nullable=False),
            sa.Column("rationale", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(
                ["criterion_id"], ["criteria.id"], ondelete="CASCADE"
            ),
            sa.ForeignKeyConstraint(["matrix_id"], ["tradeoff_matrices.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["option_id"], ["options.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "matrix_id",
                "criterion_id",
                "option_id",
                name="uq_tradeoff_assessments_matrix_criterion_option",
            ),
        )
        op.create_index(
            "ix_tradeoff_assessments_matrix_id",
            "tradeoff_assessments",
            ["matrix_id"],
            unique=False,
        )
        op.create_index(
            "ix_tradeoff_assessments_criterion_id",
            "tradeoff_assessments",
            ["criterion_id"],
            unique=False,
        )
        op.create_index(
            "ix_tradeoff_assessments_option_id",
            "tradeoff_assessments",
            ["option_id"],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("tradeoff_assessments"):
        indexes = {index["name"] for index in inspector.get_indexes("tradeoff_assessments")}
        for index_name in (
            "ix_tradeoff_assessments_matrix_id",
            "ix_tradeoff_assessments_criterion_id",
            "ix_tradeoff_assessments_option_id",
        ):
            if index_name in indexes:
                op.drop_index(index_name, table_name="tradeoff_assessments")
        op.drop_table("tradeoff_assessments")

    if inspector.has_table("tradeoff_matrices"):
        indexes = {index["name"] for index in inspector.get_indexes("tradeoff_matrices")}
        if "ix_tradeoff_matrices_decision_id" in indexes:
            op.drop_index("ix_tradeoff_matrices_decision_id", table_name="tradeoff_matrices")
        op.drop_table("tradeoff_matrices")
