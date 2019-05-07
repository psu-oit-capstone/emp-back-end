from django.db import models


class Identity(models.Model):
    # Unique person identifier
    pidm = models.IntegerField(db_column='ZGBIDMP_PIDM', primary_key=True)

    # Username
    username = models.CharField(db_column='ZGBIDMP_USERNAME', max_length=120, null=True)

    # Campus email
    email = models.CharField(db_column='ZGBIDMP_EMAIL', max_length=512, null=True)

    # Name
    first_name = models.CharField(db_column='ZGBIDMP_FIRST_NAME', max_length=240, null=True)
    last_name = models.CharField(db_column='ZGBIDMP_LAST_NAME', max_length=240, null=True)
    mi = models.CharField(db_column='ZGBIDMP_MI', max_length=240, null=True)

    class Meta:
        db_table = 'ZGBIDMP'
