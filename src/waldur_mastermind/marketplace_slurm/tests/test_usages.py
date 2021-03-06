import datetime

from rest_framework import test

from waldur_core.core.utils import month_start
from waldur_core.structure.tests import fixtures as structure_fixtures, factories as structure_factories
from waldur_mastermind.invoices import models as invoices_models
from waldur_mastermind.marketplace import models as marketplace_models
from waldur_mastermind.marketplace.plugins import manager
from waldur_mastermind.marketplace.tests import factories as marketplace_factories
from waldur_mastermind.marketplace_slurm import PLUGIN_NAME
from waldur_slurm.tests import factories as slurm_factories

from django.utils import timezone


class BaseTest(test.APITransactionTestCase):
    def setUp(self):
        fixture = structure_fixtures.ProjectFixture()
        service_settings = structure_factories.ServiceSettingsFactory(type='SLURM')
        offering = marketplace_factories.OfferingFactory(type=PLUGIN_NAME, scope=service_settings)
        plan = marketplace_factories.PlanFactory(offering=offering)
        self.allocation = slurm_factories.AllocationFactory()
        self.resource = marketplace_models.Resource.objects.create(
            scope=self.allocation,
            offering=offering,
            plan=plan,
            project=fixture.project,
        )
        self.plan_period = marketplace_models.ResourcePlanPeriod.objects.create(
            resource=self.resource,
            plan=plan,
            start=timezone.make_aware(datetime.datetime.now())
        )
        for component in manager.get_components(PLUGIN_NAME):
            offering_component = marketplace_models.OfferingComponent.objects.create(
                offering=offering,
                type=component.type,
                name=component.name,
                measured_unit=component.measured_unit,
                billing_type=marketplace_models.OfferingComponent.BillingTypes.USAGE,
            )
            marketplace_models.PlanComponent.objects.create(
                component=offering_component,
                plan=plan,
                price=3
            )

        marketplace_models.ResourcePlanPeriod.objects.create(
            start=datetime.date(2017, 1, 1),
            resource=self.resource,
            plan=plan)


class ComponentUsageTest(BaseTest):
    def test_create_component_usage(self):
        slurm_factories.AllocationUsageFactory(allocation=self.allocation, year=2017, month=1)
        self.assertTrue(marketplace_models.ComponentUsage.objects
                        .filter(resource=self.resource, component__type='cpu').exists())
        self.assertTrue(marketplace_models.ComponentUsage.objects
                        .filter(resource=self.resource, component__type='gpu').exists())
        self.assertTrue(marketplace_models.ComponentUsage.objects
                        .filter(resource=self.resource, component__type='ram').exists())

    def test_not_create_component_usage_if_create_other_allocation_usage(self):
        slurm_factories.AllocationUsageFactory()
        self.assertFalse(marketplace_models.ComponentUsage.objects
                         .filter(resource=self.resource, component__type='cpu').exists())
        self.assertFalse(marketplace_models.ComponentUsage.objects
                         .filter(resource=self.resource, component__type='gpu').exists())
        self.assertFalse(marketplace_models.ComponentUsage.objects
                         .filter(resource=self.resource, component__type='ram').exists())

    def test_invoice_price_includes_usage_components(self):
        invoice = invoices_models.Invoice.objects.get(customer=self.allocation.service_project_link.project.customer)
        self.assertEqual(invoice.price, 0)
        marketplace_models.ComponentUsage.objects.create(
            resource=self.resource,
            component=self.resource.plan.components.first().component,
            usage=1,
            date=datetime.date.today(),
            billing_period=month_start(datetime.date.today()),
            plan_period=self.plan_period
        )
        invoice.refresh_from_db()
        self.assertEqual(invoice.price, 3)


class ComponentQuotaTest(BaseTest):
    def test_create_component_quota(self):
        self.allocation.cpu_usage = 1
        self.allocation.gpu_usage = 10
        self.allocation.ram_usage = 100
        self.allocation.save()

        for component in manager.get_components(PLUGIN_NAME):
            self.assertTrue(marketplace_models.ComponentQuota.objects
                            .filter(resource=self.resource, component__type=component.type).exists())
            quota = marketplace_models.ComponentQuota.objects\
                .get(resource=self.resource, component__type=component.type)
            self.assertEqual(quota.limit, getattr(self.allocation, component.type + '_limit'))
            self.assertEqual(quota.usage, getattr(self.allocation, component.type + '_usage'))
