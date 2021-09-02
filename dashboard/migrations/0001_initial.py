# Generated by Django 3.2.6 on 2021-08-27 12:42

import django.contrib.gis.db.models.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Species",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                ("gbif_taxon_key", models.IntegerField(unique=True)),
                (
                    "group",
                    models.CharField(
                        choices=[("PL", "Plants"), ("CR", "Crayfishes")], max_length=3
                    ),
                ),
                (
                    "category",
                    models.CharField(
                        choices=[
                            (
                                "W",
                                "Widespread and abundant species in the pilot river basins",
                            ),
                            (
                                "E",
                                "Emerging species with a very restricted range in the pilot river basins",
                            ),
                            ("SA", "Species still absent from the pilot river basins"),
                        ],
                        max_length=3,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Occurrence",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("gbif_id", models.CharField(max_length=100, unique=True)),
                (
                    "location",
                    django.contrib.gis.db.models.fields.PointField(
                        blank=True, null=True, srid=3857
                    ),
                ),
                ("date", models.DateField()),
                (
                    "species",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="dashboard.species",
                    ),
                ),
            ],
        ),
    ]
