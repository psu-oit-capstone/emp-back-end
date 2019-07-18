# Taken from this video:
# https://www.youtube.com/watch?v=wVnQkKf-gHo
from django import forms
from .models import Identity, Contact, Emergency
from common.util import sanitization

class UpdateEmergencyContactForm(forms.ModelForm):
    # Provide an example of the schema of the model
    surrogate_id = forms.IntegerField(required=False)
    priority = forms.CharField()
    relt_code = forms.CharField(max_length=4)
    last_name = forms.CharField(max_length=240)
    first_name = forms.CharField(max_length=240)
    mi = forms.CharField(max_length=240, required=False, null=True)

    street_line1 = forms.CharField(max_length=300)
    street_line2 = forms.Charfield(max_length=300, required=False, null=True)
    street_line3 = forms.Charfield(max_length=300, required=False, null=True)
    city = forms.CharField(max_length=200)
    stat_code = forms.CharField(max_length=12)
    natn_code = forms.CharField(max_length=20)
    zip = forms.CharField(max_length=120)
    ctry_code_phone = forms.CharField(max_length=16)
    phone_area = forms.CharField(max_length=24)
    phone_number = forms.CharField(max_length=48)
    phone_ext = forms.CharField(max_length=40, required=False, null=True)

    class Meta:
        model = Contact
        fields = [
            'surrogate_id', 'priority', 'relt_code',
            'last_name', 'first_name', 'mi',
            'street_line1', 'street_line2', 'street_line3',
            'city', 'stat_code', 'natn_code', 'zip',
            'ctry_code_phone', 'phone_area', 'phone_number', 'phone_ext'
        ]

    def clean_phone_number(self, *args, **kwargs):
        #validation function goes here
        phone_area = self.cleaned_data.get("phone_area")
        phone_num = self.cleaned_data.get("phone_num")

        full_phone = phone_area + phone_num
        result = sanitization.validate_phone_num(full_phone)
        if result:
            return full_phone
        else:
            raise forms.ValidationError("Invalid phone number")

    def clean_relt_code(self, *args, **kwargs):
        valid_relational_codes = ['G', 'F', 'O', 'U', 'S', 'A', 'R']
        relation_code = self.cleaned_data.get("relt_code")
        if relation_code in valid_relational_codes:
            return relation_code
        else:
            raise forms.ValidationError("Invalid relation code")
