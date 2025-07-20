from django.shortcuts import render, redirect
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from .models import Note, Tag
from django import forms
from django.db.models import Q

class CustomLoginView(LoginView):
    template_name = 'Notes/login.html'
    fields='__all__'
    redirect_authenticated_user=True
    
    def get_success_url(self):
        return reverse_lazy('notes')

class RegisterPage(FormView):
    template_name = 'Notes/register.html'
    form_class = UserCreationForm
    redirect_authenticated_user= True #this is overwritten with the def get
    success_url= reverse_lazy('notes')

    def form_valid(self,form):
        user = form.save()
        if user is not None:
            login(self.request,user)
        return super(RegisterPage,self).form_valid(form)
    
    def get(self,*args,**kwargs):
        if self.request.user.is_authenticated:
            return redirect('notes')
        return super(RegisterPage,self).get(*args,**kwargs)#overwriting the top fnuction because it did not stopped logged users from entering the create account


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
            existing = Tag.objects.filter(name__iexact=raw).first()
            tag = existing if existing else Tag.objects.create(name=raw)
            self.object.tags.add(tag)

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