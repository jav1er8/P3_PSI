import json
import chess

from channels.generic.websocket import WebsocketConsumer
from rest_framework.authtoken.models import Token
from asgiref.sync import async_to_sync
from models.models import ChessGame, ChessMove, Player


class ChessConsumer(WebsocketConsumer):

    def connect(self):
        self.gameID = self.scope['url_route']['kwargs']['gameID']
        self.room_group_name = str(self.gameID)
        self.token_key = self.scope['query_string'].decode()

        # Join room group
        async_to_sync(self.accept())
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name)

        # Comprueba si el token es válido
        if self.validate_token(self.token_key) is False:
            message = 'Invalid token. Connection not authorized.'
            self.send_error(message)

        # Comprueba si el game id es válido
        if not ChessGame.objects.filter(id=self.room_group_name).exists():
            message = f'Invalid game with id {self.room_group_name}'
            self.send_error(message)

        self.user_id = self.get_token_from_user(self.token_key)
        # Comprueba si el usuario es válido del game_id
        if self.validate_user_in_game(self.gameID) is False:
            message = f'Invalid game with id {self.gameID}'
            self.send_error(message)

        # Añade el canal del cliente al grupo "room_group_name" -> asi se puede
        # enviar mensajes a todos los clientes en el mismo juego
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name)

        try:
            game = ChessGame.objects.get(id=self.gameID)
        except ChessGame.DoesNotExist:
            self.send_error(f'Error: game with id {self.gameID} \
                                does not exist')
            return

        if game.whitePlayer and game.blackPlayer and game.status != 'finished':
            game.status = 'active'
            game.save()
            status = 'active'
        else:
            status = 'pending'

        # Enviar un mensaje después de aceptar la conexión
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'game_cb',
                'message': {
                    'type': 'game',
                    'message': 'OK',
                    'status': status,
                    'playerID': self.user_id
                }
            }
        )
        return

    def disconnect(self, close_code):
        """
        This method is called when the WebSocket connection is closed.
        It removes the channel from the room group.
        """
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name)

    # 2º Peticion y cualquiera -> la maneja receive
    def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')

        game = ChessGame.objects.get(id=self.gameID)
        if game.status != 'active':
            async_to_sync(self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Error: invalid move (game is not active)'
            })))
            return

        if message_type == 'move':
            # Extraccion de los datos
            _from = data.get('from')
            to = data.get('to')
            playerID = data.get('playerID')
            promotion = data.get('promotion')

            # Comprueba si el movimiento es válido
            valid = self.validate_move_in_game(_from, to, playerID, promotion)
            if valid is False:
                self.send_error(f'Error: invalid move {_from}{to}')
                return

            # Si el movimiento es válido, lo almacena en la base de datos
            player = Player.objects.get(id=self.user_id)
            game = ChessGame.objects.get(id=self.gameID)
            chess_move = ChessMove(move_from=_from, move_to=to,
                                   game=game, player=player,
                                   promotion=promotion)
            board = chess.Board(game.board_state)

            # Comprueba si el movimiento finaliza el juego
            if board.is_checkmate() or board.is_stalemate() \
               or board.is_insufficient_material():
                # Si el juego ha terminado, cambia el estado del juego
                # a 'finished'
                game.status = 'finished'
                game.save()
            chess_move.save()
            # Envía el movimiento a todos los jugadores en el mismo juego
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'move_cb',
                    'message':
                    {
                        'type': 'move',
                        'from': _from,
                        'to': to,
                        'playerID': playerID,
                        'promotion': promotion
                    }
                }
            )

        return

    def game_cb(self, event):
        """ This method is called when the server sends a message
        to the WebSocket connection. It sends the message to the client.
        """
        message = event['message']['message']
        status = event['message']['status']
        playerID = event['message']['playerID']

        # Send message to WebSocket
        async_to_sync(self.send(text_data=json.dumps({
            'type': 'game',
            'message': message,
            'status': status,
            'playerID': playerID
        })))

    def move_cb(self, event):
        # Extrae los detalles del movimiento del evento
        _from = event['message']['from']
        to = event['message']['to']
        playerID = event['message']['playerID']
        promotion = event['message']['promotion']
        type = event['message']['type']

        # Envía el movimiento a todos los jugadores en el mismo juego
        async_to_sync(self.send(text_data=json.dumps({
            'type': type,
            'from': _from,
            'to': to,
            'playerID': playerID,
            'promotion': promotion
        })))

    # Obtener user_id a partir del token
    def get_token_from_user(self, token_key):
        try:
            token = Token.objects.get(key=token_key)
            return token.user_id
        except Token.DoesNotExist:
            return None

    # Comprobar si el token es válido
    def validate_token(self, token_key):
        return Token.objects.filter(key=token_key).exists()

    # Comprobar si el usuario en el game es valido
    def validate_user_in_game(self, game_id):
        if ChessGame.objects.filter(id=game_id,
                                    whitePlayer=self.user_id).exists() or \
           ChessGame.objects.filter(id=game_id,
                                    blackPlayer=self.user_id).exists():
            return True
        return False

    # Comprueba si el movimiento es válido
    def validate_move_in_game(self, _from, to, playerID, promotion):
        game = ChessGame.objects.get(id=self.gameID)
        board = chess.Board(game.board_state)
        mo = chess.Move.from_uci(_from + to + (promotion if promotion else ''))
        if mo not in board.legal_moves:
            return False
        return True

    # Mandar error
    def send_error(self, message):
        async_to_sync(self.send(text_data=json.dumps({
            'type': 'error',
            'message': message
        })))
        return
