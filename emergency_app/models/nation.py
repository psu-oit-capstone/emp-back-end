from django.db import models


class Nation(models.Model):
    id = models.CharField(db_column='NATION_ID', max_length=4, primary_key=True)
    value = models.CharField(db_column='NATION_VALUE', max_length=120, null=True)

    class Meta:
        db_table = 'NATION'
