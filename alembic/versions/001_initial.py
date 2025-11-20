"""Initial database schema

Revision ID: 001_initial
Revises: 
Create Date: 2025-11-21

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import func

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create products table
    op.create_table(
        'products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sku', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_products_id', 'products', ['id'])
    
    # Create case-insensitive unique index on SKU
    op.create_index(
        'idx_sku_lower',
        'products',
        [sa.text('lower(sku)')],
        unique=True
    )
    
    # Create webhooks table
    op.create_table(
        'webhooks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('url', sa.String(length=500), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_webhooks_id', 'webhooks', ['id'])
    
    # Create upload_tasks table
    op.create_table(
        'upload_tasks',
        sa.Column('id', sa.String(length=100), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('progress', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_rows', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('processed_rows', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('upload_tasks')
    op.drop_index('ix_webhooks_id', 'webhooks')
    op.drop_table('webhooks')
    op.drop_index('idx_sku_lower', 'products')
    op.drop_index('ix_products_id', 'products')
    op.drop_table('products')
