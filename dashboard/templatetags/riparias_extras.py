import json
from typing import Any
from urllib.parse import urlencode

from django import template
from django.urls import reverse
from django.utils.safestring import mark_safe

from dashboard.models import DataImport

register = template.Library()


def _my_reverse(view_name, kwargs=None, query_kwargs=None):
    """
    Custom reverse to add a query string after the url
    Example usage:
    url = my_reverse('my_test_url', kwargs={'pk': object.id}, query_kwargs={'next': reverse('home')})
    """
    url = reverse(view_name, kwargs=kwargs)

    if query_kwargs:
        return f"{url}?{urlencode(query_kwargs)}"

    return url


def _build_dashboard_url_with_filter(k: str, v: Any) -> str:
    return _my_reverse(
        "dashboard:page-index",
        query_kwargs={"filters": {k: v}},
    )


def _build_mvt_url_template(url_pattern: str) -> str:
    return (
        reverse(url_pattern, kwargs={"zoom": 1, "x": 2, "y": 3})
        .replace("1", "{z}")
        .replace("2", "{x}")
        .replace("3", "{y}")
    )


@register.simple_tag
def dashboard_url_filtered_by_data_import(data_import: DataImport) -> str:
    return _build_dashboard_url_with_filter(
        k="initialDataImportIds", v=[data_import.pk]
    )


@register.simple_tag(takes_context=True)
def js_config_object(context):
    # When adding stuff here, don't forget to update the corresponding TypeScript interface in assets/ts/interfaces.ts
    conf = {
        "authenticatedUser": context.request.user.is_authenticated,
        "apiEndpoints": {
            "speciesListUrl": reverse("dashboard:api-species-list-json"),
            "datasetsListUrl": reverse("dashboard:api-datasets-list-json"),
            "areasListUrl": reverse("dashboard:api-areas-list-json"),
            "dataImportsListUrl": reverse("dashboard:api-dataimports-list-json"),
            "observationsCounterUrl": reverse(
                "dashboard:api-filtered-observations-counter"
            ),
            "observationsJsonUrl": reverse(
                "dashboard:api-filtered-observations-data-page"
            ),
            "tileServerAggregatedUrlTemplate": _build_mvt_url_template(
                "dashboard:api-mvt-tiles-hexagon-grid-aggregated"
            ),
            "tileServerUrlTemplate": _build_mvt_url_template("dashboard:api-mvt-tiles"),
            "observationDetailsUrlTemplate": reverse(
                "dashboard:page-observation-details", kwargs={"stable_id": 1}
            ).replace("1", "{stable_id}"),
            "areasUrlTemplate": reverse(
                "dashboard:api-area-geojson", kwargs={"id": 1}
            ).replace("1", "{id}"),
            "minMaxOccPerHexagonUrl": reverse("dashboard:api-mvt-min-max-per-hexagon"),
            "observationsHistogramDataUrl": reverse(
                "dashboard:api-filtered-observations-monthly-histogram"
            ),
            "alertAsFiltersUrl": reverse("dashboard:api-alert-as-filters-json"),
        },
    }
    if context.request.user.is_authenticated:
        conf["userId"] = context.request.user.pk

    return mark_safe(json.dumps(conf))


@register.filter
def gbif_download_url(value):
    return f"https://www.gbif.org/occurrence/download/{value}"


@register.filter
def gbif_occurrence_url(value):
    return f"https://www.gbif.org/occurrence/{value}"
