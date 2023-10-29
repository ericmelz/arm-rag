import datasets

def load_gsm():
    data_path = 'data/gsm/STaR/train_rand_split.jsonl'
    dataset = load_dataset(path='json', data_files=data_path, split='train')
    
