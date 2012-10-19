#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
if sys.platform.startswith("win") : sys.path.append("C:\\Python27\\lib\\webpy")
import web; web.config.debug = False
from objet import *

# Debogue
sys.path.append("../Debogue")
from debogue import *

main = sys.modules['__main__']

Login_bdd = web.form.Form(
	web.form.Textbox("ip"),
	web.form.Textbox("port"),
	web.form.Button("Go"),
	validators = [
		web.form.Validator("Mauvais IP.",
		lambda champ : web.net.validipaddr(champ.ip)),
		web.form.Validator("Mauvais port.",
		lambda champ : web.net.validipport(champ.port))
		])


Login_p2p = web.form.Form(
	web.form.Textbox("id"),
	web.form.Button("Go"),
	validators = [
		web.form.Validator("ID inconnu.",
		lambda champ : int(champ.id) in main.maconf.paires.keys())
		])


Validation = web.form.Form(
	web.form.Textbox("ok"),
	web.form.Button("Go"),
	validators = [
		web.form.Validator("Erreur lors de l'execuction de l'ordre.",
		lambda champ : champ.ok == "ok")
		])
	

def template_xml(contenu) :
	"""
	Fonction enrobant de façon correcte un contenu XML
	"""
	return """<?xml version="1.0" encoding="ISO-8859-1" ?>
		<xml>
			{0}
		</xml>
		""".format(contenu)


class bdd(object) :
	"""
	Le flux d'échange d'information en P2P
	"""
	def GET(self) :
		#return template_xml('')
		raise web.notfound()
	
	
	def POST(self) :
		donnees_post = Login_bdd()
		
		if donnees_post.validates() :
			
			# On rassemble les données en POST
			uncontact = Contact()
			uncontact.ip = donnees_post["ip"].value
			uncontact.port = donnees_post["port"].value
			
			# On ajoute cet inconnu à la liste des contacts si elle n'y est pas déjà
			if (uncontact.ip == web.ctx.ip) :
				main.maconf.contacts[uncontact.ip] = uncontact
				
			else :
				#return template_xml('')
				raise web.notfound()
			
		else :
			#return template_xml('')
			raise web.notfound()
		
		# On crée le code XML pour transmettre les informations du Master
		contenu = ''
		if main.maconf.master.id :
			
			contenu += """
			<master>
				<id>{0.id}</id>
				<sha256>{0.sha256}</sha256>
				<date>{0.date}</date>
				<signature>{0.signature}</signature>
			</master>
			""".format(main.maconf.master)
		
		# On crée le code XML pour transmettre la liste des paires
		for paire in main.maconf.paires.values() :
			
			contenu += """
			<paire>
				<id>{0.id}</id>
				<ip>{0.ip}</ip>
				<port>{0.port}</port>
				<espace>{0.espace}</espace>
				<espace_consome>{0.espace_consome}</espace_consome>
				<privilege>{0.privilege}</privilege>
				<systeme>{0.systeme}</systeme>
				<arch>{0.arch}</arch>
				<sha256>{0.sha256}</sha256>
				<date>{0.date}</date>
				<signature>{0.signature}</signature>
				<score>{1}</score>
				<date_score>{0.date_score}</date_score>
				<signature_score>{0.signature_score}</signature_score>
				<cle>{2}</cle>
			</paire>
			""".format(paire, ' '.join([str(e) for e in paire.score]), paire.cle.exportKey())
		
		# On crée le code XML pour transmettre la liste des fichiers
		for unfichier in main.maconf.fichiers.values() :
			
			contenu += """
			<fichier>
				<id>{0.id}</id>
				<nom>{0.nom}</nom>
				<date>{0.date}</date>
				<poids>{0.poids}</poids>
				<signature>{0.signature}</signature>
			""".format(unfichier)
			
			for unchunk in unfichier.chunks :
				
				contenu += """
				<chunk>
					<id>{0.id}</id>
					<date>{0.date}</date>".format(unchunk)
					<signature>{0.signature}</signature>
				</chunk>
				""".format(unchunk)
				
				for unepaire in unchunk.stockeurs :
					contenu += "<stockeur>{0.id}</stockeur>".format(unepaire)
			
			contenu += "</fichier>"
		
		# On crée le code XML pour transmettre la liste des xor
		for unxor in main.maconf.xors.values() :
			
			contenu += """
			<xor>
				<chunk>{0.id}</chunk>
				<chunk>{0.a}</chunk>
				<chunk>{0.b}</chunk>
				<signature>{0.signature}</signature>
			</xor>
			""".format(unxor)
		
		# On crée le code XML pour transmettre la liste des utilisateurs
		for unutilisateur in main.maconf.utilisateurs.values() :
			
			contenu += """
			<utilisateur>
				<id>{0.id}</id>
				<mot_de_passe>{0.mot_de_passe}</mot_de_passe>
				<courriel>{0.courriel}</courriel>
				<date>{0.date}</date>
				<signature>{0.signature}</signature>
			</utilisateur>
			""".format(unutilisateur)
		
		## On crée le code XML pour transmettre notre empleinte logicielle
		#contenu += """
		#<digest>
			#<sha256>{0.sha256}</sha256>
			#<date>{0.date}</date>
			#<signature>{0.signature}</signature>
		#</digest>
		#""".format(main.maconf.digest)
		
		# On retourne la page en y incrustant la code XML précédement crée
		web.header('Content-Type', 'text/xml')
		return template_xml(contenu)


class commande(object) :
	"""
	Le flux de download de chunk
	"""
	def GET(self) :
		#return template_xml('')
		raise web.notfound()
	
	
	def POST(self) :
		donnees_post = Login_p2p()
		if donnees_post.validates() :
			
			# On récupère l'id de la paire courante
			lapaire_id = int(donnees_post["id"].value)
			
			# Si la paire valide l'execuction d'un ordre on le retir de la stack
			validation_post = Validation()
			if validation_post.validates() :
				main.maconf.paires[lapaire_id].stack.pop(0)
			
			# On crée le code XML de du premier ordre en stack
			try :
				if main.maconf.paires[lapaire_id].stack[0].ordre == 'r' :
					contenu = """
						<ordre>r</ordre>
						<id>{0.id}</id>
					""".format(main.maconf.paires[lapaire_id].stack[0])
					
				elif main.maconf.paires[lapaire_id].stack[0].ordre == 'w' :
					contenu = """
						<ordre>w</ordre>
						<id>{0.id}</id>
						<donnees>{0.donnees}</donnees>
					""".format(main.maconf.paires[lapaire_id].stack[0])
					
				elif main.maconf.paires[lapaire_id].stack[0].ordre == '-' :
					contenu = """
						<ordre>-</ordre>
						<id>{0.id}</id>
					""".format(main.maconf.paires[lapaire_id].stack[0])
				
				web.header('Content-Type', 'text/xml')
				return template_xml(contenu)
				
			except IndexError :
				DEBOGUE().trace("ICI", "aucun ordre en stack")
				#return template_xml('')
				raise web.notfound()
			
		else :
			#return template_xml('')
			raise web.notfound()


class mise_a_jour(object) :
	"""
	Le flux de download de la mise à jour
	"""
	def GET(self) :
		#return None
		raise web.notfound()
	
	
	def POST(self) :
		donnees_post = Login_p2p()
		if donnees_post.validates() :
			web.header("Content-Type", "application/octet-stream")
			return open(main.maconf.executable, 'rb').read()
			
		else :
			raise web.notfound()


def serveur() :
	"""
	Fonction attrapant les connexions entrantes
	"""
	urls = ("/bdd.xml",		"bdd",
		"/commande.xml",	"commande",
		"/mise_a_jour",		"mise_a_jour")

	sys.stdout.write("écoute sur ")
	sys.argv = sys.argv[0], str(main.maconf.moi.port)
	monapplication = web.application(urls, globals())  # locals()) ???
	monapplication.run()

