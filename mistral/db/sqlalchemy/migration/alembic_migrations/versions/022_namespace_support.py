# Copyright 2017 OpenStack Foundation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""namespace_support

Revision ID: 022
Revises: 021
Create Date: 2017-06-11 13:09:06.782095

"""

# revision identifiers, used by Alembic.
revision = '022'
down_revision = '021'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine import reflection
from sqlalchemy.sql import table, column


# A simple model of the workflow definitions table with only the field needed
wf_def = table('workflow_definitions_v2', column('namespace'))

# A simple model of the workflow executions table with only the field needed
wf_exec = table('workflow_executions_v2', column('workflow_namespace'))

# A simple model of the task executions table with only the field needed
task_exec = table('task_executions_v2', column('workflow_namespace'))

# A simple model of the action executions table with only the fields needed
action_executions = sa.Table(
    'action_executions_v2',
    sa.MetaData(),
    sa.Column('id', sa.String(36), nullable=False),
    sa.Column('workflow_name', sa.String(255)),
    sa.Column('workflow_namespace', sa.String(255), nullable=True)
)


def upgrade():

    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        'workflow_definitions_v2',
        sa.Column(
            'namespace',
            sa.String(length=255),
            nullable=True
        )
    )

    inspect = reflection.Inspector.from_engine(op.get_bind())

    unique_constraints = [
        unique_constraint['name'] for unique_constraint in
        inspect.get_unique_constraints('workflow_definitions_v2')
    ]

    if 'name' in unique_constraints:
        op.drop_index('name', table_name='workflow_definitions_v2')

    op.create_unique_constraint(
        None,
        'workflow_definitions_v2',
        ['name', 'namespace', 'project_id']
    )

    op.add_column(
        'workflow_executions_v2',
        sa.Column(
            'workflow_namespace',
            sa.String(length=255),
            nullable=True
        )
    )

    op.add_column(
        'task_executions_v2',
        sa.Column(
            'workflow_namespace',
            sa.String(length=255),
            nullable=True
        )
    )

    op.add_column(
        'action_executions_v2',
        sa.Column('workflow_namespace', sa.String(length=255), nullable=True)
    )

    session = sa.orm.Session(bind=op.get_bind())
    values = []

    for row in session.query(action_executions):
        values.append({'id': row[0],
                       'workflow_name': row[1]})

    with session.begin(subtransactions=True):
        session.execute(wf_def.update().values(namespace=''))
        session.execute(wf_exec.update().values(workflow_namespace=''))
        session.execute(task_exec.update().values(workflow_namespace=''))

        for value in values:
            if value['workflow_name']:
                session.execute(action_executions.update().values(
                    workflow_namespace=''
                ).where(action_executions.c.id == value['id']))

    # this commit appears to be necessary
    session.commit()

# ### end Alembic commands ###
