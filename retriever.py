from pyserini.search import FaissSearcher
from datasets import load_dataset


class Retriever:
    def __init__(self,
                 index_dir='indexes/exp5_correct',
                 dataset_file='data/results/exp5/exp5.jsonl'):
        self.dataset = load_dataset(path='json', data_files=dataset_file, split='train')
        self.encoder = FaissSearcher._init_encoder_from_str('facebook/contriever-msmarco')
        self.threads = 16
        self.searcher = FaissSearcher(index_dir=index_dir,
                                      query_encoder=self.encoder)
        self.dataset_id_to_index = {}
        for i, docid in enumerate(self.dataset['_id']):
            self.dataset_id_to_index[docid] = i

    def retrieve(self, query, k=5, obfuscate=False):
        if obfuscate:
            query = obfuscator.obfuscate(query)
        hits = self.searcher.search(query, k=k, threads=self.threads)
        rationales = []
        for idx, hit in enumerate(hits):
            rationale = self.dataset[self.dataset_id_to_index[hit.docid]]
            rationales.append(rationale)
        return rationales
        
