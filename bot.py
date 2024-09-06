#!/usr/bin/env python3

import logging

from vk_maria import Vk, types
from vk_maria.dispatcher import Dispatcher
from vk_maria.dispatcher.filters import AbstractFilter
from vk_maria.types import KeyboardModel, Button, Color
from vk_maria.upload import Upload

import handlers

try:
    import settings
except ImportError:
    exit('DO cp settings.py.default and set token!')


class TestKeyboard(KeyboardModel):
    one_time = True
    row1 = [
        Button.Text(Color.PRIMARY, 'Кнопка 1'),
        Button.Text(Color.PRIMARY, 'Кнопка 2')
    ]
    row2 = [
        Button.Text(Color.PRIMARY, 'Кнопка 3'),
        Button.Text(Color.PRIMARY, 'Кнопка 4')
    ]


class AdminFilter(AbstractFilter):
    def check(self, event: types.Message):
        return event.message.peer_id == 358695118


class UserState:
    """Состояние пользователя внутри сценария."""

    def __init__(self, scenario_name, step_name, context=None):
        self.scenario_name = scenario_name
        self.step_name = step_name
        self.context = context or {}


class Bot:
    """
    Echo bot for vk.com.
    Use Python3.12
    """

    def __init__(self, secret_token):
        """

        :param secret_token: секретный токен
        """
        self.vk = Vk(access_token=secret_token)
        self.dp = Dispatcher(self.vk)
        self.upload = Upload(self.vk)
        self.user_states = dict()  # user_id -> UserState
        self.log = logging.getLogger('bot')

    def configure_logging(self):
        self.log.setLevel(logging.DEBUG)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logging.Formatter('%(levelname)s %(message)s'))
        stream_handler.setLevel(logging.DEBUG)
        self.log.addHandler(stream_handler)

        file_handler = logging.FileHandler('bot.log')
        file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s',
                                                    datefmt='%d.%m.%Y %H:%M'))
        file_handler.setLevel(logging.DEBUG)
        self.log.addHandler(file_handler)

    def run(self):
        """
        Запуск бота.
        """

        @self.dp.message_handler(AdminFilter, commands=['/start'])
        def cmd_start(event: types.Message):
            event.reply("Hi admin!")
            event.answer(sticker_id=8046)

        @self.dp.message_handler(text='test')
        def test(event: types.Message):
            image = types.FileSystemInputFile('images/vkpython.jpg')
            foto = self.upload.photo(image)  # должен отправлять ещё фото
            self.vk.messages_send(user_id=event.message.from_id, message='Hello!',
                                  keyboard=TestKeyboard, attachment=foto)

        @self.dp.message_handler(text='Начать')
        def send_welcome(event: types.Message):
            self.vk.messages_send(user_id=event.message.from_id, message='Добро пожаловать!')

        @self.dp.event_handler(types.EventType.MESSAGE_NEW)
        def on_event(event: types.event):
            """
            Отправляет сообщение назад, если это текст.
            :param event: types.EventType object
            :return: None
            """
            if event.type != types.EventType.MESSAGE_NEW:
                self.log.debug('Мы пока не умеем обрабатывать событие типа %s', event.type)
                return

            user_id = event.message.from_id
            text = event.message.text

            if user_id in self.user_states:
                text_to_send = self.continue_scenario(user_id=user_id, text=text)
            else:
                # search intent
                for intent in settings.INTENTS:
                    self.log.debug(f'User gets {intent}')
                    if any(token in text.lower() for token in intent['tokens']):
                        # run intent
                        if intent['answer']:
                            text_to_send = intent['answer']
                        else:
                            text_to_send = self.start_scenario(intent['scenario'], user_id)
                        break
                else:
                    text_to_send = settings.DEFAULT_ANSWER
            self.vk.messages_send(user_id=user_id, message=text_to_send)

        self.dp.start_polling(debug=True)

    def continue_scenario(self, user_id, text):
        state = self.user_states[user_id]
        steps = settings.SCENARIOS[state.scenario_name]['steps']
        step = steps[state.step_name]
        handler = getattr(handlers, step['handler'])
        if handler(text, context=state.context):
            # next step
            next_step = steps[step['next_step']]
            text_to_send = next_step['text'].format(**state.context)
            if next_step['next_step']:
                # switch to next step
                state.step_name = step['next_step']
            else:
                # finish scenario
                self.log.info('Зарегистрирован: {name}, {email}'.format(**state.context))
                self.user_states.pop(user_id)
        else:
            # retry current step
            text_to_send = step['failure_text'].format(**state.context)
        return text_to_send

        # self.log.info('Sending back text of message...')

        # @self.dp.message_handler()
        # def echo(event: types.Message):
        #     event.answer(event.message.text)
        #     log.debug("Получили просто сообщение: %s, не команда, не колб эк. Запустили эхо функцию.",
        #               event.message.text)

        # @self.dp.event_handler(types.EventType.MESSAGE_TYPING_STATE)
        # def on_event(event):
        #     self.vk.messages_send(user_id=event.from_id, message='Typing...')

    def start_scenario(self, scenario_name, user_id):
        scenario = settings.SCENARIOS[scenario_name]
        first_step = scenario['first_step']
        step = scenario['steps'][first_step]
        text_to_send = step['text']
        self.user_states[user_id] = UserState(scenario_name=scenario_name, step_name=first_step)
        return text_to_send


if __name__ == '__main__':
    bot = Bot(secret_token=settings.TOKEN)
    bot.configure_logging()
    bot.run()
