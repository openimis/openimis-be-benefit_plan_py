import graphene

from django.contrib.auth.models import AnonymousUser
from django.db.models import (
    Q,
    Case,
    When,
    BooleanField,
    Value
)
from django.core.exceptions import PermissionDenied

from django.utils.translation import gettext as _
from core.gql_queries import ValidationMessageGQLType
from core.schema import OrderedDjangoFilterConnectionField
from core.services import wait_for_mutation
from core.utils import (
    append_validity_filter,
    validate_json_schema
)
from benefit_plan.apps import BenefitPlanConfig
from benefit_plan.gql_mutations import (
    CreateBenefitPlanMutation,
    UpdateBenefitPlanMutation,
    DeleteBenefitPlanMutation,
    CloseBenefitPlanMutation,
    CreateProjectMutation,
    UpdateProjectMutation,
    DeleteProjectMutation,
    UndoDeleteProjectMutation,
)
from benefit_plan.gql_queries import (
    BenefitPlanGQLType,
    BenefitPlanSchemaFieldsGQLType,
    BenefitPlanHistoryGQLType,
    ActivityGQLType, ProjectGQLType,
)
from benefit_plan.models import (
    BenefitPlan,
    Activity,
    Project,
)
from benefit_plan.validations import (
    validate_bf_unique_code,
    validate_bf_unique_name,
    validate_project_unique_name,
)
import graphene_django_optimizer as gql_optimizer
from location.apps import LocationConfig
from location.models import (
    extend_allowed_locations,
    Location
)


class BfTypeEnum(graphene.Enum):
    INDIVIDUAL = BenefitPlan.BenefitPlanType.INDIVIDUAL_TYPE
    GROUP = BenefitPlan.BenefitPlanType.GROUP_TYPE


class Query(graphene.ObjectType):
    benefit_plan = OrderedDjangoFilterConnectionField(
        BenefitPlanGQLType,
        orderBy=graphene.List(of_type=graphene.String),
        dateValidFrom__Gte=graphene.DateTime(),
        dateValidTo__Lte=graphene.DateTime(),
        applyDefaultValidityFilter=graphene.Boolean(),
        client_mutation_id=graphene.String(),
        individual_id=graphene.String(),
        group_id=graphene.String(),
        beneficiary_status=graphene.String(),
        search=graphene.String(),
        sort_alphabetically=graphene.Boolean(),
    )

    bf_code_validity = graphene.Field(
        ValidationMessageGQLType,
        bf_code=graphene.String(required=True),
        description="Checks that the specified Benefit Plan code is valid"
    )
    bf_name_validity = graphene.Field(
        ValidationMessageGQLType,
        bf_name=graphene.String(required=True),
        description="Checks that the specified Benefit Plan name is valid"
    )
    bf_schema_validity = graphene.Field(
        ValidationMessageGQLType,
        bf_schema=graphene.String(required=True),
        description="Checks that the specified Benefit Plan schema is valid"
    )
    benefit_plan_schema_field = graphene.Field(
        BenefitPlanSchemaFieldsGQLType,
        bf_type=graphene.Argument(BfTypeEnum),
        description="Endpoint responsible for getting all fields from all BF schemas"
    )
    benefit_plan_history = OrderedDjangoFilterConnectionField(
        BenefitPlanHistoryGQLType,
        orderBy=graphene.List(of_type=graphene.String),
        dateValidFrom__Gte=graphene.DateTime(),
        dateValidTo__Lte=graphene.DateTime(),
        applyDefaultValidityFilter=graphene.Boolean(),
        client_mutation_id=graphene.String(),
        individual_id=graphene.String(),
        group_id=graphene.String(),
        beneficiary_status=graphene.String(),
        search=graphene.String(),
        sort_alphabetically=graphene.Boolean(),
    )

    activity = OrderedDjangoFilterConnectionField(
        ActivityGQLType,
        orderBy=graphene.List(of_type=graphene.String),
        applyDefaultValidityFilter=graphene.Boolean(),
        client_mutation_id=graphene.String(),
    )

    project = OrderedDjangoFilterConnectionField(
        ProjectGQLType,
        orderBy=graphene.List(of_type=graphene.String),
        applyDefaultValidityFilter=graphene.Boolean(),
        client_mutation_id=graphene.String(),
        parent_location=graphene.String(),
        parent_location_level=graphene.Int(),
    )

    project_name_validity = graphene.Field(
        ValidationMessageGQLType,
        project_name=graphene.String(required=True),
        benefit_plan_id=graphene.String(required=True),
        description="Checks that the specified Project name is valid"
    )

    def resolve_bf_code_validity(self, info, **kwargs):
        if not info.context.user.has_perms(BenefitPlanConfig.gql_benefit_plan_search_perms):
            raise PermissionDenied(_("unauthorized"))
        errors = validate_bf_unique_code(kwargs['bf_code'])
        if errors:
            return ValidationMessageGQLType(False, error_message=errors[0]['message'])
        else:
            return ValidationMessageGQLType(True)

    def resolve_bf_name_validity(self, info, **kwargs):
        if not info.context.user.has_perms(BenefitPlanConfig.gql_benefit_plan_search_perms):
            raise PermissionDenied(_("unauthorized"))
        errors = validate_bf_unique_name(kwargs['bf_name'])
        if errors:
            return ValidationMessageGQLType(False, error_message=errors[0]['message'])
        else:
            return ValidationMessageGQLType(True)

    def resolve_bf_schema_validity(self, info, **kwargs):
        if not info.context.user.has_perms(BenefitPlanConfig.gql_benefit_plan_search_perms):
            raise PermissionDenied(_("unauthorized"))
        errors = validate_json_schema(kwargs['bf_schema'])
        if errors:
            return ValidationMessageGQLType(False, error_message=errors[0]['message'])
        else:
            return ValidationMessageGQLType(True)

    def resolve_benefit_plan(self, info, **kwargs):
        filters = append_validity_filter(**kwargs)

        search = kwargs.get("search", None)
        if search:
            search_terms = search.split(' ')
            search_queries = Q()
            for term in search_terms:
                search_queries |= Q(code__icontains=term) | Q(name__icontains=term)
            filters.append(search_queries)

        client_mutation_id = kwargs.get("client_mutation_id", None)
        if client_mutation_id:
            wait_for_mutation(client_mutation_id)
            filters.append(Q(mutations__mutation__client_mutation_id=client_mutation_id))

        individual_id = kwargs.get("individual_id", None)
        if individual_id:
            filters.append(Q(
                Q(beneficiary__individual__id=individual_id) |
                Q(groupbeneficiary__group__groupindividuals__individual__id=individual_id)
            ))

        group_id = kwargs.get("group_id", None)
        if group_id:
            filters.append(Q(groupbeneficiary__group__id=group_id))

        beneficiary_status = kwargs.get("beneficiary_status", None)
        if beneficiary_status:
            filters.append(Q(beneficiary__status=beneficiary_status) | Q(groupbeneficiary__status=beneficiary_status))

        Query._check_permissions(
            info.context.user,
            BenefitPlanConfig.gql_benefit_plan_search_perms
        )

        query = BenefitPlan.objects.filter(*filters)

        sort_alphabetically = kwargs.get("sort_alphabetically", None)
        if sort_alphabetically:
            query = query.order_by('code')
        return gql_optimizer.query(query, info)

    def resolve_benefit_plan_schema_field(self, info, **kwargs):
        filters = append_validity_filter(**kwargs)

        Query._check_permissions(
            info.context.user,
            BenefitPlanConfig.gql_schema_search_perms
        )

        bf_type = kwargs.get("bf_type", None)
        if bf_type:
            filters.append(Q(type=bf_type))

        query = BenefitPlan.objects.filter(*filters)
        return gql_optimizer.query(query, info)

    @staticmethod
    def _check_permissions(user, permission):
        if type(user) is AnonymousUser or not user.id or not user.has_perms(permission):
            raise PermissionError("Unauthorized")

    def resolve_benefit_plan_history(self, info, **kwargs):
        filters = append_validity_filter(**kwargs)

        search = kwargs.get("search", None)
        if search:
            search_terms = search.split(' ')
            search_queries = Q()
            for term in search_terms:
                search_queries |= Q(code__icontains=term) | Q(name__icontains=term)
            filters.append(search_queries)

        client_mutation_id = kwargs.get("client_mutation_id", None)
        if client_mutation_id:
            wait_for_mutation(client_mutation_id)
            filters.append(Q(mutations__mutation__client_mutation_id=client_mutation_id))

        individual_id = kwargs.get("individual_id", None)
        if individual_id:
            filters.append(Q(beneficiary__individual__id=individual_id))

        group_id = kwargs.get("group_id", None)
        if group_id:
            filters.append(Q(groupbeneficiary__group__id=group_id))

        beneficiary_status = kwargs.get("beneficiary_status", None)
        if beneficiary_status:
            filters.append(Q(beneficiary__status=beneficiary_status) | Q(groupbeneficiary__status=beneficiary_status))

        Query._check_permissions(
            info.context.user,
            BenefitPlanConfig.gql_benefit_plan_search_perms
        )

        query = BenefitPlan.history.filter(*filters)

        sort_alphabetically = kwargs.get("sort_alphabetically", None)
        if sort_alphabetically:
            query = query.order_by('code')
        return gql_optimizer.query(query, info)

    @staticmethod
    def _get_location_filters(parent_location, parent_location_level, prefix=""):
        query_key = "uuid"
        for i in range(len(LocationConfig.location_types) - parent_location_level - 1):
            query_key = "parent__" + query_key
        query_key = prefix + "location__" + query_key
        return Q(**{query_key: parent_location})

    def resolve_activity(self, info, **kwargs):
        Query._check_permissions(
            info.context.user,
            BenefitPlanConfig.gql_activity_search_perms
        )

        filters = append_validity_filter(**kwargs)
        query = Activity.objects.filter(*filters)
        return gql_optimizer.query(query, info)

    def resolve_project(self, info, **kwargs):
        Query._check_permissions(
            info.context.user,
            BenefitPlanConfig.gql_project_search_perms
        )

        filters = append_validity_filter(**kwargs)

        client_mutation_id = kwargs.get("client_mutation_id", None)
        if client_mutation_id:
            wait_for_mutation(client_mutation_id)
            filters.append(Q(mutations__mutation__client_mutation_id=client_mutation_id))

        parent_location = kwargs.get('parent_location')
        if parent_location is not None:
            location = Location.objects.get(uuid=parent_location)
            descendant_ids = extend_allowed_locations([location.pk])
            filters.append(Q(location__id__in=descendant_ids))

        query = Project.objects.filter(*filters)
        return gql_optimizer.query(query, info)

    def resolve_project_name_validity(self, info, **kwargs):
        if not info.context.user.has_perms(BenefitPlanConfig.gql_project_search_perms):
            raise PermissionDenied(_("unauthorized"))
        errors = validate_project_unique_name(kwargs['project_name'], kwargs['benefit_plan_id'])
        if errors:
            return ValidationMessageGQLType(False, error_message=errors[0]['message'])
        else:
            return ValidationMessageGQLType(True)


class Mutation(graphene.ObjectType):
    create_benefit_plan = CreateBenefitPlanMutation.Field()
    update_benefit_plan = UpdateBenefitPlanMutation.Field()
    delete_benefit_plan = DeleteBenefitPlanMutation.Field()
    close_benefit_plan = CloseBenefitPlanMutation.Field()

    create_project = CreateProjectMutation.Field()
    update_project = UpdateProjectMutation.Field()
    delete_project = DeleteProjectMutation.Field()
    undo_delete_project = UndoDeleteProjectMutation.Field()
