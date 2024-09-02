#!/usr/bin/env python3
# TODO fix versions!
from vk_maria import Vk, types
from vk_maria.dispatcher import Dispatcher
from vk_maria.dispatcher.filters import AbstractFilter
from vk_maria.types import KeyboardModel, Button, Color
from vk_maria.upload import Upload
import logging
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
        self.log = logging.getLogger('bot')

    def configure_logging(self):
        self.log.setLevel(logging.DEBUG)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logging.Formatter('%(levelname)s %(message)s'))
        stream_handler.setLevel(logging.INFO)
        self.log.addHandler(stream_handler)

        file_handler = logging.FileHandler('bot.log')
        file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%d.%m.%Y %H:%M'))
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
            if event.type == types.EventType.MESSAGE_NEW:
                # log.debug(event)
                self.log.info('Sending back text of message...')
                self.vk.messages_send(user_id=event.message.from_id, message=event.message.text)
            else:
                self.log.debug('Мы пока не умеем обрабатывать событие типа %s', event.type)

        # @self.dp.message_handler()
        # def echo(event: types.Message):
        #     event.answer(event.message.text)
        #     log.debug("Получили просто сообщение: %s, не команда, не колб эк. Запустили эхо функцию.",
        #               event.message.text)

        # @self.dp.event_handler(types.EventType.MESSAGE_TYPING_STATE)
        # def on_event(event):
        #     self.vk.messages_send(user_id=event.from_id, message='Typing...')

        self.dp.start_polling(debug=True)


if __name__ == '__main__':
    bot = Bot(secret_token=settings.TOKEN)
    bot.configure_logging()
    bot.run()
