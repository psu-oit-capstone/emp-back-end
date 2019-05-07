from django.db import models


class Emergency(models.Model):
    # Unique person identifier
    pidm = models.IntegerField(db_column='ZGBNNN_PIDM', primary_key=True)

    # Does this person need assistance evacuating the building
    evacuation_assistance = models.CharField(db_column='ZGBNNN_REQ_ASSIST', max_length=4, null=True)

    # Email addresses that receive PSU Alerts (campus email is read-only)
    external_email = models.CharField(db_column='ZGBNNN_EMAIL_ADDRESS', max_length=512, null=True)
    campus_email = models.CharField(db_column='ZGBNNN_EMAIL_ADDRESS2', max_length=512, null=True)

    # Voice message numbers
    primary_phone = models.CharField(db_column='ZGBNNN_MOBILE_PHONE', max_length=72, null=True)
    alternate_phone = models.CharField(db_column='ZGBNNN_BUSINESS_PHONE', max_length=72, null=True)

    # Text message number and opt-out status
    sms_status_ind = models.CharField(db_column='ZGBNNN_SMS_STATUS_IND', max_length=4, null=True)
    sms_device = models.CharField(db_column='ZGBNNN_SMS_DEVICE_1', max_length=72, null=True)

    # Date of last update
    activity_date = models.DateTimeField(db_column='ZGBNNN_ACTIVITY_DATE', auto_now=True, null=True)

    class Meta:
        db_table = 'ZGBNNN'
