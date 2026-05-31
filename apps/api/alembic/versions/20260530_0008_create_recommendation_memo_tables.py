"""create recommendation memo tables

Revision ID: 20260530_0008
Revises: 20260530_0007
Create Date: 2026-05-30 22:45:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260530_0008"
down_revision = "20260530_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    confidence_enum = sa.Enum(
        "LOW",
        "MEDIUM",
        "HIGH",
        name="recommendationconfidence",
        native_enum=False,
    )

    op.create_table(
        "recommendation_memos",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("decision_id", sa.String(length=255), nullable=False),
        sa.Column("recommended_option_id", sa.String(length=255), nullable=False),
        sa.Column("fallback_option_id", sa.String(length=255), nullable=True),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("confidence", confidence_enum, nullable=False),
        sa.Column("provider", sa.String(length=100), nullable=False),
        sa.Column("model", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["decision_id"], ["decisions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["recommended_option_id"], ["options.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["fallback_option_id"], ["options.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("decision_id"),
    )
    op.create_index(
        "ix_recommendation_memos_decision_id",
        "recommendation_memos",
        ["decision_id"],
    )
    op.create_index(
        "ix_recommendation_memos_recommended_option_id",
        "recommendation_memos",
        ["recommended_option_id"],
    )
    op.create_index(
        "ix_recommendation_memos_fallback_option_id",
        "recommendation_memos",
        ["fallback_option_id"],
    )

    op.create_table(
        "recommendation_conditions",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("memo_id", sa.String(length=255), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["memo_id"], ["recommendation_memos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_recommendation_conditions_memo_id",
        "recommendation_conditions",
        ["memo_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_recommendation_conditions_memo_id",
        table_name="recommendation_conditions",
    )
    op.drop_table("recommendation_conditions")

    op.drop_index(
        "ix_recommendation_memos_fallback_option_id",
        table_name="recommendation_memos",
    )
    op.drop_index(
        "ix_recommendation_memos_recommended_option_id",
        table_name="recommendation_memos",
    )
    op.drop_index(
        "ix_recommendation_memos_decision_id",
        table_name="recommendation_memos",
    )
    op.drop_table("recommendation_memos")
    op.execute("DROP TYPE IF EXISTS recommendationconfidence")
