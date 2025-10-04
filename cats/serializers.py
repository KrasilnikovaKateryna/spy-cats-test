from rest_framework import serializers

from cats.models import SpyCat


class SpyCatSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpyCat
        fields = ['id', 'name', 'years_of_experience', 'breed', 'salary']

class UpdateSpyCatSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpyCat
        fields = ['salary']