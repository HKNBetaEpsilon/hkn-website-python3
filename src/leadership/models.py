from __future__ import unicode_literals

from users.models import Member

from django.db import models


# Create your models here.

class Leader(models.Model):
    POSITION_TYPE = (
        ('O', 'Officer'),
        ('A', 'Advisor'),
        ('C', 'Chair'),
    )

    position = models.CharField(max_length=100)
    member = models.ForeignKey(Member, null=True, blank=True, on_delete=models.SET_NULL)
    position_type = models.CharField(max_length=1, choices=POSITION_TYPE, default='C')
    email = models.CharField(max_length=100, default='hkn-officers@umich.edu')
    description = models.CharField(max_length=140, default='Hi I\'m an officer')
    display_order = models.IntegerField(default=0)

    def __str__(self):
        return self.position
