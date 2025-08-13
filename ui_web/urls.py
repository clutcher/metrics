from django.conf import settings
from django.urls import path

from .utils.url_utils import django_normalized_base_url
from .views.current_tasks_view import CurrentTasksView, CurrentTasksChildrenView
from .views.dev_velocity_view import DevVelocityView
from .views.homepage_view import HomepageView
from .views.task_forecast_view import TaskForecastView
from .views.team_velocity_view import TeamVelocityView

app_name = 'ui_web'

_base_prefix = django_normalized_base_url(settings.METRICS_BASE_URL)

urlpatterns = [
    # Homepage
    path(_base_prefix, HomepageView.as_view(), name='homepage'),

    # Full page views
    path(_base_prefix + 'current-tasks/', CurrentTasksView.as_view(), name='current_tasks'),
    path(_base_prefix + 'current-tasks/<str:team_id>/', CurrentTasksView.as_view(), name='current_tasks_with_team'),
    path(_base_prefix + 'team-velocity/', TeamVelocityView.as_view(), name='team_velocity'),
    path(_base_prefix + 'team-velocity/<str:team_id>/', TeamVelocityView.as_view(), name='team_velocity_with_team'),
    path(_base_prefix + 'dev-velocity/', DevVelocityView.as_view(), name='dev_velocity'),
    path(_base_prefix + 'dev-velocity/<str:team_id>/', DevVelocityView.as_view(), name='dev_velocity_with_team'),
    path(_base_prefix + 'task-forecast/', TaskForecastView.as_view(), name='task_forecast'),

    # Partials for HTMX
    path(_base_prefix + 'partials/tasks/', CurrentTasksView.as_view(), name='partials_tasks'),
    path(_base_prefix + 'partials/tasks/<str:task_id>/children/', CurrentTasksChildrenView.as_view(),
         name='partials_task_children'),
]
