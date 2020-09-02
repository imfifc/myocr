"""
中国 56 个名族，不同的名族中不会出现重复的字，因此这个模块提供了一个字符的查询表，可以通过某个字符查询对应的名族全称

.. code-block:: python

   from ocr_structuring.core.utils.chinese_ethnic import ethnices_dict
   ethnic = ethnics_dict["哈"]
   # 哈尼族

"""


from .ethnices import ethnices

ethnices_dict = {}
for ethnic in ethnices:
    for c in ethnic:
        if c == "族":
            continue
        ethnices_dict[c] = ethnic
