"""Change zip_code to char(10)

Revision ID: 4e3679488f81
Revises: 10f615d4d0f4
Create Date: 2015-07-01 18:34:17.929996

"""

# revision identifiers, used by Alembic.
revision = '4e3679488f81'
down_revision = '10f615d4d0f4'

from alembic import op
import sqlalchemy as sa
from hipcooks import db
from hipcooks.models import Teacher


def upgrade():
    op.alter_column("Class_teacher", "zip_code", type_=sa.CHAR(10),
                    existing_type=sa.INT)
    db.session.execute(Teacher.__table__.update().values(
        zip_code=sa.func.LPAD(Teacher.zip_code, 5, '0')
    ))


def downgrade():
    pass
