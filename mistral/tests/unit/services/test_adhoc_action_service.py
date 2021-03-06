# Copyright 2014 - Mirantis, Inc.
# Copyright 2020 Nokia Software.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

from oslo_config import cfg

from mistral.db.v2 import api as db_api
from mistral.exceptions import DBEntityNotFoundError
from mistral.lang import parser as spec_parser
from mistral.services import adhoc_actions as adhoc_action_service
from mistral.tests.unit import base
from mistral_lib import utils

# Use the set_default method to set value otherwise in certain test cases
# the change in value is not permanent.
cfg.CONF.set_default('auth_enable', False, group='pecan')

ACTION_LIST = """
---
version: '2.0'

action1:
  tags: [test, v2]
  base: std.echo output='Hi'
  output:
    result: $

action2:
  base: std.echo output='Hey'
  output:
    result: $
"""

UPDATED_ACTION_LIST = """
---
version: '2.0'

action1:
  base: std.echo output='Hi'
  input:
    - param1
  output:
    result: $
"""

NAMESPACE = 'test_namespace'


class AdhocActionServiceTest(base.DbTestCase):
    def setUp(self):
        super(AdhocActionServiceTest, self).setUp()

        self.addCleanup(db_api.delete_action_definitions, name='action1')
        self.addCleanup(db_api.delete_action_definitions, name='action2')

    def test_create_actions(self):
        db_actions = adhoc_action_service.create_actions(ACTION_LIST)

        self.assertEqual(2, len(db_actions))

        # Action 1.
        action1_db = self._assert_single_item(db_actions, name='action1')
        action1_spec = spec_parser.get_action_spec(action1_db.spec)

        self.assertEqual('action1', action1_spec.get_name())
        self.assertListEqual(['test', 'v2'], action1_spec.get_tags())
        self.assertEqual('std.echo', action1_spec.get_base())
        self.assertDictEqual({'output': 'Hi'}, action1_spec.get_base_input())

        # Action 2.
        action2_db = self._assert_single_item(db_actions, name='action2')
        self.assertEqual('', action2_db.namespace)
        action2_spec = spec_parser.get_action_spec(action2_db.spec)

        self.assertEqual('action2', action2_spec.get_name())
        self.assertEqual('std.echo', action1_spec.get_base())
        self.assertDictEqual({'output': 'Hey'}, action2_spec.get_base_input())

    def test_create_actions_in_namespace(self):
        db_actions = adhoc_action_service.create_actions(
            ACTION_LIST,
            namespace=NAMESPACE
        )

        self.assertEqual(2, len(db_actions))

        self._assert_single_item(
            db_actions,
            name='action1',
            namespace=NAMESPACE
        )

        self._assert_single_item(
            db_actions,
            name='action2',
            namespace=NAMESPACE
        )

        self.assertRaises(
            DBEntityNotFoundError,
            db_api.get_action_definition,
            name='action1',
            namespace=''
        )

    def test_update_actions(self):
        db_actions = adhoc_action_service.create_actions(
            ACTION_LIST,
            namespace=NAMESPACE
        )

        self.assertEqual(2, len(db_actions))

        action1_db = self._assert_single_item(db_actions, name='action1')
        action1_spec = spec_parser.get_action_spec(action1_db.spec)

        self.assertEqual('action1', action1_spec.get_name())
        self.assertEqual('std.echo', action1_spec.get_base())
        self.assertDictEqual({'output': 'Hi'}, action1_spec.get_base_input())
        self.assertDictEqual({}, action1_spec.get_input())

        db_actions = adhoc_action_service.update_actions(
            UPDATED_ACTION_LIST,
            namespace=NAMESPACE
        )

        # Action 1.
        action1_db = self._assert_single_item(db_actions, name='action1')
        action1_spec = spec_parser.get_action_spec(action1_db.spec)

        self.assertEqual('action1', action1_spec.get_name())
        self.assertListEqual([], action1_spec.get_tags())
        self.assertEqual('std.echo', action1_spec.get_base())
        self.assertDictEqual({'output': 'Hi'}, action1_spec.get_base_input())
        self.assertIn('param1', action1_spec.get_input())
        self.assertIs(
            action1_spec.get_input().get('param1'),
            utils.NotDefined
        )

        self.assertRaises(
            DBEntityNotFoundError,
            adhoc_action_service.update_actions,
            UPDATED_ACTION_LIST,
            namespace=''
        )

    def test_delete_action(self):

        # Create action.
        adhoc_action_service.create_actions(ACTION_LIST, namespace=NAMESPACE)

        action = db_api.get_action_definition('action1', namespace=NAMESPACE)
        self.assertEqual(NAMESPACE, action.get('namespace'))
        self.assertEqual('action1', action.get('name'))

        # Delete action.
        db_api.delete_action_definition('action1', namespace=NAMESPACE)

        self.assertRaises(
            DBEntityNotFoundError,
            db_api.get_action_definition,
            name='action1',
            namespace=NAMESPACE
        )
