# ── Standard library ────────────────────────────────────────────────
import json
from io import BytesIO

# ── Third‑party packages ────────────────────────────────────────────
from docx import Document
from docx.shared import Pt
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
import pytz
from PIL import Image as PILImage
from docx.shared import Inches
from reportlab.platypus import Image as RLImage
from django.utils import timezone
# ── Django core ─────────────────────────────────────────────────────
from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import FileResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView

# ── Local apps ──────────────────────────────────────────────────────
from .models import Note, Tag




class NoteList(LoginRequiredMixin, ListView):
    template_name = "Notes/notes_list.html"
    model = Note
    context_object_name = "notes"

    # ───────────────────────────────────────────────────────────
    # Construct the queryset
    # ───────────────────────────────────────────────────────────
    def get_queryset(self):
        queryset = (
            super().get_queryset()
            .filter(user=self.request.user)                 # always user‑scoped
        )

        # Tag filtering (?tag=foo or ?tags=a,b)
        queryset = self.apply_tag_filters(queryset)

        # Status filtering (?status=incomplete / complete / all)
        status_filter = self.request.GET.get("status", "all").lower()
        self.current_status = status_filter                 # expose later
        if status_filter == "incomplete":
            queryset = queryset.filter(complete=False)
        elif status_filter == "complete":
            queryset = queryset.filter(complete=True)
        # If "all", leave queryset unchanged

        return queryset

    # ───────────────────────────────────────────────────────────
    # Helper: apply tag filters
    # ───────────────────────────────────────────────────────────
    def apply_tag_filters(self, queryset):
        single_tag = self.request.GET.get("tag", "").strip()
        multiple_tags_raw = self.request.GET.get("tags", "").strip()

        tag_terms = []
        if single_tag:
            tag_terms.append(single_tag)
        if multiple_tags_raw:
            tag_terms.extend(
                tag.strip() for tag in multiple_tags_raw.split(",") if tag.strip()
            )

        if not tag_terms:
            return queryset

        return queryset.filter(
            Q(tags__slug__in=tag_terms) | Q(tags__name__in=tag_terms)
        ).distinct()

    # ───────────────────────────────────────────────────────────
    # Helper: add tag‑related context
    # ───────────────────────────────────────────────────────────
    def add_tag_context(self, context):
        single_tag = self.request.GET.get("tag", "").strip()
        multiple_tags_raw = self.request.GET.get("tags", "").strip()

        selected_tags = []
        if single_tag:
            selected_tags.append(single_tag)
        if multiple_tags_raw:
            selected_tags.extend(
                tag.strip() for tag in multiple_tags_raw.split(",") if tag.strip()
            )

        context["all_tags"] = (
            Tag.objects.filter(notes__user=self.request.user)
            .distinct()
            .order_by("name")
        )
        context["selected_tags"] = selected_tags
        context["tags_query_string"] = ",".join(selected_tags)
        return context

    # ───────────────────────────────────────────────────────────
    # Build the template context
    # ───────────────────────────────────────────────────────────
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Count of incomplete notes after all filters
        context["count"] = context["notes"].filter(complete=False).count()

        # Title search filter
        search_term = self.request.GET.get("search-area", "")
        if search_term:
            context["notes"] = context["notes"].filter(title__icontains=search_term)
        context["search_input"] = search_term

        # Expose current status filter to the template
        context["status"] = getattr(self, "current_status", "all")

        # Add tag‑related helpers
        return self.add_tag_context(context)



class NoteDetail(LoginRequiredMixin, DetailView):
    context_object_name='note'
    template_name = 'Notes/notes_details.html'
    model = Note

class NoteCreate(LoginRequiredMixin, CreateView):
    context_object_name='notecreate'
    template_name = 'Notes/note_createForm.html'
    model = Note
    fields = ['title','description','complete','image']
    success_url=reverse_lazy('notes')

    def form_valid(self, form):
        # Attach the user first
        form.instance.user = self.request.user

        # Save the Note object
        response = super().form_valid(form)

        # Process tags from hidden field
        tags_raw = self.request.POST.get('tags_hidden', '')
        for raw in [t.strip() for t in tags_raw.split(',') if t.strip()]:
            # Try case-insensitive match; create if not found
            existing = Tag.objects.filter(name__iexact=raw).first() #esto es ineficiente mejor el del get_or_create que esta en TASK aca haces 2 consultas, en el get or create hace 1 consulta para ambos
            # lo ideal seria hacer el get or create
            tag = existing if existing else Tag.objects.create(name=raw)
            self.object.tags.add(tag) # esto es tomando de la misma nota, toma 

        return response


class NoteUpdate(LoginRequiredMixin, UpdateView):
    model = Note
    fields = ['title', 'description', 'complete', 'image']
    template_name = 'Notes/note_UpdateForm.html'
    success_url = reverse_lazy('notes')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Optional: tweak the file input
        form.fields['image'].widget = forms.FileInput(attrs={'accept': 'image/*'})
        return form

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Pre-populate existing tags in a comma-separated string
        existing = self.object.tags.values_list('name', flat=True)
        ctx['existing_tags'] = ",".join(existing)
        return ctx

    def form_valid(self, form):
        # Keep user assignment consistent (optional safeguard)
        if form.instance.user_id is None:
            form.instance.user = self.request.user

        response = super().form_valid(form)

        # Replace tag set with new tags from hidden input
        tags_raw = self.request.POST.get('tags_hidden', '')
        self.object.tags.clear()

        for raw in [t.strip() for t in tags_raw.split(',') if t.strip()]:
            tag = Tag.objects.filter(name__iexact=raw).first()
            if not tag:
                tag = Tag.objects.create(name=raw)
            self.object.tags.add(tag)

        return response

class NoteDelete(LoginRequiredMixin,DeleteView):
    model = Note
    context_object_name ='delete-note'
    template_name = 'Notes/note_confirm_delete.html'
    success_url = reverse_lazy('notes')


class _FilteredNotesMixin:
    def get_notes(self):
        qs = Note.objects.filter(user=self.request.user)
        # Re‑use the same tag + search filters as NoteList
        nl = NoteList()
        nl.request = self.request
        return nl.apply_tag_filters(qs)


class NotesExportPDF(_FilteredNotesMixin, View):
    def get(self, request):
        buf    = BytesIO()
        doc    = SimpleDocTemplate(buf, pagesize=A4,
                                   rightMargin=1*cm, leftMargin=1*cm,
                                   topMargin=1*cm,  bottomMargin=1*cm)
        styles = getSampleStyleSheet()
        flow   = []

        MAX_W, MAX_H = 14*cm, 14*cm

        for n in self.get_notes():
            # ➜ title with timestamps in parentheses
            created = timezone.localtime(n.created_at).strftime("%d %b %Y %H:%M")
            updated = timezone.localtime(n.updated_at).strftime("%d %b %Y %H:%M")
            title   = f"{n.title}  ({created} • {updated})"

            flow.append(Paragraph(title, styles["Heading2"]))
            flow.append(Paragraph(n.description or "(no text)", styles["BodyText"]))

            if n.image:
                pil    = PILImage.open(n.image.path)
                w, h   = pil.size
                scale  = min(MAX_W / w, MAX_H / h, 1)
                flow.append(RLImage(n.image.path, width=w*scale, height=h*scale))

            flow.append(Spacer(1, 12))

        doc.build(flow)
        buf.seek(0)
        return FileResponse(buf, as_attachment=True, filename="notes.pdf")

from docx.shared import Pt      # already imported earlier

class NotesExportDocx(_FilteredNotesMixin, View):
    def get(self, request):
        doc = Document()

        SMALL = Pt(9)            # ← 9‑point text (adjust as you like)

        for n in self.get_notes():
            created = timezone.localtime(n.created_at).strftime("%d %b %Y %H:%M")
            updated = timezone.localtime(n.updated_at).strftime("%d %b %Y %H:%M")

            doc.add_heading(n.title, level=2)

            # ── creation line (small) ──────────────────────────────
            p1 = doc.add_paragraph()
            run1 = p1.add_run(f"Creation date:  {created}")
            run1.font.size = SMALL

            # ── modification line (small) ─────────────────────────
            p2 = doc.add_paragraph()
            run2 = p2.add_run(f"Last modified:  {updated}")
            run2.font.size = SMALL

            # description + image
            doc.add_paragraph(n.description or "(no text)")
            if n.image:
                doc.add_picture(n.image.path, width=Inches(5))

            doc.add_paragraph()   # blank line between notes

        buf = BytesIO()
        doc.save(buf)
        buf.seek(0)
        return FileResponse(buf, as_attachment=True,
                            filename="notes.docx")
