from django.db import models
from django.contrib.auth.models import User
from simple_history.models import HistoricalRecords
from django.utils.text import slugify


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Note(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE, null=True,blank=True)
    title= models.CharField(max_length=200)
    description = models.TextField(null=True,blank=True)
    complete = models.BooleanField(default=False) #when item first created it is not complete
    create = models.DateTimeField(auto_now_add=True)
    tags        = models.ManyToManyField(Tag, blank=True, related_name='notes')
    image = models.ImageField(upload_to='note_images/', blank=True, null=True)
   # tags=models.ForeignKey(Tag, on_delete=models.SET_NULL, null=True, blank=True) #esto es lo mismo
    
    history = HistoricalRecords()

    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['complete']