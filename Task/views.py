from django.shortcuts import render, redirect
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from .models import Note


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

    def get_context_data(self, **kwargs):
        context =super().get_context_data(**kwargs)
        context['notes'] = context['notes'].filter(user=self.request.user)
        context['count'] = context['notes'].filter(complete = False).count()

        search_input = self.request.GET.get('search-area') or ''
        if search_input:
            context['notes']= context['notes'].filter(
                title__icontains=search_input)
        context['search_input']=search_input
        return context

class NoteDetail(LoginRequiredMixin, DetailView):
    context_object_name='note'
    template_name = 'Notes/notes_details.html'
    model = Note

class NoteCreate(LoginRequiredMixin, CreateView):
    context_object_name='notecreate'
    template_name = 'Notes/note_createForm.html'
    model = Note
    fields = ['title','description','complete']
    success_url=reverse_lazy('notes')

    def form_valid(self,form):
        form.instance.user = self.request.user
        return super(NoteCreate,self).form_valid(form)

class NoteUpdate(LoginRequiredMixin,UpdateView):
    model = Note
    template_name = 'Notes/note_createForm.html'
    fields = ['title','description','complete']
    success_url= reverse_lazy('notes')
    context_object_name='update-note'

class NoteDelete(LoginRequiredMixin,DeleteView):
    model = Note
    context_object_name ='delete-note'
    template_name = 'Notes/note_confirm_delete.html'
    success_url = reverse_lazy('notes')