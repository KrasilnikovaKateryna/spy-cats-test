from django.db import models
from django_countries.fields import CountryField

from cats.models import SpyCat


class Mission(models.Model):
    cat = models.ForeignKey(SpyCat, on_delete=models.SET_NULL, related_name='missions', null=True, blank=True)

    @property
    def is_completed(self) -> bool:
        return not self.targets.filter(completed=False).exists()


class Target(models.Model):
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE, related_name="targets")
    name = models.CharField(max_length=255)
    country = CountryField()
    completed = models.BooleanField(default=False)


class Note(models.Model):
    target = models.OneToOneField(Target, on_delete=models.CASCADE, related_name="note")
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
