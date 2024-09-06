from unittest import TestCase
from unittest.mock import patch

from bot import Bot


class Test1(TestCase):
    def test_ok(self):
        with patch('bot.vk'):
            with patch('bot.dp'):
                bot = Bot('')
                print('')
