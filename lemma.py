import itertools
import json
import sys
from collections import defaultdict
from random import sample, choice

from nltk.corpus import wordnet as wn



class Lemma:

	def __init__(self, lemma, pos, lang):
		self.lemma = lemma
		self.pos = pos
		self.lang = lang
		self.synsets = self.get_synsets()

	def get_synsets(self):
		return wn.synsets(self.lemma, self.pos, self.lang)

	def choose_combination(self):
		valid_combinations = self.get_valid_combinations()
		if not valid_combinations:
			return None
		
		chosen_combination = choice(valid_combinations)
		chosen_combination = [word.replace("_", " ")
						      for word in chosen_combination]
		return chosen_combination

	def get_valid_combinations(self):
		cleared_synsets = []

		for synset in list(self.synsets):
			# Ignore synsets that don't include the to be guessed lemma.
			# (this can happen if the lemma in POS is an inflected form in another POS).
			if self.lemma not in synset.lemma_names(lang=self.lang):
				continue
			# Ignore lemmas that are substrings of the 
			# to be guessed lemma and vice versa.
			cleared_synset = (synonym.lower()
			                 for synonym in synset.lemma_names(lang=self.lang)
					         if not any([synonym.lower() in self.lemma.lower(), 
					         self.lemma.lower() in synonym.lower()]))
			if cleared_synset:
				cleared_synsets.append(cleared_synset)

		# delete duplicated synsets
		cleared_synsets = list(set(cleared_synsets))
		# reduce number of synsets to 6
		if len(cleared_synsets) > 6:
			cleared_synsets = sample(cleared_synsets, 6)

		# all possible combinations of 2 or more synonyms from different synsets.
		# TODO: give priority to longer combinations
		combinations = 	list(itertools.product(*cleared_synsets))
		valid_combinations = [list(set(combination))
							  for combination in combinations
							  if len(set(combination)) >= 2]
		return valid_combinations	



class GameManager:

	with open('data/all_words.json') as f:
		ALL_LEMMAS = json.load(f)

	def __init__(self, pos="n", lang="eng"):
		self.current_pos = pos
		self.current_lang = lang
		self.current_lemma = None
		self.used_lemmas = defaultdict(lambda: defaultdict(list))

	def change_pos(self, pos):
		self.current_pos = pos

	def change_lang(self, lang):
		self.current_lang = lang

	def pick_lemma(self):
		lang = self.current_lang
		pos = self.current_pos
		lemma = Lemma(choice(
				self.ALL_LEMMAS[lang][pos]),
				pos, lang)
		if len(self.used_lemmas[lang][pos]) == len(self.ALL_LEMMAS[lang][pos]):
			self.used_lemmas[lang][pos] = []
		if lemma.lemma in self.used_lemmas[lang][pos]:
			return self.pick_lemma()
		self.current_lemma = lemma
		self.used_lemmas[lang][pos].append(lemma.lemma)







