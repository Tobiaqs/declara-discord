import os
import re
import discord
import json
import schwifty

from dotenv import load_dotenv

# TODO: Add question if iban/name/email is still correct -> reset otherwise

# Setup discord connection
load_dotenv()

token = os.getenv('token', default='')
user_data_file = os.getenv('user_data_file', default='user_data.json')
email_regex = r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+'


class UserData:
    user_data = None
    # TODO: Add catch when querying user_id from dict (can crash)

    def __init__(self, file_path):
        # Check if file exists
        self.file_path = file_path
        self.__load_data()

    def __load_data(self):
        print(f'testing path {self.file_path}')
        if os.path.exists(self.file_path):
            print('found it')
            with open(self.file_path) as json_file:
                # TODO: What if data is invalid???
                print('loading')
                self.user_data = json.loads(json_file.read())
                print(self.user_data)
        else:
            self.user_data = json.loads('{}')
            self.__store_data()

    def __store_data(self):
        with open(self.file_path, 'w') as json_file:
            json.dump(self.user_data, json_file, indent=4)

    def reset_user(self, user_id):
        self.__init_user_if_not_exist(user_id)
        self.user_data[user_id]['messages'] = []
        self.user_data[user_id]['attachments'] = []
        self.user_data[user_id]['send_to_board'] = True
        self.__store_data()

    def __init_user_if_not_exist(self, user_id):
        if user_id not in self.user_data:
            self.user_data[user_id] = {
                'name': '',
                'email': '',
                'iban': '',
                'messages': [],
                'attachments': [],
                'send_to_board': True
            }
        self.__store_data()

    def add_data(self, user_id, text):
        splits = text.split(';')
        message = splits[0]
        amount = splits[-1]

        try:
            amount = round(float(amount), 2)
        except ValueError:
            return False

        self.__init_user_if_not_exist(user_id)
        line = {
            'message': message,
            'amount': amount
        }
        self.user_data[user_id]['messages'].append(line)
        self.__store_data()

    def add_attachment(self, user_id, url):
        self.__init_user_if_not_exist(user_id)
        self.user_data[user_id]['attachments'].append(url)
        self.__store_data()

    def update_iban(self, user_id, iban):
        try:
            ib = schwifty.IBAN(iban)
            ib.validate()
        except:
            return False
        self.__init_user_if_not_exist(user_id)
        self.user_data[user_id]['iban'] = iban
        self.__store_data()
        return True

    def update_name(self, user_id, name):
        self.__init_user_if_not_exist(user_id)
        self.user_data[user_id]['name'] = name
        self.__store_data()

    def update_board(self, user_id, send_to_board):
        self.__init_user_if_not_exist(user_id)
        self.user_data[user_id]['send_to_board'] = bool(send_to_board)
        self.__store_data()

    def update_email(self, user_id, email):
        if not re.fullmatch(email_regex, email):
            return False
        self.__init_user_if_not_exist(user_id)
        self.user_data[user_id]['email'] = email
        self.__store_data()
        return True

    def get_all_messages(self, user_id):
        self.__init_user_if_not_exist(user_id)
        return self.user_data[user_id]['messages']

    def get(self, user_id):
        self.__init_user_if_not_exist(user_id)
        return self.user_data[user_id]

    def send(self, user_id):
        # TODO: VALIDATE CONTENT!
        ...


class MyClient(discord.Client):
    user_data = UserData(user_data_file)
    reset_commands = [
        '$reset'
    ]
    send_commands = [
        '$send'
    ]
    update_name_commands = [
        '$name'
    ]
    update_email_commands = [
        '$email'
    ]
    send_to_board_commands = [
        '$board'
    ]
    image_command = [
        '$image'
    ]
    help_commands = [
        '$help',
        '?',
        '$?'
    ]

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

    async def on_message(self, message):
        # we do not want the bot to reply to itself
        if message.author.id == self.user.id:
            return

        # F*ck int id's vs string id's when working with dicts and json...
        message.author.id = str(message.author.id)

        # All other cases for testing
        # TODO: Figure out message type
        content = message.content
        command = content.split(' ')[0]
        command_content = ' '.join(content.split(' ')[1:]).strip()
        user_id = message.author.id
        valid_iban = False
        try:
            iban = schwifty.IBAN(command_content)
            iban.validate()
            valid_iban = True
        except:
            ...

        # TODO: Do loose matching
        if valid_iban:
            if self.user_data.update_iban(user_id, command_content):
                return await message.channel.send('Updated your IBAN number!')
            return await message.channel.send('Failed to update your IBAN...')
        elif command in self.help_commands:
            return await message.channel.send(
                'Hi, I\'m Clarna and I can help you create and send declarations for Boreas!\n\n'
                'These are the commands you can send me:\n'
                '$reset: Starts over\n'
                '$send: Creates the PDF and sends it\n'
                '$email <email>: Update your email address\n'
                '$name <name>: Update your name\n'
                '$iban <iban>: Update your name\n'
                '$message <message;amount>: Add a reason and an amount, separated by a semicolon\n'
                '$board <bool> = True: Set to true to also send an email to the board\n'
                '$info: Gets the current info that I have about you\n'
            )
        elif command in self.reset_commands:
            await message.channel.send('Starting over ;\')')
            self.user_data.reset_user(user_id)
        elif command in self.send_commands:
            ...
        elif command in self.update_name_commands:
            self.user_data.update_name(user_id, command_content)
            await message.channel.send(f'Updated your name to {command_content}')
        elif command in self.update_email_commands:
            if not re.fullmatch(email_regex, command_content):
                return await message.channel.send(f'Not a valid email!')
            self.user_data.update_email(user_id, command_content)
            await message.channel.send(f'Updated your email to {command_content}')
        elif command in self.send_to_board_commands:
            try:
                send_to_board = bool(command_content)
            except:
                return await message.channel.send(f'Wrong input, go fix...')
            self.user_data.update_board(user_id, send_to_board)
        elif message.attachments:
            attachment = message.attachments[0]
            # TODO: Add check for pdf file
            if 'image' not in attachment.content_type:
                return await message.channel.send(f'Not a valid image or pdf file')
            self.user_data.add_attachment(user_id, attachment.url)
        else:
            self.user_data.add_data(message.author.id, content)

        return await message.channel.send(self.user_data.get(user_id))
        # return await message.channel.send('Something went wrong, I\'m sorry!')


intents = discord.Intents.default()
intents.message_content = True
client = MyClient(intents=intents)
client.run(token)
