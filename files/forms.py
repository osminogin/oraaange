from django import forms


class UploadForm(forms.Form):
    """ Upload pseudo-form for validation. """
    file = forms.FileField()
