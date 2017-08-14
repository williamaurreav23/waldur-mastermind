import mock
from rest_framework import test, status

from nodeconductor.structure.tests import factories as structure_factories
from nodeconductor.structure.tests import fixtures as structure_fixtures
from nodeconductor.structure import models as structure_models
from nodeconductor.users import models as user_models

from .. import models
from . import factories


class ExpertBidBaseTest(test.APITransactionTestCase):

    def setUp(self):
        self.expert_fixture = structure_fixtures.ProjectFixture()
        self.expert_manager = self.expert_fixture.owner
        self.expert_provider = factories.ExpertProviderFactory(customer=self.expert_fixture.customer)

        self.project_fixture = structure_fixtures.ProjectFixture()
        self.project = self.project_fixture.project
        self.expert_request = factories.ExpertRequestFactory(project=self.project)
        self.expert = self.project_fixture.admin


class ExpertBidListTest(ExpertBidBaseTest):
    def setUp(self):
        super(ExpertBidListTest, self).setUp()
        self.expert_bid = factories.ExpertBidFactory(
            request=self.expert_request,
            team=self.expert_fixture.project,
        )

    def test_expert_manager_can_see_owned_bid(self):
        self.client.force_authenticate(self.expert_manager)
        response = self.client.get(factories.ExpertBidFactory.get_list_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_other_expert_manager_can_not_see_expert_bid(self):
        fixture = structure_fixtures.ProjectFixture()
        factories.ExpertProviderFactory(customer=fixture.customer)
        self.client.force_authenticate(fixture.owner)
        response = self.client.get(factories.ExpertBidFactory.get_list_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_team_members_list_is_rendered_for_bid(self):
        team_member = self.expert_fixture.manager
        self.client.force_authenticate(self.expert_fixture.staff)

        response = self.client.get(factories.ExpertBidFactory.get_url(self.expert_bid))
        self.assertEqual(len(response.data['team_members']), 1)

        actual_member = response.data['team_members'][0]
        self.assertEqual(actual_member['username'], team_member.username)


class ExpertBidCreateTest(ExpertBidBaseTest):

    def test_expert_manager_can_create_expert_bid(self):
        self.client.force_authenticate(self.expert_manager)
        response = self.create_expert_bid()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_project_manager_can_not_create_expert_bid(self):
        self.client.force_authenticate(self.project_fixture.manager)
        response = self.create_expert_bid()
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_bid_can_be_created_for_pending_request_only(self):
        self.expert_request.state = models.ExpertRequest.States.ACTIVE
        self.expert_request.save()
        self.client.force_authenticate(self.expert_manager)
        response = self.create_expert_bid()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('request', response.data)

    def test_team_should_have_at_least_one_member(self):
        self.project.remove_user(self.expert)
        self.client.force_authenticate(self.expert_manager)
        response = self.create_expert_bid()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_when_expert_bid_is_created_event_is_emitted(self):
        with mock.patch('logging.LoggerAdapter.info') as mocked_info:
            expert_bid = factories.ExpertBidFactory()
            template = 'User {user_username} with full name {user_full_name} has created ' \
                       'bid for request {request_name} under {customer_name} / {project_name}.'
            context = {
                'user_username': expert_bid.user.username,
                'user_full_name': expert_bid.user.full_name,
                'request_name': expert_bid.request.name,
                'customer_name': expert_bid.request.project.customer.name,
                'project_name': expert_bid.request.project.name,
            }
            expected_message = template.format(**context)
            actual_message = mocked_info.call_args_list[-1][0][0]
            self.assertEqual(expected_message, actual_message)

    def create_expert_bid(self):
        url = factories.ExpertBidFactory.get_list_url()
        return self.client.post(url, {
            'request': factories.ExpertRequestFactory.get_url(self.expert_request),
            'team': structure_factories.ProjectFactory.get_url(self.project),
            'price': 100.00,
        })


class ExpertBidAcceptTest(ExpertBidBaseTest):

    def setUp(self):
        super(ExpertBidAcceptTest, self).setUp()
        self.team = self.expert_fixture.project
        self.expert_bid = factories.ExpertBidFactory(request=self.expert_request, team=self.team)

    def test_staff_can_accept_bid(self):
        self.client.force_authenticate(self.project_fixture.staff)
        response = self.accept_bid()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_customer_owner_can_accept_bid(self):
        self.client.force_authenticate(self.project_fixture.owner)
        response = self.accept_bid()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_project_manager_can_not_accept_bid(self):
        self.client.force_authenticate(self.project_fixture.manager)
        response = self.accept_bid()
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.data)

    def test_customer_owner_can_not_accept_bid_if_request_is_not_pending(self):
        self.expert_request.state = models.ExpertRequest.States.ACTIVE
        self.expert_request.save()
        self.client.force_authenticate(self.project_fixture.owner)
        response = self.accept_bid()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_when_bid_accepted_request_becomes_active(self):
        self.client.force_authenticate(self.project_fixture.owner)
        response = self.accept_bid()
        self.expert_request.refresh_from_db()
        self.assertEqual(self.expert_request.state, models.ExpertRequest.States.ACTIVE)

    def test_when_bid_accepted_event_is_emitted(self):
        self.client.force_authenticate(self.project_fixture.owner)
        with mock.patch('logging.LoggerAdapter.info') as mocked_info:
            response = self.accept_bid()
            template = 'Expert request {expert_request_name} has been activated.'
            context = {
                'expert_request_name': self.expert_bid.request.name,
            }
            expected_message = template.format(**context)
            actual_message = mocked_info.call_args_list[-1][0][0]
            self.assertEqual(expected_message, actual_message)

    def test_when_bid_accepted_invitations_for_expert_team_members_are_created(self):
        # Arrange
        expert_users = structure_factories.UserFactory.create_batch(3)
        for user in expert_users:
            self.team.add_user(user, structure_models.ProjectRole.ADMINISTRATOR)

        # Act
        self.client.force_authenticate(self.project_fixture.owner)
        self.accept_bid()

        # Assert
        invitations = self.get_invitations(expert_users)
        self.assertEqual(len(invitations), len(expert_users))

    @mock.patch('nodeconductor.users.tasks.send_invitation')
    def test_when_bid_accepted_invitations_for_expert_team_members_are_created(self, mocked_task):
        # Arrange
        expert_users = structure_factories.UserFactory.create_batch(3)
        for user in expert_users:
            self.team.add_user(user, structure_models.ProjectRole.ADMINISTRATOR)

        # Act
        self.client.force_authenticate(self.project_fixture.owner)
        self.accept_bid()

        # Assert
        invitations = self.get_invitations(expert_users)
        self.assertEqual(len(invitations), len(expert_users))

        calls = [
            mock.call(invitation.uuid.hex, self.project_fixture.owner.full_name)
            for invitation in invitations
        ]
        mocked_task.delay.assert_has_calls(calls)

    @mock.patch('nodeconductor_assembly_waldur.experts.tasks.send_contract')
    def test_when_bid_accepted_notification_emails_for_customer_owners_are_sent(self, mocked_task):
        self.client.force_authenticate(self.project_fixture.owner)
        self.accept_bid()
        mocked_task.delay.assert_called_once_with(
            self.expert_request.uuid.hex, self.project_fixture.owner.email)

    def test_when_bid_accepted_contract_is_created(self):
        self.client.force_authenticate(self.project_fixture.owner)
        self.accept_bid()
        self.expert_request.refresh_from_db()
        self.assertIsNotNone(self.expert_request.contract)

    def get_invitations(self, users):
        return user_models.Invitation.objects.filter(
            project=self.project,
            customer=self.project.customer,
            created_by=self.project_fixture.owner,
            email__in=[user.email for user in users],
            project_role=structure_models.ProjectRole.ADMINISTRATOR,
        )

    def accept_bid(self):
        url = factories.ExpertBidFactory.get_url(self.expert_bid, 'accept')
        return self.client.post(url)