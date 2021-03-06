# coding=utf-8
from src.config import Config
import math
from src.utils.utils import is_number, utils
import json

fee = Config.FEE or 10000


def filterFun(v):
    return v


def __hexToString(h):
    a = []
    i = 0
    strLength = len(h)

    if (strLength % 2 == 0):
        a.extend(chr(int(h[0: 1], 16)))
        i = 1

    for index in range(i, strLength, 2):
        a.extend(chr(int(h[index: index+2]), 16))

    return ''.join(a)


def __stringToHex(s):
    result = ''
    for c in s:
        b = ord(c)
        # 转换成16进制的ASCII码
        if b < 16:
            result += '0'+hex(b).replace('0x', '')
        else:
            result += hex(b).replace('0x', '')

    return result


def safe_int(num):
    try:
        return int(num)
    except ValueError:
        result = []
        for c in num:
            if not ('0' <= c <= '9'):
                break
            result.append(c)
        if len(result) == 0:
            return 0
        return int(''.join(result))


def Number(num):
    if(not is_number(num)):
        return float('nan')
    if(isinstance(num, bool) and num):
        return 1
    if(isinstance(num, bool) and not num):
        return 0
    if(isinstance(num, (int, float))):
        return num
    if '.' in num:
        return float(num)
    else:
        return int(num)


def MaxAmount(amount):
    if (isinstance(amount, str) and is_number(amount)):
        _amount = safe_int(Number(amount) * (1.0001))
        return str(_amount)
    if (isinstance(amount, dict) and utils.isValidAmount(amount)):
        _value = Number(amount['value']) * (1.0001)
        amount['value'] = str(_value)
        return amount
    return Exception('invalid amount to max')


class Transaction:
    def __init__(self, remote, filter):
        # TODO(zfn):事件驱动注册待实现
        self._remote = remote
        self.tx_json = {"Flags": 0, "Fee": fee}
        self._filter = filter or filterFun
        self._secret = 0

    set_clear_flags = {
        'AccountSet': {
            'asfRequireDest':    1,
            'asfRequireAuth':    2,
            'asfDisallowSWT':    3,
            'asfDisableMaster':  4,
            'asfNoFreeze':       6,
            'asfGlobalFreeze':   7
        }
    }

    flags = {
        # Universal flags can apply to any transaction type
        'Universal': {
            'FullyCanonicalSig':  0x80000000
        },

        'AccountSet': {
            'RequireDestTag':     0x00010000,
            'OptionalDestTag':    0x00020000,
            'RequireAuth':        0x00040000,
            'OptionalAuth':       0x00080000,
            'DisallowSWT':        0x00100000,
            'AllowSWT':           0x00200000
        },

        'TrustSet': {
            'SetAuth':            0x00010000,
            'NoSkywell':          0x00020000,
            'SetNoSkywell':       0x00020000,
            'ClearNoSkywell':     0x00040000,
            'SetFreeze':          0x00100000,
            'ClearFreeze':        0x00200000
        },

        'OfferCreate': {
            'Passive':            0x00010000,
            'ImmediateOrCancel':  0x00020000,
            'FillOrKill':         0x00040000,
            'Sell':               0x00080000
        },

        'Payment': {
            'NoSkywellDirect':    0x00010000,
            'PartialPayment':     0x00020000,
            'LimitQuality':       0x00040000
        },

        'RelationSet': {
            'Authorize':          0x00000001,
            'Freeze':             0x00000011
        }
    }

    OfferTypes = ['Sell', 'Buy']
    RelationTypes = ['trust', 'authorize', 'freeze', 'unfreeze']
    AccountSetTypes = ['property', 'delegate', 'signer']

    def parseJson(self, val):
        self.tx_json = val
        return self

    def getAccount(self):
        return self.tx_json['Account']

    def getTransactionType(self):
        return self.tx_json['TransactionType']

    def setSecret(self, secret):
        self._secret = secret

    """
    * just only memo data
    * @param memo
    """

    def addMemo(self, memo):
        if (not isinstance(memo, str)):
            self.tx_json['memo_type'] = TypeError('invalid memo type')
            return self
        if (len(memo) > 2048):
            self.tx_json['memo_len'] = TypeError('memo is too long')
            return self
        _memo = {}
        _memo['MemoData'] = __stringToHex(memo.encode("UTF-8"))
        self.tx_json['Memos'] = (self.tx_json['Memos']
                                 or []).append({'Memo': _memo})

    def setFee(self, fee):
        _fee = safe_int(fee)
        if (math.isnan(_fee)):
            self.tx_json['Fee'] = TypeError('invalid fee')
            return self
        if (fee < 10):
            self.tx_json['Fee'] = TypeError('fee is too low')
            return self
        self.tx_json['Fee'] = _fee

    """
    * set a path to payment
    * this path is repesented as a key, which is computed in path find
    * so if one path you computed self is not allowed
    * when path set, sendmax is also set.
    * @param path
    """
    def setPath (self,key):
        # sha1 string
        if (not isinstance(key,str) and len(key) != 40):
            return Exception('invalid path key')

        item = self._remote._paths.get(key)
        if (item is not None) :
            return Exception('non exists path key')

        if(item['path'] == '[]'):#沒有支付路径，不需要传下面的参数
            return
        path = json.load(item.path)
        self.tx_json['Paths'] = path
        amount = MaxAmount(item['choice'])
        self.tx_json['SendMax'] = amount

    """
    * limit send max amount
    * @param amount
    """
    def setSendMax(self,amount):
        if (utils.isValidAmount(amount) is not None):
            return Exception('invalid send max amount')
        self.tx_json['SendMax'] = amount


    """
    * transfer rate
    * between 0 and 1, type is number
    * @param rate
    """
    def setTransferRate(self,rate):
        if (not isinstance(rate,(int,float)) or rate < 0 or rate > 1) :
            return Exception('invalid transfer rate')
        self.tx_json['TransferRate'] = (rate + 1) * 1e9

    """
    * set transaction flags
    *
     """
    def setFlags(self,flags):
        if (flags is None):
             return

        if (isinstance(flags,(int,float))):
            self.tx_json['Flags'] = flags
            return

        transaction_flags = Transaction.flags[self.getTransactionType()] or {}
        if(isinstance(flags,list)):
            flag_set=flags
        else:
            flag_set=[].append(flags)

        for flag in flag_set:
            if (transaction_flags.has_key(flag)):
                self.tx_json['Flags'] += transaction_flags[flag]

    def sign(self,callback):
        from jingtum_python_baselib.src.wallet import Wallet as base
        #导入Serializer 目前未实现
        from remote import Remote
        #2018.6.2 remote类没有翻译完整
        remote = Remote({'server': self._remote._url})

        def connect_callback(err, result):
            if(err is not None):
                callback(err)
            req = remote.requestAccountInfo({'account': self.tx_json.Account, 'type': 'trust'})
            req.submit(submit_callback)

        def submit_callback(err,data):
            if(err is not None):
             return callback(err)
            self.tx_json['Sequence'] = data.account_data.Sequence
            self.tx_json['Fee'] = self.tx_json['Fee']/1000000

            #payment
            if(self.tx_json.Amount and json.dumps(self.tx_json.Amount).index('{') < 0):
                #基础货币
                self.tx_json.Amount = Number(self.tx_json.Amount)/1000000

            if(self.tx_json['Memos'] is not None):
                memo_list = self.tx_json['Memos']
                memo_list[0]["Memo"]["MemoData"] = __hexToString(memo_list[0]["Memo"]["MemoData"]).decode('UTF-8')

            if(self.tx_json['SendMax'] is not None and isinstance(self.tx_json['SendMax'],str)):
                self.tx_json['SendMax'] = Number(self.tx_json['SendMax'])/1000000

            #order
            if(self.tx_json['TakerPays'] and  json.dumps(self.tx_json['TakerPays']).index('{') < 0):
                #基础货币
                self.tx_json['TakerPays'] = Number(self.tx_json['TakerPays'])/1000000

            if(self.tx_json['TakerGets'] and json.dumps(self.tx_json['TakerGets']).index('{') < 0):
                #基础货币
                self.tx_json['TakerGets'] = Number(self.tx_json['TakerGets'])/1000000

            #2018.6.3 wallet类没有翻译完整
            """
            wt = base(self._secret)
            self.tx_json['SigningPubKey'] = wt.getPublicKey()
            prefix = 0x53545800
            hash = jser.from_json(self.tx_json).hash(prefix)
            self.tx_json['TxnSignature'] = wt.signTx(hash)
            self.tx_json['blob'] =  jser.from_json(self.tx_json).to_hex()
            """
            self._local_sign = True
            callback(None, self.tx_json['blob'])

        remote.connect(connect_callback)
