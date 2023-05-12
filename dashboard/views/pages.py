"""Views that return HTML pages"""
import tempfile

from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.gis.gdal import DataSource
from django.core.exceptions import BadRequest
from django.http import HttpResponseForbidden, HttpRequest, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.translation import gettext as _

from dashboard.forms import (
    SignUpForm,
    EditProfileForm,
    NewObservationCommentForm,
    AlertForm,
    NewCustomAreaForm,
)
from dashboard.models import DataImport, Observation, Alert, Area
from dashboard.views.helpers import (
    AuthenticatedHttpRequest,
    extract_dict_request,
    extract_str_request,
)


def index_page(request: HttpRequest) -> HttpResponse:
    try:
        filters_from_url = extract_dict_request(request, "filters")
    except ValueError:
        #  Common case of malformed input by bots, see https://github.com/riparias/early-alert-webapp/issues/106
        raise BadRequest("Invalid filter parameters.")

    if filters_from_url is not None:
        filters_for_template = filters_from_url
    else:
        filters_for_template = {}

    return render(
        request,
        "dashboard/index.html",
        {"initialFilters": filters_for_template},
    )


def about_site_page(request: HttpRequest) -> HttpResponse:
    return render(request, "dashboard/about_site.html")


def about_data_page(request: HttpRequest) -> HttpResponse:
    data_imports = DataImport.objects.all().order_by("-start")
    return render(request, "dashboard/about_data.html", {"data_imports": data_imports})


def news_page(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        request.user.mark_news_as_visited_now()

    return render(request, "dashboard/news.html")


def observation_details_page(request: HttpRequest, stable_id: str) -> HttpResponse:
    observation = get_object_or_404(Observation, stable_id=stable_id)
    observation.mark_as_seen_by(request.user)
    first_seen = observation.first_seen_at(request.user)
    origin_url = extract_str_request(request, "origin")

    if request.method == "POST":
        if (
            not request.user.is_authenticated
        ):  # Only authenticated users can post comments
            return HttpResponseForbidden()

        form = NewObservationCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.observation = observation
            comment.save()
            form = NewObservationCommentForm()  # Show a new empty one to the user
    else:
        form = NewObservationCommentForm()

    return render(
        request,
        "dashboard/observation_details.html",
        {
            "observation": observation,
            "new_comment_form": form,
            "first_seen_by_user_timestamp": first_seen,
            "origin_url": origin_url,
        },
    )


@login_required
def alert_details_page(
    request: AuthenticatedHttpRequest, alert_id: int
) -> HttpResponse:
    alert = get_object_or_404(Alert, id=alert_id)

    if alert.user == request.user:
        return render(request, "dashboard/alert_details.html", {"alert": alert})
    else:
        return HttpResponseForbidden()


@login_required
def alert_create_page(request: AuthenticatedHttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = AlertForm(request.user, request.POST)
        if form.is_valid():
            alert = form.save(commit=False)
            alert.user = request.user
            alert.save()
            form.save_m2m()
            return redirect(alert)
    else:
        form = AlertForm(for_user=request.user)

    return render(request, "dashboard/alert_create.html", {"form": form})


@login_required
def alert_edit_page(request: AuthenticatedHttpRequest, alert_id: int) -> HttpResponse:
    alert = get_object_or_404(Alert, id=alert_id)

    if alert.user == request.user:
        if request.method == "POST":
            form = AlertForm(request.user, request.POST, instance=alert)
            if form.is_valid():
                alert = form.save(commit=False)
                alert.user = request.user
                alert.save()
                form.save_m2m()
                return redirect(alert)
        else:
            form = AlertForm(for_user=request.user, instance=alert)
        return render(request, "dashboard/alert_edit.html", {"form": form})
    else:
        return HttpResponseForbidden()


def user_signup_page(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get("username")
            raw_password = form.cleaned_data.get("password1")
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect("dashboard:pages:index")
    else:
        form = SignUpForm()
    return render(request, "dashboard/user_signup.html", {"form": form})


@login_required
def user_profile_page(request: AuthenticatedHttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = EditProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _("Your profile was successfully updated."))
            return redirect("dashboard:pages:index")
    else:
        form = EditProfileForm(instance=request.user)
    return render(request, "dashboard/user_profile.html", {"form": form})


@login_required
def user_alerts_page(request: AuthenticatedHttpRequest) -> HttpResponse:
    alerts = Alert.objects.filter(user=request.user).order_by("id")
    return render(request, "dashboard/user_alerts.html", {"alerts": alerts})


# TODO: detailed exceptionsinstead of returning None
# Testing: no 1 layer, no 1 feature in layer, no multipolygon or polygon
# no SRS. SRS: provided: make sure reprojection is done
# Document / test other file formats
# Currently works with GPKG in 3857 of type mulipolygon
def uploaded_shapefile_to_multipolygon(
    data_path: str,
):
    ds = DataSource(data_path)
    if ds.layer_count != 1:
        return None
    layer = ds[0]

    if layer.num_feat != 1:
        return None

    if layer.srs is None:
        return None

    if layer.geom_type.name == "MultiPolygon":
        feature = list(layer)[0]
        return feature.geom.wkt
    # elif layer.geom_type.name == "Polygon":
    #     feature = list(layer)[0]
    #     return MultiPolygon(feature.geom)
    else:
        return None


@login_required
def user_areas_page(request: AuthenticatedHttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = NewCustomAreaForm(request.POST, request.FILES)

        # UploadedFile may be in memory (if it's small), so it lacks a proper path, need to hack with a temporary file
        with tempfile.NamedTemporaryFile(
            suffix=request.FILES["data_file"].name
        ) as temp:
            temp.write(request.FILES["data_file"].read())
            mp = uploaded_shapefile_to_multipolygon(temp.name)

            if form.is_valid() and mp is not None:
                Area.objects.create(
                    mpoly=mp, owner=request.user, name=form.cleaned_data["name"]
                )
    else:
        form = NewCustomAreaForm()

    return render(
        request,
        "dashboard/user_areas.html",
        {
            "user_areas_ids": [a.pk for a in Area.objects.filter(owner=request.user)],
            "new_custom_area_form": form,
        },
    )
