# Taken from this video:
# https://www.youtube.com/watch?v=wVnQkKf-gHo
from django import forms
from .models import Identity, Contact, Emergency

class UpdateEmergencyContactForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # make the fields in the required dictionary be required
        for field in self.Meta.required:
            self.fields[field].required = True

    class Meta:
        model = Contact
        fields = [
            'surrogate_id', 'priority', 'relt_code',
            'last_name', 'first_name', 'mi',
            'street_line1', 'street_line2', 'street_line3',
            'city', 'stat_code', 'natn_code', 'zip',
            'ctry_code_phone', 'phone_area', 'phone_number', 'phone_ext'
        ]

        required = ('priority', 'relt_code', 'last_name', 'first_name', 'street_line1',
                    'city', 'stat_code', 'natn_code', 'zip')

    def clean_phone_number(self, *args, **kwargs):
