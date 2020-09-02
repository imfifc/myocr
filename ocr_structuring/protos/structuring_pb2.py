# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: ocr_structuring/protos/structuring.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='ocr_structuring/protos/structuring.proto',
  package='ocr_structuring',
  syntax='proto3',
  serialized_options=None,
  serialized_pb=_b('\n(ocr_structuring/protos/structuring.proto\x12\x0focr_structuring\"W\n\tImageData\x12\r\n\x05width\x18\x01 \x01(\x05\x12\x0e\n\x06height\x18\x02 \x01(\x05\x12\x10\n\x08\x63hannels\x18\x03 \x01(\x05\x12\x0c\n\x04\x64\x61ta\x18\x04 \x01(\x0c\x12\x0b\n\x03shm\x18\x05 \x01(\t\"{\n\nRotatedBox\x12\n\n\x02x1\x18\x01 \x01(\x05\x12\n\n\x02y1\x18\x02 \x01(\x05\x12\n\n\x02x2\x18\x03 \x01(\x05\x12\n\n\x02y2\x18\x04 \x01(\x05\x12\n\n\x02x3\x18\x05 \x01(\x05\x12\n\n\x02y3\x18\x06 \x01(\x05\x12\n\n\x02x4\x18\x07 \x01(\x05\x12\n\n\x02y4\x18\x08 \x01(\x05\x12\r\n\x05\x61ngle\x18\t \x01(\x02\"@\n\x04\x42\x42ox\x12\x0c\n\x04left\x18\x01 \x01(\x05\x12\x0b\n\x03top\x18\x02 \x01(\x05\x12\r\n\x05right\x18\x03 \x01(\x05\x12\x0e\n\x06\x62ottom\x18\x04 \x01(\x05\"t\n\x13TextFullDataRotated\x12\x0c\n\x04word\x18\x01 \x01(\t\x12)\n\x04rbox\x18\x02 \x01(\x0b\x32\x1b.ocr_structuring.RotatedBox\x12\r\n\x05label\x18\x03 \x01(\x05\x12\x15\n\rprobabilities\x18\x04 \x03(\x02\"\xe3\x02\n\x19StructuringRequestRotated\x12=\n\x0ftexts_full_data\x18\x01 \x03(\x0b\x32$.ocr_structuring.TextFullDataRotated\x12\x0f\n\x07version\x18\x02 \x01(\t\x12.\n\nimage_data\x18\x03 \x01(\x0b\x32\x1a.ocr_structuring.ImageData\x12\x12\n\nclass_name\x18\x04 \x01(\t\x12\x15\n\rprimary_class\x18\x05 \x01(\x05\x12\x17\n\x0fsecondary_class\x18\x06 \x01(\x05\x12?\n\x11labeled_bbox_list\x18\x07 \x03(\x0b\x32$.ocr_structuring.RotatedBoxWithLabel\x12\x41\n\x11\x64\x65tection_results\x18\x08 \x03(\x0b\x32&.ocr_structuring.SingleDetectionResult\"g\n\x0cTextFullData\x12\x0c\n\x04word\x18\x01 \x01(\t\x12#\n\x04\x62\x62ox\x18\x02 \x01(\x0b\x32\x15.ocr_structuring.BBox\x12\r\n\x05label\x18\x03 \x01(\x05\x12\x15\n\rprobabilities\x18\x04 \x03(\x02\"O\n\x13RotatedBoxWithLabel\x12)\n\x04\x62\x62ox\x18\x01 \x01(\x0b\x32\x1b.ocr_structuring.RotatedBox\x12\r\n\x05label\x18\x03 \x01(\x05\"\xd5\x02\n\x12StructuringRequest\x12\x36\n\x0ftexts_full_data\x18\x01 \x03(\x0b\x32\x1d.ocr_structuring.TextFullData\x12\x0f\n\x07version\x18\x02 \x01(\t\x12.\n\nimage_data\x18\x03 \x01(\x0b\x32\x1a.ocr_structuring.ImageData\x12\x12\n\nclass_name\x18\x04 \x01(\t\x12\x15\n\rprimary_class\x18\x05 \x01(\x05\x12\x17\n\x0fsecondary_class\x18\x06 \x01(\x05\x12?\n\x11labeled_bbox_list\x18\x07 \x03(\x0b\x32$.ocr_structuring.RotatedBoxWithLabel\x12\x41\n\x11\x64\x65tection_results\x18\x08 \x03(\x0b\x32&.ocr_structuring.SingleDetectionResult\"X\n\x15SingleDetectionResult\x12?\n\x11labeled_bbox_list\x18\x07 \x03(\x0b\x32$.ocr_structuring.RotatedBoxWithLabel\"+\n\x13StructuringTimeInfo\x12\x14\n\x0c\x65lapsed_time\x18\x01 \x01(\x03\"\x89\x01\n\x13StructuringResponse\x12\x0c\n\x04\x63ode\x18\x01 \x01(\x05\x12\x0f\n\x07message\x18\x02 \x01(\t\x12\x0c\n\x04\x64\x61ta\x18\x03 \x01(\t\x12\x37\n\ttime_info\x18\x04 \x01(\x0b\x32$.ocr_structuring.StructuringTimeInfo\x12\x0c\n\x04meta\x18\x05 \x01(\t\"\x84\x02\n\x0fSingleImageInfo\x12=\n\x0ftexts_full_data\x18\x01 \x03(\x0b\x32$.ocr_structuring.TextFullDataRotated\x12.\n\nimage_data\x18\x02 \x01(\x0b\x32\x1a.ocr_structuring.ImageData\x12?\n\x11labeled_bbox_list\x18\x03 \x03(\x0b\x32$.ocr_structuring.RotatedBoxWithLabel\x12\x41\n\x11\x64\x65tection_results\x18\x04 \x03(\x0b\x32&.ocr_structuring.SingleDetectionResult\"\x7f\n\x1cMultiImageStructuringRequest\x12:\n\x10multi_image_info\x18\x01 \x03(\x0b\x32 .ocr_structuring.SingleImageInfo\x12\x0f\n\x07version\x18\x02 \x01(\t\x12\x12\n\nclass_name\x18\x03 \x01(\t2\xb7\x02\n\x0bStructuring\x12V\n\x07Process\x12#.ocr_structuring.StructuringRequest\x1a$.ocr_structuring.StructuringResponse\"\x00\x12\x64\n\x0eProcessRotated\x12*.ocr_structuring.StructuringRequestRotated\x1a$.ocr_structuring.StructuringResponse\"\x00\x12j\n\x11ProcessMultiImage\x12-.ocr_structuring.MultiImageStructuringRequest\x1a$.ocr_structuring.StructuringResponse\"\x00\x62\x06proto3')
)




_IMAGEDATA = _descriptor.Descriptor(
  name='ImageData',
  full_name='ocr_structuring.ImageData',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='width', full_name='ocr_structuring.ImageData.width', index=0,
      number=1, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='height', full_name='ocr_structuring.ImageData.height', index=1,
      number=2, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='channels', full_name='ocr_structuring.ImageData.channels', index=2,
      number=3, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='data', full_name='ocr_structuring.ImageData.data', index=3,
      number=4, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=_b(""),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='shm', full_name='ocr_structuring.ImageData.shm', index=4,
      number=5, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=61,
  serialized_end=148,
)


_ROTATEDBOX = _descriptor.Descriptor(
  name='RotatedBox',
  full_name='ocr_structuring.RotatedBox',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='x1', full_name='ocr_structuring.RotatedBox.x1', index=0,
      number=1, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='y1', full_name='ocr_structuring.RotatedBox.y1', index=1,
      number=2, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='x2', full_name='ocr_structuring.RotatedBox.x2', index=2,
      number=3, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='y2', full_name='ocr_structuring.RotatedBox.y2', index=3,
      number=4, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='x3', full_name='ocr_structuring.RotatedBox.x3', index=4,
      number=5, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='y3', full_name='ocr_structuring.RotatedBox.y3', index=5,
      number=6, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='x4', full_name='ocr_structuring.RotatedBox.x4', index=6,
      number=7, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='y4', full_name='ocr_structuring.RotatedBox.y4', index=7,
      number=8, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='angle', full_name='ocr_structuring.RotatedBox.angle', index=8,
      number=9, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=150,
  serialized_end=273,
)


_BBOX = _descriptor.Descriptor(
  name='BBox',
  full_name='ocr_structuring.BBox',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='left', full_name='ocr_structuring.BBox.left', index=0,
      number=1, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='top', full_name='ocr_structuring.BBox.top', index=1,
      number=2, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='right', full_name='ocr_structuring.BBox.right', index=2,
      number=3, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='bottom', full_name='ocr_structuring.BBox.bottom', index=3,
      number=4, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=275,
  serialized_end=339,
)


_TEXTFULLDATAROTATED = _descriptor.Descriptor(
  name='TextFullDataRotated',
  full_name='ocr_structuring.TextFullDataRotated',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='word', full_name='ocr_structuring.TextFullDataRotated.word', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='rbox', full_name='ocr_structuring.TextFullDataRotated.rbox', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='label', full_name='ocr_structuring.TextFullDataRotated.label', index=2,
      number=3, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='probabilities', full_name='ocr_structuring.TextFullDataRotated.probabilities', index=3,
      number=4, type=2, cpp_type=6, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=341,
  serialized_end=457,
)


_STRUCTURINGREQUESTROTATED = _descriptor.Descriptor(
  name='StructuringRequestRotated',
  full_name='ocr_structuring.StructuringRequestRotated',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='texts_full_data', full_name='ocr_structuring.StructuringRequestRotated.texts_full_data', index=0,
      number=1, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='version', full_name='ocr_structuring.StructuringRequestRotated.version', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='image_data', full_name='ocr_structuring.StructuringRequestRotated.image_data', index=2,
      number=3, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='class_name', full_name='ocr_structuring.StructuringRequestRotated.class_name', index=3,
      number=4, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='primary_class', full_name='ocr_structuring.StructuringRequestRotated.primary_class', index=4,
      number=5, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='secondary_class', full_name='ocr_structuring.StructuringRequestRotated.secondary_class', index=5,
      number=6, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='labeled_bbox_list', full_name='ocr_structuring.StructuringRequestRotated.labeled_bbox_list', index=6,
      number=7, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='detection_results', full_name='ocr_structuring.StructuringRequestRotated.detection_results', index=7,
      number=8, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=460,
  serialized_end=815,
)


_TEXTFULLDATA = _descriptor.Descriptor(
  name='TextFullData',
  full_name='ocr_structuring.TextFullData',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='word', full_name='ocr_structuring.TextFullData.word', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='bbox', full_name='ocr_structuring.TextFullData.bbox', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='label', full_name='ocr_structuring.TextFullData.label', index=2,
      number=3, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='probabilities', full_name='ocr_structuring.TextFullData.probabilities', index=3,
      number=4, type=2, cpp_type=6, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=817,
  serialized_end=920,
)


_ROTATEDBOXWITHLABEL = _descriptor.Descriptor(
  name='RotatedBoxWithLabel',
  full_name='ocr_structuring.RotatedBoxWithLabel',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='bbox', full_name='ocr_structuring.RotatedBoxWithLabel.bbox', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='label', full_name='ocr_structuring.RotatedBoxWithLabel.label', index=1,
      number=3, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=922,
  serialized_end=1001,
)


_STRUCTURINGREQUEST = _descriptor.Descriptor(
  name='StructuringRequest',
  full_name='ocr_structuring.StructuringRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='texts_full_data', full_name='ocr_structuring.StructuringRequest.texts_full_data', index=0,
      number=1, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='version', full_name='ocr_structuring.StructuringRequest.version', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='image_data', full_name='ocr_structuring.StructuringRequest.image_data', index=2,
      number=3, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='class_name', full_name='ocr_structuring.StructuringRequest.class_name', index=3,
      number=4, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='primary_class', full_name='ocr_structuring.StructuringRequest.primary_class', index=4,
      number=5, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='secondary_class', full_name='ocr_structuring.StructuringRequest.secondary_class', index=5,
      number=6, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='labeled_bbox_list', full_name='ocr_structuring.StructuringRequest.labeled_bbox_list', index=6,
      number=7, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='detection_results', full_name='ocr_structuring.StructuringRequest.detection_results', index=7,
      number=8, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=1004,
  serialized_end=1345,
)


_SINGLEDETECTIONRESULT = _descriptor.Descriptor(
  name='SingleDetectionResult',
  full_name='ocr_structuring.SingleDetectionResult',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='labeled_bbox_list', full_name='ocr_structuring.SingleDetectionResult.labeled_bbox_list', index=0,
      number=7, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=1347,
  serialized_end=1435,
)


_STRUCTURINGTIMEINFO = _descriptor.Descriptor(
  name='StructuringTimeInfo',
  full_name='ocr_structuring.StructuringTimeInfo',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='elapsed_time', full_name='ocr_structuring.StructuringTimeInfo.elapsed_time', index=0,
      number=1, type=3, cpp_type=2, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=1437,
  serialized_end=1480,
)


_STRUCTURINGRESPONSE = _descriptor.Descriptor(
  name='StructuringResponse',
  full_name='ocr_structuring.StructuringResponse',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='code', full_name='ocr_structuring.StructuringResponse.code', index=0,
      number=1, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='message', full_name='ocr_structuring.StructuringResponse.message', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='data', full_name='ocr_structuring.StructuringResponse.data', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='time_info', full_name='ocr_structuring.StructuringResponse.time_info', index=3,
      number=4, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='meta', full_name='ocr_structuring.StructuringResponse.meta', index=4,
      number=5, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=1483,
  serialized_end=1620,
)


_SINGLEIMAGEINFO = _descriptor.Descriptor(
  name='SingleImageInfo',
  full_name='ocr_structuring.SingleImageInfo',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='texts_full_data', full_name='ocr_structuring.SingleImageInfo.texts_full_data', index=0,
      number=1, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='image_data', full_name='ocr_structuring.SingleImageInfo.image_data', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='labeled_bbox_list', full_name='ocr_structuring.SingleImageInfo.labeled_bbox_list', index=2,
      number=3, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='detection_results', full_name='ocr_structuring.SingleImageInfo.detection_results', index=3,
      number=4, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=1623,
  serialized_end=1883,
)


_MULTIIMAGESTRUCTURINGREQUEST = _descriptor.Descriptor(
  name='MultiImageStructuringRequest',
  full_name='ocr_structuring.MultiImageStructuringRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='multi_image_info', full_name='ocr_structuring.MultiImageStructuringRequest.multi_image_info', index=0,
      number=1, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='version', full_name='ocr_structuring.MultiImageStructuringRequest.version', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='class_name', full_name='ocr_structuring.MultiImageStructuringRequest.class_name', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=1885,
  serialized_end=2012,
)

_TEXTFULLDATAROTATED.fields_by_name['rbox'].message_type = _ROTATEDBOX
_STRUCTURINGREQUESTROTATED.fields_by_name['texts_full_data'].message_type = _TEXTFULLDATAROTATED
_STRUCTURINGREQUESTROTATED.fields_by_name['image_data'].message_type = _IMAGEDATA
_STRUCTURINGREQUESTROTATED.fields_by_name['labeled_bbox_list'].message_type = _ROTATEDBOXWITHLABEL
_STRUCTURINGREQUESTROTATED.fields_by_name['detection_results'].message_type = _SINGLEDETECTIONRESULT
_TEXTFULLDATA.fields_by_name['bbox'].message_type = _BBOX
_ROTATEDBOXWITHLABEL.fields_by_name['bbox'].message_type = _ROTATEDBOX
_STRUCTURINGREQUEST.fields_by_name['texts_full_data'].message_type = _TEXTFULLDATA
_STRUCTURINGREQUEST.fields_by_name['image_data'].message_type = _IMAGEDATA
_STRUCTURINGREQUEST.fields_by_name['labeled_bbox_list'].message_type = _ROTATEDBOXWITHLABEL
_STRUCTURINGREQUEST.fields_by_name['detection_results'].message_type = _SINGLEDETECTIONRESULT
_SINGLEDETECTIONRESULT.fields_by_name['labeled_bbox_list'].message_type = _ROTATEDBOXWITHLABEL
_STRUCTURINGRESPONSE.fields_by_name['time_info'].message_type = _STRUCTURINGTIMEINFO
_SINGLEIMAGEINFO.fields_by_name['texts_full_data'].message_type = _TEXTFULLDATAROTATED
_SINGLEIMAGEINFO.fields_by_name['image_data'].message_type = _IMAGEDATA
_SINGLEIMAGEINFO.fields_by_name['labeled_bbox_list'].message_type = _ROTATEDBOXWITHLABEL
_SINGLEIMAGEINFO.fields_by_name['detection_results'].message_type = _SINGLEDETECTIONRESULT
_MULTIIMAGESTRUCTURINGREQUEST.fields_by_name['multi_image_info'].message_type = _SINGLEIMAGEINFO
DESCRIPTOR.message_types_by_name['ImageData'] = _IMAGEDATA
DESCRIPTOR.message_types_by_name['RotatedBox'] = _ROTATEDBOX
DESCRIPTOR.message_types_by_name['BBox'] = _BBOX
DESCRIPTOR.message_types_by_name['TextFullDataRotated'] = _TEXTFULLDATAROTATED
DESCRIPTOR.message_types_by_name['StructuringRequestRotated'] = _STRUCTURINGREQUESTROTATED
DESCRIPTOR.message_types_by_name['TextFullData'] = _TEXTFULLDATA
DESCRIPTOR.message_types_by_name['RotatedBoxWithLabel'] = _ROTATEDBOXWITHLABEL
DESCRIPTOR.message_types_by_name['StructuringRequest'] = _STRUCTURINGREQUEST
DESCRIPTOR.message_types_by_name['SingleDetectionResult'] = _SINGLEDETECTIONRESULT
DESCRIPTOR.message_types_by_name['StructuringTimeInfo'] = _STRUCTURINGTIMEINFO
DESCRIPTOR.message_types_by_name['StructuringResponse'] = _STRUCTURINGRESPONSE
DESCRIPTOR.message_types_by_name['SingleImageInfo'] = _SINGLEIMAGEINFO
DESCRIPTOR.message_types_by_name['MultiImageStructuringRequest'] = _MULTIIMAGESTRUCTURINGREQUEST
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

ImageData = _reflection.GeneratedProtocolMessageType('ImageData', (_message.Message,), dict(
  DESCRIPTOR = _IMAGEDATA,
  __module__ = 'ocr_structuring.protos.structuring_pb2'
  # @@protoc_insertion_point(class_scope:ocr_structuring.ImageData)
  ))
_sym_db.RegisterMessage(ImageData)

RotatedBox = _reflection.GeneratedProtocolMessageType('RotatedBox', (_message.Message,), dict(
  DESCRIPTOR = _ROTATEDBOX,
  __module__ = 'ocr_structuring.protos.structuring_pb2'
  # @@protoc_insertion_point(class_scope:ocr_structuring.RotatedBox)
  ))
_sym_db.RegisterMessage(RotatedBox)

BBox = _reflection.GeneratedProtocolMessageType('BBox', (_message.Message,), dict(
  DESCRIPTOR = _BBOX,
  __module__ = 'ocr_structuring.protos.structuring_pb2'
  # @@protoc_insertion_point(class_scope:ocr_structuring.BBox)
  ))
_sym_db.RegisterMessage(BBox)

TextFullDataRotated = _reflection.GeneratedProtocolMessageType('TextFullDataRotated', (_message.Message,), dict(
  DESCRIPTOR = _TEXTFULLDATAROTATED,
  __module__ = 'ocr_structuring.protos.structuring_pb2'
  # @@protoc_insertion_point(class_scope:ocr_structuring.TextFullDataRotated)
  ))
_sym_db.RegisterMessage(TextFullDataRotated)

StructuringRequestRotated = _reflection.GeneratedProtocolMessageType('StructuringRequestRotated', (_message.Message,), dict(
  DESCRIPTOR = _STRUCTURINGREQUESTROTATED,
  __module__ = 'ocr_structuring.protos.structuring_pb2'
  # @@protoc_insertion_point(class_scope:ocr_structuring.StructuringRequestRotated)
  ))
_sym_db.RegisterMessage(StructuringRequestRotated)

TextFullData = _reflection.GeneratedProtocolMessageType('TextFullData', (_message.Message,), dict(
  DESCRIPTOR = _TEXTFULLDATA,
  __module__ = 'ocr_structuring.protos.structuring_pb2'
  # @@protoc_insertion_point(class_scope:ocr_structuring.TextFullData)
  ))
_sym_db.RegisterMessage(TextFullData)

RotatedBoxWithLabel = _reflection.GeneratedProtocolMessageType('RotatedBoxWithLabel', (_message.Message,), dict(
  DESCRIPTOR = _ROTATEDBOXWITHLABEL,
  __module__ = 'ocr_structuring.protos.structuring_pb2'
  # @@protoc_insertion_point(class_scope:ocr_structuring.RotatedBoxWithLabel)
  ))
_sym_db.RegisterMessage(RotatedBoxWithLabel)

StructuringRequest = _reflection.GeneratedProtocolMessageType('StructuringRequest', (_message.Message,), dict(
  DESCRIPTOR = _STRUCTURINGREQUEST,
  __module__ = 'ocr_structuring.protos.structuring_pb2'
  # @@protoc_insertion_point(class_scope:ocr_structuring.StructuringRequest)
  ))
_sym_db.RegisterMessage(StructuringRequest)

SingleDetectionResult = _reflection.GeneratedProtocolMessageType('SingleDetectionResult', (_message.Message,), dict(
  DESCRIPTOR = _SINGLEDETECTIONRESULT,
  __module__ = 'ocr_structuring.protos.structuring_pb2'
  # @@protoc_insertion_point(class_scope:ocr_structuring.SingleDetectionResult)
  ))
_sym_db.RegisterMessage(SingleDetectionResult)

StructuringTimeInfo = _reflection.GeneratedProtocolMessageType('StructuringTimeInfo', (_message.Message,), dict(
  DESCRIPTOR = _STRUCTURINGTIMEINFO,
  __module__ = 'ocr_structuring.protos.structuring_pb2'
  # @@protoc_insertion_point(class_scope:ocr_structuring.StructuringTimeInfo)
  ))
_sym_db.RegisterMessage(StructuringTimeInfo)

StructuringResponse = _reflection.GeneratedProtocolMessageType('StructuringResponse', (_message.Message,), dict(
  DESCRIPTOR = _STRUCTURINGRESPONSE,
  __module__ = 'ocr_structuring.protos.structuring_pb2'
  # @@protoc_insertion_point(class_scope:ocr_structuring.StructuringResponse)
  ))
_sym_db.RegisterMessage(StructuringResponse)

SingleImageInfo = _reflection.GeneratedProtocolMessageType('SingleImageInfo', (_message.Message,), dict(
  DESCRIPTOR = _SINGLEIMAGEINFO,
  __module__ = 'ocr_structuring.protos.structuring_pb2'
  # @@protoc_insertion_point(class_scope:ocr_structuring.SingleImageInfo)
  ))
_sym_db.RegisterMessage(SingleImageInfo)

MultiImageStructuringRequest = _reflection.GeneratedProtocolMessageType('MultiImageStructuringRequest', (_message.Message,), dict(
  DESCRIPTOR = _MULTIIMAGESTRUCTURINGREQUEST,
  __module__ = 'ocr_structuring.protos.structuring_pb2'
  # @@protoc_insertion_point(class_scope:ocr_structuring.MultiImageStructuringRequest)
  ))
_sym_db.RegisterMessage(MultiImageStructuringRequest)



_STRUCTURING = _descriptor.ServiceDescriptor(
  name='Structuring',
  full_name='ocr_structuring.Structuring',
  file=DESCRIPTOR,
  index=0,
  serialized_options=None,
  serialized_start=2015,
  serialized_end=2326,
  methods=[
  _descriptor.MethodDescriptor(
    name='Process',
    full_name='ocr_structuring.Structuring.Process',
    index=0,
    containing_service=None,
    input_type=_STRUCTURINGREQUEST,
    output_type=_STRUCTURINGRESPONSE,
    serialized_options=None,
  ),
  _descriptor.MethodDescriptor(
    name='ProcessRotated',
    full_name='ocr_structuring.Structuring.ProcessRotated',
    index=1,
    containing_service=None,
    input_type=_STRUCTURINGREQUESTROTATED,
    output_type=_STRUCTURINGRESPONSE,
    serialized_options=None,
  ),
  _descriptor.MethodDescriptor(
    name='ProcessMultiImage',
    full_name='ocr_structuring.Structuring.ProcessMultiImage',
    index=2,
    containing_service=None,
    input_type=_MULTIIMAGESTRUCTURINGREQUEST,
    output_type=_STRUCTURINGRESPONSE,
    serialized_options=None,
  ),
])
_sym_db.RegisterServiceDescriptor(_STRUCTURING)

DESCRIPTOR.services_by_name['Structuring'] = _STRUCTURING

# @@protoc_insertion_point(module_scope)
