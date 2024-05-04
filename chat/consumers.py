import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from chat.models import UserProfile

class ChatConsumer(WebsocketConsumer):
    """
    Description: This consumer is used to send and receive messages between two users.
    A user will send a message ('message') along with the username ('to') of friend to send the message to the friend, also the user will send a message ('destroy') to destroy the message.
        'destroy' contains seconds after which the message will be destroyed.
    If the friend is online, the message will be sent to the friend and the user will receive a message with status 'received'.
    """
    http_user_and_session = True
    def connect(self):
        user = self.scope["user"]
        UpdateStatus = UserProfile.objects.get(username=user)
        UpdateStatus.online = 1
        UpdateStatus.save()
        self.room_name = "box_"+str(user)
        async_to_sync(self.channel_layer.group_add)(
            self.room_name,
            self.channel_name
        )
        self.accept()

    def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        to = text_data_json['to']
        destroy = text_data_json['destroy']

        if message == "ping":
            self.send(text_data=json.dumps({
                'message': "pong",
                'status': "received",
                'destroy': destroy
            }))
            return

        async_to_sync(self.channel_layer.group_send)(
            "box_"+str(to),
            {
                'type': 'chat_message',
                'message': message,
                'destroy': destroy
            }
        )   

    def chat_message(self, event):
        self.send(text_data=json.dumps({
            'message': event['message'],
            'status': "received",
            'destroy': event['destroy']
        }))


    def disconnect(self, code):
        user = self.scope["user"]
        UpdateStatus = UserProfile.objects.get(username=user)
        UpdateStatus.online = 0
        UpdateStatus.online_for = None
        UpdateStatus.save()
        self.close()


class ChatConsumerStatus(WebsocketConsumer):
    """
    Description: This consumer is used to check the online status of the user.
    A user will send a message ('check') along with the username ('for') of friend to check the online status of the friend.
    If the friend is online, the user will receive a message with status 'online' and vice versa.
    """
    http_user_and_session = True
    def connect(self):
        user = self.scope["user"]
        self.room_name = "box2_"+str(user)
        async_to_sync(self.channel_layer.group_add)(
            self.room_name,
            self.channel_name
        )
        self.accept()

    def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)

        if text_data_json['check']=="livestatus":
            ForUser = text_data_json['for']
            user = self.scope["user"]
            if UserProfile.objects.get(username=ForUser).online==1 and UserProfile.objects.get(username=ForUser).online_for==UserProfile.objects.get(username=user):
                async_to_sync(self.channel_layer.group_send)(
                    "box2_"+str(ForUser),
                    {
                        'type': 'UserLiveStatus',
                        'status': 'online',
                        'user': ForUser
                    }
                )
            else:
                self.send(text_data=json.dumps({
                    'status': 'offline',
                    'user': ForUser
                }))

    def UserLiveStatus(self, event):
        status = event['status']
        user = event['user']
        self.send(text_data=json.dumps({
            'status': status,
            'user': user
        }))

    def disconnect(self, code):
        self.close()

class ChatConsumerCurrentStatus(WebsocketConsumer):
    """
    Description: This consumer is used to check the current status of the user (typing/not typing).
    A user will send a message ('status') along with the username ('for') of friend to check the current status of the friend.
    If the friend is typing, the user will receive a message with status 'typing' otherwise 'online'.
    """
    http_user_and_session = True
    def connect(self):
        user = self.scope["user"]
        self.room_name = "box3_"+str(user)
        async_to_sync(self.channel_layer.group_add)(
            self.room_name,
            self.channel_name
        )
        self.accept()


    def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)

        if text_data_json['for'] != "NULL":
            status = text_data_json['status']
            ForUser = text_data_json['for']
            user = self.scope["user"]
            UserUpdate = UserProfile.objects.get(username=user)
            UserUpdate.online_for = UserProfile.objects.get(username=ForUser)
            UserUpdate.save()

            async_to_sync(self.channel_layer.group_send)(
                "box3_"+str(ForUser),
                {
                    'type': 'In_chat_message',
                    'status': status,
                    'user': ForUser
                }
            )

    def In_chat_message(self, event):
        status = event['status']
        user = event['user']
        self.send(text_data=json.dumps({
            'status': status,
            'user': user
        }))

    def disconnect(self, code):
        self.close()