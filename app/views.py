import hashlib
import hmac
import os

import git
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import HttpResponse
from django.http.response import JsonResponse
from django.shortcuts import HttpResponseRedirect, render
from django.urls import reverse
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django_htmx.http import HttpResponseClientRefresh
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from app.custom_logger import logger
from .forms import PlayerForm, PlayerUpdateForm, DrawForm, DrawUpdateForm
from .models import BonusBall, Player, Draw

w_secret = os.environ.get('GIT_HOOK_SECRET', '')


# pylint: disable=line-too-long
# https://simpleisbetterthancomplex.com/tutorial/2018/11/22/how-to-implement-token-authentication-using-django-rest-framework.html

class HelloView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        content = {'message': 'Hello, World!'}
        return Response(content)


class PostResult(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        if request.method == 'POST':
            try:
                data = JSONParser().parse(request)
                bonus_ball = data['bonus_ball']
                draw_date = data['draw_date']
                logger.debug('Received request with data: %s', data)
                logger.info('Draw for %s received with bonus ball %s', draw_date, bonus_ball)
                # pylint:disable=invalid-name
                bb = BonusBall.objects.get(pk=bonus_ball)
                draw = Draw.objects.create(draw_date=draw_date, bonus_ball=bb)
                logger.info('Draw for %s with bonus ball %s saved. ', draw.draw_date, draw.bonus_ball.ball_id)

                draw = Draw.objects.values('bonus_ball_id', 'draw_date', 'bonus_ball__player__name').order_by(
                    "-draw_date").annotate(  # works
                    wins=Count('bonus_ball__player__bonusball__draw')).first()

                context = {"draw": draw}
                logger.info(context)
                return JsonResponse(context, status=status.HTTP_201_CREATED)
            except Exception as exception:  # pylint: disable=broad-exception-caught
                return JsonResponse({'error': str(exception)}, status=status.HTTP_400_BAD_REQUEST)
        return JsonResponse({'error': 'Invalid request, method must be POST'}, status=status.HTTP_400_BAD_REQUEST)


def is_valid_signature(x_hub_signature, data, private_key):
    # x_hub_signature and data are from the webhook payload
    # private key is your webhook secret
    hash_algorithm, github_signature = x_hub_signature.split('=', 1)
    algorithm = hashlib.__dict__.get(hash_algorithm)
    encoded_key = bytes(private_key, 'latin-1')
    mac = hmac.new(encoded_key, msg=data, digestmod=algorithm)
    return hmac.compare_digest(mac.hexdigest(), github_signature)


@csrf_exempt
def update_app(request):
    """
    Updates the codebase from the git repo.
    """
    if request.method == "POST":

        x_hub_signature = request.headers.get('X-Hub-Signature')

        if not is_valid_signature(x_hub_signature, request.body, w_secret):
            return HttpResponse(f'Deploy signature failed: {x_hub_signature}')

        repo = git.Repo("wv-lottery/")
        origin = repo.remotes.origin
        origin.pull()
        return HttpResponse("Updated code on PythonAnywhere")

    return HttpResponse("Couldn't update the code on PythonAnywhere")


@login_required
def index(request):
    draw = Draw.objects.all().order_by("-draw_date").annotate(wins=Count('bonus_ball__player__bonusball__draw'))

    context = {
        'draws': draw,
    }

    return render(request, "app/index.html", context)


@login_required
def latest_result(request):
    draw = Draw.objects.order_by("-draw_date").annotate(wins=Count('bonus_ball__player__bonusball__draw')).first()

    context = {
        'draw': draw,
    }

    return render(request, "app/latest_result.html", context)


@login_required
def players(request):
    players_list = Player.objects.prefetch_related('bonusball_set').filter(active=True).order_by("name").annotate(
        draws=Count('bonusball__draw')
    )

    context = {
        'players': players_list,
    }

    return render(request, "app/players.html", context)


# pylint: disable=too-many-ancestors
class DrawCreateView(CreateView):
    model = Draw
    form_class = DrawForm
    success_url = reverse_lazy('index')


# pylint: disable=too-many-ancestors
class DrawUpdateView(UpdateView):
    model = Draw
    form_class = DrawUpdateForm
    success_url = reverse_lazy('index')


# pylint: disable=too-many-ancestors
class DrawDeleteView(DeleteView):
    model = Draw
    success_url = reverse_lazy('index')


class PlayerCreateView(CreateView):
    model = Player
    form_class = PlayerForm
    success_url = reverse_lazy('players')


# pylint: disable=too-many-ancestors
class PlayerUpdateView(UpdateView):
    model = Player
    form_class = PlayerUpdateForm
    success_url = reverse_lazy('players')


# pylint: disable=too-many-ancestors
class PlayerDeleteView(DeleteView):
    model = Player
    success_url = reverse_lazy('players')


@login_required
def numbers(request):
    # pylint:disable=invalid-name
    bb = BonusBall.objects.all().order_by("ball_id")
    used_bb = BonusBall.objects.exclude(player=None)
    unused_bb = BonusBall.objects.filter(player=None)

    context = {
        'numbers': bb,
        'unused_numbers': unused_bb,
        'used_numbers': used_bb,
    }

    return render(request, "app/numbers.html", context)


# pylint: disable=inconsistent-return-statements
@csrf_exempt
@login_required
def edit_number__player(request, pk):  # pylint:disable=invalid-name
    if request.method == "GET":
        # pylint:disable=invalid-name
        bb = BonusBall.objects.get(pk=pk)
        players_list = Player.objects.filter(active=True).order_by('name')

        return render(request, "app/edit_bonus_ball__player_partial.html", context={
            'number': bb,
            'players': players_list,
        })
    elif request.method == "POST":
        bb_to_edit = BonusBall.objects.get(pk=pk)

        if request.POST['selected_player_id'] == '0':
            new_player = None
        else:
            new_player = Player.objects.get(id=request.POST['selected_player_id'])

        bb_to_edit.player = new_player
        bb_to_edit.save(update_fields=['player'])

        return HttpResponseClientRefresh()


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "app/sign_in.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "app/sign_in.html")


def logout_view(request):
    logout(request)
    return render(request, "app/sign_in.html")
