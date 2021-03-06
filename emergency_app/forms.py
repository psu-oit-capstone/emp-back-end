# Taken from this video:
# https://www.youtube.com/watch?v=wVnQkKf-gHo
from django import forms
# from emergency_app.models.identity import Identity
from emergency_app.models.contact import Contact
from emergency_app.models.emergency import Emergency
from emergency_app.models.nation import Nation
# from emergency_app.models.state import State
from common.util import sanitization

# When required field=false, clean() would normalize empty value of CharField into empty string
# However, null value was needed to follow the sample data provided. Therefore, this function is declared.
# alternatively, to_python function for each field could use this function.
# Source: https://docs.djangoproject.com/en/2.2/ref/forms/fields/
def empty_string_handler(field):
    # if field either empty string or empty/null value
    if not(str(field)) or str(field) in ("", "null", "N/A"):
        return None
    else:
        return field

# Form for validating the request update of user's emergency contact
class UpdateEmergencyContactForm(forms.ModelForm):
    # Provide an example of the schema of the model
    # pidm was needed to search all contacts related to related user.
    pidm = forms.IntegerField()
    surrogate_id = forms.IntegerField(required=False)
    priority = forms.CharField(max_length=4)
    relt_code = forms.CharField(max_length=4, required=False)
    last_name = forms.CharField(max_length=240)
    first_name = forms.CharField(max_length=240)
    mi = forms.CharField(max_length=240, required=False)

    street_line1 = forms.CharField(max_length=75, required=False)
    street_line2 = forms.CharField(max_length=75, required=False)
    street_line3 = forms.CharField(max_length=75, required=False)
    city = forms.CharField(max_length=50, required=False)
    stat_code = forms.CharField(max_length=3, required=False)
    natn_code = forms.CharField(max_length=5, required=False)
    zip = forms.CharField(max_length=30, required=False)
    ctry_code_phone = forms.CharField(max_length=16, required=False)
    phone_area = forms.CharField(max_length=6, required=False)
    phone_number = forms.CharField(max_length=12, required=False)
    phone_ext = forms.CharField(max_length=10, required=False)

    class Meta:
        model = Contact
        fields = [
            'pidm', 'surrogate_id', 'priority', 'relt_code',
            'last_name', 'first_name', 'mi',
            'street_line1', 'street_line2', 'street_line3',
            'city', 'stat_code', 'natn_code', 'zip',
            'ctry_code_phone', 'phone_area', 'phone_number', 'phone_ext'
        ]

    # clean() for validating fields that depend on each other, this function apparently runs after clean_<field_name>() got executed
    def clean(self):
        self.cleaned_data = super(UpdateEmergencyContactForm, self).clean()
        # checking whether given surrogate id is actually in database.
        surrogate_id = self.cleaned_data.get("surrogate_id")
        pidm = self.cleaned_data.get("pidm")
        if surrogate_id:
            try:
                Contact.objects.get(surrogate_id=surrogate_id, pidm=pidm)
            except Contact.DoesNotExist:
                print("Invalid Surrogate ID. ")
                raise forms.ValidationError("Invalid Surrogate ID")

        # checking whether given priority is actually in the correct range (1 to (n+1)) for new entry
        # and range (1 to n) for old entry (the one with surrogate id given correctly)
        priority = self.cleaned_data.get("priority")
        entries = Contact.objects.filter(pidm=pidm)
        if not priority:
            print("Missing priority number. ")
            raise forms.ValidationError("Missing priority number")
        if (not surrogate_id and not(1 <= int(priority) <= (len(entries) + 1)) or
            (surrogate_id and not(1 <= int(priority) <= len(entries)))):
            print("Invalid priority number. ")
            raise forms.ValidationError("Invalid priority number")

        # empty string handler for the rest fields
        # this seems ugly, it's probably better to use clean_<field_name>() for each of these fields.
        for field in self.cleaned_data:
            try:
                # since these fields are handled manually, skipping these two
                if field not in ("relt_code", "natn_code", "stat_code"):
                    self.cleaned_data[field] = empty_string_handler(self.cleaned_data[field])
            except NameError:
                self.cleaned_data[field] = None

        # checking whether given address is complete (street line1, city, and either state + zip or country) or completely empty
        street_line1 = self.cleaned_data.get("street_line1")
        city = self.cleaned_data.get("city")
        stat_code = self.cleaned_data.get("stat_code")
        zip = self.cleaned_data.get("zip")
        natn_code = self.cleaned_data.get("natn_code")
        if (street_line1 or city or stat_code or zip or natn_code):
            print("Invalid address, need street_line1, city, and either stat_code + zip or natn_code be filled correctly.")
            if not street_line1:
                print("Invalid street line1. ")
                raise forms.ValidationError('street_line1', "Address field is required")
            if not city:
                print("Invalid city. ")
                raise forms.ValidationError('city', "City field is required")
            if not natn_code and not(stat_code and zip):
                print("Invalid natn_code or stat_code + zip. ")
                raise forms.ValidationError("Nation field, or State + Zip fields is/are required")

        # commenting validations related to USA option part since it needs more revisions
        """
        # checking specifically for USA country, whether given state, zip, and phone number are correct or completely empty.
        # need revisions since it's complicated on implementation
        if natn_code == Nation.objects.get(value="USA").id: # alternatively, == "LUS":
            if not(stat_code is None or stat_code != "00")):
                print("Invalid stat_code")
                raise forms.ValidationError("Invalid state code")
            if not(zip is None or sanitization.validate_zip_usa(zip)):
                print("Invalid zip")
                raise forms.ValidationError("Invalid zip code")
            # this if statement is weird, but OIT website behaves like this
            if stat_code and not zip:
                print("Invalid natn_code or stat_code + zip. ")
                raise forms.ValidationError("Nation field, or State + Zip fields is/are required")
            # Below phone number validation is not completely true, people live in USA may have phone number from foreign country
            # may add if ctry_code_phone == Nation.objects.get(value="USA").phone_code but Canada adds more complication
            phone_area = self.cleaned_data.get("phone_area")
            phone_number = self.cleaned_data.get("phone_number")
            if ((phone_area or phone_number) and
                not(len(phone_area) == 3 and len(phone_number) == 7 and
                    sanitization.validate_phone_num_usa(phone_area + phone_number))):
                print("Invalid phone area + number. ")
                raise forms.ValidationError("Invalid phone area and number")
        """

        return self.cleaned_data
        # Possible TODOs: check validity of address, city and state based on zipcode

    # clean_<field_name>() function is reponsible to validate one specific field.
    def clean_relt_code(self, *args, **kwargs):
        relt_code = self.cleaned_data.get("relt_code")
        relt_code = empty_string_handler(relt_code)
        if not(relt_code is None or sanitization.validate_relation(relt_code)):
            print("Invalid relation code. ")
            raise forms.ValidationError("Invalid relation code")

        return relt_code

    # adding this field validation since all state values are based on the table list anyway
    def clean_stat_code(self, *args, **kwargs):
        stat_code = self.cleaned_data.get("stat_code")
        stat_code = empty_string_handler(stat_code)
        if not(stat_code is None or sanitization.validate_state_usa(stat_code)):
            print("Invalid stat_code. ")
            raise forms.ValidationError("Invalid state code")

        return stat_code

    def clean_natn_code(self, *args, **kwargs):
        natn_code = self.cleaned_data.get("natn_code")
        natn_code = empty_string_handler(natn_code)
        if not(natn_code is None or sanitization.validate_nation_code(natn_code)):
            print("Invalid natn_code. ")
            raise forms.ValidationError("Invalid nation code")

        return natn_code

    def clean_ctry_code_phone_code(self, *args, **kwargs):
        ctry_code_phone_code = self.cleaned_data.get("ctry_code_phone_code")
        ctry_code_phone_code = empty_string_handler(ctry_code_phone_code)
        if not(ctry_code_phone_code is None or sanitization.validate_country_phone_code(ctry_code_phone_code)):
            print("Invalid ctry_code_phone_code. ")
            raise forms.ValidationError("Invalid country phone code")

        return ctry_code_phone_code


# Form for validating the request update of user's evacuation assistance
class SetEvacuationAssistanceForm(forms.ModelForm):
    evacuation_assistance = forms.CharField(max_length=4)

    class Meta:
        model = Emergency
        fields = [
            'evacuation_assistance'
        ]

    def clean_evacuation_assistance(self, *args, **kwargs):
        evacuation_assistance = self.cleaned_data.get("evacuation_assistance")
        # since evacuation assistance form must submit some values, evacuation_assistance should not be None
        # hence, skipping empty_string_handler function
        if not(sanitization.validate_checkbox(evacuation_assistance)):
            print("Invalid checkbox evacuation_assistance. ")
            raise forms.ValidationError("Invalid checkbox value")

        return evacuation_assistance

# Form for validating the request update of user's emergency notifications
class SetEmergencyNotificationsForm(forms.ModelForm):
    external_email = forms.CharField(max_length=128, required=False)
    primary_phone = forms.CharField(max_length=72, required=False)
    alternate_phone = forms.CharField(max_length=72, required=False)
    sms_status_ind = forms.CharField(max_length=4)
    sms_device = forms.CharField(max_length=72, required=False)

    class Meta:
        model = Emergency
        fields = [
            'external_email', 'primary_phone', 'alternate_phone', 'sms_status_ind', 'sms_device'
        ]

    def clean_external_email(self, *args, **kwargs):
        external_email = self.cleaned_data.get("external_email")
        external_email = empty_string_handler(external_email)
        if not(external_email is None or sanitization.validate_email(external_email)):
            print("Invalid external email. ")
            raise forms.ValidationError("Invalid email")

        return external_email

    def clean_primary_phone(self, *args, **kwargs):
        primary_phone = self.cleaned_data.get("primary_phone")
        primary_phone = empty_string_handler(primary_phone)
        if not(primary_phone is None or sanitization.validate_phone_num_usa(primary_phone)):
            print("Invalid primary phone number. ")
            raise forms.ValidationError("Invalid phone number")

        return primary_phone

    def clean_alternate_phone(self, *args, **kwargs):
        alternate_phone = self.cleaned_data.get("alternate_phone")
        alternate_phone = empty_string_handler(alternate_phone)
        if not(alternate_phone is None or sanitization.validate_phone_num_usa(alternate_phone)):
            print("Invalid alternate phone. ")
            raise forms.ValidationError("Invalid phone number")

        return alternate_phone

    def clean_sms_status_ind(self, *args, **kwargs):
        sms_status_ind = self.cleaned_data.get("sms_status_ind")
        sms_status_ind = empty_string_handler(sms_status_ind)
        # since sms_status_ind must be submitted with a value, it should not be none
        if not(sanitization.validate_checkbox(sms_status_ind)):
            print("Invalid checkbox sms_status_ind. ")
            raise forms.ValidationError("Invalid checkbox value")

        return sms_status_ind

    # probably better placing this function in clean() instead, since it's dependent on another field.
    def clean_sms_device(self, *args, **kwargs):
        # if the user decides to opt out, then empty the device number
        sms_status_ind = self.cleaned_data.get("sms_status_ind")
        if sms_status_ind == "Y":
            return None     # sms_device = None
        sms_device = self.cleaned_data.get("sms_device")
        sms_device = empty_string_handler(sms_device)
        if not(sms_device is None or sanitization.validate_phone_num_usa(sms_device)):
            print("Invalid sms_device phone number. ")
            raise forms.ValidationError("Invalid phone number")

        return sms_device
