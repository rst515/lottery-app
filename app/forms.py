import datetime

from django import forms

from .models import Player, Draw, BonusBall


class DrawForm(forms.ModelForm):
    draw_date = forms.DateField(
        initial=datetime.date.today,
        widget=forms.SelectDateWidget,
        label="Draw date"
    )
    bonus_ball = forms.ModelChoiceField(BonusBall.objects.order_by('ball_id'))

    # pylint: disable=[too-few-public-methods
    class Meta:
        model = Draw
        fields = ('draw_date', 'bonus_ball')


class DrawUpdateForm(forms.ModelForm):
    draw_date = forms.DateField(
        initial=datetime.date.today,
        widget=forms.SelectDateWidget,
        label="Draw date"
    )
    bonus_ball = forms.ModelChoiceField(BonusBall.objects.order_by('ball_id'))

    # pylint: disable=[too-few-public-methods
    class Meta:
        model = Draw
        fields = ('draw_date', 'bonus_ball')


class PlayerForm(forms.ModelForm):
    datestamp_active_from = forms.DateField(
        initial=datetime.date.today,
        widget=forms.SelectDateWidget,
        label="Active from"
    )

    # pylint: disable=[too-few-public-methods
    class Meta:
        model = Player
        fields = ('name', 'datestamp_active_from')


class PlayerUpdateForm(forms.ModelForm):
    datestamp_active_from = forms.DateField(
        initial=datetime.date.today,
        widget=forms.SelectDateWidget,
        label="Active from"
    )

    # datestamp_active_until = forms.DateField(
    #     required=False,
    #     widget=forms.SelectDateWidget,
    #     label="Active until"
    # )
    # pylint: disable=[too-few-public-methods
    class Meta:
        model = Player
        fields = ('name', 'datestamp_active_from')  # , 'datestamp_active_until', 'active')
