from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from nodeconductor.core import serializers as core_serializers
from nodeconductor.structure import models as structure_models, SupportedServices

from . import models


User = get_user_model()


class IssueSerializer(core_serializers.AugmentedSerializerMixin,
                      serializers.HyperlinkedModelSerializer):
    resource = core_serializers.GenericRelatedField(
        related_models=structure_models.ResourceMixin.get_all_models(), required=False)
    reporter_user = serializers.HyperlinkedRelatedField(
        source='reporter.user',
        view_name='user-detail',
        lookup_field='uuid',
        queryset=User.objects.all(),
        required=False,
        allow_null=True,
    )
    caller_user = serializers.HyperlinkedRelatedField(
        source='caller.user',
        view_name='user-detail',
        lookup_field='uuid',
        read_only=True,
    )
    assignee_user = serializers.HyperlinkedRelatedField(
        source='assignee.user',
        view_name='user-detail',
        lookup_field='uuid',
        read_only=True,
    )
    resource_type = serializers.SerializerMethodField()

    class Meta(object):
        model = models.Issue
        fields = (
            'url', 'uuid', 'type', 'key', 'backend_id',
            'summary', 'description', 'status', 'resolution',
            'reporter_name', 'reporter_user',
            'caller_name', 'caller_user',
            'assignee_name', 'assignee_user',
            'customer', 'customer_uuid', 'customer_name',
            'project', 'project_uuid', 'project_name',
            'resource', 'resource_type',
            'created', 'modified',
        )
        read_only_fields = ('key', 'status', 'resolution', 'backend_id')
        protected_fields = ('customer', 'project', 'resource', 'type', 'reporter_user')
        extra_kwargs = dict(
            url={'lookup_field': 'uuid', 'view_name': 'support-issue-detail'},
            customer={'lookup_field': 'uuid', 'view_name': 'customer-detail'},
            project={'lookup_field': 'uuid', 'view_name': 'project-detail'},
        )
        related_paths = dict(
            reporter=('name',),
            caller=('name',),
            assignee=('name',),
            customer=('uuid', 'name',),
            project=('uuid', 'name',),
        )

    def get_resource_type(self, obj):
        if obj.resource:
            return SupportedServices.get_name_for_model(obj.resource_content_type.model_class())

    @transaction.atomic()
    def create(self, validated_data):
        caller_user = self.context['request'].user
        reporter_user = validated_data.get('reporter', {}).get('user', caller_user)
        validated_data['reporter'], _ = models.SupportUser.objects.get_or_create(
            user=reporter_user, defaults={'name': reporter_user.full_name})
        validated_data['caller'], _ = models.SupportUser.objects.get_or_create(
            user=caller_user, defaults={'name': caller_user.full_name})

        resource = validated_data.get('resource')
        if resource:
            validated_data['project'] = resource.service_project_link.project
        project = validated_data.get('project')
        if project:
            validated_data['customer'] = project.customer

        issue = super(IssueSerializer, self).create(validated_data)
        # Hotfix. Should be removed after proper integration implementation.
        issue.key = 'SUPPORT-%s' % issue.id
        issue.status = 'New'
        issue.save()

        return issue


class CommentSerializer(core_serializers.AugmentedSerializerMixin,
                        serializers.HyperlinkedModelSerializer):
    # should be initialized with issue in context on creation
    author_user = serializers.HyperlinkedRelatedField(
        source='author.user',
        view_name='user-detail',
        lookup_field='uuid',
        read_only=True,
    )

    class Meta(object):
        model = models.Comment
        fields = ('url', 'uuid', 'issue', 'description', 'is_public', 'author_name', 'author_user', 'backend_id')
        read_only_fields = ('issue', 'backend_id',)
        extra_kwargs = dict(
            url={'lookup_field': 'uuid', 'view_name': 'support-comment-detail'},
            issue={'lookup_field': 'uuid', 'view_name': 'support-issue-detail'},
        )
        related_paths = dict(
            author=('name',),
        )

    @transaction.atomic()
    def create(self, validated_data):
        author_user = self.context['request'].user
        validated_data['author'], _ = models.SupportUser.objects.get_or_create(
            user=author_user, defaults={'name': author_user.full_name})
        validated_data['issue'] = self.context['issue']
        return super(CommentSerializer, self).create(validated_data)