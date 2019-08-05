from django.db import models


class State(models.Model):
    id = models.CharField(db_column='STATE_ID', max_length=4, primary_key=True)
    value = models.CharField(db_column='STATE_VALUE', max_length=120, null=True)

    class Meta:
        db_table = 'STATE'
