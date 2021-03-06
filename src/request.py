# coding=utf-8
"""
 * Created with PyCharm.
 * User: 彭诗杰
 * Date: 2018/5/7
 * Time: 16:44
 * Description: request类
"""
from src.utils.utils import *
import re


class Request:
    def __init__(self, remote, command, filter):
        self.remote = remote
        self.command = command
        self.filter = filter

        self.message = {}

    def submit(self, callback):
        for key in self.message:
            if isinstance(self.message[key], Exception):
                return callback(self.message[key].message)

        self.remote.submit(self.command, self.message, self.filter, callback)

    def select_ledger(self, ledger):
        """
        该方法用于选定ledger账本
        :param ledger:  账本的Index或者hash
        :return: Request对象
        """
        if (isinstance(ledger, str) and ~LEDGER_STATES.index(ledger)):
            self.message['ledger_index'] = ledger
        elif (isinstance(ledger, str) and is_number(ledger)):
            self.message['ledger_index'] = ledger
        elif (re.match('^[A-F0-9]+$', ledger) is not None):
            self.message['ledger_index'] = ledger
        else:
            self.message['ledger_index'] = 'validated'
        return self
