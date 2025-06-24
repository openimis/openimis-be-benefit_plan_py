import copy

from django.test import TestCase

from benefit_plan.models import BenefitPlan
from benefit_plan.services import BenefitPlanService
from benefit_plan.tests.data import (
    service_add_payload,
    service_add_payload_no_ext,
    service_update_payload, service_add_payload_same_code,
    service_add_payload_same_name,
    service_add_payload_invalid_schema
)
from core.test_helpers import LogInHelper


class BenefitPlanServiceTest(TestCase):
    user = None
    service = None
    query_all = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = LogInHelper().get_or_create_user_api()
        cls.service = BenefitPlanService(cls.user)
        cls.query_all = BenefitPlan.objects.filter(is_deleted=False)

    def test_add_benefit_plan(self):
        result = self.service.create(service_add_payload)
        self.assertTrue(result.get('success', False), result.get('detail', "No details provided"))
        uuid = result.get('data', {}).get('uuid', None)
        query = self.query_all.filter(uuid=uuid)
        self.assertEqual(query.count(), 1)

    def test_add_benefit_plan_no_ext(self):
        result = self.service.create(service_add_payload_no_ext)
        self.assertTrue(result.get('success', False), result.get('detail', "No details provided"))
        uuid = result.get('data', {}).get('uuid')
        query = self.query_all.filter(uuid=uuid)
        self.assertEqual(query.count(), 1)

    def test_update_benefit_plan(self):
        result = self.service.create(service_add_payload)
        self.assertTrue(result.get('success', False), result.get('detail', "No details provided"))
        uuid = result.get('data', {}).get('uuid')
        update_payload = copy.deepcopy(service_update_payload)
        update_payload['id'] = uuid
        result = self.service.update(update_payload)
        self.assertTrue(result.get('success', False), result.get('detail', "No details provided"))
        query = self.query_all.filter(uuid=uuid)
        self.assertEqual(query.count(), 1)
        self.assertEqual(query.first().name, update_payload.get('name'))

    def test_delete_benefit_plan(self):
        result = self.service.create(service_add_payload)
        self.assertTrue(result.get('success', False), result.get('detail', "No details provided"))
        uuid = result.get('data', {}).get('uuid')
        delete_payload = {'id': uuid}
        result = self.service.delete(delete_payload)
        self.assertTrue(result.get('success', False), result.get('detail', "No details provided"))
        query = self.query_all.filter(uuid=uuid)
        self.assertEqual(query.count(), 0)

    def test_add_not_unique_code_benefit_plan(self):
        first_bf = self.service.create(service_add_payload)
        self.assertTrue(first_bf.get('success', False), first_bf.get('detail', "No details provided"))
        uuid = first_bf.get('data', {}).get('uuid', None)
        query = self.query_all.filter(uuid=uuid)
        self.assertEqual(query.count(), 1)
        second_bf = self.service.create(service_add_payload_same_code)
        self.assertFalse(second_bf.get('success', True))
        code = first_bf['data']['code']
        code_query = self.query_all.filter(code=code)
        self.assertEqual(code_query.count(), 1)

    def test_add_not_unique_name_benefit_plan(self):
        first_bf = self.service.create(service_add_payload)
        self.assertTrue(first_bf.get('success', False), first_bf.get('detail', "No details provided"))
        uuid = first_bf.get('data', {}).get('uuid', None)
        query = self.query_all.filter(uuid=uuid)
        self.assertEqual(query.count(), 1)
        second_bf = self.service.create(service_add_payload_same_name)
        self.assertFalse(second_bf.get('success', True))
        name = first_bf['data']['name']
        name_query = self.query_all.filter(name=name)
        self.assertEqual(name_query.count(), 1)

    def test_add_invalid_schema_benefit_plan(self):
        result = self.service.create(service_add_payload_invalid_schema)
        self.assertFalse(result.get('success', True))
