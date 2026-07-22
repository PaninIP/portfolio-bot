"""add lead attachments

Revision ID: b7341d22e603
Revises: a42b10a559e6
Create Date: 2026-07-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "b7341d22e603"
down_revision: Union[str, Sequence[str], None] = "a42b10a559e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


attachment_type_enum = postgresql.ENUM(
    "document",
    "photo",
    "video",
    "audio",
    "voice",
    name="attachment_type",
    create_type=False,
)


def upgrade() -> None:
    """Upgrade schema."""

    bind = op.get_bind()
    attachment_type_enum.create(bind, checkfirst=True)

    op.create_table(
        "lead_attachments",
        sa.Column(
            "id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "lead_id",
            sa.BigInteger(),
            nullable=False,
        ),
        sa.Column(
            "attachment_type",
            attachment_type_enum,
            nullable=False,
        ),
        sa.Column(
            "telegram_file_id",
            sa.String(length=512),
            nullable=False,
        ),
        sa.Column(
            "telegram_file_unique_id",
            sa.String(length=128),
            nullable=False,
        ),
        sa.Column(
            "file_name",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "mime_type",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "file_size",
            sa.BigInteger(),
            nullable=True,
        ),
        sa.Column(
            "caption",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["lead_id"],
            ["leads.id"],
            name=op.f(
                "fk_lead_attachments_lead_id_leads"
            ),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name=op.f("pk_lead_attachments"),
        ),
    )

    op.create_index(
        "ix_lead_attachments_lead_created_at",
        "lead_attachments",
        ["lead_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(
        "ix_lead_attachments_lead_created_at",
        table_name="lead_attachments",
    )
    op.drop_table("lead_attachments")

    bind = op.get_bind()
    attachment_type_enum.drop(bind, checkfirst=True)
