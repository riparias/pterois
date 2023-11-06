"""Custom script to import the river basins areas (Wallonia) for the LIFE RIPARIAS project.

The usual load_area.py script cannot be used because the specifities of the data make it unsuitable for the usual
LayerMapping helper.

See task description at: https://github.com/riparias/early-alert-webapp/issues/10
"""

import os

from django.contrib.gis.gdal import DataSource, SpatialReference, CoordTransform
from django.core.management import BaseCommand

from dashboard.management.commands.helpers import get_multipolygon_from_feature
from dashboard.models import Area, DATA_SRID

THIS_FILE_DIR = os.path.dirname(__file__)
SOURCE_DATA_STRID = SpatialReference("EPSG:31370")

ct = CoordTransform(SOURCE_DATA_STRID, SpatialReference(f"EPSG:{DATA_SRID}"))

SOURCE_DATA: dict[str, dict] = {
    "Basins": {
        "path": f"{THIS_FILE_DIR}/../../../source_data/public_areas/wallonia_river_basins/river_basins_wallonia.gpkg",
        "name_field": "river_basin",
        "tags": ["Wallonia", "river basin"],
    },
}


class Command(BaseCommand):
    help = "Import river areas from Wallonia in the database."

    def handle(self, *args, **options) -> None:
        self.stdout.write("Importing Flemish river areas")
        for layer_name, layer_config in SOURCE_DATA.items():
            self.stdout.write(f"Importing layer {layer_name}")

            ds = DataSource(layer_config["path"])
            layer = ds[0]
            self.stdout.write(f"Found {layer.num_feat} features")  # type: ignore
            for feature in layer:
                area_name = feature[layer_config["name_field"]]  # type: ignore
                tags = layer_config["tags"].copy()
                try:
                    tags.append(feature[layer_config["dynamic_tag_field"]].value)  # type: ignore
                except KeyError:
                    pass
                self.stdout.write(f"Creating area {area_name}, with tags {tags}")

                multipolygon = get_multipolygon_from_feature(feature)
                reprojected_multipolygon = multipolygon.transform(ct, clone=True)

                area = Area.objects.create(mpoly=reprojected_multipolygon.wkt, name=area_name)  # type: ignore
                area.tags.add(*tags)
