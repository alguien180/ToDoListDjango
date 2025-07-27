from django.urls import path
from .views import (
    # NOTES
    NoteList, NoteDetail, NoteCreate, NoteUpdate, NoteDelete, NotesExportDocx,NotesExportPDF

)

urlpatterns = [
    # ─────────── Notes ───────────
    path("notes/",                     NoteList.as_view(),   name="notes"),
    path("notes/add/",                 NoteCreate.as_view(), name="note-create"),
    path("notes/<int:pk>/",            NoteDetail.as_view(), name="note-detail"),
    path("notes/<int:pk>/edit/",       NoteUpdate.as_view(), name="note-update"),
    path("notes/<int:pk>/delete/",     NoteDelete.as_view(), name="note-delete"),
    path("notes/export/pdf/",  NotesExportPDF.as_view(),  name="notes_export_pdf"),
    path("notes/export/docx/", NotesExportDocx.as_view(), name="notes_export_docx"),
]