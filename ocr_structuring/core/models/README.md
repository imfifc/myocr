- StructureResult：所有结构化 Processor 返回的结果应该继承这个基类，并实现 `to_dict()` 返回一个只包含基础类型的 `Dict`
- StructureItem：可以使用 `utils.to_dict()` 把以下两种格式的数据转成只包含基础数据类型的 plain dict
    - `Dict[str, StructureItem]` 用于表示 `key-value` 形式的结构化结果
    - `List[Dict[str, StructureItem]]` 表格类型
- MultiImgResult：用于表示多张图片的结构化结果。例如航空发票一套可能有 3 张，这个类中会保存类型，每张的结构化结果
以及多张合并的结构化结果(实现 `merge_per_page_result` 函数)
