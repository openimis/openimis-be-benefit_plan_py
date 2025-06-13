import logging
from django.db import transaction

from core.services import BaseService
from core.signals import register_service_signal
from benefit_plan.models import (
    BenefitPlan,
    Project
)

from benefit_plan.validation import (
    BenefitPlanValidation,
    ProjectValidation,
)
from tasks_management.services import (
    UpdateCheckerLogicServiceMixin,
    CheckerLogicServiceMixin,
    crud_business_data_builder
)
from core.services.utils import (
    output_exception,
    model_representation,
    output_result_success
)


logger = logging.getLogger(__name__)


class BenefitPlanService(BaseService, UpdateCheckerLogicServiceMixin):
    OBJECT_TYPE = BenefitPlan

    def __init__(self, user, validation_class=BenefitPlanValidation):
        super().__init__(user, validation_class)

    @register_service_signal('benefit_plan_service.create')
    def create(self, obj_data):
        return super().create(obj_data)

    @register_service_signal('benefit_plan_service.update')
    def update(self, obj_data):
        return super().update(obj_data)

    @register_service_signal('benefit_plan_service.delete')
    def delete(self, obj_data):
        obj_data = {k: v for k, v in obj_data.items() if k != 'user'}
        return super().delete(obj_data)

    @register_service_signal('benefit_plan_service.close')
    def close_benefit_plan(self, obj_data):
        from tasks_management.models import Task
        from tasks_management.apps import TasksManagementConfig
        from tasks_management.services import _get_std_task_data_payload, TaskService
        from benefit_plan.apps import BenefitPlanConfig
        benefit_plan = BenefitPlan.objects.filter(id=obj_data.get('id')).first()
        data = {'benefit_plan_id': benefit_plan.id}
        TaskService(self.user).create({
            'source': 'BenefitPlanService',
            'entity': benefit_plan,
            'status': Task.Status.RECEIVED,
            'executor_action_event': TasksManagementConfig.default_executor_event,
            'business_event': BenefitPlanConfig.benefit_plan_suspend,
            'data': _get_std_task_data_payload(data)
        })


class ProjectService(BaseService):
    OBJECT_TYPE = Project

    def __init__(self, user, validation_class=ProjectValidation):
        super().__init__(user, validation_class)

    @register_service_signal("project_service.create")
    def create(self, obj_data):
        return super().create(obj_data)

    @register_service_signal("project_service.update")
    def update(self, obj_data):
        return super().update(obj_data)

    @register_service_signal("project_service.delete")
    def delete(self, obj_data):
        return super().delete(obj_data)

    @register_service_signal('project_service.undo_delete')
    def undo_delete(self, obj_data):
        try:
            with transaction.atomic():
                self.validation_class.validate_undo_delete(obj_data)
                obj_ = self.OBJECT_TYPE.objects.filter(id=obj_data['id']).first()
                obj_.is_deleted = False
                obj_.save(user=self.user.user)
                return {
                    "success": True,
                    "message": "Ok",
                    "detail": "Undo Delete",
                }
        except Exception as exc:
            return output_exception(
                model_name=self.OBJECT_TYPE.__name__, method="undo_delete", exception=exc
            )
