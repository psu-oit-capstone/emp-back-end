# Taken from this video:
# https://www.youtube.com/watch?v=wVnQkKf-gHo
from django import forms
from .models import Identity, Contact, Emergency
from common.util import sanitization

class UpdateEmergencyContactForm(forms.ModelForm):
    # Provide an example of the schema of the model
    pidm = forms.IntegerField(required=False)
    surrogate_id = forms.IntegerField(required=False)
    priority = forms.CharField()
    relt_code = forms.CharField(max_length=4)
    last_name = forms.CharField(max_length=240)
    first_name = forms.CharField(max_length=240)
    mi = forms.CharField(max_length=240, required=False)

    street_line1 = forms.CharField(max_length=300)
    street_line2 = forms.CharField(max_length=300, required=False)
    street_line3 = forms.CharField(max_length=300, required=False)
    city = forms.CharField(max_length=200)
    stat_code = forms.CharField(max_length=12)
    natn_code = forms.CharField(max_length=20)
    zip = forms.CharField(max_length=120)
    ctry_code_phone = forms.CharField(max_length=16)
    phone_area = forms.CharField(max_length=24)
    phone_number = forms.CharField(max_length=48)
    phone_ext = forms.CharField(max_length=40, required=False)

    class Meta:
        model = Contact
        fields = [
            'pidm', 'surrogate_id', 'priority', 'relt_code',
            'last_name', 'first_name', 'mi',
            'street_line1', 'street_line2', 'street_line3',
            'city', 'stat_code', 'natn_code', 'zip',
            'ctry_code_phone', 'phone_area', 'phone_number', 'phone_ext'
        ]

    def clean_phone_number(self, *args, **kwargs):
        #validation function goes here
        phone_area = self.cleaned_data.get("phone_area")
        phone_num = self.cleaned_data.get("phone_number")

        phone_area = str(phone_area)
        phone_num = str(phone_num)

        full_phone = phone_area + phone_num
        result = sanitization.validate_phone_num(full_phone)
        if result:
            return phone_num
        else:
            raise forms.ValidationError("Invalid phone number")

    def clean_relt_code(self, *args, **kwargs):
        valid_relational_codes = ['G', 'F', 'O', 'U', 'S', 'A', 'R']
        relation_code = self.cleaned_data.get("relt_code")
        if relation_code in valid_relational_codes:
            return relation_code
        else:
            raise forms.ValidationError("Invalid relation code")


class SetEvacuationAssistanceForm(forms.ModelForm):
    evacuation_assistance = forms.CharField(max_length=4, required=False)

    class Meta:
        model = Emergency
        fields = [
            'evacuation_assistance'
        ]

    def clean_evacuation_assistance(self, *args, **kwargs):
        evacuation_assistance = self.cleaned_data.get("evacuation_assistance")

        # cleaned_data.get method returns empty string instead of null value
        if evacuation_assistance == "":
            evacuation_assistance = None

        result = sanitization.validate_checkbox(evacuation_assistance)

        if result:
            return evacuation_assistance
        else:
            raise forms.ValidationError("Invalid relation code")


class SetEmergencyNotificationsForm(forms.ModelForm):
    external_email = forms.CharField(max_length=512, required=False)
    primary_phone = forms.CharField(max_length=72, required=False)
    alternate_phone = forms.CharField(max_length=72, required=False)
    sms_status_ind = forms.CharField(max_length=4, required=False)
    sms_device = forms.CharField(max_length=72, required=False)

    class Meta:
        model = Emergency
        fields = [
            'external_email', 'primary_phone', 'alternate_phone', 'sms_status_ind', 'sms_device'
        ]

    def clean_external_email(self, *args, **kwargs):
        external_email = self.cleaned_data.get("external_email")

        if external_email == "":
            # external_email = None
            return None

        result = sanitization.validate_email(external_email)

        if result:
            return external_email
        else:
            raise forms.ValidationError("Invalid email")

    def clean_primary_phone(self, *args, **kwargs):
        primary_phone = self.cleaned_data.get("primary_phone")

        if primary_phone == "":
            # primary_phone = None
            return None

        result = sanitization.validate_phone_num(primary_phone)

        if result:
            return primary_phone
        else:
            raise forms.ValidationError("Invalid phone number")

    def clean_alternate_phone(self, *args, **kwargs):
        alternate_phone = self.cleaned_data.get("alternate_phone")

        if alternate_phone == "":
            # alternate_phone = None
            return None

        result = sanitization.validate_phone_num(alternate_phone)

        if result:
            return alternate_phone
        else:
            raise forms.ValidationError("Invalid phone number")

    def clean_sms_status_ind(self, *args, **kwargs):
        sms_status_ind = self.cleaned_data.get("sms_status_ind")

        # cleaned_data.get method returns empty string instead of null value
        if sms_status_ind == "":
            sms_status_ind = None

        result = sanitization.validate_checkbox(sms_status_ind)

        if result:
            return sms_status_ind
        else:
            raise forms.ValidationError("Invalid checkbox value")

    def clean_sms_device(self, *args, **kwargs):
        sms_device = self.cleaned_data.get("sms_device")

        if sms_device == "":
            # sms_device = None
            return None

        result = sanitization.validate_phone_num(sms_device)

        if result:
            return sms_device
        else:
            raise forms.ValidationError("Invalid phone number")
