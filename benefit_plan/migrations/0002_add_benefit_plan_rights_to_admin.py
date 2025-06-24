from django.db import migrations
from core.utils import insert_role_right_for_system, remove_role_right_for_system

benefit_plan_rights = [160001, 160002, 160003, 160004]
imis_administrator_system = 64


def add_rights(apps, schema_editor):
    for right_id in benefit_plan_rights:
        insert_role_right_for_system(imis_administrator_system, right_id, apps)


def remove_rights(apps, schema_editor):
    for right_id in benefit_plan_rights:
        remove_role_right_for_system(imis_administrator_system, right_id, apps)

class Migration(migrations.Migration):
    dependencies = [
        ('benefit_plan', '0001_initial')
    ]

    operations = [
        migrations.RunPython(add_rights, remove_rights),
    ]
