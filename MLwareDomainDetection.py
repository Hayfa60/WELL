#!/usr/bin/python
from urllib.parse import urlparse
import requests
import json
import math
import re

domain = ''
domain_arr = []
path=''
path_arr = []
starts_with_http = re.compile('^http')
j = {}
tlds = []
file_name = 'angler_domains.txt'

def bigrams(input_list):
	return zip(input_list, input_list[1:])

def probability_score(word):
	score = 0
	# if no char pairs, return score = 0
	if len(word) < 2:
		return score

	# else compute score
	b = bigrams(word)
	for char_tuple in b:
		pair = char_tuple[0] + char_tuple[1]
		# try to lookup tuple scores in rendered json
		# if it fails, we do not have a tuple in json
		# in that case assign an arbitrary high value
		try:
			tuple_lookup_value = j[pair]['log']
		except KeyError:
			tuple_lookup_value = -5

		score = score + tuple_lookup_value
	return score

def parse_url(url):
	global domain
	global domain_arr
	global path
	global path_arr
	global starts_with_http

	# ensure url includes the scheme, as urlparse doesnt work if scheme absent
	http_result = starts_with_http.match(url)
	if http_result:
		pass
	else:
		url = 'http://' + url

	# parse url
	u = urlparse(url)

	# separate url into domain and path
	if u and u.netloc:
		domain = u.netloc
	else:
		print('Domain parse error')

	# remove www and split on '.'
	domain = re.sub('^www\.', '', domain)
	domain_arr = domain.split('.')

	# we want to eliminate as much useless info as possible, e.g tlds
	tld = domain_arr[-1]
	if tld in tlds:
		domain_arr.pop()
		domain = '.'.join(domain_arr)

	# split domain again on '-' and '.'
	domain_arr = re.split('[-.]', domain)

	# eliminate empty strings from list
	domain_arr = filter(None, domain_arr)		
	print('DOMAIN             ==> ', domain)

	# separate path components into 'words'
	if u and u.path:
		path = u.path
		path_arr = re.split('[/_.-]', path)
		# eliminate empty strings from list
		path_arr = filter(None, path_arr)
		print('PATH               ==> ', path)
	else:
		print('PATH               ==> No path info in URL')

	# words[] is a list containing the terms to evaluate
	words = domain_arr + path_arr
	return words


def main():
	global domain
	global domain_arr
	global path
	global path_arr	
	global file_name
	global tlds
	global j

	# read in pre-rendered json
	with open('character_pair_probabilities.json') as fi:
		j = json.load(fi)
	print('-- Read json --')

	# fetch latest icann TLD list
	r = requests.get('http://data.iana.org/TLD/tlds-alpha-by-domain.txt')
	arr2 = r.text.lower().split('\n')

	# obtain tld's in array for comparison
	tlds = arr2[1:]
	print('-- Fetched latest ICANN TLDs --\n')

	# read url
	with open(file_name, 'r') as fi:
		for url in fi:
			# ensure we reset all variables
			domain = ''
			path = ''
			domain_arr = []
			path_arr = []

			url = url.rstrip().lower()
			print('URL                ==> ', url)
			words = parse_url(url)
			print('EVALUATING WORDS   ==> ', words)
			
			# calculate a score
			for word in words:
				score = probability_score(word)
				# to nullify effect of longer words producing high scores
				# calculate exp(score/len(word)) rounded to 3 decimals
				malware_score = round(math.exp(abs(score)/len(word)), 3)
				if malware_score > 15:
					print('POSSIBLY MALICIOUS ==> ', word, malware_score)			
			print('\n')

if __name__ == "__main__":
	main()