#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simple Telegram Bot that lets you guess synonyms.

This Bot is based on data from the WordNet project.
"""

import logging
import os

from telegram import ReplyKeyboardMarkup
from telegram.ext import (
			Updater, 
			CommandHandler, 
			MessageHandler, 
			Filters, 
			RegexHandler,
			ConversationHandler)


from lemma import GameManager, Lemma


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


MAIN_CHOICE, OPTIONS_CHOICE, TYPING_REPLY, TRY_AGAIN = range(4)

keybords = {
			'menu':[['Guess', 'Part of speech'], 
		           ['Language', 'Done']],

		    'part of speech': [['Noun', 'Verb'],
		    				  ['Adjective', 'Adverb']],

		    'language': [['English', 'Spanish']],

		    'try': [['Try again', "No, thank you"]]
}

choice_mapping = {

			'English': 'eng',
			'Spanish': 'spa',
			'Noun': 'n',
			'Verb': 'v',
			'Adjective': 'a',
			'Adverb': 'r'
	
}

menu_markup = ReplyKeyboardMarkup(keybords['menu'], one_time_keyboard=True)


def start(bot, update):
	global gm
	gm = GameManager()
	start_message = "WELCOME TO THE SYNONYM GAME!"
	start_message += "\n\n"
	start_message += "In this game, you will be presented with lists of words. " +\
					 "The words in each list may or may not be synonyms, " +\
					 "but they do have a synonym in common. " +\
					 "Your goal will be to guess this common synonym."
	start_message += "\n\n"
	start_message += get_option_message()

	update.message.reply_text(start_message, reply_markup=menu_markup)

	return MAIN_CHOICE


def get_option_message():
	message =  "Guess: find a synonym for the given words. \n"
	message += "Part of speech: choose another part of speech (default: noun). \n"
	message += "Language: choose another language (default: English). \n"
	message += "Done: end the game. \n\n"
	message += "You can also end the game anytime " +\
			   "by simply typing /done."
	return message


def menu_choice(bot, update):
	text = update.message.text.lower()
	update.message.reply_text(
		"Please, choose a {} from the options below.".format(text),
		reply_markup=ReplyKeyboardMarkup(keybords[text], one_time_keyboard=True))

	return OPTIONS_CHOICE


def choose_pos(bot, update):
	text = update.message.text
	gm.change_pos(choice_mapping[text])
	update.message.reply_text(
		"You changed your part of speech to: {}. \n"
		"What would you like to do next?"
		.format(text.lower()), reply_markup=menu_markup)

	return MAIN_CHOICE


def choose_language(bot, update):
	text = update.message.text
	gm.change_lang(choice_mapping[text])
	update.message.reply_text(
		"You changed your language to: {}. \n"
		"What would you like to do next?"
		.format(text), reply_markup=menu_markup)

	return MAIN_CHOICE


def start_guessing(bot, update):
	gm.pick_lemma()
	lemma = gm.current_lemma.lemma
	synonyms = gm.current_lemma.choose_combination()
	message = "The words below have a synonym in common. " +\
			  "Can you figure out this synonym?\n"
	message += '\n'.join(synonyms).join(['\n', '\n'])
	update.message.reply_text(message)
	
	return TYPING_REPLY


def give_reply(bot, update):
	text = update.message.text
	message = "You said: {}. \n".format(text)
	if text.lower() == gm.current_lemma.lemma.lower():
		message += "Congratulations! This is the correct answer. "
		message += "What would you like to do next?"
		update.message.reply_text(
			message, reply_markup=menu_markup)
		return MAIN_CHOICE
	message += "Unfortunately, this answer is not correct. \n"
	message += "Would you like to try again?"
	update.message.reply_text(
		message, reply_markup=ReplyKeyboardMarkup(keybords['try'],
			one_time_keyboard=True))

	return TRY_AGAIN


def get_new_try(bot, update):
	update.message.reply_text(
		"Please, type your new guess.")

	return TYPING_REPLY


def skip_new_try(bot, update):
	update.message.reply_text(
		"The correct answer was: {}. \n"
		"What would you like to do next?"
		.format(gm.current_lemma.lemma),
		reply_markup=menu_markup)

	return MAIN_CHOICE


def done(bot, update):
	update.message.reply_text(
		"Hope you enjoyed our synonym game. "
		"We hope to see you again for more synonym guessing."
		"To start a new game session, please type /start.")
	return ConversationHandler.END


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)



def main():	

	updater = Updater(token=os.environ.get('TELEGRAM_TOKEN'))
	dispatcher = updater.dispatcher

	conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
        	MAIN_CHOICE: [RegexHandler('^(Language|Part of speech)$',
        			                   menu_choice),
        				  RegexHandler('^Guess$',
        			             start_guessing)],

        	OPTIONS_CHOICE: [RegexHandler('^(English|Spanish)$',
        			                   choose_language),

        					RegexHandler('^(Noun|Verb|Adjective|Adverb)$',
        			                   choose_pos)],


        	TYPING_REPLY: [MessageHandler(Filters.text, 
        					give_reply)],

        	TRY_AGAIN: [RegexHandler('^Try again$', get_new_try),
        			    RegexHandler('^No, thank you$', skip_new_try)]
        },

        fallbacks=[RegexHandler('^Done$', done),
		           CommandHandler('done', done)]
    )


	dispatcher.add_handler(conv_handler)

	dispatcher.add_error_handler(error)

	updater.start_polling()

	updater.idle()


if __name__ == "__main__":
	main()