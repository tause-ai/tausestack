"""
Initial DB structure for workflows and executions
"""
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None
from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as pg

def upgrade():
    op.create_table(
        'workflows',
        sa.Column('id', pg.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(128), unique=True, nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('definition', pg.JSONB, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False)
    )
    op.create_table(
        'workflow_executions',
        sa.Column('id', pg.UUID(as_uuid=True), primary_key=True),
        sa.Column('workflow_id', pg.UUID(as_uuid=True), sa.ForeignKey('workflows.id'), nullable=False),
        sa.Column('input_data', pg.JSONB, nullable=True),
        sa.Column('steps', pg.JSONB, nullable=False),
        sa.Column('history', pg.JSONB, nullable=False),
        sa.Column('error', sa.Text, nullable=True),
        sa.Column('started_at', sa.DateTime, nullable=False),
        sa.Column('finished_at', sa.DateTime, nullable=False)
    )

def downgrade():
    op.drop_table('workflow_executions')
    op.drop_table('workflows')
