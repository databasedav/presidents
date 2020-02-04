# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: game_action.proto

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database

# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import (
    timestamp_pb2 as google_dot_protobuf_dot_timestamp__pb2,
)


DESCRIPTOR = _descriptor.FileDescriptor(
    name="game_action.proto",
    package="",
    syntax="proto3",
    serialized_options=None,
    serialized_pb=b'\n\x11game_action.proto\x1a\x1fgoogle/protobuf/timestamp.proto"z\n\nGameAction\x12\x0f\n\x07game_id\x18\x01 \x01(\t\x12\x0e\n\x06\x61\x63tion\x18\x02 \x01(\x0f\x12-\n\ttimestamp\x18\x03 \x01(\x0b\x32\x1a.google.protobuf.Timestamp\x12\x0b\n\x03sid\x18\x04 \x01(\t\x12\x0f\n\x07user_id\x18\x05 \x01(\tb\x06proto3',
    dependencies=[google_dot_protobuf_dot_timestamp__pb2.DESCRIPTOR],
)


_GAMEACTION = _descriptor.Descriptor(
    name="GameAction",
    full_name="GameAction",
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name="game_id",
            full_name="GameAction.game_id",
            index=0,
            number=1,
            type=9,
            cpp_type=9,
            label=1,
            has_default_value=False,
            default_value=b"".decode("utf-8"),
            message_type=None,
            enum_type=None,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            serialized_options=None,
            file=DESCRIPTOR,
        ),
        _descriptor.FieldDescriptor(
            name="action",
            full_name="GameAction.action",
            index=1,
            number=2,
            type=15,
            cpp_type=1,
            label=1,
            has_default_value=False,
            default_value=0,
            message_type=None,
            enum_type=None,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            serialized_options=None,
            file=DESCRIPTOR,
        ),
        _descriptor.FieldDescriptor(
            name="timestamp",
            full_name="GameAction.timestamp",
            index=2,
            number=3,
            type=11,
            cpp_type=10,
            label=1,
            has_default_value=False,
            default_value=None,
            message_type=None,
            enum_type=None,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            serialized_options=None,
            file=DESCRIPTOR,
        ),
        _descriptor.FieldDescriptor(
            name="sid",
            full_name="GameAction.sid",
            index=3,
            number=4,
            type=9,
            cpp_type=9,
            label=1,
            has_default_value=False,
            default_value=b"".decode("utf-8"),
            message_type=None,
            enum_type=None,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            serialized_options=None,
            file=DESCRIPTOR,
        ),
        _descriptor.FieldDescriptor(
            name="user_id",
            full_name="GameAction.user_id",
            index=4,
            number=5,
            type=9,
            cpp_type=9,
            label=1,
            has_default_value=False,
            default_value=b"".decode("utf-8"),
            message_type=None,
            enum_type=None,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            serialized_options=None,
            file=DESCRIPTOR,
        ),
    ],
    extensions=[],
    nested_types=[],
    enum_types=[],
    serialized_options=None,
    is_extendable=False,
    syntax="proto3",
    extension_ranges=[],
    oneofs=[],
    serialized_start=54,
    serialized_end=176,
)

_GAMEACTION.fields_by_name[
    "timestamp"
].message_type = google_dot_protobuf_dot_timestamp__pb2._TIMESTAMP
DESCRIPTOR.message_types_by_name["GameAction"] = _GAMEACTION
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

GameAction = _reflection.GeneratedProtocolMessageType(
    "GameAction",
    (_message.Message,),
    {
        "DESCRIPTOR": _GAMEACTION,
        "__module__": "game_action_pb2"
        # @@protoc_insertion_point(class_scope:GameAction)
    },
)
_sym_db.RegisterMessage(GameAction)


# @@protoc_insertion_point(module_scope)
