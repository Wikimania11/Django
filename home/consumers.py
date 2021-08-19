import logging
logger = logging.getLogger(__name__)
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.db import connection
import json
import time

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        # метод отправки всех диалогов
        # дальше метод по отправке всех сообщений из диалога, на который нажал пользователь

        self.room_name = self.scope['url_route']['kwargs']['room_id']
        logger.warning('room_name' + str(self.scope['url_route']))
        self.room_group_name = 'chat_%s' % self.room_name

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    def receive(self, text_data):
        #  отправка сообщения от пользователя
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        user2_id = text_data_json['user2_id']
        id_pair = text_data_json['id_pair']


        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM Pair WHERE id = {id_pair}")
        psd = cursor.fetchone() #
        if psd[2] == user2_id :
            time.sleep(1)
            print(90)
            cursor.execute(f"INSERT INTO Message (id_pair, text, is_read, direction1_2) VALUES (%s, %s, 1, 0)",(id_pair, message))
            user_id = psd[1]
            group_id = psd[4]

        else:
            time.sleep(1)
            cursor.execute(f"INSERT INTO Message (id_pair, text, is_read, direction1_2) VALUES (%s, %s, 1, 1)",(id_pair, message))
            print(91)
            user_id = psd[2]
            group_id = psd[3]

        # Send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'user_id': user_id,
                'group_id': group_id
            }
        )

    # Receive message from room group
    def chat_message(self, event):
        message = event['message']
        user_id = event['user_id']
        group_id = event['group_id']
        logger.warning('message' + message)

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'message': message,
            'user_id': user_id,
            'group_id': group_id
        }))
