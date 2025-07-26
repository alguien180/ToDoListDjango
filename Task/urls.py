from django.urls import path
from .views import (
    # NOTES
    NoteList, NoteDetail, NoteCreate, NoteUpdate, NoteDelete,
    # TASKS
    TaskListView, TaskCreateView, TaskEditView, TaskDeleteView, TaskToggleView,
    TaskICSExportView, TaskRescheduleView, TaskToggleSeriesView, TaskDeleteAPIView,DashboardView
)

urlpatterns = [
    # ─────────── Notes ───────────
    path("notes/",                     NoteList.as_view(),   name="notes"),
    path("notes/add/",                 NoteCreate.as_view(), name="note-create"),
    path("notes/<int:pk>/",            NoteDetail.as_view(), name="note-detail"),
    path("notes/<int:pk>/edit/",       NoteUpdate.as_view(), name="note-update"),
    path("notes/<int:pk>/delete/",     NoteDelete.as_view(), name="note-delete"),

    # ─────────── Tasks ───────────
    path("tasks/",                     TaskListView.as_view(),          name="task_manager"),
    path("tasks/add/",                 TaskCreateView.as_view(),        name="task_create"),
    path("tasks/<int:pk>/edit/",       TaskEditView.as_view(),          name="task_edit"),
    path("tasks/<int:pk>/delete/",     TaskDeleteView.as_view(),        name="delete_task"),
    path("tasks/<int:pk>/toggle/",     TaskToggleView.as_view(),        name="toggle_task"),

    # extras / API
    path("tasks/export/",              TaskICSExportView.as_view(),     name="tasks_export"),
    path("tasks/<int:pk>/reschedule/", TaskRescheduleView.as_view(),    name="task_reschedule"),
    path("tasks/<int:pk>/toggle-series/", TaskToggleSeriesView.as_view(), name="task_toggle_series"),

    # JSON‑only endpoint (keep it under an API prefix)
    path("api/tasks/<int:pk>/delete/", TaskDeleteAPIView.as_view(),     name="api_task_delete"),

        # ─────────── Dashboard ───────────
    path("dashboard/",                     DashboardView.as_view(),   name="dashboard"),
]