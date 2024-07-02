from django.db import models

# Create your models here.
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.models import AbstractUser
import chess


class myClassView(APIView):

    def get(self, request):
        # Devuelve json ya que hereda APIView
        return Response({'message': 'Got some data!'})


class Player(AbstractUser):
    # Default user class, just in case we want to add
    # something extra in he future
    # add extra fields here
    rating = models.IntegerField(default=-1)

    def __str__(self):
        return f'{self.username} ({self.rating})'


class ChessGame(models.Model):
    ACTIVE = 'active'
    PENDING = 'pending'
    FINISHED = 'finished'

    STATUS_CHOICES = [
        (PENDING, 'pending'),
        (ACTIVE, 'active'),
        (FINISHED, 'finished')
    ]

    DEFAULT_BOARD_STATE = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR \
                            w KQkq - 0 1'

    id = models.AutoField(primary_key=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES,
                              default='pending')
    board_state = models.TextField(default=DEFAULT_BOARD_STATE)   # Formato FEN
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    timeControl = models.CharField(max_length=15, default='30')
    whitePlayer = models.ForeignKey(Player, on_delete=models.CASCADE,
                                    related_name='whitePlayer', 
                                    null=True, 
                                    blank=True)
    blackPlayer = models.ForeignKey(Player, on_delete=models.CASCADE,
                                    related_name='blackPlayer', 
                                    null=True, blank=True)
    winner = models.ForeignKey(Player, on_delete=models.SET_NULL,
                               related_name='winner', null=True, 
                               blank=True)

    def __str__(self):
        # board = chess.Board(self.board_state)
        # Crea un tablero de ajedrez con el estado actual
        whitePlayer = (
            f'{self.whitePlayer.username} ({self.whitePlayer.rating})'
            if self.whitePlayer
            else 'unknown'
            )
        blackPlayer = (
            f'{self.blackPlayer.username} ({self.blackPlayer.rating})'
            if self.blackPlayer
            else 'unknown'
        )
        return f'GameID=({self.id}) {whitePlayer} vs {blackPlayer}'

# CASCADE: si se borra un jugador se borran
# todas las partidas en las que participa
# SET_NULL: si se borra un jugador se pone a null el campo winner


class ChessMove(models.Model):
    id = models.AutoField(primary_key=True)
    game = models.ForeignKey(ChessGame, on_delete=models.CASCADE,
                             related_name='moves')
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    move_from = models.CharField(max_length=2)
    move_to = models.CharField(max_length=2)
    promotion = models.CharField(max_length=1, null=True, blank=True)

    def save(self, *args, **kwargs):
        self.game.refresh_from_db()
        if self.game.status == 'active':
            fen_board = chess.Board(self.game.board_state)
            coords = str(self.move_from)+str(self.move_to)
            if self.promotion:
                coords = coords + str(self.promotion)
            move = chess.Move.from_uci(coords)
            if move not in fen_board.legal_moves:
                raise ValueError("Error, accion ilegal")
            else:
                fen_board.push(move)
                self.game.board_state = fen_board.fen()
                self.game.save()
                super().save(*args, **kwargs)

    def __str__(self):
        if self.promotion:
            return (f'{self.player} {self.move_from} -'
                    f'> {self.move_to} {self.promotion}')
        return f'{self.player}: {self.move_from} -> {self.move_to}'
