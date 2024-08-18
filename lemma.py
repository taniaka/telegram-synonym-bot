import itertools
import json
import copy
from random import sample, choice

from nltk.corpus import wordnet as wn
from fuzzywuzzy import fuzz



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
		print(self.lemma)

		for synset in list(self.synsets):
			# Ignore synsets that don't include current lemma
			# (happens if lemma in this POS is an inflected form in another POS).
			if self.lemma not in synset.lemma_names(lang=self.lang):
				continue

			# Ignore lemmas similar to current lemma
			cleared_synset = (synonym for synonym in synset.lemma_names(lang=self.lang)
					         if not self.are_similar(synonym, self.lemma))
			if cleared_synset:
				cleared_synsets.append(cleared_synset)

		# delete duplicate synsets
		cleared_synsets = list(set(cleared_synsets))
		# reduce number of synsets to 6
		if len(cleared_synsets) > 6:
			cleared_synsets = sample(cleared_synsets, 6)

		# all possible combinations of 2 or more synonyms from different synsets.
		combinations = 	list(itertools.product(*cleared_synsets))

		print(combinations)
		valid_combinations = []

		for combination in combinations:
			print(combination)
			combination = list(set(combination))
		
			valid_combination = []
			for word in combination:
				is_redund = False
				for clean_word in valid_combination:
					if self.are_similar(clean_word, word): 
						is_redund = True
						break
				if not is_redund:
					valid_combination.append(word)

			print(valid_combination)
			if len(valid_combination) > 1:
				valid_combinations.append(valid_combination)

		print(valid_combinations)
		return valid_combinations

	@staticmethod
	def are_similar(word1, word2):
		if any([word1 == word2,
				word1[:5] == word2[:5],
				fuzz.ratio(word1, word2) > 80,
				word1 in word2, 
				word2 in word1]):
			return True
		return False




class GameManager:

	with open('data/all_words.json') as f:
		ALL_LEMMAS = json.load(f)

	def __init__(self, pos="n", lang="eng"):
		self.current_pos = pos
		self.current_lang = lang
		self.current_lemma = None
		self.unused_lemmas = copy.deepcopy(self.ALL_LEMMAS)

	def change_pos(self, pos):
		self.current_pos = pos

	def change_lang(self, lang):
		self.current_lang = lang

	def pick_lemma(self):
		lang = self.current_lang
		pos = self.current_pos

		lemma = Lemma(choice(
				self.unused_lemmas[lang][pos]),
				pos, lang)
		self.current_lemma = lemma

		# remove lemma from list of unused lemmas
		self.unused_lemmas[lang][pos].remove(lemma.lemma)

		# if no lemmas left for a lang/pos, restart from full list
		if len(self.unused_lemmas[lang][pos]) == 0:
			self.unused_lemmas[lang][pos] = copy.deepcopy(self.ALL_LEMMAS[lang][pos])