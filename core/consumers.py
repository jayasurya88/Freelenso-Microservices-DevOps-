import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatRoom, ChatMessage, UserProfile

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json.get('message', '')
        sender_id = text_data_json.get('sender_id')
        file_url = text_data_json.get('file_url')

        if not message and not file_url:
            return

        # Save message to database
        await self.save_message(sender_id, message, file_url)

        # Get sender information
        sender = await self.get_sender_info(sender_id)

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender_id': sender_id,
                'sender_name': sender.user.username if sender else 'Unknown',
                'file_url': file_url
            }
        )

    async def chat_message(self, event):
        message = event['message']
        sender_id = event['sender_id']
        sender_name = event['sender_name']
        file_url = event.get('file_url')

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'sender_id': sender_id,
            'sender_name': sender_name,
            'file_url': file_url
        }))

    @database_sync_to_async
    def save_message(self, sender_id, message, file_url=None):
        try:
            sender = UserProfile.objects.get(id=sender_id)
            room = ChatRoom.objects.get(id=self.room_id)
            
            chat_message = ChatMessage.objects.create(
                room=room,
                sender=sender,
                message=message,
                file=file_url
            )
            
            # Update last message timestamp
            room.save()
            
            return chat_message
        except Exception as e:
            print(f"Error saving message: {str(e)}")
            return None

    @database_sync_to_async
    def get_sender_info(self, sender_id):
        try:
            return UserProfile.objects.get(id=sender_id)
        except UserProfile.DoesNotExist:
            return None 