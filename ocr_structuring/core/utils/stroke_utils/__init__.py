"""
用于返回汉字的笔画数

.. code-block:: python

   from ocr_structuring.core.utils.stroke_utils import stroke_utils
   strokes = stroke_utils.get_stroke_of_string('一二')
   # [1, 2]
"""

from .strokes_util import stroke_utils
