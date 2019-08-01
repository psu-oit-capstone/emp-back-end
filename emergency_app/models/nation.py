from django.db import models


class Nation(models.Model):
    id = models.CharField(db_column='NATION_ID', max_length=4, primary_key=True)
    value = models.CharField(db_column='NATION_VALUE', max_length=120, null=True)
    phone_code = models.CharField(db_column='NATION_PHONE_CODE', max_length=16, null=True)
    svgimg = models.CharField(db_column='NATION_SVGIMG', max_length=72, null=True)

    class Meta:
        db_table = 'NATION'
