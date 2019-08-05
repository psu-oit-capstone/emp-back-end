from django.db import models

# should we put foreign keys on this model?
class Contact(models.Model):
    # Primary key
    surrogate_id = models.IntegerField(db_column='SPREMRG_SURROGATE_ID', primary_key=True)

    # Personal identifier
    pidm = models.IntegerField(db_column='SPREMRG_PIDM')

    # Contact priority
    priority = models.CharField(db_column='SPREMRG_PRIORITY', max_length=4)

    # Contact's relation to this person
    relt_code = models.CharField(db_column='SPREMRG_RELT_CODE', max_length=4, null=True)

    # Contact name
    last_name = models.CharField(db_column='SPREMRG_LAST_NAME', max_length=240)
    first_name = models.CharField(db_column='SPREMRG_FIRST_NAME', max_length=240)
    mi = models.CharField(db_column='SPREMRG_MI', max_length=240, null=True)

    # Contact address
    street_line1 = models.CharField(db_column='SPREMRG_STREET_LINE1', max_length=300, null=True)
    street_line2 = models.CharField(db_column='SPREMRG_STREET_LINE2', max_length=300, null=True)
    street_line3 = models.CharField(db_column='SPREMRG_STREET_LINE3', max_length=300, null=True)
    city = models.CharField(db_column='SPREMRG_CITY', max_length=200, null=True)
    stat_code = models.CharField(db_column='SPREMRG_STAT_CODE', max_length=12, null=True)
    natn_code = models.CharField(db_column='SPREMRG_NATN_CODE', max_length=20, null=True)
    zip = models.CharField(db_column='SPREMRG_ZIP', max_length=120, null=True)

    # Contact phone number
    ctry_code_phone = models.CharField(db_column='SPREMRG_CTRY_CODE_PHONE', max_length=16, null=True)
    phone_area = models.CharField(db_column='SPREMRG_PHONE_AREA', max_length=24, null=True)
    phone_number = models.CharField(db_column='SPREMRG_PHONE_NUMBER', max_length=48, null=True)
    phone_ext = models.CharField(db_column='SPREMRG_PHONE_EXT', max_length=40, null=True)

    # Date of last update
    activity_date = models.DateTimeField(db_column='SPREMRG_ACTIVITY_DATE', auto_now=True)

    class Meta:
        db_table = 'SPREMRG'
