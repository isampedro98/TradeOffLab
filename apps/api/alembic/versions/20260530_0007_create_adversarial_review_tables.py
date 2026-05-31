"""create adversarial review tables

Revision ID: 20260530_0007
Revises: 20260530_0006
Create Date: 2026-05-30 22:10:00

"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260530_0007"
down_revision: str | None = "20260530_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("adversarial_reviews"):
        op.create_table(
            "adversarial_reviews",
            sa.Column("id", sa.String(length=255), nullable=False),
            sa.Column("decision_id", sa.String(length=255), nullable=False),
            sa.Column("summary", sa.Text(), nullable=False),
            sa.Column(
                "overall_risk",
                sa.Enum("LOW", "MEDIUM", "HIGH", name="adversarialreviewseverity", native_enum=False),
                nullable=False,
            ),
            sa.Column("provider", sa.String(length=100), nullable=False),
            sa.Column("model", sa.String(length=255), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["decision_id"], ["decisions.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("decision_id"),
        )
        op.create_index(
            "ix_adversarial_reviews_decision_id",
            "adversarial_reviews",
            ["decision_id"],
            unique=True,
        )

    if not inspector.has_table("adversarial_review_findings"):
        op.create_table(
            "adversarial_review_findings",
            sa.Column("id", sa.String(length=255), nullable=False),
            sa.Column("review_id", sa.String(length=255), nullable=False),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column(
                "severity",
                sa.Enum("LOW", "MEDIUM", "HIGH", name="adversarialreviewseverity", native_enum=False),
                nullable=False,
            ),
            sa.Column("critique", sa.Text(), nullable=False),
            sa.Column("consequence", sa.Text(), nullable=False),
            sa.Column("mitigation_test", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(
                ["review_id"], ["adversarial_reviews.id"], ondelete="CASCADE"
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_adversarial_review_findings_review_id",
            "adversarial_review_findings",
            ["review_id"],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("adversarial_review_findings"):
        indexes = {
            index["name"] for index in inspector.get_indexes("adversarial_review_findings")
        }
        if "ix_adversarial_review_findings_review_id" in indexes:
            op.drop_index(
                "ix_adversarial_review_findings_review_id",
                table_name="adversarial_review_findings",
            )
        op.drop_table("adversarial_review_findings")

    if inspector.has_table("adversarial_reviews"):
        indexes = {index["name"] for index in inspector.get_indexes("adversarial_reviews")}
        if "ix_adversarial_reviews_decision_id" in indexes:
            op.drop_index(
                "ix_adversarial_reviews_decision_id",
                table_name="adversarial_reviews",
            )
        op.drop_table("adversarial_reviews")

    bind.execute(sa.text("DROP TYPE IF EXISTS adversarialreviewseverity"))
