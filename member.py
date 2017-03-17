#! /usr/bin/env python
# coding=utf-8
import requests
import re
from lxml import html
import json
import csv
import pdb
import argparse
import urllib

def email_decode(crypted_email):
	e = ''
	r = int(crypted_email[0:2], 16) | 0
	n = 2
	while len(crypted_email) > n:
		e += '%' + "%0.2x" % (int(crypted_email[n:n+2],16)^r)
		n += 2
	return urllib.unquote(e).decode('utf8') 


parser = argparse.ArgumentParser()
parser.add_argument('f', type=argparse.FileType('wb'), metavar='Outfile', help='output file')
parser.add_argument('-t', choices=['csv', 'json'], help='output type (csv/json)', required=True)
args = parser.parse_args()
db = []

area = ["central", "wc", "south", "east", "kt", "ssp", "ytm", "wts", "kc", "island", "tw", "yl", "north", "st", "sk", "kwt", "tp", "tm"]
list_url = "http://www.districtcouncils.gov.hk/%s/tc_chi/members/info/dc_member_list.php"
detail_url = "http://www.districtcouncils.gov.hk/%s/tc_chi/members/info/dc_member_list_detail.php?member_id=%s"

for a in area:
	url = list_url % a
	r = requests.get(url)
	m = re.findall("dc_member_list_detail.php\?member_id=(\d+)", r.text)
	for id in m:
		d = dict()
		url = detail_url % (a,id)
		r = requests.get(url)
		corrected_text = re.sub('h1','h2',r.content) # fix bug in original html!
		root = html.fromstring(corrected_text)
		
		d[u"姓名"] = root.findtext(".//h2[@class='h2 member_name']").strip()
		d[u"區議會"] = root.findtext(".//h2[@class='mySection']").strip()
		
		td = root.find(".//td[@style='padding-left:2em']")
		l = td.findall(".//p")
		d[u"席位"] = re.sub(u'.*席位\r\n\t*\r\n\t*', '', l[0].text_content().strip())
		d[u"選區"]  = re.sub(u'.*選區\r\n\t*\r\n\t*', '', l[1].text_content().strip())
		d[u"職業"] = re.sub(u'.*職業\r\n\t*\r\n\t*', '', l[2].text_content().strip())
		d[u"所屬政治聯繫"] = re.sub(u'.*所屬政治聯繫\r\n\t*\r\n\t*', '', l[3].text_content().strip())
		
		contact_e = root.find('.//table[@style="width:100%; margin-top:1em; margin-bottom:1.5em; "]')
		d[u"地址"] = re.sub(u'\r\n', u'|', contact_e.find('./tr[1]/td[2]').text_content().strip())
		d[u"電話"] = contact_e.find('./tr[2]/td[2]').text_content().strip()
		d[u"傳真"] = contact_e.find('./tr[3]/td[2]').text_content().strip()
		emails = contact_e.findall('.//*[@data-cfemail]')
		email_list = [];
		for email in emails:
			email_list.append(email_decode(email.get("data-cfemail")))
		d[u"電郵地址"] = ";".join(email_list)
		d[u"網頁"] = contact_e.find('./tr[5]/td[2]/span').text_content().strip()
		db.append(d)

if args.t == "json":
	json.dump(db,args.f)
elif args.t == "csv":
	if len(db) > 0:
		args.f.write(u'\ufeff'.encode('utf8'))
		w = csv.DictWriter(args.f,[k.encode('utf8') for k in sorted(db[0].keys())])
		count = 0
		for row in db:
			if count == 0:
				w.writeheader()
				count += 1
			w.writerow({k.encode('utf8'):v.encode('utf8') for k,v in row.items()})
args.f.close()	  
	  
	  
  
  
