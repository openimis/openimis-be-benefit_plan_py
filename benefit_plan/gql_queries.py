import graphene
from django.contrib.auth.models import AnonymousUser
from graphene import ObjectType
from graphene_django import DjangoObjectType
import django_filters

from contribution_plan.models import PaymentPlan
from core import prefix_filterset, ExtendedConnection
from benefit_plan.apps import BenefitPlanConfig
from benefit_plan.models import (
    BenefitPlan,
    Activity,
    Project
)


def _have_permissions(user, permission):
    if isinstance(user, AnonymousUser):
        return False
    if not user.id:
        return False
    return user.has_perms(permission)


class JsonExtMixin:
    def resolve_json_ext(self, info):
        if _have_permissions(info.context.user, BenefitPlanConfig.gql_schema_search_perms):
            return self.json_ext
        return None


class BenefitPlanGQLType(DjangoObjectType, JsonExtMixin):
    uuid = graphene.String(source='uuid')
    has_payment_plans = graphene.Boolean()

    class Meta:
        model = BenefitPlan
        interfaces = (graphene.relay.Node,)
        filter_fields = {
            "id": ["exact"],
            "code": ["exact", "iexact", "startswith", "istartswith", "contains", "icontains"],
            "name": ["exact", "iexact", "startswith", "istartswith", "contains", "icontains"],
            "date_valid_from": ["exact", "lt", "lte", "gt", "gte"],
            "date_valid_to": ["exact", "lt", "lte", "gt", "gte"],
            "max_beneficiaries": ["exact", "lt", "lte", "gt", "gte"],
            "institution": ["exact", "iexact", "startswith", "istartswith", "contains", "icontains"],
            "type": ["exact", "iexact", "startswith", "istartswith", "contains", "icontains"],

            "date_created": ["exact", "lt", "lte", "gt", "gte"],
            "date_updated": ["exact", "lt", "lte", "gt", "gte"],
            "is_deleted": ["exact"],
            "version": ["exact"],
            "description": ["exact", "iexact", "startswith", "istartswith", "contains", "icontains"],
        }
        connection_class = ExtendedConnection

    def resolve_beneficiary_data_schema(self, info):
        if _have_permissions(info.context.user, BenefitPlanConfig.gql_schema_search_perms):
            return self.beneficiary_data_schema
        return None

    def resolve_has_payment_plans(self, info):
        return PaymentPlan.objects.filter(benefit_plan_id=self.id).exists()


class BenefitPlanSchemaFieldsGQLType(ObjectType):
    schema_fields = graphene.List(graphene.String)

    def resolve_schema_fields(self, info, **kwargs):
        schemas = self.values_list("beneficiary_data_schema__properties", flat=True)
        field_list = set(
            f'json_ext__{field}'
            for schema in schemas  # Iterate over each schema
            if schema  # Ensure the schema is not None or empty
            for field in schema  # Iterate over fields in the schema
        )
        return field_list


class BenefitPlanHistoryGQLType(DjangoObjectType, JsonExtMixin):
    uuid = graphene.String(source='uuid')
    has_payment_plans = graphene.Boolean()

    def resolve_user_updated(self, info):
        return self.user_updated

    class Meta:
        model = BenefitPlan.history.model
        interfaces = (graphene.relay.Node,)
        filter_fields = {
            "id": ["exact"],
            "code": ["exact", "iexact", "startswith", "istartswith", "contains", "icontains"],
            "name": ["exact", "iexact", "startswith", "istartswith", "contains", "icontains"],
            "date_valid_from": ["exact", "lt", "lte", "gt", "gte"],
            "date_valid_to": ["exact", "lt", "lte", "gt", "gte"],
            "max_beneficiaries": ["exact", "lt", "lte", "gt", "gte"],
            "institution": ["exact", "iexact", "startswith", "istartswith", "contains", "icontains"],

            "date_created": ["exact", "lt", "lte", "gt", "gte"],
            "date_updated": ["exact", "lt", "lte", "gt", "gte"],
            "is_deleted": ["exact"],
            "version": ["exact"],
            "description": ["exact", "iexact", "startswith", "istartswith", "contains", "icontains"],
        }
        connection_class = ExtendedConnection

    def resolve_beneficiary_data_schema(self, info):
        if _have_permissions(info.context.user, BenefitPlanConfig.gql_schema_search_perms):
            return self.beneficiary_data_schema
        return None

    def resolve_has_payment_plans(self, info):
        return PaymentPlan.objects.filter(benefit_plan_id=self.id).exists()


class ActivityFilter(django_filters.FilterSet):
    class Meta:
        model = Activity
        fields = {
            "id": ["exact"],
            "name": ["exact", "iexact", "startswith", "istartswith", "contains", "icontains"],
            "date_created": ["exact", "lt", "lte", "gt", "gte"],
            "date_updated": ["exact", "lt", "lte", "gt", "gte"],
            "is_deleted": ["exact"],
            "version": ["exact"],
        }


class ActivityGQLType(DjangoObjectType, JsonExtMixin):
    uuid = graphene.String(source='uuid')

    class Meta:
        model = Activity
        interfaces = (graphene.relay.Node,)
        filterset_class = ActivityFilter
        connection_class = ExtendedConnection


class ProjectFilter(django_filters.FilterSet):
    class Meta:
        model = Project
        fields = {
            "id": ["exact"],
            "name": ["exact", "iexact", "startswith", "istartswith", "contains", "icontains"],
            'status': ['exact', 'icontains'],
            'benefit_plan__id': ['exact'],
            'activity__id': ['exact'],
            'location__id': ['exact'],
            'target_beneficiaries': ['exact', 'gte', 'lte'],
            'working_days': ['exact', 'gte', 'lte'],
            "date_created": ["exact", "lt", "lte", "gt", "gte"],
            "date_updated": ["exact", "lt", "lte", "gt", "gte"],
            "is_deleted": ["exact"],
            "version": ["exact"],
        }

class ProjectGQLType(DjangoObjectType, JsonExtMixin):
    uuid = graphene.String(source='uuid')

    class Meta:
        model = Project
        interfaces = (graphene.relay.Node,)
        filterset_class = ProjectFilter
        connection_class = ExtendedConnection
