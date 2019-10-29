from typing import Optional, Dict, Any
from unittest import TestCase

from kaniko import Kaniko


class KanikoTest(TestCase):
    @classmethod
    def get_config(cls):
        return {
            'kaniko_path': '/kaniko/path',
            'build_args': ['1', '2', '3'],
            'cache': True,
            'force': True,
            'nonexistent_attribute': True,
        }

    @classmethod
    def get_shell_command(cls):
        return [
            '/kaniko/path/executor',
            '--build-arg=1',
            '--build-arg=2',
            '--build-arg=3',
            '--cache',
            '--force'
        ]

    @classmethod
    def get_nonexistent_attributes(cls, config: Optional[Dict[str, Any]] = None):
        kaniko = Kaniko()
        if config is None:
            config = cls.get_config()

        return [attr for attr in config if not hasattr(kaniko, attr)]

    def test_configure(self):
        kaniko = Kaniko()
        config = self.get_config()
        nonexistent_attributes = self.get_nonexistent_attributes(config=config)
        kaniko.configure(**config)

        for key, value in config.items():
            if key in nonexistent_attributes:
                self.assertFalse(hasattr(kaniko, key))
                continue

            self.assertEqual(getattr(kaniko, key), value)

    def test_shell_command(self):
        kaniko = Kaniko()
        kaniko.configure(**self.get_config())
        self.assertEqual(kaniko.shell_command, self.get_shell_command())

    def test_parse_logs(self):
        logs = '\nsome\n little\n strings \n'.encode('utf-8')
        expected = ['some', 'little', 'strings']
        actual = Kaniko()._parse_logs(logs=logs)
        self.assertEqual(actual, expected)
