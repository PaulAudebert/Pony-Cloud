#!/usr/bin/env python
# -*- coding: utf-8 -*-

################################################################################
# Projet : Pony Cloud
# Fonction : Installe un service de stockage distribué l'inssu de l'utilisateur
################################################################################
#
# Copyleft CDAISI 2011
#
################################################################################

# Import générique
import os, sys
import logging
import logging.handlers
#import multiprocessing
import threading
import time.sleep

# Import Pony Cloud
sys.path.append("biblio")
from objet import *
from init import *
from interface import *
from client import *
from serveur import *


######################################################################
# Main
######################################################################

if __name__ == "__main__":
	os.system("cls")
	
	# Variables globales
	g_version = "1.0.4"
	g_maintainer = "paul.audebert@gmail.com"
	maconf = Conf()
	
	# Initialitation du système de log
	if "--debug" in sys.argv :
		log = logging.getLogger()
		log.setLevel(logging.DEBUG)
		outputSdt = logging.StreamHandler()
		outputSdt.setLevel(logging.DEBUG)
		outputSdt.setFormatter(logging.Formatter(datefmt = "%H:%M:%S", fmt = "%(asctime)s %(levelname)s : %(message)s"))
		log.addHandler(outputSdt)
		log.debug("DEBUG MODE")
	
	# Vérification du contexte
	if os.path.splitext(maconf.executable)[1] == ".py" : sys.exit(1)

	# On se place au bon endroit
	log.debug("// Lancement dans " + os.path.abspath(os.curdir))
	print('#'*79)
	print('#' + ' '*77 + '#')
	print('#' + u"{} {} Copyleft CDAISI 2011".format(os.path.splitext(maconf.executable)[0], g_version).center(77,' ') + '#')
	print('#' + ' '*77 + '#')
	print('#'*79)
	os.chdir(maconf.monrep)
	log.debug("Entrer dans " + os.path.abspath(os.curdir))

	# On lance la procédure d'installation
	log.info("Etape 1/4 : Installation")
	if not installation() :
		log.error("La plate-forme n'est pas prise en charge.")
		sys.exit(1)

	# On charge les paramêtres
	log.info("Etape 2/4 : Configuration")
	configuration()
	#try :
		#configuration()
		
	#except Exception :
		#log.debug("Erreur", "Problème dans le chargement des paramêtres.")
		#sys.exit(1)

	# L'interface d'administration nous sert de verrou pour se prémunir des multi-instances
	log.info("Etape 3/4 : Verrou exclusif")
	#moninterface = multiprocessing.Process(target=interface)
	moninterface = threading.Thread(target=interface)
	moninterface.start()
	time.sleep(1)
	#if not moninterface.is_alive() :
	if not moninterface.isAlive() :
		log.error("Le service fonctionne déjà.")
		sys.exit(1)

	# On lance une instance serveur chargée de distribuer la base de données
	log.info("Etape 4/4 : Démarrage des composants")
	#monserveur = multiprocessing.Process(target=serveur)  # pas de mémoire partagée
	monserveur = threading.Thread(target=serveur)
	#monclient = multiprocessing.Process(target=client)  # pas de mémoire partagée
	monclient = threading.Thread(target=client)
	if "--admin" in sys.argv :
		print(" Mode ADMINISTRATION (interface web uniquement)".center(79,'#'))
		
	elif "--serveur" in sys.argv :
		print(" Mode SERVEUR (uniquement) ".center(79,'#'))
		monserveur.start()
		
	# On lance une instance client chargée de demander la base de données distribuée
	elif "--client" in sys.argv :
		print(" Mode CLIENT (uniquement) ".center(79,'#'))
		monclient.start()

	# S'il n'y a pas d'instruction, on lance une double instance (serveur & client)
	else :
		print(" Mode NORMAL ".center(79,'#'))
		monserveur.start()
		monclient.start()

	# Pilotage des thread
	try:
		status = "load"
		while True :
			log.debug("status", status)
			if status == "load" :
				time.sleep(5)
				
			elif status == "reload" :
				moninterface.join()
				log.debug("moninterface.isAlive() " + moninterface.isAlive())
				moninterface.start()
				log.debug("moninterface.isAlive() " + moninterface.isAlive())
				status = "load"
				
			elif status == "restart" :
				os.execl(maconf.monchemin, '', sys.argv)
		
	except KeyboardInterrupt :
		moninterface.join()
		log.debug("moninterface.isAlive()", moninterface.isAlive())
		monserveur.join()
		log.debug("monserveur.isAlive()", monserveur.isAlive())
		monclient.join()
		log.debug("monclient.isAlive()", monclient.isAlive())
	
	# Fin
	sys.exit(0)
