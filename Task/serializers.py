from rest_framework import serializers
from .models import Note
#hace referencia a los objetos, no a los metodos (Hyperlink....)
class NotesSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model=Note
        fields = ['title', 'description', 'complete', 'image']
