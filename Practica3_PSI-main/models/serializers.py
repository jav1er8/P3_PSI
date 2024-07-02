from rest_framework import serializers
from models.models import ChessGame, ChessMove, Player


class ChessGameSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChessGame
        fields = '__all__'


class ChessMoveSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChessMove
        fields = '__all__'


class PlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        fields = '__all__'
