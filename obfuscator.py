import random
import re

import util


NOUN_PREAMBLE = 'Given the following question, list the nouns.  Return the answer as a list' \
    ' of bullet points, or say None if there are no items.'

PRONOUN_PREAMBLE = 'Given the following question, list the pronouns.  Return the answer as a ' \
    'list of bullet points, or say None if there are no items.'

PROPER_NOUN_PREAMBLE = 'Given the following question, list the proper nouns.  Return the answer ' \
    'as a list of bullet points, or say None if there are no items.'

MALE_NAME_PREAMBLE = 'Given the following question, list the males mentioned in the question.  ' \
    'Return the answer as a list of bullet points, or say None if there are no items.'

FEMALE_NAME_PREAMBLE = 'Given the following question, list the females mentioned in the question.  ' \
    'Return the answer as a list of bullet points, or say None if there are no items'
    

WEIRD_THINGS = [
    'fluffernackle',
    'spiggotwhap',
    'blibberfudge',
    'quizzletoe',
    'plumbuzzle',
    'trinkleshuff',
    'flibberjig',
    'whackledorf',
    'snooptoggle',
    'zibberflap',
    'gobblequark',
    'dinglefrap',
    'snickerblast',
    'floopernoodle',
    'wobblegruff',
    'crinklethorp',
    'blubberclank',
    'mumblestitch',
    'quarkleflop',
    'slippleshank'
]

FEMALE_NAMES = [
    'Isolde',
    'Seraphine',
    'Elowen',
    'Thalassa',
    'Vespera',
    'Calista',
    'Ondine',
    'Belphoebe',
    'Isabeau',
    'Eulalia',
]

MALE_NAMES = [
    'Thorne',
    'Jorvik',
    'Elsdon',
    'Calix',
    'Vero',
    'Orlan',
    'Brevin',
    'Tyrus',
    'Halvard',
    'Dainan'
]
    

def extract_list_items(list_string):
    items = list_string.split('\n')
    items = [item.replace('- ', '') for item in items]
    items = list(filter(lambda x: x != 'None', items))
    return items


def get_entities(preamble, query):
    """
    Given a preamble, fetch a list of entities.
    """
    prompt = f'{preamble}\n{query}'
    response = util.call_gpt(prompt)
    list_string = response.choices[0]['message']['content']
    if list_string == 'None':
        return []
    return extract_list_items(list_string)


def get_proper_nouns(query):
    return get_entities(PROPER_NOUN_PREAMBLE, query)


def get_nouns(query, no_numbers=True):
    nouns = get_entities(NOUN_PREAMBLE, query)
    if no_numbers:
        nouns = list(filter(lambda n: not re.match(r'.*\d.*', n), nouns))
    return nouns


def get_males(query):
    return get_entities(MALE_NAME_PREAMBLE, query)


def get_females(query):
    return get_entities(FEMALE_NAME_PREAMBLE, query)


def get_non_name_nouns(names, nouns):
    noun_set = set(nouns)
    name_set = set(names)
    non_name_noun_set = set(noun_set).difference(name_set)
    return list(non_name_noun_set)


def obfuscate_query(query):
    males = get_males(query)
    females = get_females(query)
    people = males + females
    nouns = get_nouns(query)
    non_name_nouns = get_non_name_nouns(people, nouns)
    random.shuffle(WEIRD_THINGS)
    random.shuffle(MALE_NAMES)
    random.shuffle(FEMALE_NAMES)
    
    male_mapping = {real: fake for real, fake in zip(males, MALE_NAMES)}
    female_mapping = {real: fake for real, fake in zip(females, FEMALE_NAMES)}
    thing_mapping = {real: fake for real, fake in zip(non_name_nouns, WEIRD_THINGS)}
    
    s = query
    for real, fake in male_mapping.items():
        s = s.replace(real, fake)
    for real, fake in female_mapping.items():
        s = s.replace(real, fake)
    for real, fake in thing_mapping.items():
        s = s.replace(real, fake)
        
    return s
