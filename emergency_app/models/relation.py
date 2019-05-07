from django.db import models


class Relation(models.Model):
    code = models.CharField(db_column='STVRELT_CODE', max_length=4, primary_key=True)
    description = models.CharField(db_column='STVRELT_DESC', max_length=120, null=True)

    class Meta:
        db_table = 'STVRELT'
