from typing import Dict, List
import re
from numpy import ndarray

from ocr_structuring.core.models.structure_item import StructureItem
from ocr_structuring.core.template.common_parser import CommonParser
from ocr_structuring.core.template.tp_fg_item import FGItem
from ocr_structuring.core.template.tp_node_item import TpNodeItem


class TplBased(CommonParser):
    def tmpl_post_proc(self, structure_items: Dict[str, StructureItem], fg_items: Dict[str, FGItem], img: ndarray):
        """
        :param img: 经过roi、旋转、小角度处理后的图片（如果相关模块已启用）
        :param structure_items: dict. key: item_name value: StructureItem
        :return: 与 structure_items 的类型相同，可能会添加新的 item，或者修改原有 item 的值
        :param fg_items: dict. key: item_name.  value: FGItem
        """
        return structure_items

    # def _pre_func_xxx(self,
    #                   item_name: str,
    #                   passed_nodes: Dict[str, TpNodeItem],
    #                   node_items: Dict[str, TpNodeItem],
    #                   img: ndarray):
    #     pass

    # def _post_func_xxx(self,
    #                    item_name: str,
    #                    passed_nodes: Dict[str, TpNodeItem],
    #                    node_items: Dict[str, TpNodeItem],
    #                    img: ndarray) -> (str, List[float]):
    #     return self._post_func_max_w_regex(item_name, passed_nodes, node_items, img)

    def _post_func_name(self,
                        item_name: str,
                        passed_nodes: Dict[str, TpNodeItem],
                        node_items: Dict[str, TpNodeItem],
                        img: ndarray) -> (str, List[float]):

        mylist = []
        for passed_node in passed_nodes.values():
            # if passed_node.text == '人':
            #     continue
            # if passed_node.probability < 0.5:
            #     continue
            mylist.append(passed_node.text)
        text = ''.join([re.sub('\d+', '', i) for i in mylist])
        return text, [1]
        # cn_text
        # passed_node.

    def _post_func_address(self,
                           item_name: str,
                           passed_nodes: Dict[str, TpNodeItem],
                           node_items: Dict[str, TpNodeItem],
                           img: ndarray) -> (str, List[float]):
        
        mylist=[]
        score=[]
        for k,v in passed_nodes.items():
            mylist.append(v.text)
            score.extend(v.scores)
        return ''.join(mylist), score


        # print('passed_nodes',passed_nodes)
        # print('*'*50)
        

    def _post_func_prevelige(self,
                           item_name: str,
                           passed_nodes: Dict[str, TpNodeItem],
                           node_items: Dict[str, TpNodeItem],
                           img: ndarray) -> (str, List[float]):
        content=[]
        for k,v in passed_nodes.items():
            if v.text.find('转让') !=-1:
                continue
            content.append(v.text)
        return ''.join(content), [1]
        

    def _post_func_get_way(self,
                        item_name: str,
                        passed_nodes: Dict[str, TpNodeItem],
                        node_items: Dict[str, TpNodeItem],
                        img: ndarray) -> (str, List[float]):
        content=[]
        for k,v in passed_nodes.items():
            if v.text=='出让' or v.text=="转让":
                content.append(v.text)      
        return ''.join(content), [1]


    def _post_func_land_no(self,
                        item_name: str,
                        passed_nodes: Dict[str, TpNodeItem],
                        node_items: Dict[str, TpNodeItem],
                        img: ndarray) -> (str, List[float]):

        texts=[i.text for i in passed_nodes.values() if not i.text.find('.')!=-1 ]
        return ''.join(texts), [1]


    def _post_func_land_area(self,
                        item_name: str,
                        passed_nodes: Dict[str, TpNodeItem],
                        node_items: Dict[str, TpNodeItem],
                        img: ndarray) -> (str, List[float]):
    
         texts=[i.text for i in passed_nodes.values()]
         return ''.join(texts), [1]

    def _post_func_use_area(self,
                        item_name: str,
                        passed_nodes: Dict[str, TpNodeItem],
                        node_items: Dict[str, TpNodeItem],
                        img: ndarray) -> (str, List[float]):

        texts=[i.text for i in passed_nodes.values()]
        return ''.join(texts), [1]

    # def _post_func_private_area(self,
    #                     item_name: str,
    #                     passed_nodes: Dict[str, TpNodeItem],
    #                     node_items: Dict[str, TpNodeItem],
    #                     img: ndarray) -> (str, List[float]):
    #     pass

    def _post_func_com_area(self,
                        item_name: str,
                        passed_nodes: Dict[str, TpNodeItem],
                        node_items: Dict[str, TpNodeItem],
                        img: ndarray) -> (str, List[float]):

        # sorted_passed_nodes = sorted([node for node in passed_nodes.values()], key=lambda x: x.bbox.left,reverse=False)
        # texts=[(i.text,i.scores) for i in sorted_passed_nodes]
        # print('111',texts,texts[1][1])
        # return texts[1][0], texts[1][1]
        texts=[i.text for i in passed_nodes.values()]
        return ''.join(texts), [1]

    def _post_func_use_time(self,
                        item_name: str,
                        passed_nodes: Dict[str, TpNodeItem],
                        node_items: Dict[str, TpNodeItem],
                        img: ndarray) -> (str, List[float]):

         texts=[i.text for i in passed_nodes.values()]
         return ''.join(texts), [1]

    def _post_func_floor_no(self,
                        item_name: str,
                        passed_nodes: Dict[str, TpNodeItem],
                        node_items: Dict[str, TpNodeItem],
                        img: ndarray) -> (str, List[float]):

        text,score=self._post_func_max_w_regex(item_name,passed_nodes,node_items,img)
        # print(text,score)
        # _passed_nodes = sorted([node for node in passed_nodes.values()], key=lambda x: x.bbox.left,reverse=False)
        # print(passed_nodes)
        # print('111',node_items)
        # for k,v in node_items.items():
        #     if v.text=='幢':
        #         print(v)
        #         height=abs(v.bbox.top-v.bbox.bottom)
        #         h1=v.bbox.cy
        # print(height/2,h1)
        # for v in  passed_nodes.values():
        #     h2=v.bbox.cy
        #     if abs(h1-h2) < height/2:
        #         print('true',h2)

                
        num=[i for i in list(text) if i in list('详见附记')]
        if len(num)>=2:
            return '详见附记', [1]


        return text,score
        # texts=[i.text for i in passed_nodes.values()]
        # text=''.join(texts)
        # num=[i for i in list(text) if i in list('详见附记')]
        # if len(num)>=2:
        #     return '详见附记', [1]
        # return ''.join(texts), [1]

    def _post_func_room_no(self,
                        item_name: str,
                        passed_nodes: Dict[str, TpNodeItem],
                        node_items: Dict[str, TpNodeItem],
                        img: ndarray) -> (str, List[float]):

        sort_passed_nodes=sorted([node for node in passed_nodes.values()], key=lambda x: x.bbox.left,reverse=False)
        # print(sort_passed_nodes)
        text=sort_passed_nodes[0].text
        text=re.sub('_','',text)
        # texts=[i.text for i in passed_nodes.values()]
        # text=''.join(texts)
        
        # result=re.search('\d+',text)
        # if result:
        #     return result.group(),[1]

        num=[i for i in list(text) if i in list('详见附记')]
        if len(num)>=2:
            return '详见附记', [1]
        
        return text, [1]


    def _post_func_build_area(self,
                        item_name: str,
                        passed_nodes: Dict[str, TpNodeItem],
                        node_items: Dict[str, TpNodeItem],
                        img: ndarray) -> (str, List[float]):

        texts=[i.text for i in passed_nodes.values()]
        text=''.join(texts)
        result=re.search('\d+\.\d+',text)
        if result:
            return result.group(),[1]

        num=[i for i in list(text) if i in list('详见附记')]
        if len(num)>=2:
            text='详见附记'
            return text, [1]
        else:
            return '',[1]

    def _post_func_build_type(self,
                        item_name: str,
                        passed_nodes: Dict[str, TpNodeItem],
                        node_items: Dict[str, TpNodeItem],
                        img: ndarray) -> (str, List[float]):
        
        text=[i.text for i in passed_nodes.values()][0]
        if text.find('公寓')!=-1:
            i='公寓'
        elif text.find('联列住宅')!=-1:
            i='联列住宅'
        else:
            return '详见附记',[1]
        return i, [1]

    def _post_func_all_layer(self,
                        item_name: str,
                        passed_nodes: Dict[str, TpNodeItem],
                        node_items: Dict[str, TpNodeItem],
                        img: ndarray) -> (str, List[float]):
        
        texts=[i.text for i in passed_nodes.values()]
        text=''.join(texts)
        result=re.search('\d{1,2}',text)
        if result:
            return result.group(),[1]

        num=[i for i in list(text) if i in list('详见附记')]
        if len(num)>=2:
            text='详见附记'
            return text, [1]
        else:
            return '',[1]
        # sorted_passed_nodes = sorted([node for node in passed_nodes.values()], key=lambda x: x.bbox.left,reverse=False)
        # # print(sorted_passed_nodes)   [-19 [1015 537 1063 564], 19日6、房瑞广段进 [1020 531 1426 575]]
        # texts=[i.text for i in sorted_passed_nodes]
        # return ''.join(texts[0]), [1]
        # return self._post_func_max_w_regex(item_name, passed_nodes, node_items, img)

    
    def _post_func_done_time(self,
                        item_name: str,
                        passed_nodes: Dict[str, TpNodeItem],
                        node_items: Dict[str, TpNodeItem],
                        img: ndarray) -> (str, List[float]):

        texts=[i.text for i in passed_nodes.values()]
        text=''.join(texts)
        num=[i for i in list(text) if i in list('详见附记')]
        if len(num)>=2:
            year='详见附记'
            return year, [1]

        if re.search('\d+',text):
            nums=re.findall('\d+',text)
            for num in nums:
                if len(num)==4:
                    year=num+'年'
                    return year, [1]
        
        return '', [1]

    
    def _post_func_company(self,
                        item_name: str,
                        passed_nodes: Dict[str, TpNodeItem],
                        node_items: Dict[str, TpNodeItem],
                        img: ndarray) -> (str, List[float]):

        texts,score=self._post_func_max_w_regex(item_name, passed_nodes, node_items, img)
        # print(texts,score)
        # texts=[i.text for i in passed_nodes.values()]
        # for k,v in node_items.items():
        #     print(k,(type(v),v.cn_text,v.en_text,v.filter_areas,v.filter_regexes,v.get_final_w(),v.get_scores()))
        return ''.join(texts), [1]

    