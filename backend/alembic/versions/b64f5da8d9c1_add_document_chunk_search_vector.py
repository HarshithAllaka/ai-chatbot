"""add document chunk search vector

Revision ID: b64f5da8d9c1
Revises: aebf2dc1adca
Create Date: 2026-08-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "b64f5da8d9c1"
down_revision: Union[str, Sequence[str], None] = "aebf2dc1adca"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "document_chunks",
        sa.Column(
            "search_vector",
            postgresql.TSVECTOR(),
            sa.Computed(
                "to_tsvector('english', content)",
                persisted=True,
            ),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_document_chunks_search_vector",
        "document_chunks",
        ["search_vector"],
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_document_chunks_search_vector",
        table_name="document_chunks",
    )

    op.drop_column(
        "document_chunks",
        "search_vector",
    )
