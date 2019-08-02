# Taken from this video:
# https://www.youtube.com/watch?v=wVnQkKf-gHo
from django import forms
from .models.identity import Identity
from .models.contact import Contact
from .models.emergency import Emergency
from .models.nation import Nation
from .models.state import State
from common.util import sanitization

# When required field=false, clean() would normalize empty value of CharField into empty string
# However, null value was needed to follow the sample data provided. Therefore, this function is declared.
# Source: https://docs.djangoproject.com/en/2.2/ref/forms/fields/
def empty_string_handler(field):
    # if field either empty string or empty/null value
    if not field:
        return None
    else:
        return field


class UpdateEmergencyContactForm(forms.ModelForm):
    # Provide an example of the schema of the model
    pidm = forms.IntegerField()
    surrogate_id = forms.IntegerField(required=False)
    priority = forms.CharField(max_length=4)
    relt_code = forms.CharField(max_length=4, required=False)
    last_name = forms.CharField(max_length=240)
    first_name = forms.CharField(max_length=240)
    mi = forms.CharField(max_length=240, required=False)

    street_line1 = forms.CharField(max_length=300, required=False)
    street_line2 = forms.CharField(max_length=300, required=False)
    street_line3 = forms.CharField(max_length=300, required=False)
    city = forms.CharField(max_length=200, required=False)
    stat_code = forms.CharField(max_length=12, required=False)
    natn_code = forms.CharField(max_length=20, required=False)
    zip = forms.CharField(max_length=120, required=False)
    ctry_code_phone = forms.CharField(max_length=16, required=False)
    phone_area = forms.CharField(max_length=24, required=False)
    phone_number = forms.CharField(max_length=48, required=False)
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

    def clean(self):
        cleaned_data = super(UpdateEmergencyContactForm, self).clean()
        surrogate_id = cleaned_data.get("surrogate_id")
        pidm = cleaned_data.get("pidm")
        if surrogate_id:
            check_pidm = Contact.objects.filter(surrogate_id=surrogate_id, pidm=pidm)
            if len(check_pidm) != 1:
                raise forms.ValidationError("Invalid Surrogate ID")

        priority = cleaned_data.get("priority")
        entries = Contact.objects.filter(pidm=pidm)
        if not priority:
            raise forms.ValidationError("Missing priority number")
        if not(0 < int(priority) < (len(entries) + 2)):
            raise forms.ValidationError("Invalid priority number")

        street_line1 = cleaned_data.get("street_line1")
        city = cleaned_data.get("city")
        stat_code = cleaned_data.get("stat_code")
        zip = cleaned_data.get("zip")
        natn_code = cleaned_data.get("natn_code")
        if (street_line1 or city or stat_code or zip or natn_code):
            if not street_line1:
                self.add_error('street_line1', "Address field is required")
            if not city:
                self.add_error('city', "City field is required")
            if not natn_code and not(stat_code and zip):
                msg = "Nation field, or State + Zip fields is/are required"
                self.add_error('natn_code', msg)
                self.add_error('stat_code', msg)
                self.add_error('zip', msg)

        if natn_code == "LUS":
            stat_code = cleaned_data.get("stat_code")
            if not(sanitization.validate_state_usa(stat_code)):
                raise forms.ValidationError("Invalid state code")
            zip = cleaned_data.get("zip")
            if not(sanitization.validate_zip_usa(zip)):
                raise forms.ValidationError("Invalid zip code")
            phone_area = cleaned_data.get("phone_area")
            phone_number = cleaned_data.get("phone_number")
            phone_area = str(phone_area)
            phone_number = str(phone_number)
            full_phone = phone_area + phone_number
            if len(phone_area) != 3 or len(phone_number) != 7 or not(sanitization.validate_phone_num_usa(full_phone)):
                raise forms.ValidationError("Invalid phone number")

        return cleaned_data

    def clean_relt_code(self, *args, **kwargs):
        relt_code = self.cleaned_data.get("relt_code")
        relt_code = empty_string_handler(relt_code)
        if not(relt_code == None or sanitization.validate_relation(relt_code)):
            raise forms.ValidationError("Invalid relation code:")

        return relt_code

    def clean_stat_code(self, *args, **kwargs):
        stat_code = self.cleaned_data.get("stat_code")
        stat_code = empty_string_handler(stat_code)

        return stat_code

    def clean_natn_code(self, *args, **kwargs):
        natn_code = self.cleaned_data.get("natn_code")
        natn_code = empty_string_handler(natn_code)
        if not(natn_code == None or sanitization.validate_nation_code(natn_code)):
            raise forms.ValidationError("Invalid nation code:")

        return natn_code

    def clean_zip(self, *args, **kwargs):
        zip = self.cleaned_data.get("zip")
        zip = empty_string_handler(zip)

        return zip

    def clean_phone_area(self, *args, **kwargs):
        phone_area = self.cleaned_data.get("phone_area")
        phone_area = empty_string_handler(phone_area)

        return phone_area

    def clean_phone_number(self, *args, **kwargs):
        phone_number = self.cleaned_data.get("phone_number")
        phone_number = empty_string_handler(phone_number)

        return phone_number

    # ctry_code_phone and phone_ext seem does not need clean_<field> method


class SetEvacuationAssistanceForm(forms.ModelForm):
    # since checkbox is either "Y" or None, the field is not required
    evacuation_assistance = forms.CharField(max_length=4, required=False)

    class Meta:
        model = Emergency
        fields = [
            'evacuation_assistance'
        ]

    def clean_evacuation_assistance(self, *args, **kwargs):
        evacuation_assistance = self.cleaned_data.get("evacuation_assistance")
        evacuation_assistance = empty_string_handler(evacuation_assistance)
        if not(evacuation_assistance == None or sanitization.validate_checkbox(evacuation_assistance)):
            raise forms.ValidationError("Invalid checkbox value")

        return evacuation_assistance


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
        external_email = empty_string_handler(external_email)
        if not(external_email == None or sanitization.validate_email(external_email)):
            raise forms.ValidationError("Invalid email")

        return external_email

    def clean_primary_phone(self, *args, **kwargs):
        primary_phone = self.cleaned_data.get("primary_phone")
        primary_phone = empty_string_handler(primary_phone)
        if not(primary_phone == None or sanitization.validate_phone_num_usa(primary_phone)):
            raise forms.ValidationError("Invalid phone number")

        return primary_phone

    def clean_alternate_phone(self, *args, **kwargs):
        alternate_phone = self.cleaned_data.get("alternate_phone")
        alternate_phone = empty_string_handler(alternate_phone)
        if not(alternate_phone == None or sanitization.validate_phone_num_usa(alternate_phone)):
            raise forms.ValidationError("Invalid phone number")

        return alternate_phone

    def clean_sms_status_ind(self, *args, **kwargs):
        sms_status_ind = self.cleaned_data.get("sms_status_ind")
        sms_status_ind = empty_string_handler(sms_status_ind)
        if not(sms_status_ind == None or sanitization.validate_checkbox(sms_status_ind)):
            raise forms.ValidationError("Invalid checkbox value")

        return sms_status_ind

    def clean_sms_device(self, *args, **kwargs):
        # if the user decides to opt out, then empty the device number
        sms_status_ind = self.cleaned_data.get("sms_status_ind")
        if sms_status_ind == "Y":
            return None     # sms_device = None
        sms_device = self.cleaned_data.get("sms_device")
        sms_device = empty_string_handler(sms_device)
        if not(sms_device == None or sanitization.validate_phone_num_usa(sms_device)):
            raise forms.ValidationError("Invalid phone number")

        return sms_device
