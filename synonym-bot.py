#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Simple Telegram Bot for synonym guessing.
The Bot is based on data from the WordNet project.
"""

import os
import logging
from dotenv import load_dotenv
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Update)
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler, ContextTypes, ConversationHandler, MessageHandler, filters)
from typing import Final

from lemma import GameManager, Lemma


load_dotenv()


TOKEN: Final = os.getenv("TELEGRAM_TOKEN")

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


MAIN_CHOICE, LANGUAGE_CHOICE, POS_CHOICE, TYPING_REPLY, TRY_AGAIN = range(5)


choice_mapping = {
			'English': 'eng',
			'Spanish': 'spa',
			'Noun': 'n',
			'Verb': 'v',
			'Adjective': 'a',
			'Adverb': 'r'	
}

inv_mapping = {v: k for k, v in choice_mapping.items()}


main_keyboard = [
        [InlineKeyboardButton("Guess a word", callback_data = "Guess a word")],
        [InlineKeyboardButton("Select part of speech", callback_data = "Select a part of speech")],
		[InlineKeyboardButton("Select language", callback_data = "Select a language")],
        [InlineKeyboardButton("Exit game", callback_data = "Exit the game")]
    ]

main_markup = InlineKeyboardMarkup(main_keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

	# create GameManager object to keep track of current state of the game

	global gm
	gm = GameManager()

	# show start message

	start_message = "👋 WELCOME TO THE SYNONYM GAME 👋\n\n"
	start_message += "In this game, you'll be shown a list of words. " +\
					 "These words may or may not be synonyms, " +\
					 "but they all have a synonym in common." +\
					 "Your goal is to find this common synonym 🕵️\n\n"

	start_message += "For example, <b>seat</b> 💺 and <b>president</b> 🏛 are not synonyms " +\
					 "but both are synonymous with <b>chair.</b> " +\
					 "So <b>chair</b> would be the correct answer.\n\n"

	start_message += "Start playing 🎲 by choosing one of the following actions:\n\n" +\
			"<b>Guess a word</b>: find a word based on its synonyms.\n" +\
			"<b>Select part of speech</b>: choose between noun, verb, adjective and adverb.\n" +\
			"<b>Select language</b>: choose between English or Spanish.\n" +\
			"<b>Exit game</b>: end the game. You can also type /done to exit the game at any time."

	await update.message.reply_text(
		start_message,
		parse_mode = "HTML"
	)

	# show main menu message + keybord
	await menu_message(update, context)

	return MAIN_CHOICE



async def menu_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
	"""Shows main menu keybord"""

	message = "What would you like to do now?\n\n"

	try:
		await update.message.reply_text(
			message,
			parse_mode='HTML',
			reply_markup = main_markup)
	except:
		# exception is thrown if function is called from a callback query
		await update.callback_query.answer()
		await update.callback_query.message.reply_text(
			message,
			parse_mode='HTML',
			reply_markup = main_markup)


async def choose_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	"""Processes choice made by user in made menu """

	query = update.callback_query
	await query.answer()
	action = query.data

	await query.edit_message_text("You chose to " + action.lower())
	# await query.message.reply_text(action, parse_mode="HTML")

	if action == "Guess a word":
		synonyms = None

		# pick random lemma for current lang and pos,
		# if it has no valid synonym combinations, pick another

		while (synonyms == None):
			gm.pick_lemma()
			synonyms = gm.current_lemma.choose_combination()

		message = "The following words have a synonym in common. " +\
			  	  "Can you figure it out? 🤯\n<b>"
		message += "\n".join(synonyms).join(["\n", "\n"])
		message += "</b>\n\nPlease type your guess below 👇🏻"
		await query.message.reply_text(message, parse_mode="HTML")
	
		return TYPING_REPLY

	elif action == "Select a part of speech":
		keyboard = [[InlineKeyboardButton("Noun", callback_data = "Noun")],
        			[InlineKeyboardButton("Verb", callback_data = "Verb")],
					[InlineKeyboardButton("Adjective", callback_data = "Adjective")],
        			[InlineKeyboardButton("Adverb", callback_data = "Adverb")]]

		markup = InlineKeyboardMarkup(keyboard)

		await query.message.reply_text(
			f"Pick a part of speech from the options below " +\
			f"(current: <b>{inv_mapping[gm.current_pos].lower()}</b>)",
			parse_mode="HTML",
			reply_markup = markup)
		return POS_CHOICE

	elif action == "Select a language":
		keyboard = [[InlineKeyboardButton("English", callback_data = "English")],
        			[InlineKeyboardButton("Spanish", callback_data = "Spanish")]]

		markup = InlineKeyboardMarkup(keyboard)
		
		await query.message.reply_text(
			f"Pick a language from the options below " +\
			f"(current: <b>{inv_mapping[gm.current_lang]}</b>)",
			parse_mode="HTML",
			reply_markup = markup)
		return LANGUAGE_CHOICE

	else:
		await done(update, context)



async def choose_pos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	"""Captures user choice of POS and sets it as current POS"""

	query = update.callback_query
	await query.answer()
	pos = query.data

	gm.change_pos(choice_mapping[pos])

	await query.edit_message_text(
		f"You changed your part of speech to <b>{pos.lower()}</b>",
		parse_mode="HTML"
	)
	await menu_message(update, context)

	return MAIN_CHOICE


async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	"""Captures user choice of language and sets it as current language"""

	query = update.callback_query
	await query.answer()
	lang = query.data

	gm.change_lang(choice_mapping[lang])
	await query.edit_message_text(
		f"You changed your language to <b>{lang}</b>",
		parse_mode="HTML"
	)
	await menu_message(update, context)

	return MAIN_CHOICE



async def give_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	"""Processes user's guess. If guess is correct
	shows main menu. If not, offers to try again."""

	guess = update.message.text
	message = f"You said: <b>{guess.upper()}</b>\n\n"

	if guess.lower() == gm.current_lemma.lemma.lower():
		message += "CONGRATULATIONS👏👏👏  THIS IS THE CORRECT ANSWER 🎉"
		await update.message.reply_text(message, parse_mode='HTML')
		await menu_message(update, context)

		return MAIN_CHOICE

	message += "Unfortunately, the answer is not correct 😕, but you can have another try."

	keyboard = [
        [InlineKeyboardButton("I will try again", callback_data = "try again")],
        [InlineKeyboardButton("I give up", callback_data = "give up")],
    ]

	markup = InlineKeyboardMarkup(keyboard)

	await update.message.reply_text(
		message, 
		parse_mode='HTML',
		reply_markup = markup
	)

	return TRY_AGAIN


async def new_try(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
	"""If user chose a new try, prompts them to give a new answer.
	   If not, shows the correct answer and brings up the main menu."""

	query = update.callback_query
	await query.answer()
	decision = query.data

	if decision == "try again":
		await query.edit_message_text("You decided to try again")
		await query.message.reply_text("Please enter your new guess 👇🏻👇🏻👇🏻")
		return TYPING_REPLY

	else:
		await query.edit_message_text("You decided to give up")
		message = f"The correct answer was: <b>{gm.current_lemma.lemma.upper()}</b>\n\n" +\
				  "OK, this was a difficult one, but I encourage you to play one more time 🎲"
		await query.message.reply_text(message, parse_mode = "HTML")
		
		await menu_message(update, context)

		return MAIN_CHOICE



async def done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

	message = "Bye 👋, hope you enjoyed the game and see you back soon.\n\n" +\
		"Whenever you want to start a new session, just type /start."

	try:
		await update.message.reply_text(message)
	except:
		# exception is thrown if function is called from a callback query
		await update.callback_query.answer()
		await update.callback_query.message.reply_text(message)

	return ConversationHandler.END



async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log Errors caused by Updates."""
    logger.warning(f"Update {update} caused error {context.error}")



def main() -> None:
	"""Run the bot."""
	app = Application.builder().token(TOKEN).build()

	conv_handler = ConversationHandler(
		entry_points=[CommandHandler("start", start)], 
		states = {
			MAIN_CHOICE: [CallbackQueryHandler(choose_action)],
			POS_CHOICE: [CallbackQueryHandler(choose_pos)],
			LANGUAGE_CHOICE: [CallbackQueryHandler(choose_language)],
			TYPING_REPLY: [MessageHandler(filters.TEXT & (~ filters.COMMAND), give_reply)],
			TRY_AGAIN: [CallbackQueryHandler(new_try)]
        },
        fallbacks=[CommandHandler("done", done), CommandHandler("start", start)]
    )

	app.add_handler(conv_handler)
	app.add_handler(CommandHandler("start", start))
	# app.add_handler(CommandHandler("done", done))
	app.add_error_handler(error)

	app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
	main()