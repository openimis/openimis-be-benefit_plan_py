from django.db import models
from django.db.models import Func
from django.utils.translation import gettext as _

from core import models as core_models
from core.models import UUIDModel, ObjectMutation, MutationLog
from location.models import Location


class BenefitPlan(core_models.HistoryBusinessModel):
    class BenefitPlanType(models.TextChoices):
        INDIVIDUAL_TYPE = "INDIVIDUAL", _("INDIVIDUAL")
        GROUP_TYPE = "GROUP", _("GROUP")

    code = models.CharField(max_length=8, null=False)
    name = models.CharField(max_length=255, null=False)
    max_beneficiaries = models.SmallIntegerField(null=True, blank=True)
    ceiling_per_beneficiary = models.DecimalField(
        max_digits=18, decimal_places=2, blank=True, null=True,
    )
    institution = models.CharField(max_length=255, null=True, blank=True)
    beneficiary_data_schema = models.JSONField(null=True, blank=True)
    type = models.CharField(
        max_length=100, choices=BenefitPlanType.choices, default=BenefitPlanType.INDIVIDUAL_TYPE, null=False
    )
    description = models.CharField(max_length=1024, null=True, blank=True)

    def __str__(self):
        return f'Benefit Plan {self.code}'


class BenefitPlanMutation(UUIDModel, ObjectMutation):
    benefit_plan = models.ForeignKey(BenefitPlan, models.DO_NOTHING, related_name='mutations')
    mutation = models.ForeignKey(MutationLog, models.DO_NOTHING, related_name='benefit_plan')


class Activity(core_models.HistoryBusinessModel):
    name = models.CharField(max_length=255, null=False, unique=True)

    class Meta:
        verbose_name = "Activity"
        verbose_name_plural = "Activities"


class ProjectStatus(models.TextChoices):
    PREPARATION = "PREPARATION", _("PREPARATION")
    IN_PROGRESS = "IN_PROGRESS", _("IN PROGRESS")
    COMPLETED = "COMPLETED", _("COMPLETED")


class Project(core_models.HistoryBusinessModel):
    benefit_plan = models.ForeignKey(BenefitPlan, models.DO_NOTHING, null=False)
    name = models.CharField(max_length=255, null=False)
    status = models.CharField(
        max_length=100,
        choices=ProjectStatus.choices,
        default=ProjectStatus.PREPARATION,
        null=False
    )
    activity = models.ForeignKey(Activity, models.DO_NOTHING, null=False)
    location = models.ForeignKey(Location, models.DO_NOTHING, null=False)
    target_beneficiaries = models.SmallIntegerField(null=False)
    working_days = models.SmallIntegerField(null=False)


class JSONUpdate(Func):
    function = 'JSONB_SET'
    arity = 3
