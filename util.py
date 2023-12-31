import json
import openai
import re
import os

from datasets import load_dataset


def load_gsm():
    data_path = 'data/gsm/STaR/train_rand_split.jsonl'
    dataset = load_dataset(path='json', data_files=data_path, split='train')
    return dataset


def call_gpt(prompt, n=1, retries=5):
    while retries > 0:
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                n=n,
                messages=[
                    {"role": "user", "content": prompt},
                ]
            )
            return response
        except Exception as e:
            print("**** CAUGHT EXCEPTION")
            print(e)
            print(f"**** RETRYING (retries left={retries})")
            retries -= 1
    

def extract_boxed_answer(gpt_answer):
  p = r'\\boxed{(.*)}'
  m = re.search(p, gpt_answer, re.DOTALL)
  if m:
    return m[1]
  else:
    return '<UNK>'


def extract_gpt_answers(gpt_response):
  answers = []
  for choice in gpt_response.choices:
    answer = choice['message']['content']
    answers.append(answer)
  return answers


def is_prediction_correct(prediction, gold):
  # strip commas from numbers
  cleaned_prediction = prediction.replace(',', '')
  return cleaned_prediction == gold


def extract_gsm_answer(example):
  p = r'####(.*)$'
  m = re.search(p, example['answer'], re.DOTALL)
  if m:
    return m[1].strip()
  else:
    return '<UNK>'


def gen_examples(start=0, end=5, n=2, id_prefix='ex4', verbose=False,
                 k=3, retriever=None, obfuscate=False):
  """
  start: start of dataset
  end: end of datset
  n: number of gpt examples to run

  output:
  examples, list of objects of form
    { STaR_idx, title (question), gold_answer, gpt_answers}

  gpt_answers is object of form
    { correct_answers, incorrect_answers, pct_correct}
  where pct_correct is percent correct, *_answers is list of 
    { _id, rationale, predicted_answer }
  
  """
  dataset = load_gsm()

  if end is None or end > len(dataset):
    end = len(dataset)
  examples = []
  for i in range(start, end):
    gsm_example = dataset[i]
    gold_answer = extract_gsm_answer(gsm_example)

    question = gsm_example['question']
    if verbose:
      print(f'Q{i}: {question}')

    if retriever is not None:
        question = generate_prompt_from_kb(question, k=k, retriever=retriever, obfuscate=obfuscate)
        
    example = {
      'star_idx': i,
      'question': question,
      'gold_answer': gold_answer
    }
    correct_answers = []
    incorrect_answers = []
    gpt_answers = {
        'correct_answers': correct_answers,
        'incorrect_answers': incorrect_answers,
        'pct_correct': 0
    }
    example['gpt_answers'] = gpt_answers

    examples.append(example)
    
    if n > 0:
      response = call_gpt(question, n=n)
      gpt_predicted_answers = extract_gpt_answers(response)
      for ans_id, gpt_answer in enumerate(gpt_predicted_answers):
        id = f'{id_prefix}_{i}_{ans_id}'
        boxed_answer = extract_boxed_answer(gpt_answer)
        answer = {
          '_id': id,
          'rationale': gpt_answer,
          'predicted_answer': boxed_answer
        }
        if is_prediction_correct(boxed_answer, gold_answer):
          correct_answers.append(answer)
        else:
          incorrect_answers.append(answer)

      gpt_answers['pct_correct'] = len(correct_answers) / n

  return examples


def accuracy(examples):
  correct_examples = [e for e in examples if e['gpt_answers']['pct_correct'] > 0]
  return len(correct_examples) / len(examples)


def output_correct_results(examples, exp='exp6', start=None, end=None,
                           basedir=None):
    if basedir is None:
        basedir = f'data/results/{exp}'
    os.makedirs(basedir, exist_ok=True)    

    filename = f'{basedir}/{exp}_{start}_{end}.jsonl'
    print(f'writing {filename}...')
    with open(filename, 'w') as file:
        for example in examples:
            question = example['question']
            for gpt_answer in example['gpt_answers']['correct_answers']:
                data = {'_id': gpt_answer['_id'],
                        'title': question,
                        'text': gpt_answer['rationale']
                       }
                file.write(json.dumps(data) + '\n')


def output_accuracy_results(examples, exp='exp6', start=None, end=None,
                            basedir=None):
    if basedir is None:
        basedir = f'data/results/{exp}'
    os.makedirs(basedir, exist_ok=True)    

    filename = f'{basedir}/{exp}_{start}_{end}_accuracy.csv'
    print(f'writing {filename}...')
    with open(filename, 'w') as file:
        file.write(f'{start},{end},{end-start},{accuracy(examples)}\n')


def generate_prompt_from_kb(question=None, k=3, retriever=None, obfuscate=False):
    preamble = """Given a math problem, generate an answer with a rationale.

Question / answer pairs have the form

Question: ${question}

${answer}
    
Examples:
    """
    if retriever is None:
        return f'{preamble}\n{question}'
    
    examples = retriever.retrieve(question, obfuscate=obfuscate)

    lines = []
    lines.append(preamble)
    for example in examples:
        lines.append(f'Question: {example["title"]}\n')
        lines.append(example['text'])
        lines.append('\n')
    lines.append(f'Question: {question}\n')
    return('\n'.join(lines))


def process_batch(instance_num=0,
                  batch_size=10,
                  offset=0,
                  batches_per_instance=100,
                  n=5,
                  exp='exp6',
                  k=3,
                  basedir=None,
                  retriever=None,
                  obfuscate=False):
    for batch in range(batches_per_instance - offset // batch_size):
        start = instance_num * batch_size * batches_per_instance + batch * batch_size + offset
        end = start + batch_size
        print(f'Processing {batch=}.  {start=}, {end=}')
        examples = gen_examples(start=start, end=end, n=n, verbose=True,
                                k=k, retriever=retriever, obfuscate=obfuscate)
        the_accuracy = accuracy(examples)
        print(f'{the_accuracy=:.2f}')
        print()
        output_correct_results(examples, exp=exp, start=start, end=end,
                               basedir=basedir)
        output_accuracy_results(examples, exp=exp, start=start, end=end,
                                basedir=basedir)


def hi():
    print('hi from util')
