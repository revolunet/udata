# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from udata.api import api, pager, fields

from udata.core.organization.api_fields import OrganizationReference
from udata.core.dataset.api_fields import DatasetReference
from udata.core.user.api_fields import UserReference

from .models import REUSE_TYPES

reuse_fields = api.model('Reuse', {
    'id': fields.String(description='The reuse identifier'),
    'title': fields.String(description='The reuse title', required=True),
    'slug': fields.String(description='The reuse permalink string', readonly=True),
    'type': fields.String(description='The reuse type', required=True, enum=REUSE_TYPES.keys()),
    'url': fields.String(description='The reuse remote URL (website)', required=True),
    'description': fields.Markdown(description='The reuse description in Markdown', required=True),
    'tags': fields.List(fields.String, description='Some keywords to help in search'),
    'featured': fields.Boolean(description='Is the reuse featured', readonly=True),
    'image': fields.ImageField(description='The reuse thumbnail'),
    'created_at': fields.ISODateTime(description='The reuse creation date', readonly=True),
    'last_modified': fields.ISODateTime(description='The reuse last modification date', readonly=True),
    'deleted': fields.ISODateTime(description='The organization identifier', readonly=True),
    'datasets': fields.List(DatasetReference, description='The reused datasets'),
    'organization': OrganizationReference(description='The publishing organization', readonly=True),
    'owner': UserReference(description='The owner user', readonly=True),
    'metrics': fields.Raw(description='The reuse metrics'),
    'uri': fields.UrlFor('api.reuse', lambda o: {'reuse': o},
        description='The reuse API URI', required=True),
    'page': fields.UrlFor('reuses.show', lambda o: {'reuse': o},
        description='The reuse page URL', required=True),
})

reuse_page_fields = api.model('ReusePage', pager(reuse_fields))

reuse_suggestion_fields = api.model('ReuseSuggestion', {
    'id': fields.String(description='The reuse identifier', required=True),
    'title': fields.String(description='The reuse title', required=True),
    'slug': fields.String(description='The reuse permalink string', required=True),
    'image_url': fields.String(description='The reuse thumbnail URL'),
    'score': fields.Float(description='The internal match score', required=True),
})
