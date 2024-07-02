from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
# from django.contrib.auth.models import User
from models.models import ChessGame
from django.contrib.auth import get_user_model
from models.models import Player, ChessGame, ChessMove 

from channels.testing import ChannelsLiveServerTestCase
from rest_framework.authtoken.models import Token
from models.consumers import ChessConsumer
from channels.testing import WebsocketCommunicator
from django.urls import path
from channels.routing import URLRouter
from channels.db import database_sync_to_async
from models.routing import websocket_urlpatterns
import logging
import chess
from channels.layers import get_channel_layer
from asgiref.sync import sync_to_async
# you may modify the following lines
URL = '/api/v1/games/'
# do not modify the code below

User = get_user_model()

User_consumer = get_user_model()
application = URLRouter([
    path("ws/play/<int:gameID>/", ChessConsumer.as_asgi()),
])


class TestsAdditionalForApi(TestCase):

	def setUp(self):
		# API 
		ChessGame.objects.all().delete()
		self.client = APIClient()
		self.user1 = User.objects.create_user(
				username='user1', password='testpassword')
		self.user2 = User.objects.create_user(
				username='user2', password='testpassword')

	def test_001_delete_anomalous_games(self):
		"""Delete all games that have a whitePlayer or blackPlayer
		that does not exist in the User table."""
		game = ChessGame.objects.create(
				status=ChessGame.ACTIVE,
				whitePlayer=self.user1)
		game.save()
		self.client.force_authenticate(user=self.user2)
		response = self.client.post(f'{URL}', {})
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertEqual(ChessGame.objects.count(), 0) 
		self.assertEqual(response.data['detail'], 'Create Error: Anomalous games found and deleted')
			
	def test_002_check_if_there_is_active_game(self):
		"""Check if there is an active game. If there is one, create 
		should return an error. """
		game = ChessGame.objects.create(
				status=ChessGame.ACTIVE, 
				whitePlayer=self.user1, 
				blackPlayer=self.user2)
		game.save() 
		
		client2 = APIClient()
		self.client.force_authenticate(user=self.user1)
		client2.force_authenticate(user=self.user2)
		response = self.client.post(f'{URL}', {})
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertEqual(response.data['detail'], 'Create Error: Game is already active')     
        
class TestsAdditionalForModels(TestCase):  
  
		def setUp(self):
			self.player1 = Player.objects.create(username='player1', rating=1500)
			self.player2 = Player.objects.create(username='player2', rating=1600)
			self.game = ChessGame.objects.create(
					whitePlayer=self.player1,
					blackPlayer=self.player2,
					status='active',
					board_state=ChessGame.DEFAULT_BOARD_STATE,
					timeControl='10+5'
			)
		
		def test_001_get(self):
			"""Test the get method of myClassView"""
			# Create a new user
			user = User.objects.create_user(
					username='testuser',
					password='testpassword'
			)
			# Authenticate the user
			self.client.force_login(user)
			# Send a GET request
			response = self.client.get('/api/v1/myclassView/')
			# Check if the response is correct
			self.assertEqual(response.status_code, 200)
			self.assertEqual(response.json(), {'message': 'Got some data!'})
        
		def test_026_str_with_no_promotion(self):
			move = ChessMove.objects.create(
					game=self.game,
					player=self.player1,
					move_from='e2',
					move_to='e4'
			)
			self.assertEqual(str(move), 'player1 (1500): e2 -> e4')
    
		def test_027_str_with_promotion(self):
			fen = "rnbqkbnr/Pppppppp/p7/8/8/8/PPP1PPPP/RNBQKBNR w KQkq - 0 1"
			self.game.board_state = fen
			self.game.save()
			move = ChessMove(
					game=self.game,
					player=self.player1,
					move_from='a7',
					move_to='b8',
					promotion='q'
			)
			move.save()
			self.assertEqual(str(move), 'player1 (1500) a7 -> b8 q')
   
