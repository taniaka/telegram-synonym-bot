import json

from lemma import Lemma


def clean_words():

    with open('data/all_words.json') as infile:
	    all_words = json.load(infile)

    for lang, value in all_words.items():
        for pos, words in value.items():
            for word in words:
                lemma = Lemma(word, pos, lang)
                if not lemma.get_valid_combinations():
                    all_words[lang][pos].remove(lemma.lemma)
                    print(lemma.lemma + " has been removed")
                else:
                    print(lemma.lemma + " not removed")

    json_object = json.dumps(all_words, indent=4)

    with open("data/new_words.json", "w") as outfile:
        outfile.write(json_object)


if __name__ == "__main__":
	clean_words()