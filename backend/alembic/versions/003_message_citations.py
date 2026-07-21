"""Message citations linked to assistant chat messages.

Revision ID: 003_message_citations
Revises: 002_documents_and_chunks
Create Date: 2026-07-21
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003_message_citations"
down_revision: Union[str, Sequence[str], None] = "002_documents_and_chunks"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "message_citations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("message_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chunk_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("marker", sa.Integer(), nullable=False),
        sa.Column("quote", sa.Text(), nullable=True),
        sa.Column("source", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["message_id"], ["chat_messages.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["chunk_id"], ["document_chunks.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["document_id"], ["source_documents.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_message_citations_message_id"),
        "message_citations",
        ["message_id"],
        unique=False,
    )

    op.execute("ALTER TABLE message_citations ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY message_citations_select_own ON message_citations
        FOR SELECT TO authenticated
        USING (
            EXISTS (
                SELECT 1
                FROM chat_messages m
                JOIN chat_threads t ON t.id = m.thread_id
                WHERE m.id = message_citations.message_id
                  AND t.user_id = auth.uid()
            )
        )
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP POLICY IF EXISTS message_citations_select_own ON message_citations"
    )
    op.execute("ALTER TABLE message_citations DISABLE ROW LEVEL SECURITY")
    op.drop_index(
        op.f("ix_message_citations_message_id"), table_name="message_citations"
    )
    op.drop_table("message_citations")
