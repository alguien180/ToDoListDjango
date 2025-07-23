from django.shortcuts import render, redirect
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.utils.timezone import now
from django.http import (
    HttpResponse,
    JsonResponse,
)
from datetime import datetime, timedelta, time
from io import BytesIO
import json


from django.urls import reverse_lazy

from django.contrib.auth.mixins import LoginRequiredMixin


from .models import Note, Tag,Task
from django import forms
from django.db.models import Q

#other app imports
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic.edit import DeleteView


# ───── Third-party libs ───────────────────────────────────────────────
from icalendar import Calendar, Event
from docx import Document
from docx.shared import Pt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
import pytz
from docx import Document




class NoteList(LoginRequiredMixin, ListView):
    template_name = 'Notes/notes_list.html'
    model = Note
    context_object_name = 'notes'

    # NEW: central queryset construction (adds user filter + tag filtering)
    def get_queryset(self):
        qs = super().get_queryset()
        # Scope to current user (you were doing this in context; doing it here
        # means downstream filters & counts start from correct set)
        qs = qs.filter(user=self.request.user)
        # Apply tag filters (single or multi)
        qs = self.apply_tag_filters(qs)
        return qs

    # NEW: helper to apply tag filtering
    def apply_tag_filters(self, qs):
        """
        Apply tag filtering based on ?tag= (single) or ?tags= (comma-separated).
        Accepts tag slugs OR names (case-insensitive for names).
        """
        single = self.request.GET.get('tag', '').strip()
        multi_raw = self.request.GET.get('tags', '').strip()

        tag_terms = []
        if single:
            tag_terms.append(single)
        if multi_raw:
            tag_terms.extend([t.strip() for t in multi_raw.split(',') if t.strip()])

        if not tag_terms:
            return qs

        # Match slug exactly OR name case-insensitively.
        return qs.filter(
            Q(tags__slug__in=tag_terms) |
            Q(tags__name__in=tag_terms)
        ).distinct()

    # NEW: inject tag context (non-destructive)
    def inject_tag_context(self, context):
        single = self.request.GET.get('tag', '').strip()
        multi_raw = self.request.GET.get('tags', '').strip()

        selected = []
        if single:
            selected.append(single)
        if multi_raw:
            selected.extend([t.strip() for t in multi_raw.split(',') if t.strip()])

        # All available tags for this user (to build pill UI)
        context['all_tags'] = Tag.objects.filter(
            notes__user=self.request.user
        ).distinct().order_by('name')

        context['selected_tags'] = selected
        context['tags_query_string'] = ",".join(selected)
        return context

    # ORIGINAL METHOD (body untouched except final return line)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Your original user scoping & count (qs already user-filtered in get_queryset,
        # but we keep your logic intact as requested)
        context['notes'] = context['notes'].filter(user=self.request.user)
        context['count'] = context['notes'].filter(complete=False).count()

        search_input = self.request.GET.get('search-area') or ''
        if search_input:
            context['notes'] = context['notes'].filter(title__icontains=search_input)
        context['search_input'] = search_input

        # Add tag context WITHOUT altering preceding logic
        return self.inject_tag_context(context)




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





#from the other APP version

class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = "Task/TaskManager.html"      # create this template
    context_object_name = "incomplete_tasks"
    ordering = ["-date_created"]                # matches Task.Meta

    def get_queryset(self):
        return Task.objects.filter(
            user=self.request.user,
            completed=False
        ).order_by("-date_created")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        all_user_tasks = Task.objects.filter(user=self.request.user)

        ctx["incomplete_tasks"] = all_user_tasks.filter(completed=False).order_by("-date_created")
        ctx["completed_tasks"]  = all_user_tasks.filter(completed=True).order_by("-date_created")

        # Provide a flat tag list for possible filtering UI (distinct)
        ctx["all_task_tags"] = Tag.objects.filter(tasks__user=self.request.user).distinct().order_by("name")

        # Example: optional tag filter (?tags=foo,bar)
        raw = self.request.GET.get("tags", "")
        selected = str(raw)
        ctx["selected_task_tags"] = selected

        if selected:
            ctx["incomplete_tasks"] = ctx["incomplete_tasks"].filter(
                Q(tags__name__in=selected) | Q(tags__slug__in=selected)
            ).distinct()
            ctx["completed_tasks"] = ctx["completed_tasks"].filter(
                Q(tags__name__in=selected) | Q(tags__slug__in=selected)
            ).distinct()

        return ctx
# ───────────────────────────────────────────────────────────────
#  Task Export  (ICS)
# ───────────────────────────────────────────────────────────────
@method_decorator(csrf_exempt, name="dispatch")
class TaskICSExportView(LoginRequiredMixin, View):
    """GET → download an .ics file of *all* the user’s tasks."""
    def get(self, request):
        tasks = (
            Task.objects
            .filter(user=request.user)
            .order_by("start_date")
        )

        cal = Calendar()
        cal.add("prodid", "-//TaskManager Export//")
        cal.add("version", "2.0")

        def str_to_time(t):
            if not t:
                return None
            return (
                datetime.strptime(t, "%H:%M").time()
                if isinstance(t, str) else t
            )

        for task in tasks:
            if not task.start_date:
                continue

            evt = Event()
            evt.add("summary", task.title)
            evt.add("description", task.notes or "")

            tz = pytz.timezone(task.timezone or "UTC")
            start_dt = tz.localize(
                datetime.combine(
                    task.start_date,
                    str_to_time(task.start_time) or datetime.min.time(),
                )
            )

            if task.end_time:
                end_dt = tz.localize(
                    datetime.combine(task.start_date, str_to_time(task.end_time))
                )
                if end_dt < start_dt:  # crosses midnight
                    end_dt += timedelta(days=1)
            else:
                end_dt = start_dt + timedelta(minutes=30)

            evt.add("dtstart", start_dt)
            evt.add("dtend", end_dt)
            cal.add_component(evt)

        response = HttpResponse(
            cal.to_ical(),
            content_type="text/calendar",
            headers={"Content-Disposition": 'attachment; filename="tasks.ics"'},
        )
        return response


# ───────────────────────────────────────────────────────────────
#  Task Drag / Resize (reschedule)
# ───────────────────────────────────────────────────────────────
def _iso_to_dt(s):
    if not s:  # empty / null
        return None
    if s.endswith("Z"):  # “Zulu” UTC marker
        s = s[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(s)  # Python 3.11+
    except ValueError:
        return None
@method_decorator(csrf_exempt, name="dispatch")
class TaskRescheduleView(LoginRequiredMixin, View):
    """
    POST  /tasks/<pk>/reschedule/
    Payload: {"start": "...ISO...", "end": "...ISO..."|null}
    """
    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk, user=request.user)
        data = json.loads(request.body)

        start_dt = _iso_to_dt(data.get("start"))
        if not start_dt:
            return JsonResponse(
                {"status": "error", "message": "Invalid start datetime"}, status=400
            )

        task.start_date = start_dt.date()
        end_dt = _iso_to_dt(data.get("end"))
        task.end_date = end_dt.date() if end_dt else None
        task.save()
        return JsonResponse({"status": "ok"})


# ───────────────────────────────────────────────────────────────
#  Toggle *all* recurring instances
# ───────────────────────────────────────────────────────────────
@method_decorator(csrf_exempt, name="dispatch")
class TaskToggleSeriesView(LoginRequiredMixin, View):
    """
    POST  /tasks/<pk>/toggle-series/
    Flip completed ↔ incomplete for **all** tasks that share
    title + start_date + repeat pattern with the clicked task.
    """
    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk, user=request.user)
        mark_done = not task.completed
        Task.objects.filter(
            title=task.title,
            start_date__gte=task.start_date,
            repeat=task.repeat,
            user=request.user,
        ).update(completed=mark_done)
        return JsonResponse({"status": "ok"})


# ───────────────────────────────────────────────────────────────
#  Delete via API
# ───────────────────────────────────────────────────────────────
@method_decorator(csrf_exempt, name="dispatch")
class TaskDeleteAPIView(LoginRequiredMixin, View):
    """
    POST  /api/tasks/<pk>/delete/
    Returns {"status":"ok"} on success.
    """
    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk, user=request.user)
        task.delete()
        return JsonResponse({"status": "ok"})

# -----------------------------------------------------------------
#  CREATE  (AJAX posts the form fields)
# -----------------------------------------------------------------
@method_decorator(csrf_exempt, name="dispatch")
class TaskCreateView(LoginRequiredMixin, View):
    """
    POST /tasks/add/
    Returns {"status":"ok","task_id":<id>} or {"status":"error", ...}
    """
    def post(self, request):
        data = request.POST

        try:
            # ── Tags: free‑text → Tag row (or None) ──────────────────── ACA ESTA EL PEDO. SI haz el strip pero haz un lambda para cada tag que reciba, por cada objeto generar un tag nuevo. o hacer un create.
            tag_string = (data.get("tags") or "").strip() #esto es la lista de tags.
            tag_obj = (
                Tag.objects.get_or_create(tags=tag_string)[0] # Cuando es generado, genera una tupla, si no hay nada = none
                if tag_string else None
            )

            # ── Create row ────────────────────────────────────────────
            #task = Este metodo genera una intancia del objecto task. Si quieres set los Tags a Task. 
            # TIENES QUE ABAJO DE LA LLAMADA DE LA FUNCION, CREAR Task.set("el ") 
            task = Task.objects.create(
                user             = request.user,
                title            = data.get("title"),
                start_date       = data.get("start_date"),
                end_date         = data.get("end_date") or None,
                start_time       = data.get("start_time") or None,
                end_time         = data.get("end_time") or None,
                priority         = data.get("priority") or "M",
                repeat           = data.get("repeat") or "",
                timezone         = data.get("timezone") or "",
                custom_days      = data.get("custom_days") or "",
                repeat_until     = data.get("repeat_until") or None,
                repeat_forever   = data.get("repeat_forever") == "true",
                notes            = data.get("notes") or "",
               # tags             = tag_obj,
                color            = data.get("color") or "blue",
                completed        = False,
            )
            import ipdb #esto es para hacer debugging
            ipdb.set_trace()
            print(tag_obj)
            #agrega un reverse lazy hacia el task code no ese desmadre de arriba
            return JsonResponse({"status": "ok", "task_id": task.id})
        except Exception as exc:
            return JsonResponse(
                {"status": "error", "message": str(exc)},
                status=400,
            )


# -----------------------------------------------------------------
#  EDIT / UPDATE
# -----------------------------------------------------------------
@method_decorator(csrf_exempt, name="dispatch")
class TaskEditView(LoginRequiredMixin, View):
    """
    POST /tasks/<pk>/edit/
    Same payload as “create”; returns {"status":"ok","task_id":<pk>}
    """
    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk, user=request.user)
        data = request.POST

        # ── Tags ─────────────────────────────────────────────────────
        tag_string = (data.get("tags") or "").strip()
        task.tags = (
            Tag.objects.get_or_create(tags=tag_string)[0]
            if tag_string else None
        )

        # ── Simple scalar fields ─────────────────────────────────────
        scalar_fields = [
            "title", "start_date", "end_date",
            "start_time", "end_time", "priority",
            "repeat", "timezone", "custom_days",
            "repeat_until", "notes", "color",
        ]
        for fld in scalar_fields:
            val = data.get(fld) or None
            setattr(task, fld, val)

        # ── Flags ────────────────────────────────────────────────────
        task.repeat_forever = data.get("repeat_forever") == "true"

        task.save()
        return JsonResponse({"status": "ok", "task_id": task.id})


# -----------------------------------------------------------------
#  DELETE  (confirmation page + redirect)
# -----------------------------------------------------------------
class TaskDeleteView(LoginRequiredMixin, DeleteView):
    model = Task

    success_url = reverse_lazy("task_manager")   # adjust namespace

    def get_queryset(self):
        # limit to current user
        return Task.objects.filter(user=self.request.user)


# -----------------------------------------------------------------
#  TOGGLE single task completed ↔ incomplete
# -----------------------------------------------------------------
@method_decorator(csrf_exempt, name="dispatch")
class TaskToggleView(LoginRequiredMixin, View):
    """
    POST /tasks/<pk>/toggle/
    Flip the “completed” flag, then redirect to task list.
    """
    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk, user=request.user)
        task.completed = not task.completed
        task.save()
        return redirect("task_manager")




class DashboardView(LoginRequiredMixin, View):
    template_name = "Dashboard/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Tags filter logic
        selected_tags = self.request.GET.get("tags", "").split(",")
        selected_tags = [tag.strip() for tag in selected_tags if tag.strip()]

        # Task filtering
        task_filter = self.request.GET.get("task_filter", "all")
        show_notes = self.request.GET.get("show_notes") == "on"
        group_colour = self.request.GET.get("group_colour") == "on"

        tasks = Task.objects.filter(user=user)
        if selected_tags:
            tasks = tasks.filter(tags__name__in=selected_tags).distinct()

        if task_filter == "completed":
            completed_tasks = tasks.filter(completed=True)
            incomplete_tasks = Task.objects.none()
        elif task_filter == "incomplete":
            completed_tasks = Task.objects.none()
            incomplete_tasks = tasks.filter(completed=False)
        elif task_filter == "none":
            completed_tasks = Task.objects.none()
            incomplete_tasks = Task.objects.none()
        else:
            completed_tasks = tasks.filter(completed=True)
            incomplete_tasks = tasks.filter(completed=False)

        notes = Note.objects.filter(user=user)
        if selected_tags:
            notes = notes.filter(tags__name__in=selected_tags).distinct()

        all_tags = set(
            list(tasks.values_list("tags__name", flat=True)) +
            list(notes.values_list("tags__name", flat=True))
        )

        context.update({
            "incomplete_tasks": incomplete_tasks,
            "completed_tasks": completed_tasks,
            "notes": notes if show_notes else None,
            "all_tags": sorted(filter(None, all_tags)),
            "selected_tags": selected_tags,
            "show_notes": show_notes,
            "group_colour": group_colour,
            "task_events_json": self._build_events(tasks)
        })
        return context

    @staticmethod
    def _build_events(tasks):
        events, MAX_REPEAT_DAYS = [], 730

        def _hms(t):
            if not t:
                return ""
            if isinstance(t, time):
                return t.strftime("%H:%M:%S")
            return str(t) if ":" in str(t) else f"{t}:00"

        for task in tasks:
            if not task.start_date:
                continue

            if task.repeat_forever:
                end_limit = 365
            elif task.repeat_until:
                end_limit = max(0, min((task.repeat_until - task.start_date).days, MAX_REPEAT_DAYS))
            else:
                end_limit = 30

            def add_event(date_obj):
                has_start = bool(task.start_time)
                has_end = bool(task.end_time)

                start_iso = f"{date_obj}T{_hms(task.start_time)}" if has_start else str(date_obj)
                end_iso = f"{date_obj}T{_hms(task.end_time)}" if has_end else None

                evt = {
                    "id": task.id,
                    "title": task.title,
                    "start": start_iso,
                    "allDay": not has_start,
                    "color": task.color,
                    "extendedProps": {
                        "notes": task.notes or "",
                        "tags": task.tags.tags if task.tags else "",
                        "priority": task.priority,
                        "repeat": task.repeat,
                        "timezone": task.timezone or "",
                        "customDays": task.custom_days or "",
                        "repeatUntil": str(task.repeat_until) if task.repeat_until else "",
                        "repeatForever": str(task.repeat_forever).lower(),
                        "rawDue": str(task.start_date),
                        "start_time": _hms(task.start_time) if has_start else "",
                        "end_time": _hms(task.end_time) if has_end else "",
                    },
                }
                if end_iso:
                    evt["end"] = end_iso
                events.append(evt)

            if task.repeat == "custom" and task.custom_days:
                for d in get_recurring_dates(task.start_date, task.custom_days, end_limit):
                    add_event(d)
            else:
                for i in range(end_limit + 1):
                    if task.repeat == "daily":
                        date = task.start_date + timedelta(days=i)
                    elif task.repeat == "weekly":
                        date = task.start_date + timedelta(weeks=i)
                    elif task.repeat == "monthly":
                        try:
                            date = task.start_date.replace(month=(task.start_date.month + i - 1) % 12 + 1)
                        except ValueError:
                            continue
                    elif task.repeat == "yearly":
                        try:
                            date = task.start_date.replace(year=task.start_date.year + i)
                        except ValueError:
                            continue
                    else:
                        date = task.start_date
                        if i:
                            break
                    add_event(date)

        return events