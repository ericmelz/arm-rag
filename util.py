from datasets import load_dataset

def load_gsm():
    data_path = 'data/gsm/STaR/train_rand_split.jsonl'
    dataset = load_dataset(path='json', data_files=data_path, split='train')
    return dataset
    
