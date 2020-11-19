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

from oslo_log import log as logging
import pecan
from pecan import hooks
from pecan import rest
from wsme import types as wtypes
import wsmeext.pecan as wsme_pecan

from mistral.api import access_control as acl
from mistral.api.controllers.v2 import resources
from mistral.api.controllers.v2 import types

from mistral.api.hooks import content_type as ct_hook
from mistral import context

from mistral.db.v2 import api as db_api
from mistral.services import code_sources

from mistral.utils import filter_utils
from mistral.utils import rest_utils

LOG = logging.getLogger(__name__)


class CodeSourcesController(rest.RestController, hooks.HookController):
    __hooks__ = [ct_hook.ContentTypeHook("application/json", ['POST', 'PUT'])]

    @rest_utils.wrap_pecan_controller_exception
    @pecan.expose(content_type="multipart/form-data")
    def post(self, namespace='', **files):
        """Creates new Code Sources.

        :param namespace: Optional. The namespace to create the code sources
            in.
        :params **files: a list of files to create code sources from,
            the variable name of the file will be the module name
        """

        acl.enforce('code_sources:create', context.ctx())

        LOG.debug(
            'Creating Code Sources with names: %s in namespace:[%s]',
            files.keys(),
            namespace
        )

        code_sources_db = code_sources.create_code_sources(namespace, **files)

        code_sources_list = [
            resources.CodeSource.from_db_model(db_cs)
            for db_cs in code_sources_db
        ]

        return resources.CodeSources(code_sources=code_sources_list).to_json()

    @wsme_pecan.wsexpose(resources.CodeSources, types.uuid, int,
                         types.uniquelist, types.list, types.uniquelist,
                         wtypes.text, wtypes.text,
                         resources.SCOPE_TYPES, types.uuid, wtypes.text,
                         wtypes.text, bool, wtypes.text)
    def get_all(self, marker=None, limit=None, sort_keys='created_at',
                sort_dirs='asc', fields='', name=None,
                tags=None, scope=None,
                project_id=None, created_at=None, updated_at=None,
                all_projects=False, namespace=None):
        """Return a list of Code Sources.

        :param marker: Optional. Pagination marker for large data sets.
        :param limit: Optional. Maximum number of resources to return in a
                      single result. Default value is None for backward
                      compatibility.
        :param sort_keys: Optional. Columns to sort results by.
                          Default: created_at.
        :param sort_dirs: Optional. Directions to sort corresponding to
                          sort_keys, "asc" or "desc" can be chosen.
                          Default: asc.
        :param fields: Optional. A specified list of fields of the resource to
                       be returned. 'id' will be included automatically in
                       fields if it's provided, since it will be used when
                       constructing 'next' link.
        :param name: Optional. Keep only resources with a specific name.
        :param namespace: Optional. Keep only resources with a specific
                          namespace
        :param input: Optional. Keep only resources with a specific input.
        :param definition: Optional. Keep only resources with a specific
                           definition.
        :param tags: Optional. Keep only resources containing specific tags.
        :param scope: Optional. Keep only resources with a specific scope.
        :param project_id: Optional. The same as the requester project_id
                           or different if the scope is public.
        :param created_at: Optional. Keep only resources created at a specific
                           time and date.
        :param updated_at: Optional. Keep only resources with specific latest
                           update time and date.
        :param all_projects: Optional. Get resources of all projects.
        """

        acl.enforce('code_sources:list', context.ctx())

        filters = filter_utils.create_filters_from_request_params(
            created_at=created_at,
            name=name,
            scope=scope,
            tags=tags,
            updated_at=updated_at,
            project_id=project_id,
            namespace=namespace
        )

        LOG.debug(
            "Fetch code sources. marker=%s, limit=%s, sort_keys=%s, "
            "sort_dirs=%s, fields=%s, filters=%s, all_projects=%s",
            marker,
            limit,
            sort_keys,
            sort_dirs,
            fields,
            filters,
            all_projects
        )

        return rest_utils.get_all(
            resources.CodeSources,
            resources.CodeSource,
            db_api.get_code_sources,
            db_api.get_code_source,
            marker=marker,
            limit=limit,
            sort_keys=sort_keys,
            sort_dirs=sort_dirs,
            fields=fields,
            all_projects=all_projects,
            **filters
        )

    @rest_utils.wrap_wsme_controller_exception
    @wsme_pecan.wsexpose(resources.CodeSource, wtypes.text, wtypes.text)
    def get(self, identifier, namespace=''):
        """Return the named Code Source.

        :param identifier: Name or UUID of the code source to retrieve.
        :param namespace: Optional. Namespace of the code source to retrieve.
        """

        acl.enforce('code_sources:get', context.ctx())

        LOG.debug(
            'Fetch Code Source [identifier=%s], [namespace=%s]',
            identifier,
            namespace
        )

        db_model = rest_utils.rest_retry_on_db_error(
            code_sources.get_code_source)(
            identifier=identifier,
            namespace=namespace
        )

        return resources.CodeSource.from_db_model(db_model)

    @rest_utils.wrap_pecan_controller_exception
    @wsme_pecan.wsexpose(None, wtypes.text, wtypes.text, status_code=204)
    def delete(self, identifier, namespace=''):
        """Delete a Code Source.

        :param identifier: Name or ID of Code Source to delete.
        :param namespace: Optional. Namespace of the Code Source to delete.
        """

        acl.enforce('code_sources:delete', context.ctx())

        LOG.debug(
            'Delete Code Source  [identifier=%s, namespace=%s]',
            identifier,
            namespace
        )

        rest_utils.rest_retry_on_db_error(
            code_sources.delete_code_source
        )(
            identifier=identifier,
            namespace=namespace
        )

    @rest_utils.wrap_pecan_controller_exception
    @pecan.expose(content_type="multipart/form-data")
    def put(self, namespace='', **files):
        """Update Code Sources.

        :param namespace: Optional. The namespace of the code sources.
        :params **files: a list of files to update code sources from.
        """
        acl.enforce('code_sources:update', context.ctx())

        LOG.debug(
            'Updating Code Sources with names: %s in namespace:[%s]',
            files.keys(),
            namespace
        )

        code_sources_db = code_sources.update_code_sources(namespace, **files)

        code_sources_list = [
            resources.CodeSource.from_db_model(db_cs)
            for db_cs in code_sources_db
        ]

        return resources.CodeSources(code_sources=code_sources_list).to_json()