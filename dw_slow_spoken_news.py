import feedparser
from textblob import TextBlob
from telegraphapi import Telegraph
import telegram
from telegram.error import Unauthorized, NetworkError
import re
from newspaper import Article
import sys
import requests
from telegram.ext import *
import datetime
import time
import os

TOKEN_TELEGRAM = os.environ['TOKEN_TELEGRAM']
bot = telegram.Bot(TOKEN_TELEGRAM)
TELEGRAPH_ACCOUNT = 'DW'
telegraph = Telegraph()
telegraph.createAccount(TELEGRAPH_ACCOUNT)

def start(bot, update):
    text = "Welcome!\nYou will receive daily news starting from tomorrow."
    update.message.reply_text(text)

def getArticleImage(url):
	article = Article(url)
	article.download()
	article.parse()
	text = article.text
	articleImage = article.top_image
	return articleImage

def getTelegraphText(rawString,url):
	string = ""
	string += '<img src="{}"></img>\n'.format( getArticleImage(url) )
	rawString = re.sub( r"^Trainiere dein Hörverstehen mit den Nachrichten der Deutschen Welle von [a-zA-z]+ – als Text und als verständlich gesprochene Audio-Datei." , "" , rawString) # elimina
	rawString = rawString.replace("\n\n","\n")
	blob = TextBlob(rawString) 
	for sentence in blob.sentences:
		string = string + '<b>{}</b>\n<i>{}</i>\n\n'.format( sentence, str( sentence.translate(to="en") ) )
	return string

def getCaptionText(title, mp3Size):
	string = ""
	string += title.split("–")[0].strip()
	string += "\n" + str(  round( int(mp3Size) / (1024*1024), 2 )  ) + " MB." 
	return string
	
def getDailyNews():
	url = 'http://partner.dw.com/xml/DKpodcast_lgn_de'
	entries = feedparser.parse( url ).entries
	i = 0
	title = entries[i].title
	summary = entries[i].summary
	link = entries[i].link
	publishedDate = entries[i].published
	mp3Url = entries[i].links[1]['href']
	mp3Size = entries[i].links[1]['length']
	page = telegraph.createPage( title = title,  html_content= getTelegraphText(summary, link), author_name="DW - Langsam gesprochene Nachrichten" )
	url2send = 'http://telegra.ph/' + page['path']
	text = '<a href="{}">[DW]</a>\n<b>{}</b>\n\nOriginal <a href="{}">Post</a> published on {}'.format(url2send, title, link, publishedDate) + "\n" + u"\u2063" #it is the invisible character: stealth mode here motherfucker!!!
	caption = getCaptionText(title, mp3Size)
	return text, caption, mp3Url
	
chat_idList = [31923577]

updater = Updater(TOKEN_TELEGRAM) 
dp = updater.dispatcher
updater.dispatcher.add_handler(CommandHandler('start', start))

def ciao(bot, job):
	print("func ciao")
	text, caption, mp3Url = getDailyNews()
	for chat_id in chat_idList:
		bot.sendMessage(chat_id = chat_id, text = text, parse_mode="Html")
		bot.sendAudio( chat_id = chat_id, audio = mp3Url, caption = caption )

j = updater.job_queue
HOUR_I_WANNA_GET_MESSAGE = 13
MINUTES_I_WANNA_GET_MESSAGE = 38
utc_offset_heroku = time.localtime().tm_gmtoff / 3600
print(utc_offset_heroku)
hour = HOUR_I_WANNA_GET_MESSAGE+ ( int(utc_offset_heroku) - 2 ) # 2 is my offset
print(hour)
time2 = datetime.time(hour ,MINUTES_I_WANNA_GET_MESSAGE)

j.run_daily(ciao, time2 )

updater.start_polling()
updater.idle()
