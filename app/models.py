from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse


class User(AbstractUser):

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Player(models.Model):
    name = models.CharField(max_length=60, unique=True)
    email = models.EmailField(blank=True, null=True)
    datestamp_active_from = models.DateField()
    datestamp_active_until = models.DateField(blank=True, null=True)
    # win_count = models.SmallIntegerField(blank=True, null=True)
    # last_win_date = models.DateField(blank=True, null=True)
    active = models.BooleanField(default=True)

    def get_absolute_url(self):
        return reverse('player-detail', kwargs={'pk': self.pk})

    def __str__(self):
        return f'{self.name}'


class BonusBall(models.Model):
    ball_id = models.SmallIntegerField(primary_key=True, unique=True)
    player = models.ForeignKey(Player, on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        if self.player:
            name = self.player.name
        else:
            name = ''
        return f'{self.ball_id} {name}'


class Draw(models.Model):
    draw_date = models.DateField(unique=True)
    bonus_ball = models.ForeignKey(BonusBall, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.draw_date}: {self.bonus_ball.ball_id}"
