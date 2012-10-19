#!/usr/bin/env python
# -*- coding: utf-8 -*-

################################################################################
# Projet : Pony Cloud							       #
# Fonction : Installe un service de stockage distribué l'inssu de l'utilisateur#
################################################################################
#									       #
# Copyleft 2011 by CDAISI						       #
#									       #
################################################################################

# Import générique
import os, sys
#import multiprocessing
import threading
import time.sleep
sys.path.append("biblio")
from objet import *
from init import *

# Import pour l'interface web
from interface import *

# Import pour la partie client
from client import *

# Import pour la partie serveur
from serveur import *

# Import pour le debogue
sys.path.append("../Debogue")
from debogue import *


# Variables
maconf = Conf()
if os.path.splitext(maconf.executable)[1] == ".py" : sys.exit(1)
try : maconf.mode = sys.argv.pop(1)
except IndexError : pass

# On se place au bon endroit
os.chdir(maconf.monrep)

# On lance la procédure d'installation
DEBOGUE().trace("Etape 1/4", "Installation")
if not installation() :
	DEBOGUE().trace("Erreur", "La plate-forme n'est pas prise en charge.")
	sys.exit(1)

# On charge les paramêtres
DEBOGUE().trace("Etape 2/4", "Configuration")
configuration()
#try :
	#configuration()
	
#except Exception :
	#DEBOGUE().trace("Erreur", "Problème dans le chargement des paramêtres.")
	#sys.exit(1)

# L'interface d'administration nous sert de verrou pour se prémunir des multi-instances
DEBOGUE().trace("Etape 3/4", "Verrou exclusif")
#moninterface = multiprocessing.Process(target=interface)
moninterface = threading.Thread(target=interface)
moninterface.start()
time.sleep(1)
#if not moninterface.is_alive() :
if not moninterface.isAlive() :
	DEBOGUE().trace("Erreur", "Le service fonctionne déjà.")
	sys.exit(1)

# On lance une instance serveur chargée de distribuer la base de données
DEBOGUE().trace("Etape 4/4", "Démarrage")
status = "foke"
#monserveur = multiprocessing.Process(target=serveur)  # pas de mémoire partagée
monserveur = threading.Thread(target=serveur)
#monclient = multiprocessing.Process(target=client)  # pas de mémoire partagée
monclient = threading.Thread(target=client)
if maconf.mode == "--admin" :
	print(" Mode ADMINISTRATION ".center(80,'#'))
	
elif maconf.mode == "--serveur" :
	print(" Mode SERVEUR (uniquement) ".center(80,'#'))
	monserveur.start()
	
# On lance une instance client chargée de demander la base de données distribuée
elif maconf.mode == "--client" :
	print(" Mode CLIENT (uniquement) ".center(80,'#'))
	monclient.start()

# S'il n'y a pas d'instruction, on lance une double instance (serveur & client)
else :
	print(" Mode NORMAL ".center(80,'#'))
	monserveur.start()
	monclient.start()

# Pilotage des thread
try:
	status = "load"
	while True :
		DEBOGUE().trace("status", status)
		if status == "load" :
			time.sleep(5)
			
		elif status == "reload" :
			moninterface.join()
			DEBOGUE().trace("moninterface.isAlive()", moninterface.isAlive())
			moninterface.start()
			DEBOGUE().trace("moninterface.isAlive()", moninterface.isAlive())
			status = "load"
			
		elif status == "restart" :
			os.execl(maconf.monchemin, '', maconf.mode)
	
except KeyboardInterrupt :
	moninterface.join()
	DEBOGUE().trace("moninterface.isAlive()", moninterface.isAlive())
	monserveur.join()
	DEBOGUE().trace("monserveur.isAlive()", monserveur.isAlive())
	monclient.join()
	DEBOGUE().trace("monclient.isAlive()", monclient.isAlive())
# Fin

