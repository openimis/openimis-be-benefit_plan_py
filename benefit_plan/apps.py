from django.apps import AppConfig

from core.custom_filters import CustomFilterRegistryPoint


DEFAULT_CONFIG = {
    "gql_benefit_plan_search_perms": ["160001"],
    "gql_benefit_plan_create_perms": ["160002"],
    "gql_benefit_plan_update_perms": ["160003"],
    "gql_benefit_plan_delete_perms": ["160004"],
    "gql_benefit_plan_close_perms": ["160005"],
    "gql_schema_search_perms": ["171001"],
    "gql_schema_create_perms": ["171002"],
    "gql_schema_update_perms": ["171003"],
    "gql_schema_delete_perms": ["171004"],
    "gql_activity_search_perms": ["208001"],
    "gql_project_search_perms": ["209001"],
    "gql_project_create_perms": ["209002"],
    "gql_project_update_perms": ["209003"],
    "gql_project_delete_perms": ["209004"],

    "gql_check_benefit_plan_update": True,
    "benefit_plan_suspend": "benefit_plan.benefit_plan_suspend",
}


class BenefitPlanConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'benefit_plan'
    verbose_name = 'Benefit Plan'

    gql_benefit_plan_search_perms = None
    gql_benefit_plan_create_perms = None
    gql_benefit_plan_update_perms = None
    gql_benefit_plan_delete_perms = None
    gql_benefit_plan_close_perms = None
    gql_schema_search_perms = None
    gql_schema_create_perms = None
    gql_schema_update_perms = None
    gql_schema_delete_perms = None
    gql_activity_search_perms = None
    gql_project_search_perms = None
    gql_project_create_perms = None
    gql_project_update_perms = None
    gql_project_delete_perms = None

    gql_check_benefit_plan_update = None
    benefit_plan_suspend = None

    def ready(self):
        from core.models import ModuleConfiguration

        cfg = ModuleConfiguration.get_or_default(self.name, DEFAULT_CONFIG)
        self.__load_config(cfg)
        self.__register_masking_class()


    @classmethod
    def __load_config(cls, cfg):
        """
        Load all config fields that match current AppConfig class fields, all custom fields have to be loaded separately
        """
        for field in cfg:
            if hasattr(BenefitPlanConfig, field):
                setattr(BenefitPlanConfig, field, cfg[field])

        from benefit_plan.custom_filters import BenefitPlanCustomFilterWizard
        CustomFilterRegistryPoint.register_custom_filters(
            module_name=cls.name,
            custom_filter_class_list=[BenefitPlanCustomFilterWizard]
        )
