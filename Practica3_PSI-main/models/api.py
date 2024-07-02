from djoser.views import TokenCreateView
from djoser.conf import settings
from rest_framework import viewsets, mixins, status
from models.models import ChessGame
from models.serializers import ChessGameSerializer
from rest_framework.response import Response
from random import choice
from django.db.models import Q
from rest_framework.request import Request


# Añadir user_id y rating a la respuesta ya que djoser no lo ofrece por defecto
class MyTokenCreateView(TokenCreateView):
    def _action(self, serializer):
        response = super()._action(serializer)
        tokenString = response.data['auth_token']
        tokenObject = settings.TOKEN_MODEL.objects.get(key=tokenString)
        response.data['user_id'] = tokenObject.user.id
        response.data['rating'] = tokenObject.user.rating
        return response


class ChessGameViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin,
                       viewsets.GenericViewSet):

    queryset = ChessGame.objects.all()
    serializer_class = ChessGameSerializer

    def create(self, request, *args, **kwargs):
        # Detectar anomalias -> eliminarlas en caso de que haya
        anomalous_games = ChessGame.objects.filter(
            Q(whitePlayer__isnull=True) | Q(blackPlayer__isnull=True),
            ~Q(status=ChessGame.PENDING)
        )
        if anomalous_games.exists():
            # Los elimino
            anomalous_games.delete()
            return Response({'detail': ('Create Error: '
                             'Anomalous games found and deleted')},
                            status=status.HTTP_400_BAD_REQUEST)
        
        # 1 - Verificar si hay juegos disponibles con un jugador ausente ->
        # me devuelve la primera clase de Chessgame que lo cumpla
        game = ChessGame.objects.filter(Q(whitePlayer__isnull=True) |
                                        Q(blackPlayer__isnull=True),
                                        status=ChessGame.PENDING).first()
        # 2 - Si hay una partida -> Unir al usuario a ella
        if game and game.status == ChessGame.PENDING:
            self.kwargs['pk'] = game.id
            return self.update(request, *args, **kwargs, game_instance=game)
        else:
            # 2.1 - Crear una partida nueva y establecer estado a pending
            mutable_data = request.data.copy()
            mutable_data['status'] = ChessGame.PENDING

            # Asignar aleatoriamente el color
            if choice([True, False]):
                mutable_data['whitePlayer'] = request.user.id
            else:
                mutable_data['blackPlayer'] = request.user.id

            # Crear una nueva instancia de Request con los datos modificados
            new_request = Request(request._request)
            new_request._full_data = mutable_data
            return super().create(new_request, *args, **kwargs)

    # Unir al jugador a un juego existente
    def update(self, request, *args, **kwargs):
        game = kwargs.get('game_instance')

        # 1 - Cambio el estado a active
        game.status = ChessGame.ACTIVE

        # 2 - Asigna al usuario actual como el jugador
        # opuesto al que ya está en el juego
        # request.user = usuario que hizo la solicitud
        if game.whitePlayer is None:
            game.whitePlayer = request.user
        elif game.blackPlayer is None:
            game.blackPlayer = request.user

        game.save()
        return super().update(request, *args, **kwargs)
