# coding=utf-8
"""
 * Created with PyCharm.
 * User: 彭诗杰
 * Date: 2018/5/8
 * Time: 14:57
 * Description:
"""
import sys
sys.path.append("..")

from jingtum_python_baselib.src.utils import utils as baselib
from src.config import Config

import re

def is_number(s):
    """
    判断字符串是否是数字类型
    :param s:
    :return:
    """
    try:
        float(s)
        return True
    except ValueError:
        pass

    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass

    return False


LEDGER_STATES = ['current', 'closed', 'validated']


class utils:
    # input num may contain one '.' and one '-'
    def isNum(amount):
        return str(amount).replace('.', '', 1).replace('-', '', 1).isdigit()

    def isValidCurrency(currency):
        CURRENCY_RE = '^([a-zA-Z0-9]{3,6}|[A-F0-9]{40})$'
        if (not currency or not isinstance(currency, str) or currency == ''):
            return False
        if re.search(CURRENCY_RE, currency):  # 判断字符串是否符合某一正则表达式
            return True
        else:
            return False

    """
     * check {value: '', currency:'', issuer: ''}
     * @param amount
     * @returns {boolean}
    """
    def isValidAmount(amount):
        if (not amount):
            return False
        # check amount value
        if ((not amount.value and amount.value != 0) or not utils.isNum(amount.value)):
            return False
        # check amount currency
        if (not amount.currency or not utils.isValidCurrency(amount.currency)):
            return False
        # native currency issuer is empty
        if (amount.currency == Config.currency and amount.issuer != ''):
            return False
        # non native currency issuer is not allowed to be empty
        if (amount.currency != Config.currency
                and not baselib.isValidAddress(amount.issuer)):
            return False
        return True

    """
     * check {currency: '', issuer: ''}
     * @param amount
     * @returns {boolean}
    """

    def isValidAmount0(amount):
        if (not amount):
            return False
        # check amount currency
        if (not amount.currency or not utils.isValidCurrency(amount.currency)):
            return False
        # native currency issuer is empty
        if (amount.currency == Config.currency and amount.issuer != ''):
            return False
        # non native currency issuer is not allowed to be empty
        if (amount.currency != Config.currency
                and not baselib.isValidAddress(amount.issuer)):
            return False
        return True
