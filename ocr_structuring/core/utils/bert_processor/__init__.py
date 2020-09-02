from bert_base.client import BertClient
from ocr_structuring.settings import MyConfig


def get_NER_result(target_string):
    if len(target_string) <= 126:
        segments = [target_string]
    else:
        segments = [
            target_string[i : i + 126] for i in range(0, len(target_string), 126)
        ]
    res_dict = {}
    res_dict = info_retrieval(segments, res_dict)
    return res_dict


def info_retrieval(segments, targets):
    cfg = MyConfig()
    for target_string in segments:
        with BertClient(
            ip=cfg.ner_ip_addr.value,
            port=cfg.ner_port_in.value,
            port_out=cfg.ner_port_out.value,
            mode="NER",
        ) as bc:
            rst = bc.encode([list(target_string)], is_tokenized=True)
            zipped = list(zip(list(target_string), rst[0]))
            rolling_content = ""
            rolling_tag = "O"
            for i in range(len(zipped)):
                current_tag = zipped[i][1].split("-")[-1]
                if current_tag != rolling_tag or zipped[i][1].startswith("B"):
                    targets.setdefault(rolling_tag, [])
                    targets[rolling_tag].append(rolling_content)
                    rolling_tag = current_tag
                    rolling_content = ""
                rolling_content += zipped[i][0]
            if len(rolling_content) != 0:
                targets.setdefault(rolling_tag, [])
                targets[rolling_tag].append(rolling_content)
    del targets["O"]
    return targets
