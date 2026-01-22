import datetime

from google.protobuf import timestamp_pb2 as _timestamp_pb2
from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class EpisodeType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    EPISODE_TYPE_UNSPECIFIED: _ClassVar[EpisodeType]
    EPISODE_TYPE_MESSAGE: _ClassVar[EpisodeType]
    EPISODE_TYPE_JSON: _ClassVar[EpisodeType]
    EPISODE_TYPE_TEXT: _ClassVar[EpisodeType]

class ComparisonOperator(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    COMPARISON_OPERATOR_UNSPECIFIED: _ClassVar[ComparisonOperator]
    COMPARISON_OPERATOR_EQUALS: _ClassVar[ComparisonOperator]
    COMPARISON_OPERATOR_NOT_EQUALS: _ClassVar[ComparisonOperator]
    COMPARISON_OPERATOR_GREATER_THAN: _ClassVar[ComparisonOperator]
    COMPARISON_OPERATOR_LESS_THAN: _ClassVar[ComparisonOperator]
    COMPARISON_OPERATOR_GREATER_THAN_EQUAL: _ClassVar[ComparisonOperator]
    COMPARISON_OPERATOR_LESS_THAN_EQUAL: _ClassVar[ComparisonOperator]
    COMPARISON_OPERATOR_IS_NULL: _ClassVar[ComparisonOperator]
    COMPARISON_OPERATOR_IS_NOT_NULL: _ClassVar[ComparisonOperator]
EPISODE_TYPE_UNSPECIFIED: EpisodeType
EPISODE_TYPE_MESSAGE: EpisodeType
EPISODE_TYPE_JSON: EpisodeType
EPISODE_TYPE_TEXT: EpisodeType
COMPARISON_OPERATOR_UNSPECIFIED: ComparisonOperator
COMPARISON_OPERATOR_EQUALS: ComparisonOperator
COMPARISON_OPERATOR_NOT_EQUALS: ComparisonOperator
COMPARISON_OPERATOR_GREATER_THAN: ComparisonOperator
COMPARISON_OPERATOR_LESS_THAN: ComparisonOperator
COMPARISON_OPERATOR_GREATER_THAN_EQUAL: ComparisonOperator
COMPARISON_OPERATOR_LESS_THAN_EQUAL: ComparisonOperator
COMPARISON_OPERATOR_IS_NULL: ComparisonOperator
COMPARISON_OPERATOR_IS_NOT_NULL: ComparisonOperator

class OperationResult(_message.Message):
    __slots__ = ("success", "message", "error_code", "error_details")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    ERROR_CODE_FIELD_NUMBER: _ClassVar[int]
    ERROR_DETAILS_FIELD_NUMBER: _ClassVar[int]
    success: bool
    message: str
    error_code: str
    error_details: str
    def __init__(self, success: bool = ..., message: _Optional[str] = ..., error_code: _Optional[str] = ..., error_details: _Optional[str] = ...) -> None: ...

class Message(_message.Message):
    __slots__ = ("uuid", "name", "role", "role_type", "content", "timestamp", "source_description")
    UUID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    ROLE_FIELD_NUMBER: _ClassVar[int]
    ROLE_TYPE_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    SOURCE_DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    uuid: str
    name: str
    role: str
    role_type: str
    content: str
    timestamp: _timestamp_pb2.Timestamp
    source_description: str
    def __init__(self, uuid: _Optional[str] = ..., name: _Optional[str] = ..., role: _Optional[str] = ..., role_type: _Optional[str] = ..., content: _Optional[str] = ..., timestamp: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., source_description: _Optional[str] = ...) -> None: ...

class DateFilter(_message.Message):
    __slots__ = ("date", "comparison_operator")
    DATE_FIELD_NUMBER: _ClassVar[int]
    COMPARISON_OPERATOR_FIELD_NUMBER: _ClassVar[int]
    date: _timestamp_pb2.Timestamp
    comparison_operator: ComparisonOperator
    def __init__(self, date: _Optional[_Union[datetime.datetime, _timestamp_pb2.Timestamp, _Mapping]] = ..., comparison_operator: _Optional[_Union[ComparisonOperator, str]] = ...) -> None: ...

class PropertyFilter(_message.Message):
    __slots__ = ("property_name", "string_value", "int_value", "float_value", "bool_value", "comparison_operator")
    PROPERTY_NAME_FIELD_NUMBER: _ClassVar[int]
    STRING_VALUE_FIELD_NUMBER: _ClassVar[int]
    INT_VALUE_FIELD_NUMBER: _ClassVar[int]
    FLOAT_VALUE_FIELD_NUMBER: _ClassVar[int]
    BOOL_VALUE_FIELD_NUMBER: _ClassVar[int]
    COMPARISON_OPERATOR_FIELD_NUMBER: _ClassVar[int]
    property_name: str
    string_value: str
    int_value: int
    float_value: float
    bool_value: bool
    comparison_operator: ComparisonOperator
    def __init__(self, property_name: _Optional[str] = ..., string_value: _Optional[str] = ..., int_value: _Optional[int] = ..., float_value: _Optional[float] = ..., bool_value: bool = ..., comparison_operator: _Optional[_Union[ComparisonOperator, str]] = ...) -> None: ...

class PaginationCursor(_message.Message):
    __slots__ = ("uuid_cursor", "limit")
    UUID_CURSOR_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    uuid_cursor: str
    limit: int
    def __init__(self, uuid_cursor: _Optional[str] = ..., limit: _Optional[int] = ...) -> None: ...
