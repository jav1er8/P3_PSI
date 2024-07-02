from django.contrib import admin
from models.models import ChessGame, ChessMove, Player
# Register your models here.


class ChessGameAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'start_time', 'end_time',
                    'timeControl', 'whitePlayer', 'blackPlayer',
                    'winner')
    list_filter = ('status', 'timeControl', 'winner')
    search_fields = ('id', 'status', 'timeControl', 'winner')
    ordering = ('-start_time',)


admin.site.register(ChessGame, ChessGameAdmin)


class ChessMoveAdmin(admin.ModelAdmin):
    list_display = ('id', 'game', 'player', 'move_from', 'move_to')
    list_filter = ('player',)
    search_fields = ('id', 'game', 'player', 'move_from', 'move_to')
    ordering = ('-id',)


admin.site.register(ChessMove, ChessMoveAdmin)


class PlayerAdmin(admin.ModelAdmin):
    list_display = ('username', 'rating')
    search_fields = ('username', )
    ordering = ('username',)


admin.site.register(Player, PlayerAdmin)
