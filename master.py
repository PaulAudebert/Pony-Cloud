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
import time
import sqlite3
import socket
import hashlib
from itertools import izip, cycle
from math import ceil


def fichier2id(fichier_nom) :
	"""
	Fonction appelée par fichier2chunk() pour avoir le fichier_id correspondant à un fichier
	C'est sensiblement la même chose que l'inoeud sur un FS, c'est un entier unique.
	"""
	with sqlite3.connect(nom_bdd) as cnx :
		c = cnx.cursor()
		c.execute("""
			SELECT id
			FROM fichier
			WHERE nom = '{0}'
			""".format(fichier_nom))
		resultat = c.fetchone()
	
	# On retourne le fichier_id (première collone dans le resultat)
	if resultat : return (True, resultat[0])
	
	# On retourne un fichier_id sans importance en disant (False) qu'il n'existe pas dans la base
	else : return (False, 0)


def fichier2chunk(fichier_nom) :
	"""
	Fonction renvoyant la liste des chunk_id correspondant à un fichier
	Si le fichier n'existe pas dans le cloud la liste sera vide (=False)
	"""
	lchunk = []
	
	# On traduit le fichier_nom en son identifiant unique
	existe,fichier_id = fichier2id(fichier_nom)
	
	# Si fichier2id() nous indique qu'il n'est pas dans la base de données on retourne une liste vide (fausse)
	if not existe : return lchunk
	
	# On récupère toutes les lignes correspondant au chunk_id
	with sqlite3.connect(nom_bdd) as cnx :
		c = cnx.cursor()
		c.execute("""
			SELECT chunk.id, paire_id
			FROM chunk
			INNER JOIN stocker ON chunk.id = chunk_id
			WHERE fichier_id = '{0}'
			ORDER BY chunk.rowid
			""".format(fichier_id))
		lchunk = c.fetchall()
	
	return lchunk


def chunk2xor(chunk_id_mort) :
	"""
	Fonction renvoyant pour un chunk_id mort le id du chunk XOR et le chunk_id du chunk qu'a servit au XOR
	"""
	lxor = []
	
	# On récupère toutes les lignes correspondant au chunk_id
	with sqlite3.connect(nom_bdd) as cnx :
		c = cnx.cursor()
		
		# On recherche le chunk_id du XOR dans la collone A
		c.execute("""
			SELECT chunkxor_id, chunk_id_B
			FROM xor
			WHERE chunk_id_A = '{0}'
			""".format(chunk_id_mort))
		resultat = c.fetchone()
		
		# Si on a pas trouvé on recherche dans la collone B
		if not resultat :
			c.execute("""
				SELECT chunkxor_id, chunk_id_A
				FROM xor
				WHERE chunk_id_B = '{0}'
				""".format(chunk_id_mort))
			resultat = c.fetchone()
		
		# On récupère toutes les ligne correspondant à l'id (le chunk XOR) et au chunk_id (l'autre chunk)
		if resultat :
			c.execute("""
				SELECT chunk_id, paire_id
				FROM stocker
				WHERE chunk_id IN ({0})
				ORDER BY rowid
				""".format(','.join(["'"+str(e)+"'" for e in resultat])))
			lxor = c.fetchall()
	
	return lxor


def upload1chunk(paire_id, chunk_id, chunk_data) :
	"""
	Fonction appelée par upload() pour uploader un chunk sur le cloud
	"""
	global paire
	client = paire[paire_id]
	
	verrou.acquire()
	
	# On envoi l'ordre + le chunk_id
	client.send(dict_ordre["write"] + chunk_id)
	
	# On envoi les données du chunk
	client.send(chunk_data)
	
	# On attend l'acquitement (merci les sockets bloquantes)
	rep = client.recv(len(reponse))
	
	verrou.release()
	
	if rep == reponse :
		print("Le chunk {0} de {1} octets à été envoyé".format(chunk_id[:10], len(chunk_data)))


def xor(chunk_data_A, chunk_data_B) :
	"""
	Fonction retournant les data "XORée" des deux data entrées en paramètres
	"""
	chunkxor_data = ''.join(chr(ord(x) ^ ord(y)) for (x,y) in izip(chunk_data_A, cycle(chunk_data_B)))
	return chunkxor_data


def referencer(table, *parametre) :
	"""
	Fonctionn appelée par upload() pour ajouter dans la base de donnée
	- la références d'un fichier
	- la références d'un chunk
	- la relation "tel chunk est stocké par telle paire"
	- la relation XOR entre trois chunks
	"""
	with sqlite3.connect(nom_bdd) as cnx :
		c = cnx.cursor()
		c.execute("INSERT INTO {0} VALUES{1}".format(table, parametre).replace("'NULL'", "NULL"))
	return c.lastrowid


def raid1(fichier_id, chunk_id, chunk_data) :
	"""
	Fonction réalisant un RAID1 sur deux paires
	"""
	global paire
	
	# On enregistre la reférence du chunk dans la table chunk
	referencer("chunk", chunk_id, fichier_id)
	
	# On envoie le chunk à chaque paire
	for paire_id in paire.keys() :
		upload1chunk(paire_id, chunk_id, chunk_data)
		
		# On enregistre que la paire possède le chunk
		referencer("stocker", chunk_id, paire_id)


def raid5(i, fichier_id, chunk_id, chunk_data) :
	"""
	Fonction réalisant un RAID5 sur trois paires
	"""
	global paire
	global chunk_data_precedent
	global chunk_id_precedent
	
	# On récupère les trois paire_id
	paire_id_A,paire_id_B,paire_id_C = paire.keys()

	# Si on en est au premier, troisième, cinquième... chunk (i impaire)
	if i % 2 :
		# On met de côté le chunk_data et le chunk_id courant pour l'avoir au prochain bouclage
		chunk_data_precedent = chunk_data
		chunk_id_precedent = chunk_id
		
		# On envoie le chunk à la première paire
		upload1chunk(paire_id_A, chunk_id, chunk_data)
		
		# On enregistre la reférence du chunk dans la table chunk
		referencer("chunk", chunk_id, fichier_id)
		
		# On enregistre que la paire possède le chunk
		referencer("stocker", chunk_id, paire_id_A)

	# Sinon ça veux dire qu'on a déjà mit de coté un chunk
	else :
		# On envoie le chunk à la deuxième paire
		upload1chunk(paire_id_B, chunk_id, chunk_data)
		
		# On enregistre la reférence du chunk dans la table chunk
		referencer("chunk", chunk_id, fichier_id)
		
		# On enregistre que la paire possède le chunk
		referencer("stocker", chunk_id, paire_id_B)
		
		# On fait le XOR des deux chunk_data qu'on a
		chunkxor_data = xor(chunk_data_precedent, chunk_data)
		
		# On génère le chunkxor_id avec le hash de son contenu
		chunkxor_id = hashlib.sha256(chunkxor_data).hexdigest()
		
		# On envoie le chunk à la troisième paire
		upload1chunk(paire_id_C, chunkxor_id, chunkxor_data)
		
		# On enregistre la reférence du chunk XOR dans la table chunk avec un fichier_id à 0
		referencer("chunk", chunkxor_id, 0)
		
		# On enregistre que la paire possède le chunk
		referencer("stocker", chunkxor_id, paire_id_C)
		
		# On enregistre les dépendances du chunk XOR dans la table xor
		referencer("xor", chunkxor_id, chunk_id_precedent, chunk_id)


def raid6() :
	"""
	Fonction réalisant un pseudo RAID6. Dans ce cas de figure, on répartit les chunks et leur XOR sur autant de paires qu’il faut pour garantir une disponibilité continue sur 24 heures. On choisie les paires d’après la courbe de leur présence, établie grâce au score par heure qu’elles ont obtenu auparavant.
	Enfin, on réplication l'opération afin de parer l'inaccessibilité non prévisible d’une paire. Les scores étant seulement indicatifs, prévoir qu’une paire reviendra en ligne à telle heure peut s'avérer inexact.

	"""
	# On prend la meilleur paire de l'heure courante.

	# On fait la moyenne (y'a peut être plus pertinent) de tous ses scores, ce sera son seuil critique de disponibilité: en dessous de ce score critique on ne peut pas compter sur cette paire.

	# On regardes à partir de quelle heure qui suit la paire passe en dessous de son seuil critique

	# On part de cette heure et on cherche la meilleure paire pour cette heure.

	# On reprend à la deuxieme étape jusqu'à ce qu'on n'ait plus de chunk à uploader
	pass
	

def upload(fichier_nom) :
	"""
	Fonction découpant et envoyant un fichier en chunks
	"""
	global paire
	i = 1
	existe,fichier_id = fichier2id(fichier_nom)
	
	# Si le fichier existe on le supprime avant
	if existe :
		print("Le fichier {0} existe déjà dans le cloud, il va être supprimé avant de continuer".format(fichier_nom))
		delete(fichier_nom, fichier2chunk(fichier_nom))
	
	# On l'enregistre dans la table fichier
	fichier_droit = "-rw-rw-rw-"
	fichier_proprietaire = "root"
	fichier_groupe = "root"
	fichier_date = time.strftime("%y-%m-%d %H:%M",time.localtime())
	fichier_id = referencer("fichier", "NULL", fichier_droit, fichier_proprietaire, fichier_groupe, fichier_date, fichier_nom)
	
	# On calcule combien de chunks il faut générer pour le fichier
	fichier_taille = os.path.getsize(rep_upload + fichier_nom)
	nb_chunk = ceil(float(fichier_taille) / float(chunk_taille))		# division décimal arrondie à l'entier supérieur si decimales
	
	# On lit n octets du fichier à chaque boucle pour forger les chunks
	with open(rep_upload + fichier_nom) as fichier :
		
		# Initialisation du compteur pour le RAID 5
		while i <= nb_chunk :
			
			# On lit n octets du fichier
			chunk_data = fichier.read(chunk_taille)
			
			# On génère le chunk_id avec le hash de son contenu
			chunk_id = hashlib.sha256(chunk_data).hexdigest()
			
			# On distribue le fichier sur le cloud
			if len(paire) <= 2 : raid1(fichier_id, chunk_id, chunk_data)
			elif len(paire) == 3 : raid5(i, fichier_id, chunk_id, chunk_data)
			elif len(paire) > 3 : raid6()
			
			# On n’oublie pas d'incrémenter le compteur de boucle
			i += 1


def download1chunk(paire_id, chunk_id) :
	"""
	Fonction appelée par download() pour downloader un chunk
	"""
	global paire
	client = paire[paire_id]
	
	verrou.acquire()
	
	# On envoie l'ordre
	client.send(dict_ordre["read"] + chunk_id)
	
	# On recoit les données du chunk
	chunk_data = client.recv(chunk_taille)
	
	# On envoie l'aquitement
	client.send(reponse)
	
	verrou.release()
	
	print("Le chunk {0} de {1} octets à été receptionné.".format(chunk_id[:10 ], len(chunk_data)))
	return chunk_data


def download1xor(chunk_id_mort) :
	"""
	Fonction appelée par download() pour downloader un chunk quand il est mort
	"""
	global paire
	
	chunk_id_precedent = ""
	erreur = False
	
	lxor = chunk2xor(chunk_id_mort)
	lchunk_data = []
	for chunk_id,paire_id in lxor :
		
		# Si c'est le même chunk ET que le précédent était mort OU si c'est un autre chunk ET que le précédent était bon
		if (chunk_id_alt == chunk_id_precedent and erreur) or (chunk_id != chunk_id_precedent and not erreur) :
			
			# On ajoute le chunk_data à notre liste
			print("débogue IIx : chunk précédent")
			chunk_data = download1chunk(paire_id, chunk_id)
			if lchunk_data :	
				lchunk_data.append(chunk_data)
				erreur = False
			else :
				erreur = True
			print("débogue IIy : lchunk = " + len(lchunk))
		
		# On ne peut rien faire si l'un des deux composant du XOR est impossible à télécharger
		else :
			return
		
		chunk_id_precedent = chunk_id
	
	return xor(lchunk_data[0], lchunk_data[1])


def download(fichier_nom, lchunk) :
	"""
	Fonction recomposant un fichier à partir de la liste des chunks
	"""
	global paire
	
	chunk_id_precedent = ""
	erreur = False
	
	with  open(rep_download + fichier_nom, "w") as fichier :
		# On télécharge en mémoire les chunks
		for chunk_id,paire_id in lchunk :
			
			# Si c'est le même chunk ET que le précédent était mort OU si c'est un autre chunk ET que le précédent était bon
			if (chunk_id == chunk_id_precedent and erreur) or (chunk_id != chunk_id_precedent and not erreur) :
				
				# On ajoute le chunk à notre fichier
				chunk_data = download1chunk(paire_id, chunk_id)
				if chunk_data :
					fichier.write(chunk_data)
					erreur = False
				else :
					erreur = True
			
			# Si c'est un autre chunk ET que le précédent était mort, on doit faire le XOR pour récupérer le chunk précédent
			elif chunk_id != chunk_id_precedent and erreur :
				
				# On ajoute le chunk précédent à notre fichier
				print("débogue IIa : chunk précédent")
				chunk_data = download1xor(chunk_id_precedent)
				if chunk_data :
					fichier.write(chunk_data)
					erreur = False
				else :
					erreur = True
					break # sinon le boléen risque d'etre ecrasé par l'étape suivante
				print("débogue IIb : lchunk = " + len(lchunk))
				
				# Et on ajoute le chunk courant à notre fichier
				print("débogue IIIa : chunk courant")
				chunk_data = download1chunk(paire_id, chunk_id)
				if chunk_data :
					fichier.write(chunk_data)
					erreur = False
				else :
					erreur = True
				print("débogue IIIb : lchunk = " + len(lchunk))
			
			chunk_id_precedent = chunk_id
			
			# Si il y a eu une erreur
			if erreur :
				print("Le fichier {0} est impossible à réassembler (peut être seulement pour le moment).".format(fichier_nom))
				os.remove(rep_download + fichier_nom)
				break


def dereferencer(fichier_nom) :
	"""
	Fonction supprimant de la base de données un fichier.
	Les ON DELETE CASCADE et le TRIGGER delete_chunkxor_id garderont la base propre
	"""
	with sqlite3.connect("{0}.sqlite".format(nom_serveur)) as cnx :
		c = cnx.cursor()
		c.execute("PRAGMA foreign_keys = ON")	# Pour activer les DELETE en cascade
		c.execute("""
			DELETE FROM fichier
			WHERE nom = '{0}'
			""".format(fichier_nom))


def delete(fichier_nom, lchunk) :
	"""
	Fonction supprimant tous les chunks correspondant à un fichier
	"""
	global paire
	lxor = []
	
	# On prépare la liste des chunk et chunk XOR correspondant au fichier
	for chunk_id,paire_id in lchunk :
		lxor.extend(chunk2xor(chunk_id))
	
	# On supprime les doublons (étape necessaire à cause de ce que chunk2xor() renvois)
	lxor = list(set(lxor))
		
	# On envoie les ordre de suppression au paire stockant les chunks et les chunks XOR
	for chunk_id,paire_id in lxor :
		
		client = paire[paire_id]
		
		verrou.acquire()
		
		# On envoie l'ordre
		client.send(dict_ordre["delete"] + chunk_id)
		
		# On attend l'aquitement (merci les sockets bloquantes)
		rep = client.recv(len(reponse))
		
		verrou.release()
		
		if rep == reponse :
			print("Le chunk {0} sur {1} a été supprimé".format(chunk_id[:10], paire_id))
	
	# Il faut supprimer le fichier de la base de données
	dereferencer(fichier_nom)


def ls() :
	"""
	Fonction listant les fichiers disponibles sur le cloud à partir du fichier chunk.db
	"""
	with sqlite3.connect(nom_bdd) as cnx :
		c = cnx.cursor()
		c.execute("""
			SELECT droit, proprietaire, groupe, date, nom
			FROM fichier
			ORDER BY nom
			""")
		resultat = c.fetchall()
		
	for ligne in resultat :
		# On affiche les champs séparé d'un espace
		print(" ".join([e for e in ligne]))


def ls_paire() : 
	"""
	Fonction listant les paires connectées à la moulinettes à l'instant t
	"""
	global paire
	print(", ".join([str(paire_id) for paire_id in paire.keys()]))


def maj_paire(paire_id) :
	"""
	Met à jour le client de stockage
	"""
	global paire
	client = paire[paire_id]
	
	verrou.acquire()
	
	with open(nom_client) as fichier :
		fichier_data = fichier.read()
		
		# On envoie l'ordre puis la taille du client de stockage ajusté à une fenetre de 64 octets
		client.send(dict_ordre["maj"] + str(len(fichier_data)).ljust(64))
		client.send(fichier_data)
	
	# On attend l'aquitement (merci les sockets bloquantes)
	rep = client.recv(len(reponse))
	
	verrou.release()
	
	if rep == reponse :
		print("\nLa mise à jour v{0} de {1} octets a été réceptionné par la paire {2}.".format(version, len(fichier_data), paire_id))


def quit() :
	"""
	Fonction signalant aux paires de fermer leur connection TCP avant que le master quitte
	"""
	global paire
	
	for paire_id in paire.keys() :
		client = paire[paire_id]
		
		# On envoie l'ordre
		verrou.acquire()
		client.send(dict_ordre["quit"])
		verrou.release()
	
	sys.exit(0)


""" Fonction de déboguage, ne pas y faire attention... """
i = 1
def DEBOGUE(nom_variable, variable) :
	global i
	print("\033[31mdébogue {0} : {1} {2} = {3}\033[0m".format(i, nom_variable, type(variable), variable))
	i += 1
""" ...merci """


################################################################################
# Fonctions threadées							       #

def alive(paire_id) :
	"""
	Fonction gardant en vie la connexion TCP d'un client.
	On tient également à jour le dictionnaire paire{}
	"""
	global paire
	client = paire[paire_id]
	heure = ""
	
	try :
		while 1 :
			time.sleep(echo_duree)
			
			# On maintient la connexion TCP actives
			verrou.acquire()
			client.send(dict_ordre["echo"].ljust(64))
			client.recv(len(reponse))
			verrou.release()
			
			# On incremente le score/heure de la paire
			heure_new = time.strftime("%H",time.localtime())
			if heure != heure_new :
				heure = heure_new
				with sqlite3.connect(nom_bdd) as cnx :
					c = cnx.cursor()
					c.execute("UPDATE paire SET {0} = {0}+1 WHERE id = {1}".format("h"+heure, paire_id))
	
	except socket.error :
		# La connexion a laché, on retire le client de l'annuaire des paire connecté (mais elle reste dans la base de données)
		del paire[paire_id]


def server() :
	"""
	Fonction attrapant les connexions entrantes
	"""
	global paire
	
	while 1:
		# On réceptionne la connection entrante
		client,adresse = s.accept()
		
		# On enregistre le client dans l'annuaire des paires connectées
		# notement parce que threading.Thread() ne permet pas d'envoyer
		# en "args=" un objet socket.client, donc on lui donnera paire_id
		# et il retrouvera le socket.client via le dictionnaire paire{}
		paire_id,paire_version = client.recv(32).split()
		paire_id = int(paire_id)
		paire_version = float(paire_version)
		paire[paire_id] = client
		
		# On enregistre le client dans la base de données
		with sqlite3.connect(nom_bdd) as cnx :
			c = cnx.cursor()
			try :
				c.execute("INSERT INTO paire(id, version) VALUES({0},{1})".format(paire_id, paire_version))
			except sqlite3.IntegrityError :
				c.execute("UPDATE paire SET version = {1} WHERE id = {0}".format(paire_id, paire_version))
		
		# On envoie nos paramètres ajusté dans une fenetre de 32 octets
		client.send(reponse.ljust(32))
		client.send(str(chunk_taille).ljust(32))
		client.send(str(echo_duree).ljust(32))
		
		# Et si le client de stockage n'est pas à la dernière version, on lance la mise à jour
		if paire_version < version : maj_paire(paire_id)
		
		# pour finir on met les nouveaux arrivants dans des thread qui maintient en vie leur connexion TCP
		vivante = threading.Thread(target=alive,args=(paire_id,))
		vivante.setDaemon(True)
		vivante.start()


################################################################################
# Fonction principale							       #

# Paramêtres
rep_upload = "upload/"
try : os.mkdir(rep_upload)
except OSError : pass
rep_download = "download/"
try : os.mkdir(rep_download)
except OSError : pass
version = 0.5
port = 1212
nbclient = 10
chunk_taille = 10000
paire_id_taille = 3
reponse = "ok"
dict_ordre = {
	"read":"r",
	"write":"w",
	"delete":"-",
	"echo":"?",
	"maj":"%",
	"quit":"q"
	}
echo_duree = 15 # secondes
pause = "\n[ENTRER]"

# Variables
paire = {}			# dictionnaire paire_id => socket.client
verrou = threading.Lock()	# bloquera alive() durant upload(), download() et delete() pour ne pas être parasité par les échos
nom_serveur = sys.argv[0].split('.')[0]
nom_client = "slave.py"
nom_bdd = nom_serveur + ".sqlite"

# Mise en place de la base de données si elle n'existe pas déjà
try :
	with sqlite3.connect(nom_bdd) as cnx :
		c = cnx.cursor()
		
		c.execute("""
			CREATE TABLE fichier(
				id		INTEGER PRIMARY KEY AUTOINCREMENT,
				droit		VARCHAR(10) not null,
				proprietaire	VARCHAR(10) not null,
				groupe		VARCHAR(10) not null,
				date		DATE TEXT not null,
				nom		VARCHAR(128) not null unique
			)""")
		
		c.execute("""
			CREATE TABLE chunk(
				id		VARCHAR(64) PRIMARY KEY,
				fichier_id	INTEGER not null,
				
				CONSTRAINT fk FOREIGN KEY(fichier_id) REFERENCES fichier(id) ON DELETE CASCADE
			)""")
		
		c.execute("""
			CREATE TABLE xor(
				chunkxor_id	VARCHAR(64) not null,
				chunk_id_A	VARCHAR(64) not null,
				chunk_id_B	VARCHAR(64) not null,
				
				CONSTRAINT fk1 FOREIGN KEY(chunkxor_id) REFERENCES chunk(id),
				CONSTRAINT fk2 FOREIGN KEY(chunk_id_A) REFERENCES chunk(id) ON DELETE CASCADE,
				CONSTRAINT fk2 FOREIGN KEY(chunk_id_B) REFERENCES chunk(id) ON DELETE CASCADE,
				CONSTRAINT pk PRIMARY KEY(chunkxor_id, chunk_id_A, chunk_id_B)
			)""")

		c.execute("""
			CREATE TABLE paire(
				id		INTEGER PRIMARY KEY,
				version		FLOAT,
				h00		INTEGER DEFAULT 0,
				h01		INTEGER DEFAULT 0,
				h02		INTEGER DEFAULT 0,
				h03		INTEGER DEFAULT 0,
				h04		INTEGER DEFAULT 0,
				h05		INTEGER DEFAULT 0,
				h06		INTEGER DEFAULT 0,
				h07		INTEGER DEFAULT 0,
				h08		INTEGER DEFAULT 0,
				h09		INTEGER DEFAULT 0,
				h10		INTEGER DEFAULT 0,
				h11		INTEGER DEFAULT 0,
				h12		INTEGER DEFAULT 0,
				h13		INTEGER DEFAULT 0,
				h14		INTEGER DEFAULT 0,
				h15		INTEGER DEFAULT 0,
				h16		INTEGER DEFAULT 0,
				h17		INTEGER DEFAULT 0,
				h18		INTEGER DEFAULT 0,
				h19		INTEGER DEFAULT 0,
				h20		INTEGER DEFAULT 0,
				h21		INTEGER DEFAULT 0,
				h22		INTEGER DEFAULT 0,
				h23		INTEGER DEFAULT 0
			)""")

		c.execute("""
			CREATE TABLE stocker(
				chunk_id	VARCHAR(64) not null,
				paire_id	INTEGER not null,
				
				CONSTRAINT fk1 FOREIGN KEY(chunk_id) REFERENCES chunk(id) ON DELETE CASCADE,
				CONSTRAINT fk2 FOREIGN KEY(paire_id) REFERENCES paire(id),
				CONSTRAINT pk PRIMARY KEY(chunk_id, paire_id)
			)""")
		
		c.execute("""
			CREATE TRIGGER delete_chunkxor_id BEFORE DELETE ON xor
			BEGIN
				DELETE FROM chunk
				WHERE id = OLD.chunkxor_id;
			END
			""")
		
# Pour le déboguage
except sqlite3.OperationalError : pass

# On ouvre une socket qui accepte les connexions de n'importe qui sur le port 1212 pour n client
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)	# vérifier si "socket.socket()" marche aussi
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)	# cette ligne évite "socket.error: [Errno 98] Address already in use"
s.bind(("",port))
s.listen(nbclient)

# Lancement de notre serveur TCP en démon
serveur = threading.Thread(target=server)
serveur.setDaemon(True)
serveur.start()
print("Le serveur écoute...")
time.sleep(2)

# Lancement de l'interface
try :
	while 1 :
		os.system("clear")
		print("Vous pouvez :")
		print("1) Déposer un fichier")
		print("2) Récupérer un fichier")
		print("3) Supprimer un fichier")
		print("4) Lister les fichiers")
		print("5) Lister les paires")
		print("6) Vider la base de données (fonction de débogue)")
		print("7) Peupler la base de données (fonction de débogue)")
		print("q) Quitter")
		choix = raw_input("Que souhaitez vous faire? ")
		
		# Déposer un fichier dans le cloud
		if choix == '1' :
			fichier_nom = raw_input("Quel est le fichier à déposer : ")
			if not fichier_nom : continue
			if os.path.isfile(rep_upload + fichier_nom) :
				upload(fichier_nom)
			else :
				print("Désolé, {0} n'est pas dans le répertoire {1}.".format(fichier_nom,rep_upload))
			raw_input(pause)
		
		# Récupérer un fichier à partir du cloud
		elif choix == '2' :
			fichier_nom = raw_input("Quel est le fichier distant à récupérer : ")
			if not fichier_nom : continue
			lchunk = fichier2chunk(fichier_nom)
			if lchunk :
				download(fichier_nom, lchunk)
			else :
				print("Désolé, {0} n'est pas dans le cloud.".format(fichier_nom))
			raw_input(pause)
		
		# Supprimer un fichier du cloud
		elif choix == '3' :
			fichier_nom = raw_input("Quel est le fichier distant à supprimer : ")
			if not fichier_nom : continue
			lchunk = fichier2chunk(fichier_nom)
			if lchunk :
				delete(fichier_nom, lchunk)
			else :
				print("Désolé, {0} n'est pas dans le cloud.".format(fichier_nom))
			raw_input(pause)
			
		# Lister les fichiers
		elif choix == '4' :
			print("Les fichier héberger sur le cloud sont :")
			ls()
			raw_input(pause)
		
		# Lister les paires connectées
		elif choix == '5' :
			print("Les paires actives sont :")
			ls_paire()
			raw_input(pause)
		
		# DEBOGUE : vider la base de données
		elif choix == '6' :
			with sqlite3.connect(nom_bdd) as cnx :
				c = cnx.cursor()
				c.execute("DELETE FROM fichier")
				c.execute("DELETE FROM paire")
			raw_input(pause)
		
		# DEBOGUE : remplir la base de données
		elif choix == '7' :
			with sqlite3.connect(nom_bdd) as cnx :
				c = cnx.cursor()
				lpaire_id = paire.keys()
				c.execute("""
					INSERT INTO paire(h18, h19, h20, h21, h22, h23, h0, h1, h2)
					VALUES(2,1,10,17,20,18,10,1,1)
					WHERE id = {2}
					""".format(lpaire_id[0]))
					
				c.execute("""
					INSERT INTO paire(h9, h10, h11, h12, h13, h14, h15, h16, h17, h18)
					VALUES(20,18,21,15,17,18,20,21,16,1)
					WHERE id = {2}
					""".format(lpaire_id[1]))
				
				c.execute("""
					INSERT INTO paire(h0, h1, h2, h3, h4, h5, h6, h7, h8, h9, h10, h11, h12, h13, h14, h15, h16, h17, h18, h19, h20, h21, h22, h23)
					VALUES(17,20,18,17,20,18,17,20,18,17,20,18,17,20,18,17,20,18,17,20,18,17,20,18)
					WHERE id = {2}
					""".format(lpaire_id[2]))
				
				#c.execute("""
				#	INSERT INTO paire(h21, h22, h23, h0, h1, h2, h3, h4, h5)
				#	VALUES(2,1,10,17,20,18,10,1,1)
				#	WHERE id = {2}
				#	""".format(lpaire_id[3]))
				#
				#c.execute("""
				#	INSERT INTO paire(h7, h8, h12, h13, h18, h19)
				#	VALUES(15,16,20,17,30,28)
				#	WHERE id = {2}
				#	""".format(lpaire_id[4]))
			raw_input(pause)
		
		# Quitter le programme
		elif choix == 'q' :
			quit()

# Pour le déboguage
except Exception, e :
	print(e)

# Quoi qu'il arrive on quitte proprement
finally :
	quit()

# Fin									       #
################################################################################
