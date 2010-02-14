import nose
import random
import sys
import types

from pycanlib import CAN, InputValidation

TEST_SAMPLE_LENGTH = 10
MAX_INVALID_PAYLOAD_LENGTH = 25

INVALID_TIMESTAMPS = [-50, -0.2, 0, 100, "foo", [], None]
VALID_TIMESTAMPS = [0.0, 500.0, 0.123456, 10.5]

VALID_STANDARD_ARBITRATION_IDS = [0, 1, 2, 2**10, 2**11-2, 2**11-1]
INVALID_STANDARD_ARBITRATION_IDS = [-2, -1, 2**11, "foo", [], None]

VALID_EXTENDED_ARBITRATION_IDS = [0, 1, 2, 2**28, 2**29-2, 2**29-1]
INVALID_EXTENDED_ARBITRATION_IDS = [-2, -1, 2**29, "foo", [], None]

def __generate_valid_payloads(num_payloads):
    retval = []
    for i in xrange(num_payloads):
        _payload = []
        for _payload_index in xrange(random.randint(0, 8)):
            _payload.append(random.randint(0, 255))
        retval.append(_payload)
    return retval

def __generate_invalid_payloads(num_payloads):
    _random_payload_item_types = [types.IntType, types.FloatType, types.StringType, types.NoneType, types.ListType]
    retval = []
    for i in xrange(num_payloads):
        _payload = []
        print i
        for _payload_index in xrange(random.randint(1, MAX_INVALID_PAYLOAD_LENGTH)):
            print "\t", _payload_index
            _payload_item_type = _random_payload_item_types[random.randint(0, len(_random_payload_item_types)-1)]
            if _payload_item_type == types.IntType:
                _payload_item = 0
                while _payload_item in xrange(0, 255):
                    _payload_item = random.randint(-sys.maxint, sys.maxint)
                _payload.append(_payload_item)
            elif _payload_item_type == types.FloatType:
                _payload.append(float(random.randint(-sys.maxint, sys.maxint))/1000)
            elif _payload_item_type == types.StringType:
                _payload_item = ""
                for _payload_item_length in xrange(random.randint(0, 5)):
                    _payload_item += "%c" % random.randint(0, 255)
                _payload.append(_payload_item)
            elif _payload_item_type == types.NoneType:
                _payload.append(None)
            elif _payload_item_type == types.ListType:
                _payload_item = []
                for _payload_item_length in xrange(random.randint(0, 5)):
                    _payload_item.append(random.randint(-sys.maxint, sys.maxint))
                _payload.append(_payload_item)
        retval.append(_payload)
    return retval

VALID_PAYLOADS = __generate_valid_payloads(TEST_SAMPLE_LENGTH)
INVALID_PAYLOADS = __generate_invalid_payloads(TEST_SAMPLE_LENGTH)

VALID_DLCS = range(0, 9)
INVALID_DLCS = [-2, -1, 9, 10, 50]

def testREQ_ShallCreateCANMessageObject():
    _message = None
    _message = CAN.Message()
    assert _message.timestamp == 0.0
    assert _message.is_remote_frame == False
    assert _message.id_type == CAN.ID_TYPE_STANDARD
    assert _message.is_wakeup == False
    assert _message.is_error_frame == False
    assert _message.arbitration_id == 0
    assert _message.data == []
    assert _message.dlc == 0

def testREQ_ShallNotAcceptInvalidTimestamps():
    for _timestamp in VALID_TIMESTAMPS:
        yield __verify_invalid_timestamp_response, _timestamp
    for _timestamp in INVALID_TIMESTAMPS:
        yield __verify_invalid_timestamp_response, _timestamp

def __verify_invalid_timestamp_response(timestamp):
    _message = None
    _exception = None
    try:
        _message = CAN.Message(timestamp=timestamp)
    except InputValidation.pycanlibError as _exception:
        pass
    if timestamp in VALID_TIMESTAMPS and isinstance(timestamp, types.FloatType):
        assert _exception == None
        assert _message.timestamp == timestamp
    else:
        assert _message == None
        assert _exception.parameter_name == "timestamp"
        assert _exception.parameter_value == timestamp

def testREQ_ShallNotAcceptInvalidArbitrationIDs():
    for _arbitration_id in VALID_STANDARD_ARBITRATION_IDS:
        yield __verify_invalid_arbitration_id_response, _arbitration_id, CAN.ID_TYPE_STANDARD
    for _arbitration_id in INVALID_STANDARD_ARBITRATION_IDS:
        yield __verify_invalid_arbitration_id_response, _arbitration_id, CAN.ID_TYPE_STANDARD
    for _arbitration_id in VALID_EXTENDED_ARBITRATION_IDS:
        yield __verify_invalid_arbitration_id_response, _arbitration_id, CAN.ID_TYPE_STANDARD
    for _arbitration_id in INVALID_EXTENDED_ARBITRATION_IDS:
        yield __verify_invalid_arbitration_id_response, _arbitration_id, CAN.ID_TYPE_STANDARD

def __verify_invalid_arbitration_id_response(arbitration_id, arbitration_id_type):
    _message = None
    _exception = None
    try:
        _message = CAN.Message(id_type=arbitration_id_type, arbitration_id=arbitration_id)
    except InputValidation.pycanlibError as _exception:
        pass
    if arbitration_id_type == CAN.ID_TYPE_STANDARD:
        _acceptable_ids = VALID_STANDARD_ARBITRATION_IDS
    else:
        _acceptable_ids = VALID_EXTENDED_ARBITRATION_IDS
    if arbitration_id in _acceptable_ids:
        assert _exception == None
        assert _message.arbitration_id == arbitration_id
    else:
        assert _message == None
        assert _exception.parameter_name == "arbitration_id"
        assert _exception.parameter_value == arbitration_id

def testREQ_ShallNotAcceptInvalidPayload():
    for _payload in VALID_PAYLOADS:
        yield __verify_invalid_payload_response, _payload
    for _payload in INVALID_PAYLOADS:
        yield __verify_invalid_payload_response, _payload

def __verify_invalid_payload_response(payload):
    _message = None
    _exception = None
    try:
        _message = CAN.Message(data=payload)
    except InputValidation.pycanlibError as _exception:
        pass
    if payload in VALID_PAYLOADS:
        assert _exception == None
        assert _message.data == payload
    else:
        assert _message == None
        assert _exception.parameter_name.startswith("data")

def testREQ_ShallNotAcceptInvalidDLC():
    for _dlc in VALID_DLCS:
        yield __verify_invalid_dlc_response, _dlc
    for _dlc in INVALID_DLCS:
        yield __verify_invalid_dlc_response, _dlc

def __verify_invalid_dlc_response(dlc):
    _message = None
    _exception = None
    try:
        _message = CAN.Message(dlc=dlc)
    except InputValidation.pycanlibError as _exception:
        pass
    if dlc in VALID_DLCS:
        assert _exception == None
        assert _message.dlc == dlc
    else:
        assert _message == None
        assert _exception.parameter_name == "dlc"
        assert _exception.parameter_value == dlc
