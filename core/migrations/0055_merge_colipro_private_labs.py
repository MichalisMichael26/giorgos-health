"""Merge the independent Colipro and private lab migrations.

Both migrations branch from 0053 and may already have been applied in
different environments. This dependency-only merge retains both histories,
does not rerun a completed migration, and never removes clinical records.
"""
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0054_deactivate_colipro"),
        ("core", "0054_import_private_20261027_labs"),
    ]

    operations = []
