import openai
import re
import os

from datasets import load_dataset


def load_gsm():
    data_path = 'data/gsm/STaR/train_rand_split.jsonl'
    dataset = load_dataset(path='json', data_files=data_path, split='train')
    return dataset


def call_gpt(prompt, n=1):
  response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    n=n,
    messages=[
        {"role": "user", "content": prompt},
    ]
  )
  return response
    

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


def gen_examples(start=0, end=5, n=2, id_prefix='ex4', verbose=False):
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
