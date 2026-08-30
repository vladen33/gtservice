
from django import forms
from .models import (
    Doc,
    # OrdCancellation,
    DocResponsible
)

class DocForm(forms.ModelForm):
    class Meta:
        model = Doc
        # fields = '__all__'
        fields = [
            'number', 'date', 'doc_type', 'title', 'summary',
            'valid_from_date', 'valid_to_date', 'status'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'style': 'width: 100%;'}),
            'summary': forms.Textarea(attrs={'rows': 3, 'cols': 120}),
        }


class DocResponsibleForm(forms.ModelForm):
    class Meta:
        model = DocResponsible
        # fields = '__all__'
        fields = ['person', 'role', 'deadline', 'is_indefinite', 'task']
        widgets = {
            'task': forms.Textarea(attrs={'rows': 3, 'cols': 120}),
        }

