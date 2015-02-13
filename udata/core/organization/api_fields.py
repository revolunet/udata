# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from flask import url_for

from udata.api import api, pager, fields

from .models import ORG_ROLES, MEMBERSHIP_STATUS


@api.model(fields={
    'id': fields.String(description='The organization identifier', required=True),
    'name': fields.String(description='The organization name', required=True),
    'uri': fields.String(description='The organization API URI', required=True),
    'page': fields.String(description='The organization web page URL', required=True),
    'image_url': fields.String(description='The organization logo URL'),
})
class OrganizationReference(fields.Raw):
    def format(self, organization):
        return {
            'id': str(organization.id),
            'uri': url_for('api.organization', org=organization, _external=True),
            'page': url_for('organizations.show', org=organization, _external=True),
            'name': organization.name,
            'logo': organization.logo(external=True),
        }


from udata.core.user.api_fields import UserReference

request_fields = api.model('MembershipRequest', {
    'status': fields.String(description='The current request status', required=True,
        enum=MEMBERSHIP_STATUS.keys()),
    'comment': fields.String(description='A request comment from the user', required=True),
})

member_fields = api.model('Member', {
    'user': UserReference,
    'role': fields.String(description='The member role in the organization', required=True,
        enum=ORG_ROLES.keys())
})


org_fields = api.model('Organization', {
    'id': fields.String(description='The organization identifier', required=True),
    'name': fields.String(description='The organization name', required=True),
    'acronym': fields.String(description='The organization acronym'),
    'url': fields.String(description='The organization website URL'),
    'slug': fields.String(description='The organization string used as permalink', required=True),
    'description': fields.Markdown(description='The organization description in Markdown', required=True),
    'created_at': fields.ISODateTime(description='The organization creation date', readonly=True),
    'last_modified': fields.ISODateTime(description='The organization last modification date', readonly=True),
    'deleted': fields.ISODateTime(description='The organization deletion date if deleted', readonly=True),
    'metrics': fields.Raw(description='The organization metrics', readonly=True),
    'uri': fields.UrlFor('api.organization', lambda o: {'org': o},
        description='The organization API URI', readonly=True),
    'page': fields.UrlFor('organizations.show', lambda o: {'org': o},
        description='The organization page URL', readonly=True),
    'logo': fields.ImageField(description='The organization logo URLs'),
    'members': api.as_list(fields.Nested(member_fields, description='The organization members')),
})

org_page_fields = api.model('OrganizationPage', pager(org_fields))

org_suggestion_fields = api.model('OrganizationSuggestion', {
    'id': fields.String(description='The organization identifier', readonly=True),
    'name': fields.String(description='The organization name', readonly=True),
    'slug': fields.String(description='The organization permalink string', readonly=True),
    'image_url': fields.String(description='The organization logo URL', readonly=True),
    'score': fields.Float(description='The internal match score', readonly=True),
})
