import os
import codecs
import torch
import json

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
MODELS_DIR = os.path.join(CURRENT_DIR, 'models')
VOCAB_DIR = os.path.join(CURRENT_DIR, 'vocab')


class GRUModel(object):
    def __init__(self, torch_script_model, word_dict_path):

        with codecs.open(os.path.join(VOCAB_DIR, word_dict_path), 'r', 'utf-8') as f:
            self.word_dict = json.loads(f.read(), encoding='utf-8')

        self.model = torch.jit.load(os.path.join(MODELS_DIR, torch_script_model))
        self.model.eval()

    def run(self, x):
        if x.strip() == '':
            return False
        x = [c for c in x]
        x = [self.word_dict[word] if self.word_dict.get(word) else 1 for word in x]
        inputs = torch.tensor(x, dtype=torch.long).reshape(1, -1)
        pred = self.model(inputs)
        pred = torch.where(pred >= 0.7, torch.tensor([1], dtype=torch.float), torch.tensor([0], dtype=torch.float))
        return pred.item() == 1


gru_model = GRUModel('word_classify-cpu.pt', 'word2vec_char.json')

if __name__ == '__main__':
    with open(os.path.join(VOCAB_DIR, 'detail_charges.txt'), 'r', encoding='utf-8') as f:
        data = f.readlines()
        data = [d.split(' ') for d in data]
        test_data = [d[0] for d in data]
        test_label = [d[1].strip() for d in data]

    total = len(test_data)
    acc = 0
    for i, data in enumerate(test_data):
        result = gru_model.run(data)
        result = '1' if result else '0'
        print(f'{data} {test_label[i]} {result}')
        if result == test_label[i]:
           acc += 1.0

    print(acc / total)









