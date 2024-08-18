#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Simple Telegram Bot for synonym guessing.
The Bot is based on data from the WordNet project.
"""


import logging
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, Update)
from telegram.ext import (Application, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters)
from typing import Final

from lemma import GameManager, Lemma



TOKEN: Final = os.environ.get("TELEGRAM_TOKEN")

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


MAIN_CHOICE, LANGUAGE_CHOICE, POS_CHOICE, TYPING_REPLY, TRY_AGAIN = range(5)

keybords = {
			'menu':[['Guess', 'Part of speech'], 
		           ['Language', 'Done']],
		    'part of speech': [['Noun', 'Verb'],
		    				  ['Adjective', 'Adverb']],
		    'language': [['English', 'Spanish']],
		    'try': [['I will try again', "I give up"]]
}

choice_mapping = {
			'English': 'eng',
			'Spanish': 'spa',
			'Noun': 'n',
			'Verb': 'v',
			'Adjective': 'a',
			'Adverb': 'r'	
}

inv_mapping = {v: k for k, v in choice_mapping.items()}



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

	# create GameManager object to keep track of current state of the game
	global gm
	gm = GameManager()

	# show start message
	start_message = "WELCOME TO THE SYNONYM GAME!\n\n"
	start_message += "In this game, you will be shown a list of words. " +\
					 "These words may or may not be synonyms, " +\
					 "but they definitely have a synonym in common.\n\n" +\
					 "Your goal will be to guess this common synonym."

	start_message += "For example, <b>knot</b> and <b>arc</b> are not synonyms but they both are synonymous with <b>bow.</b>" +\
					 "So here <b>bow</b> would be the correct answer.\n\n"

	start_message += "You can end the game anytime by typing /done"

	await update.message.reply_text(
		start_message,
		parse_mode = "HTML"
	)

	# show main menu message + keybord
	await menu_message(update, context)

	return MAIN_CHOICE



async def menu_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Shows main menu keybord amd explanatory message"""

	message = "What would you like to do now?\n\n"

	message += 	"<b>Guess</b>: guess a word\n" +\
				f"<b>Part of speech</b>:  pick a part of speech (current: {inv_mapping[gm.current_pos]})\n" +\
				f"<b>Language</b>:  pick a language (current: {inv_mapping[gm.current_lang]})\n" +\
				"<b>Done</b>: end the game\n"

	await update.message.reply_text(
		message,
		parse_mode='HTML',
		reply_markup = ReplyKeyboardMarkup(
				keybords['menu'], 
				one_time_keyboard=True
		)
	)


async def choose_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	"""Processes choice made by user in made menu """

	user_choice = update.message.text.lower()

	if user_choice in ["language", "part of speech"]:
		await update.message.reply_text(
		    	f"Please, choose a {user_choice.lower()} from the options below.",
				reply_markup = ReplyKeyboardMarkup(
						keybords[user_choice])
		)
		if user_choice == "language":
			return LANGUAGE_CHOICE
		else:
			return POS_CHOICE

	elif user_choice == "guess":
		synonyms = None

		# pick random lemma for current lang and pos,
		# if lemma has no valid synonym combinations, pick another
		while (synonyms == None):
			gm.pick_lemma()
			synonyms = gm.current_lemma.choose_combination()

		message = "The words below have a synonym in common. " +\
			  	  "Can you figure it out?\n<b>"
		message += "\n".join(synonyms).join(["\n", "\n"])
		message += "</b>\n\nPlease type your guess below"
		await update.message.reply_text(message, parse_mode="HTML")
	
		return TYPING_REPLY
	
	elif user_choice == "done":
		await done(update, context)

	# if user types random text instead of picking menu option, bring back main menu
	else:
		await update.message.reply_text(
			f"Please pick one of the proposed options.")

		await menu_message(update, context)

		return MAIN_CHOICE


async def choose_pos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	"""Captures user choice of POS and sets it as current POS"""

	text = update.message.text

	try:
		gm.change_pos(choice_mapping[text])
		await update.message.reply_text(f"You changed your part of speech to: {text.lower()}.")
		await menu_message(update, context)

		return MAIN_CHOICE

	except:
		# if user entered random text instead of POS name, bring back POS menu
		await update.message.reply_text(
			f"You should pick one of the options below.",
			reply_markup = ReplyKeyboardMarkup(keybords["part of speech"]))

		return POS_CHOICE


async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	"""Captures user choice of language and sets it as current language"""

	text = update.message.text

	try:
		gm.change_lang(choice_mapping[text])
		await update.message.reply_text(f"You changed your language to: {text}.")
		await menu_message(update, context)

		return MAIN_CHOICE
	
	except:
		# if user entered random text instead of language, bring back language menu
		await update.message.reply_text(
			f"You should pick one of the options below.",
			reply_markup = ReplyKeyboardMarkup(keybords['language']))

		return LANGUAGE_CHOICE


async def give_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	"""Processes user's guess. If guess is correct brings up main menu. 
	   If guess is not correct, offers to try again."""

	text = update.message.text
	message = f"You said: <b>{text}</b>.\n\n"

	if text.lower() == gm.current_lemma.lemma.lower():
		message += "CONGRATULATIONS! THIS IS THE CORRECT ANSWER."
		await update.message.reply_text(message, parse_mode='HTML')
		await menu_message(update, context)

		return MAIN_CHOICE

	message += "Unfortunately, this answer is not correct."
	await update.message.reply_text(message, parse_mode='HTML')

	await update.message.reply_text(
		"What do you want to do now?", 
		reply_markup = ReplyKeyboardMarkup(keybords['try'],
										one_time_keyboard = True)
	)

	return TRY_AGAIN


async def new_try(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	"""Processes user response to whether they want a new try.
	   If yes, prompts user to give a new answer.
	   If no, shows the correct answer and bring up the main menu."""
	text = update.message.text

	if text == "I will try again":
		await update.message.reply_text("Please, type your new guess.")
		return TYPING_REPLY

	elif text == "I give up":
		await update.message.reply_text(f"The correct answer was: {gm.current_lemma.lemma.upper()}.")
		await menu_message(update, context)
		return MAIN_CHOICE

	else:
		# if user entered random text, bring back the try-again menu
		await update.message.reply_text(
			f"Please click on one of the options below",
			reply_markup = ReplyKeyboardMarkup(
							keybords["try"], 
							one_time_keyboard = True)
			)

		return TRY_AGAIN


async def done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

	await update.message.reply_text(
		"Bye, hope you enjoyed the game.\n\n"
		"To start a new game session, please type /start.",
		reply_markup = ReplyKeyboardRemove()
	)

	return ConversationHandler.END


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log Errors caused by Updates."""
    logger.warning(f"Update {update} caused error {context.error}")



def main() -> None:
	"""Run the bot."""
	app = Application.builder().token(TOKEN).build()

	conv_handler = ConversationHandler(
		entry_points=[CommandHandler('start', start)], 
		states = {
			MAIN_CHOICE: [MessageHandler(filters.TEXT & (~ filters.COMMAND), choose_action)],
        	LANGUAGE_CHOICE: [MessageHandler(filters.TEXT & (~ filters.COMMAND), choose_language)],
			POS_CHOICE:  [MessageHandler(filters.TEXT & (~ filters.COMMAND), choose_pos)],
        	TYPING_REPLY: [MessageHandler(filters.TEXT & (~ filters.COMMAND), give_reply)],
			TRY_AGAIN: [MessageHandler(filters.TEXT & (~ filters.COMMAND), new_try)],
        },
        fallbacks=[MessageHandler(filters.Regex(r'^Done$'), done),
		           CommandHandler('done', done)]
    )

	app.add_handler(conv_handler)
	app.add_handler(CommandHandler("start", start))
	app.add_handler(CommandHandler("done", done))
	app.add_error_handler(error)

	app.run_polling()


if __name__ == "__main__":
	main()