#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys
import sqlite3
from Crypto.PublicKey.RSA import importKey

main = sys.modules['__main__']

class Conf(object) :
	def __init__(self) :
		self.monchemin = os.path.abspath(sys.argv[0])
		self.monrep = os.path.dirname(self.monchemin)
		self.executable = os.path.basename(self.monchemin)
		self.mabdd = os.path.splitext(self.executable)[0] + ".sqlite"
		
		self.moi = Paire()
		self.master = Master()
		self.contacts = dict()
		
		self._paires = dict()
		self._fichiers = dict()
		self._xors = dict()
		self._utilisateurs = dict()
	
	# lecture automatique en base de données de la liste des paires
	def _get_paires(self) :
		if not self._paires :
			with sqlite3.connect(self.mabdd) as cnx :
				c = cnx.cursor()
				c.execute("SELECT id FROM paire;")
			
			for (unid,) in c.fetchall() :
				unepaire = Paire()
				unepaire.id = int(unid)
				self._paires[unepaire.id] = unepaire
		
		return self._paires
	
	paires = property(_get_paires)
	
	# lecture automatique en base de données de la liste des fichiers
	def _get_fichiers(self) :
		if not self._fichiers :
			with sqlite3.connect(self.mabdd) as cnx :
				c = cnx.cursor()
				c.execute("""
					SELECT id
					FROM fichier
					ORDER BY fichier.nom;
					""")
			
			for (unid,) in c.fetchall() :
				unfichier = Fichier()
				unfichier.id = int(unid)
				self._fichiers[unfichier.id] = unfichier
		
		return self._fichiers
	
	fichiers = property(_get_fichiers)	
	
	# lecture automatique en base de données de la liste des xors
	def _get_xors(self) :
		if not self._xors :
			with sqlite3.connect(self.mabdd) as cnx :
				c = cnx.cursor()
				c.execute("SELECT chunkxor_id FROM xor;")
			
			for (unid,) in c.fetchall() :
				unxor = Fichier()
				unxor.id = unid
				self._xors[unxor.id] = unxor
		
		return self._xors
	
	xors = property(_get_xors)	
	
	# lecture automatique en base de données de la liste des utilisateurs
	def _get_utilisateurs(self) :
		if not self._utilisateurs :
			with sqlite3.connect(self.mabdd) as cnx :
				c = cnx.cursor()
				c.execute("SELECT id FROM utilisateur;")
			
			for (unid,) in c.fetchall() :
				unutilisateur = Utilisateur()
				unutilisateur.id = unid
				self._utilisateurs[unutilisateur.id] = unutilisateur
		
		return self._utilisateurs
	
	utilisateurs = property(_get_utilisateurs)	


class Utilisateur(object) :
	def __init__(self) :
		self.id = str()
		self._mot_de_passe = str()
		self._courriel = str()
		self._date = float()
		self._signature = long()
	
	# Methode pour enregistrer notre objet en base de données
	def save(self) : 
		with sqlite3.connect(main.maconf.mabdd) as cnx :
			c = cnx.cursor()
			try : c.execute("""
				INSERT INTO utilisateur(id, mot_de_passe,
					courriel, date, signature)
				VALUES('{0.id}', '{0.mot_de_passe}',
					'{0.courriel}', '{0.date}', '{0.signature}')
				""".format(self))
				
			except sqlite3.IntegrityError :
				c.execute("""
				UPDATE utilisateur
				SET	mot_de_passe = '{0.mot_de_passe}',
					courriel = '{0.courriel}',
					date = '{0.date}',
					signature = '{0.signature}'
				WHERE id = '{0.id}';
				""".format(self))
	
	# lecture automatique en base de données du mot_de_passe
	def _get_mot_de_passe(self) :
		if not self._mot_de_passe :
			with sqlite3.connect(main.maconf.mabdd) as cnx :
				c = cnx.cursor()
				c.execute("""
					SELECT mot_de_passe
					FROM utilisateur
					WHERE id = '{0.id}';
					""".format(self))
			
			self._mot_de_passe, = c.fetchone()
		
		return self._mot_de_passe
	
	def _set_mot_de_passe(self, mot_de_passe) :
		self._mot_de_passe = mot_de_passe
	
	mot_de_passe = property(_get_mot_de_passe, _set_mot_de_passe)

	# lecture automatique en base de données du courriel
	def _get_courriel(self) :
		if not self._courriel :
			with sqlite3.connect(main.maconf.mabdd) as cnx :
				c = cnx.cursor()
				c.execute("""
					SELECT courriel
					FROM utilisateur
					WHERE id = '{0.id}';
					""".format(self))
			
			self._courriel, = c.fetchone()
		
		return self._courriel
	
	def _set_courriel(self, courriel) :
		self._courriel = courriel
	
	courriel = property(_get_courriel, _set_courriel)

	# lecture automatique en base de données de la date
	def _get_date(self) :
		if not self._date :
			with sqlite3.connect(main.maconf.mabdd) as cnx :
				c = cnx.cursor()
				c.execute("""
					SELECT date
					FROM utilisateur
					WHERE id = '{0.id}';
					""".format(self))
			
			resultat, = c.fetchone()
			self._date = float(resultat)
		
		return self._date
	
	def _set_date(self, date) :
		self._date = date
	
	date = property(_get_date, _set_date)

	# lecture automatique en base de données de la signature
	def _get_signature(self) :
		if not self._signature :
			with sqlite3.connect(main.maconf.mabdd) as cnx :
				c = cnx.cursor()
				c.execute("""
					SELECT signature
					FROM utilisateur
					WHERE id = '{0.id}';
					""".format(self))
			
			resultat, = c.fetchone()
			self._signature = long(resultat)
		
		return self._signature
	
	def _set_signature(self, signature) :
		self._signature = signature
	
	signature = property(_get_signature, _set_signature)


class Commande(object) :
	def __init__(self) :
		self.ordre = char()
		self.id = str()
		self.donnees = str()


class Chunk(object) :
	def __init__(self) :
		self.id = str()
		self.donnees = str()
		self._date = float()
		self._signature = long()
		self._stockeurs = list()
		#self._date_stockeurs
		#self._signature_stockeurs
	
	# Methode pour enregistrer notre objet en base de données
	def save(self) : 
		with sqlite3.connect(main.maconf.mabdd) as cnx :
			c = cnx.cursor()
			c.execute("""
				INSERT INTO chunk(id, date, signature)
				VALUES('{0.id}', '{0.date}', '{0.signature}')
				ON DUPLICATE KEY
				UPDATE date = '{0.date}', signature = '{0.signature}';
				""".format(self))
			
			for unepaire in self.stockeurs :
				try : c.execute("""
					INSERT INTO stocker(chunk_id, paire_id)
					VALUES('{0.id}', '{1.id}');
					""".format(self, unepaire))
					
				except sqlite3.IntegrityError : pass
	
	# lecture automatique en base de données de la date
	def _get_date(self) :
		if not self._date :
			with sqlite3.connect(main.maconf.mabdd) as cnx :
				c = cnx.cursor()
				c.execute("""
					SELECT date
					FROM chunk
					WHERE id = '{0.id}';
					""".format(self))
			
			resultat, = c.fetchone()
			self._date = float(resultat)
		
		return self._date
	
	def _set_date(self, date) :
		self._date = date
	
	date = property(_get_date, _set_date)
	
	# lecture automatique en base de données des paire stockant le chunk
	def _get_stockeurs(self) :
		if not self._stockeurs :
			with sqlite3.connect(main.maconf.mabdd) as cnx :
				c = cnx.cursor()
				c.execute("""
					SELECT paire_id
					FROM stocker
					WHERE chunk_id = '{0.id}'
					ORDER BY stocker.rowid;
					""".format(self))
			
			for (e,) in c.fetchall() :
				unepaire = Paire()
				unepaire.id = int(e)
				self._stockeurs.append(unepaire)
	
	stockeur = property(_get_stockeurs)

	# lecture automatique en base de données de la signature
	def _get_signature(self) :
		if not self._signature :
			with sqlite3.connect(main.maconf.mabdd) as cnx :
				c = cnx.cursor()
				c.execute("""
					SELECT signature
					FROM chunk
					WHERE id = '{0.id}';
					""".format(self))
			
			resultat, = c.fetchone()
			self._signature = long(resultat)
		
		return self._signature
	
	def _set_signature(self, signature) :
		self._signature = signature
	
	signature = property(_get_signature, _set_signature)


class Xor(object) :
	def __init__(self) :
		self.id = str()
		self._a = str()
		self._b = str()
		self._date = float()
		self._signature = long()
	
	# Methode pour enregistrer notre objet en base de données
	def save(self) : 
		with sqlite3.connect(main.maconf.mabdd) as cnx :
			c = cnx.cursor()
			c.execute("""
				INSERT INTO xor(chunkxor_id, chunk_id_A,
					chunk_id_B, date, signature)
				VALUES('{0.id}', '{0.a}', '{0.b}', '{0.date}',
					'{0.signature}')
				ON DUPLICATE KEY
				UPDATE chunk_id_A = '{0.a}', chunk_id_B = '{0.b}',
					date = '{0.date}', signature = '{0.signature}';
				""".format(self))
	
	# lecture/enregistrement automatique en base de données du chunk A
	def _get_a(self) :
		if not self._a :
			with sqlite3.connect(main.maconf.mabdd) as cnx :
				c = cnx.cursor()
				c.execute("""
					SELECT chunk_id_A
					FROM xor
					WHERE chunkxor_id = '{0.id}';
					""".format(self))
				self._a, = c.fetchone()
		
		return self._a
	
	def _set_a(self, a) :
		self._a = a
	
	ip = property(_get_a, _set_a)
	
	# lecture/enregistrement automatique en base de données du chunk B
	def _get_b(self) :
		if not self._b :
			with sqlite3.connect(main.maconf.mabdd) as cnx :
				c = cnx.cursor()
				c.execute("""
					SELECT chunk_id_B
					FROM xor
					WHERE chunkxor_id = '{0.id}';
					""".format(self))
				self._b, = c.fetchone()
		
		return self._b
	
	def _set_b(self, b) :
		self._b = b
	
	ip = property(_get_b, _set_b)
	
	# lecture/enregistrement automatique en base de données de la date
	def _get_date(self) :
		if not self._date :
			with sqlite3.connect(main.maconf.mabdd) as cnx :
				c = cnx.cursor()
				c.execute("""
					SELECT date
					FROM xor
					WHERE chunkxor_id = '{0.id}';
					""".format(self))
				self._date, = c.fetchone()
		
		return self._date
	
	def _set_date(self, date) :
		self._date = date
	
	ip = property(_get_date, _set_date)
	
	# lecture/enregistrement automatique en base de données de la signature
	def _get_signature(self) :
		if not self._signature :
			with sqlite3.connect(main.maconf.mabdd) as cnx :
				c = cnx.cursor()
				c.execute("""
					SELECT signature
					FROM xor
					WHERE chunkxor_id = '{0.id}';
					""".format(self))
				self._signature, = c.fetchone()
		
		return self._signature
	
	def _set_signature(self, signature) :
		self._signature = signature
	
	ip = property(_get_signature, _set_signature)


class Fichier(object) :
	def __init__(self) :
		self.id = int()
		self._nom = str()
		self._date = float()
		self._poids = int()
		self._signature = long()
		self._chunks = list()
	
	# Methode pour enregistrer notre objet en base de données
	def save(self) : 
		with sqlite3.connect(main.maconf.mabdd) as cnx :
			c = cnx.cursor()
			c.execute("""
				INSERT INTO fichier(id, nom, date, poids,
					signature)
				VALUES('{0.id}', '{0.nom}', '{0.date}',
					'{0.poids}', '{0.signature}')
				ON DUPLICATE KEY
				UPDATE id = '{0.id}', nom = '{0.nom}',
					date = '{0.date}', poids = '{0.poids}',
					signature = '{0.signature}';
				""".format(self))
			
			for unchunk in self.chunks : unchunk.save()
	
	# lecture automatique en base de données du nom du fichier
	def _get_nom(self) :
		if not self._nom :
			with sqlite3.connect(main.maconf.mabdd) as cnx :
				c = cnx.cursor()
				c.execute("""
					SELECT nom
					FROM fichier
					WHERE id = '{0.id}';
					""".format(self))
				self._nom, = c.fetchone()
		
		return self._nom
	
	def _set_nom(self, nom) :
		self._nom = nom
	
	ip = property(_get_nom, _set_nom)
	
	# lecture automatique en base de données de la date du fichier
	def _get_date(self) :
		if not self._date :
			with sqlite3.connect(main.maconf.mabdd) as cnx :
				c = cnx.cursor()
				c.execute("""
					SELECT date
					FROM fichier
					WHERE id = '{0.id}';
					""".format(self))
				self._date, = c.fetchone()
		
		return self._date
	
	def _set_date(self, date) :
		self._date = date
	
	ip = property(_get_date, _set_date)
	
	# lecture automatique en base de données du poids en octets
	def _get_poids(self) :
		if not self._poids :
			with sqlite3.connect(main.maconf.mabdd) as cnx :
				c = cnx.cursor()
				c.execute("""
					SELECT poids
					FROM fichier
					WHERE id = '{0.id}';
					""".format(self))
				self._poids, = c.fetchone()
		
		return self._poids
	
	def _set_poids(self, poids) :
		self._poids = poids
	
	ip = property(_get_poids, _set_poids)
	
	# lecture automatique en base de données de la signature des paramêtres
	def _get_signature(self) :
		if not self._signature :
			with sqlite3.connect(main.maconf.mabdd) as cnx :
				c = cnx.cursor()
				c.execute("""
					SELECT signature
					FROM fichier
					WHERE id = '{0.id}';
					""".format(self))
				self._signature, = c.fetchone()
		
		return self._signature
	
	def _set_signature(self, signature) :
		self._signature = signature
	
	ip = property(_get_signature, _set_signature)
	
	# lecture automatique en base de données
	def _get_chunks(self) :
		if not self._get_chunks :
			with sqlite3.connect(main.maconf.mabdd) as cnx :
				c = cnx.cursor()
				c.execute("""
					SELECT id
					FROM chunk
					WHERE fichier_id = '{0.id}'
					ORDER BY chunk.rowid;
					""".format(self))
			
			for (unid,) in c.fetchall() :
				unchunk = Chunk()
				unchunk.id = unid
				self.append(unchunk)
	
	chunks = property(_get_chunks)


class Contact(object) :
	def __init__(self) :
		self.ip = str()
		self.port = int()


class Paire(object) :
	def __init__(self) :
		self.id = int()
		self._ip = str()
		self._port = int()
		self._espace = int()
		self._espace_consome = int()
		self._privilege = str()
		self._systeme = str()
		self._arch = str()
		self._sha256 = str()
		self._date = float()
		self._signature = long()  # de "<id>\n<ip>\n<port>\n<espace>\n
		                          # <espace_consome>\n<privilege>\n
		                          # <systeme>\n<arch>\n<sha256>\n<date>"
		self._score = [0]*24
		self._date_score = float()
		self._signature_score = long()  # de "<id>\n<score>\n<date_score>"
		self._cle = None
		self.stack = list()
	
	# Methode pour enregistrer notre objet en base de données
	def save(self) : 
		with sqlite3.connect(main.maconf.mabdd) as cnx :
			c = cnx.cursor()
			try : c.execute("""
				INSERT INTO paire(id, ip, port, espace,
					espace_consome, privilege, systeme,
					arch, sha256, date, signature,
					h00, h01, h02, h03, h04,
					h05, h06, h07, h08, h09,
					h10, h11, h12, h13, h14,
					h15, h16, h17, h18, h19,
					h20, h21, h22, h23,
					date_score, signature_score, cle)
				VALUES('{0.id}', '{0.ip}', '{0.port}',
					'{0.espace}', '{0.espace_consome}',
					'{0.privilege}', '{0.systeme}',
					'{0.arch}', '{0.sha256}', '{0.date}',
					'{0.signature}',
					'{0.score[0]}', '{0.score[1]}',
					'{0.score[2]}', '{0.score[3]}', 
					'{0.score[4]}', '{0.score[5]}',
					'{0.score[6]}', '{0.score[7]}',
					'{0.score[8]}', '{0.score[9]}',
					'{0.score[10]}', '{0.score[11]}',
					'{0.score[12]}', '{0.score[13]}',
					'{0.score[14]}', '{0.score[15]}',
					'{0.score[16]}', '{0.score[17]}',
					'{0.score[18]}', '{0.score[19]}',
					'{0.score[20]}', '{0.score[21]}',
					'{0.score[22]}', '{0.score[23]}',
					'{0.date_score}', '{0.signature_score}',
					'{1}');
				""".format(self, self.cle.exportKey()))
				
			except sqlite3.IntegrityError :
				c.execute("""
				UPDATE paire
				SET	ip = '{0.ip}',
					port = '{0.port}',
					espace = '{0.espace}',
					espace_consome = '{0.espace_consome}',
					privilege = '{0.privilege}',
					systeme = '{0.systeme}',
					arch = '{0.arch}',
					sha256 = '{0.sha256}',
					date = '{0.date}',
					signature = '{0.signature}',
					h00 = '{0.score[0]}', h01 = '{0.score[1]}',
					h02 = '{0.score[2]}', h03 = '{0.score[3]}',
					h04 = '{0.score[4]}', h05 = '{0.score[5]}',
					h06 = '{0.score[6]}', h07 = '{0.score[7]}',
					h08 = '{0.score[8]}', h09 = '{0.score[9]}',
					h10 = '{0.score[10]}', h11 = '{0.score[11]}',
					h12 = '{0.score[12]}', h13 = '{0.score[13]}',
					h14 = '{0.score[14]}', 	h15 = '{0.score[15]}',
					h16 = '{0.score[16]}', h17 = '{0.score[17]}',
					h18 = '{0.score[18]}', h19 = '{0.score[19]}',
					h20 = '{0.score[20]}', h21 = '{0.score[21]}',
					h22 = '{0.score[22]}', h23 = '{0.score[23]}',
					date_score = '{0.date_score}',
					signature_score = '{0.signature_score}',
					cle = '{1}'
				WHERE id = '{0.id}';
				""".format(self, self.cle.exportKey()))
	
	# lecture automatique en base de données de l'IP
	def _get_ip(self) :
		if not self._ip :
			with sqlite3.connect(main.maconf.mabdd) as cnx :
				c = cnx.cursor()
				c.execute("""
					SELECT ip
					FROM paire
					WHERE id = '{0.id}';
					""".format(self))
			
			try : self._ip, = c.fetchone()
			except TypeError : pass
		
		return self._ip
	
	def _set_ip(self, ip) :
		self._ip = ip
	
	ip = property(_get_ip, _set_ip)
	
	# lecture automatique en base de données du port TCP
	def _get_port(self) :
		if not self._port :
			with sqlite3.connect(main.maconf.mabdd) as cnx :
				c = cnx.cursor()
				c.execute("""
					SELECT port
					FROM paire
					WHERE id = '{0.id}';
					""".format(self))
			
			try : self._port, = c.fetchone()
			except TypeError : pass
		
		return self._port
	
	def _set_port(self, port) :
		self._port = port

	port = property(_get_port, _set_port)
	
	# lecture automatique en base de données
	def _get_espace(self) :
		if not self._espace :
			with sqlite3.connect(main.maconf.mabdd) as cnx :
				c = cnx.cursor()
				c.execute("""
					SELECT espace
					FROM paire
					WHERE id = '{0.id}';
					""".format(self))
			
			try : self._espace, = c.fetchone()
			except TypeError : pass
		
		return self._espace
	
	def _set_espace(self, espace) :
		self._espace = espace

	espace = property(_get_espace, _set_espace)
	
	# lecture automatique en base de données
	def _get_espace_consome(self) :
		if not self._espace_consome :
			with sqlite3.connect(main.maconf.mabdd) as cnx :
				c = cnx.cursor()
				c.execute("""
					SELECT espace_consome
					FROM paire
					WHERE id = '{0.id}';
					""".format(self))
			
			try : self._espace_consome, = c.fetchone()
			except TypeError : pass
		
		return self._espace_consome
	
	def _set_espace_consome(self, espace_consome) :
		self._espace_consome = espace_consome

	espace_consome = property(_get_espace_consome, _set_espace_consome)
	
	# lecture automatique en base de données
	def _get_privilege(self) :
		if not self._privilege :
			with sqlite3.connect(main.maconf.mabdd) as cnx :
				c = cnx.cursor()
				c.execute("""
					SELECT privilege
					FROM paire
					WHERE id = '{0.id}';
					""".format(self))
			
			try : self._privilege, = c.fetchone()
			except TypeError : pass
		
		return self._privilege
	
	def _set_privilege(self, privilege) :
		self._privilege = privilege
	
	privilege = property(_get_privilege, _set_privilege)
	
	# lecture automatique en base de données
	def _get_systeme(self) :
		if not self._systeme :
			with sqlite3.connect(main.maconf.mabdd) as cnx :
				c = cnx.cursor()
				c.execute("""
					SELECT systeme
					FROM paire
					WHERE id = '{0.id}';
					""".format(self))
			
			try : self._systeme, = c.fetchone()
			except TypeError : pass
		
		return self._systeme
	
	def _set_systeme(self, systeme) :
		self._systeme = systeme
	
	systeme = property(_get_systeme, _set_systeme)
	
	# lecture automatique en base de données
	def _get_arch(self) :
		if not self._arch :
			with sqlite3.connect(main.maconf.mabdd) as cnx :
				c = cnx.cursor()
				c.execute("""
					SELECT arch
					FROM paire
					WHERE id = '{0.id}';
					""".format(self))
			
			try : self._arch, = c.fetchone()
			except TypeError : pass
		
		return self._arch
	
	def _set_arch(self, arch) :
		self._arch = arch
	
	arch = property(_get_arch, _set_arch)
	
	# lecture automatique en base de données
	def _get_sha256(self) :
		if not self._sha256 :
			with sqlite3.connect(main.maconf.mabdd) as cnx :
				c = cnx.cursor()
				c.execute("""
					SELECT sha256
					FROM paire
					WHERE id = '{0.id}';
					""".format(self))
			
			try : self._sha256, = c.fetchone()
			except TypeError : pass
		
		return self._sha256
	
	def _set_sha256(self, sha256) :
		self._sha256 = sha256
	
	sha256 = property(_get_sha256, _set_sha256)
	
	# lecture automatique en base de données de la date des paramêtres
	def _get_date(self) :
		if not self._date :
			with sqlite3.connect(main.maconf.mabdd) as cnx :
				c = cnx.cursor()
				c.execute("""
					SELECT date
					FROM paire
					WHERE id = '{0.id}';
					""".format(self))
			
			try : self._date, = c.fetchone()
			except TypeError : pass
		
		return self._date
	
	def _set_date(self, date) :
		self._date = date
	
	date = property(_get_date, _set_date)
	
	# lecture automatique en base de données de la signature des paramêtres
	def _get_signature(self) :
		if not self._signature :
			with sqlite3.connect(main.maconf.mabdd) as cnx :
				c = cnx.cursor()
				c.execute("""
					SELECT signature
					FROM paire
					WHERE id = '{0.id}';
					""".format(self))
			
			try : self._signature, = c.fetchone()
			except TypeError : pass
		
		return self._signature
	
	def _set_signature(self, signature) :
		self._signature = signature
	
	signature = property(_get_signature, _set_signature)
	
	# electure automatique en base de données des scores
	def _get_score(self) :
		if not self._score :
			with sqlite3.connect(main.maconf.mabdd) as cnx :
				c = cnx.cursor()
				c.execute("""
					SELECT h00, h01, h02, h03, h04,
					       h05, h06, h07, h08, h09,
					       h10, h11, h12, h13, h14,
					       h15, h16, h17, h18, h19,
					       h20, h21, h22, h23
					FROM paire
					WHERE id = '{0.id}';
					""".format(self))
			
			self._score = c.fetchone()
			#try : self._score = c.fetchone()
			#except TypeError : pass
		
		return self._score
	
	def _set_score(self, score) :
		self._score = score
	
	score = property(_get_score, _set_score)
	
	# lecture automatique en base de données de la date des scores
	def _get_date_score(self) :
		if not self._date_score :
			with sqlite3.connect(main.maconf.mabdd) as cnx :
				c = cnx.cursor()
				c.execute("""
					SELECT date_score
					FROM paire
					WHERE id = '{0.id}';
					""".format(self))
			
			try : self._date_score, = c.fetchone()
			except TypeError : pass
		
		return self._date_score
	
	def _set_date_score(self, date_score) :
		self._date_score = date_score
	
	date_score = property(_get_date_score, _set_date_score)
	
	# lecture automatique en base de données de la signature des scores
	def _get_signature_score(self) :
		if not self._signature_score :
			with sqlite3.connect(main.maconf.mabdd) as cnx :
				c = cnx.cursor()
				c.execute("""
					SELECT signature_score
					FROM paire
					WHERE id = '{0.id}';
					""".format(self))
			
			try : self._signature_score, = c.fetchone()
			except TypeError : pass
		
		return self._signature_score
	
	def _set_signature_score(self, signature_score) :
		self._signature_score = signature_score
	
	signature_score = property(_get_signature_score, _set_signature_score)
	
	# lecture automatique en base de données de la clé
	def _get_cle(self) :
		if not self._cle :
			with sqlite3.connect(main.maconf.mabdd) as cnx :
				c = cnx.cursor()
				c.execute("""
					SELECT cle
					FROM paire
					WHERE id = '{0.id}';
					""".format(self))
			
			try :
				resultat, = c.fetchone()
				self._cle = importKey(resultat)
			except TypeError : pass
		
		return self._cle
	
	def _set_cle(self, cle) :
		self._cle = cle
	
	cle = property(_get_cle, _set_cle)


class Master(object) :
	def __init__(self) :
		self._id = int()
		self._ip = str()
		self._port = int()
		self._sha256 = str()
		self._date = float()
		self._signature = long()
		self.cle = importKey("-----BEGIN PUBLIC KEY-----\n\
		MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEAmDRmI5HLoenaMc4J7fHC\n\
		rhVYBqR3quZiBq4NMQrjIVv90yHVDrOp1y6M83gh2w7Ty1CL6wLIXiXoC81AnI1n\n\
		m5no9l/wb33mCdFuyt7+8oMwrM1MFH/CX29Jiwgow2ZjkslX9eRRIhCClaaviM1d\n\
		7i4TWk5ucM5qmHy4K9Fd0H7PxgNNsTLUOoapyk5uAFCT3tPSiqHssM9HRwdBsWSr\n\
		JaN80axWlWXp2nU0zTJVjIibHG+woLTXjVdUkJQrg7AWrfZgYIKFPVDwpSD1/RUt\n\
		6jEsIQDS7rYhwnrlbhCHa/YZQYy+cPCSY9MsX59YddAcxK8kkFrgFEM6WpRWJrKO\n\
		drh3P3nmEVjprwQl18oIkz8gw2AOefZgS+h3B0zRSPWL+ER3ixHvzy/HMmqULwHt\n\
		9eAN4lhIRSWMubi/9bXtyyo4rU3YMGSvU80QRghxLqXXyQj8BBma/wOjNMvJ0RkS\n\
		H86U0NHxTpaCZOPPQioTCTod93/i9eO66i/Hl0olsaPCdP50QCTmTjTHHEtvyZV3\n\
		R+W4L8H/HYYP4PXFGKef/OnsPlm+girFKl3OjJBrB6dMG79mxuuQita1ii/3qCtJ\n\
		n7XFnOx//it/FaCF2ondnXdFZF+jsz+4prMgZIlUryKIW1+9JH4pTIWP/p0VzKSN\n\
		JK9A2LezGAOsyNSNZLw12F0CAwEAAQ==\n\
		-----END PUBLIC KEY-----")
	
	# Methode pour enregistrer notre objet en base de données
	def save(self) : 
		with sqlite3.connect(main.maconf.mabdd) as cnx :
			c = cnx.cursor()
			try : c.execute("""
				INSERT INTO parametre(cle, valeur)
				VALUES('master_id', '{0.id}')
				""".format(self))
				
			except sqlite3.IntegrityError :
				c.execute("""
				UPDATE parametre
				SET valeur = '{0.id}'
				WHERE cle = 'master_id';
				""".format(self))
			
			try : c.execute("""
				INSERT INTO parametre(cle, valeur)
				VALUES('master_date', '{0.date}')
				""".format(self))
				
			except sqlite3.IntegrityError :
				c.execute("""
				UPDATE parametre
				SET valeur = '{0.date}'
				WHERE cle = 'master_date';
				""".format(self))
			
			try : c.execute("""
				INSERT INTO parametre(cle, valeur)
				VALUES('master_signature', '{0.signature}')
				""".format(self))
				
			except sqlite3.IntegrityError :
				c.execute("""
				UPDATE parametre
				SET valeur = '{0.signature}'
				WHERE cle = 'master_signature';
				""".format(self))
	
	# lecture automatique en base de données
	def _get_id(self) :
		if not self._id :
			with sqlite3.connect(main.maconf.mabdd) as cnx :
				c = cnx.cursor()
				c.execute("""
					SELECT valeur
					FROM parametre
					WHERE cle = 'master_id';
					""".format(self))
			
			try : self._id, = c.fetchone()
			except TypeError : pass
		
		return self._id
	
	def _set_id(self, id) :
		self._id = id
	
	id = property(_get_id, _set_id)
	
	# lecture automatique en base de données
	def _get_ip(self) :
		if not self._ip :
			with sqlite3.connect(main.maconf.mabdd) as cnx :
				c = cnx.cursor()
				c.execute("""
					SELECT ip
					FROM paire
					WHERE id = '{0.id}';
					""".format(self))
			
			try : self._ip, = c.fetchone()
			except TypeError : pass
		
		return self._ip
	
	ip = property(_get_ip)
	
	# lecture automatique en base de données
	def _get_port(self) :
		if not self._port :
			with sqlite3.connect(main.maconf.mabdd) as cnx :
				c = cnx.cursor()
				c.execute("""
					SELECT port
					FROM paire
					WHERE id = '{0.id}';
					""".format(self))
			
			try : self._port, = c.fetchone()
			except TypeError : pass
		
		return self._port
	
	port = property(_get_port)
	
	# lecture automatique en base de données
	def _get_sha256(self) :
		if not self._sha256 :
			with sqlite3.connect(main.maconf.mabdd) as cnx :
				c = cnx.cursor()
				c.execute("""
					SELECT sha256
					FROM paire
					WHERE id = '{0.id}';
					""".format(self))
			
			try : self._sha256, = c.fetchone()
			except TypeError : pass
		
		return self._sha256
	
	sha256 = property(_get_sha256)
	
	# lecture/enregistrement automatique en base de données de la date des paramêtres
	def _get_date(self) :
		if not self._date :
			with sqlite3.connect(main.maconf.mabdd) as cnx :
				c = cnx.cursor()
				c.execute("""
					SELECT valeur
					FROM parametre
					WHERE cle = 'master_date';
					""")
				
			try : self._date, = c.fetchone()
			except TypeError : pass
		
		return self._date
	
	def _set_date(self, date) :
		self._date = date
	
	date = property(_get_date, _set_date)
	
	# lecture/enregistrement automatique en base de données de la signature des paramêtres
	def _get_signature(self) :
		if not self._signature :
			with sqlite3.connect(main.maconf.mabdd) as cnx :
				c = cnx.cursor()
				c.execute("""
					SELECT valeur
					FROM parametre
					WHERE cle = 'master_signature';
					""")
			
			try : self._signature, = c.fetchone()
			except TypeError : pass
		
		return self._signature
	
	def _set_signature(self, signature) :
		self._signature = signature
	
	signature = property(_get_signature, _set_signature)
	
