#!/usr/bin/env python
# -*- coding: utf-8 -*-

import __builtin__
import sys
import time.time
import random.sample
import hashlib.sha256
import urllib2
if sys.platform.startswith("win") : sys.path.append("C:\\Python27\\lib\\webpy")
import web; web.config.debug = False
import socket.error
from objet import *
from serveur import Login_bdd, Login_p2p, Validation

# Debogue
sys.path.append("../Debogue")
from debogue import *

main = sys.modules['__main__']

Ajout_utilisateur = web.form.Form(
	web.form.Textbox("utilisateur", description="Utilisateur"),
	web.form.Textbox("courriel", description="Courriel"),
	web.form.Button("Ajouter"),
	validators = [
		web.form.Validator("Vous n'avez pas les droits.",
		lambda champ : session.utilisateur == "root"),
		web.form.Validator("Cette paire n'a pas les droits.",
		lambda champ : main.maconf.moi.id == main.maconf.master.id),
		web.form.Validator("L'utilisateur existe déjà.",
		lambda champ : not main.maconf.utilisateurs.has_key(champ.utilisateur)),
		web.form.Validator("L'utilisateur n'a pas de courriel.",
		lambda champ : champ.courriel )
		])


Modif_utilisateur = web.form.Form(
	web.form.Password("mot_de_passe_old", description="Ancien mot de passe"),
	web.form.Password("mot_de_passe_old_verif", description="Vérification"),
	web.form.Password("mot_de_passe", description="Nouveau mot de passe"),	
	web.form.Button("Enregistrer"),
	validators = [
		web.form.Validator("Les mots de passe ne corespondent pas.",
		lambda champ : champ.mot_de_passe_old == champ.mot_de_passe_old_verif ),
		web.form.Validator("Le mots de passe n'est pas diférent.",
		lambda champ : champ.mot_de_passe != champ.mot_de_passe_old ),
		web.form.Validator("Le mots de passe est incorrect.",
		lambda champ : hashlib.sha256(champ.mot_de_passe).hexdigest() \
			== main.maconf.utilisateurs[champ.utilisateur].mot_de_passe )
		])


Login_web = web.form.Form(
	web.form.Textbox("utilisateur", description="Utilisateur"),
	web.form.Password("mot_de_passe", description="Mot de passe"),
	web.form.Button("Connexion"),
	validators = [
		web.form.Validator("Le nom d'utilisateur ou le mot de passe est incorrect.",
		lambda champ : hashlib.sha256(champ.mot_de_passe).hexdigest() \
			== main.maconf.utilisateurs[champ.utilisateur].mot_de_passe )
		])


Upload = web.form.Form(
	web.form.File("fichier", description="Fichier"),
	web.form.Button("Televerser"),
	validators = [
		web.form.Validator("Aucun fichier a uploader.",
		lambda champ : champ.fichier)
		])


def template_html(titre, contenu) :
	"""
	Fonction enrobant de façon correcte un contenu HTML
	"""
	return """
	<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" 
	"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
	<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="fr" lang="fr">
	<head>
		<meta charset="utf-8" />
		<title>Pony Cloud</title>
		<link rel="icon" type="image/png" href="{0[favicon.png]}" />
		<link href="/style.css"	title="Défaut" rel="stylesheet"
		type="text/css" media="screen" /> 
	</head>
	<body>
		<!-- GLOBAL --> 
		<div id="conteneur">
		<div id="header"><!-- Header --></div>
		
		<!-- CONTENU -->
		<div id="contenu">	
			<!-- COLONNE DE GAUCHE -->  
			<div id="left">
				<!-- Titre du site -->
				<img src="{0[titre.png]}" alt=""/>
				<a href="/"><img src="{0[accueil.png]}" alt=""/></a>
				<a href="/cloud/"><img src="{0[download.png]}" alt=""/></a>
				
				<!-- MENU -->
				<div class="menu_haut">Pages :</div>
				<div class="menu_fond">
				<ul>
				<li><a href="/">- Administration</a></li>
				<li><a href="/cloud/">- Les fichiers hébergés</a></li>
				<li><a href="/deconnexion.html">- Déconnexion</a></li>
				<li></li>
				<li><a href="/debogue.html">- [Debogue]</a></li>
				</ul>
				</div><div class="menu_bas"></div>
				<!-- FIN MENU --> 
			</div>
			<!-- FIN COLONNE DE GAUCHE -->	 
			
			<!-- COLONNE DE DROITE -->
			<div id="right">	
				
				<!-- CADRE -->
				<div class="cadre_haut"></div>
				<div class="cadre_fond">	
					<span>{1}</span><br /> 
					{2}
				</div>
				<div class="cadre_bas"></div>
				<!-- FIN CADRE -->  
					
				<!-- CADRE -->	
				<div class="cadre_haut"></div>
				<div class="cadre_fond">
					<div style="text-align: center">
					<img src="{0[donation.png]}" alt=""/>	 
					</div>
				</div><div class="cadre_bas"></div>
				<!-- FIN CADRE --> 		
			</div>
			<!-- FIN COLONNE DE DROITE -->
			
			<div id="clear"><!-- NE PAS SUPPRIMER --></div>	 
		</div>
		<!-- FIN CONTENU -->
		
		<!-- PIED -->
		<div id="pied"></div>
		</div>
		<!-- FIN GLOBAL -->	  
	</body>
	</html>	
	""".format(images, titre, contenu)


class index(object) :
	"""
	La page d'accueil
	"""
	def GET(self) :
		if session.utilisateur != "anonyme" :
			monformulaire = Modif_utilisateur()
			contenu = "<form name=\"main\" action=\"\"  method=\"post\"> \
				<fieldset><legend>Modifier le mot de passe</legend>" \
				+ monformulaire.render() + \
				"</fieldset></form>"
			
			if session.utilisateur == "root" :
				contenu += "<br/><p>Liste des paires :</p><ul>"
				for unepaire in main.maconf.paires.values() :
					contenu += "<li>- {0.id} ({0.ip})</li>".format(unepaire)
				contenu += "</ul><br/>"
				
				contenu += "<p>Liste des contacts :</p><ul>"
				for uncontact in main.maconf.contacts.values() :
					contenu += "<li>- {0.ip}:{0.port}</li>".format(uncontact)
				contenu += "</ul><br/>"
				
				contenu += "<p>Liste des utilisateurs :</p><ul>"
				for unutilisateur in main.maconf.utilisateurs.values() :
					contenu += "<li>- {0.id} ({0.courriel})</li>".format(unutilisateur)
				contenu += "</ul><br/>"
				
				monformulaire = Ajout_utilisateur()
				contenu += "<form name=\"main\" action=\"\" method=\"post\"> \
					<fieldset><legend>Ajouter un utilisateur</legend>" \
					+ monformulaire.render() + \
					"</fieldset></form>"
			
			return template_html("Administration", contenu)
			
		else : raise web.seeother("/connexion.html")
	
	
	def POST(self) :
		monlogin_web = Login_web()
		if monlogin_web.validates() :
			session.utilisateur = monlogin_web["utilisateur"].value
		
		monajout_utilisateur = Ajout_utilisateur()
		if monajout_utilisateur.validates() :
			unutilisateur = Utilisateur()
			unutilisateur.id = monajout_utilisateur["utilisateur"].value
			unutilisateur.courriel = monajout_utilisateur["courriel"].value
			caracteres = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMN\
				OPQRSTUVWXYZ1234567890&#{}()|-_^@=$%<>!:;.,?"
			mot_de_passe_clair = ''.join(random.sample(caracteres, 8))
			DEBOGUE().trace("mot_de_passe_clair", mot_de_passe_clair)
			unutilisateur.mot_de_passe = hashlib.sha256(mot_de_passe_clair).hexdigest()
			unutilisateur.date = time.time()
			message = "{0.id}\n{0.mot_de_passe}\n{0.courriel}\n{0.date}".format(unutilisateur)
			unutilisateur.signature = main.maconf.master.cle_privee.sign(message, None)[0]
			main.maconf.utilisateurs[unutilisateur.id] = unutilisateur
			main.maconf.utilisateurs[unutilisateur.id].save()
		
		mamodif_utilisateur = Modif_utilisateur()
		if mamodif_utilisateur.validates() :
			main.maconf.utilisateurs[session.utilisateur].mot_de_passe \
				= hashlib.sha256(monlogin_web["mot_de_passe"].value).hexdigest()
			main.maconf.utilisateurs[session.utilisateur].save()
		
		return index.GET(self)


class index2(object) :
	"""
	La page de redirection vers la paire master (quand on est pas le master)
	"""
	def GET(self) :
		raise web.seeother("http://{0}:{1}/".format(main.maconf.master.ip, \
			main.maconf.master.port + 1))


class debogue(object) :
	"""
	La page outil pour deboguer le mécanisme p2p
	"""
	def GET(self) :
		if session.utilisateur == "root" :
			monformulaire = Login_bdd()
			contenu = "<form name=\"main\" \
				action=\"http://{0.ip}:{0.port}/bdd.xml\" \
				method=\"post\"> \
				<fieldset><legend>bdd.xml</legend>".format(main.maconf.moi) \
				+ monformulaire.render() + \
				"</fieldset></form><br/>"
			
			monformulaire = Login_p2p()
			contenu += "<form name=\"main\" \
				action=\"http://{0.ip}:{0.port}/commande.xml\" \
				method=\"post\"> \
				<fieldset><legend>commande.xml</legend>".format(main.maconf.moi) \
				+ monformulaire.render() + \
				"</fieldset></form><br/>"
			
			monformulaire = Login_p2p()
			contenu += "<form name=\"main\" \
				action=\"http://{0.ip}:{0.port}/mise_a_jour\" \
				method=\"post\"> \
				<fieldset><legend>La mise à jour</legend>".format(main.maconf.moi) \
				+ monformulaire.render() + \
				"</fieldset></form><br/>"
			
			monformulaire = Validation()
			contenu += "<form name=\"main\" \
				action=\"http://{0.ip}:{0.port}/commande.xml\" \
				method=\"post\"> \
				<fieldset><legend>commande.xml</legend>".format(main.maconf.moi) \
				+ monformulaire.render() + \
				"</fieldset></form>"
			
			return template_html("[Debogue]", contenu)
			
		else : raise web.seeother("/connexion.html")


class cloud(object) :
	"""
	La page de l'espace de stockage
	"""
	def GET(self, chemin) :
		if session.utilisateur != "anonyme" :
			monformulaire = Upload()
			
			# /!\ code en html, le convertir pour le kit graphique en XHTML
			
			contenu = """<table>
				<tr><th><img/></th>
				<th><a href="?C=N;O=D">Nom</a></th>
				<th><a href="?C=M;O=A">Dernière modification</a></th>
				<th><a href="?C=S;O=A">Poids</a></th>
				<th><a href="?C=D;O=A">Description</a></th></tr>
				<tr><th colspan="5"><hr></th></tr>"""
			
			for unfichier in main.maconf.fichiers.values() :
				contenu += """<tr><td valign=\"top\"><img/></td>
					<td><a href=\"{0.nom}\">{0.nom}</a></td>
					<td align=\"right\">{0.date}</td>
					<td align=\"right\">{0.poids}</td><td></td></tr>
					""".format(unfichier)
			
			contenu += "<tr><th colspan=\"5\"><hr></th></tr></table>"
			
			contenu += "<form name=\"main\" \
				action=\"http://{0}:{1}/cloud/\" \
				method=\"post\"> \
				<fieldset><legend>Téléverser un fichier</legend>".format(main.maconf.moi.ip, main.maconf.moi.port + 1) \
				+ monformulaire.render() + \
				"</fieldset></form>"
			
			return template_html("Stockage", contenu)
			
		else : raise web.seeother("/connexion.html")
	
	
	def POST(self) :
		fichier_post = Upload()
		if fichier_post.validates() :
			unfichier = Fichier()
			donnees = fichier_post["fichier"].value
		
		return cloud.GET(self)


class connexion(object) :
	"""
	La page de connexion
	"""
	def GET(self) :
		if session.utilisateur == "anonyme" :
			monlogin_web = Login_web()
			
			contenu = """
			<!DOCTYPE html>
			<html>
				<head>
					<meta charset="utf-8" />
					<title>Connexion</title>
				</head>
				<body>
					<div align=\"center\">
					<form name=\"main\" action=\"/\" method=\"post\">"""
			
			contenu	+= monlogin_web.render()
			
			contenu += """	</form>
					</div>
				</body>
			</html>"""
			
			return contenu
			
		else : raise web.seeother('/')


class deconnexion(object) :
	"""
	La page de déconnexion
	"""
	def GET(self) :
		if session.utilisateur != "anonyme" : session.kill()
		
		raise web.seeother("/connexion.html")


class style(object) :
	"""
	La page d'accueil
	"""
	def GET(self) :
		if session.utilisateur != "anonyme" :
			web.header("Content-Type", "text/css")
			return """
			body, html {{
				background: url({0[fond.jpg]});
				margin:0;
				padding:0;
				font-family:Verdana, Arial, Helvetica, sans-serif;
				text-align:center;
				color:#FFF;
				background-attachment: fixed;
				font-size:11px;
			}}
			#conteneur {{
				margin:0 auto;
				width: 800px;
			}}	
			#header {{
				height:65px; 
				background:url({0[header.png]}) no-repeat top;
				margin:0 auto;
				width:800px;
			}}   
			#contenu {{
				background:url({0[fond_contenu.png]});
				width:800px;
			}}  
			#left {{
				width: 240px;
				float: left;
				padding:0 0 0 5px;
			}}	 	 
			#right {{
				margin:0 0 0 245px;
				width:540px;
				text-align:left;
			}} 
			#pied {{
				background:url({0[pied.png]}) no-repeat;
				height:25px;
				width:800px;
			}} 
			ul {{
				width:238px;
				margin:0;
				padding:0;
				list-style:none;
				text-align:left;
			}}
			ul li a {{
				width:208px;
				display: block ;
				color:#fff;
				outline:none;
				padding:0 0 0 30px;
				margin:0;
				text-decoration: none;
				outline:none;
				font-weight:bold;
			}}	
			ul li a:hover {{
				color: #3295d5;
				text-decoration: none;
			}}	
			span {{
				color:#3295d5;
				text-decoration:none;
				outline:none;
				font-size: 14px;
				font-weight:bold;
			}}	
			img, p, h1, h2, h3, h4, h5, h6, Span, object, table, td, tr {{
				border:0;
				margin:0;
				padding:0;
			}}   
			a {{
				color: #fff;
				text-decoration:underline;
				outline:none;
			}} 	
			a:hover	{{
				color: #fff;
				text-decoration: none;
			}}	
			#clear {{
				clear: both;
				visibility: hidden; 
			}}	
			.copyright {{
				padding:0;
				margin :0;
				color:#fff;
				font-size:10px;
			}}   
			.copyright a {{
				color:#fff;
				text-decoration: none;
				outline:none;
				font-size:10px;
			}}
			.copyright a:hover {{
				color: #fff;
				text-decoration:underline;
			}} 
			.menu_haut {{
				padding:14px 0 0 0;
				height:21px; 
				background:url({0[menu_haut.png]});
				margin:0 auto;
				width:238px;
			}}
			.menu_fond {{
				background:url({0[menu_fond.png]});
				margin:0 auto;
				width:238px;
			}}
			.menu_bas {{
				height:20px; 
				background:url({0[menu_bas.png]}) no-repeat;
				margin:0 auto;
				width:238px;
			}}
			.cadre_haut {{
				height:15px;
				background:url({0[cadre_haut.png]});
				margin:0 auto 0 auto;width:530px
			}}
			.cadre_fond {{
				background:url({0[cadre_fond.png]});
				margin:0 auto;
				width:500px;
				padding:0 10px 0 20px;
			}}
			.cadre_bas {{
				height:15px; 
				background:url({0[cadre_bas.png]});
				margin:0 auto;
				width:530px;
			}}
			""".format(images)
			
		else : raise web.seeother("/connexion.html")
	
	
def interface() :
	"""
	Fonction attrapant les connexions entrantes
	"""
	try :
		urllib2.urlopen("http://{0.ip}:{0.port}/".format(main.maconf.master), None, 3)
		urls = ("/(.*)",		"index2")
		DEBOGUE().trace("ICI", "/(.*) => index2")
		
	except urllib2.URLError :
		urls = ("/",			"index",
			"/cloud/(.*)",		"cloud",
			"/connexion.html",	"connexion",
			"/deconnexion.html",	"deconnexion",
			"/style.css",		"style",
			
			"/debogue.html",	"debogue")
		
		__builtin__.images = {
			"accueil.png" : "http://img100.imageshack.us/img100/742/accueilo.png",
			#"attention.png" : "http://img822.imageshack.us/img822/4697/attentionm.png",
			#"bouton.png" : "http://img7.imageshack.us/img7/7826/boutondb.png",
			"cadre_bas.png" : "http://img52.imageshack.us/img52/2263/cadrebas.png",
			"cadre_fond.png" : "http://img152.imageshack.us/img152/938/cadrefond.png",
			"cadre_haut.png" : "http://img571.imageshack.us/img571/5918/cadrehautw.png",
			"connexion.png" : "http://img594.imageshack.us/img594/7555/connexionin.png",
			#"contact.png" : "http://img4.imageshack.us/img4/2312/contactpw.png",
			#"design54_01.jpg" : "http://img521.imageshack.us/img521/3290/design5401.jpg",
			"donation.png" : "http://img94.imageshack.us/img94/4300/donationdp.png",
			"download.png" : "http://img507.imageshack.us/img507/9645/downloadcr.png",
			#"envoyer.png" : "http://img690.imageshack.us/img690/8444/envoyer.png",
			"favicon.png" : "http://img831.imageshack.us/img831/7123/faviconurg.png",
			"fond.jpg" : "http://img856.imageshack.us/img856/1264/fondse.jpg",
			"fond_contenu.png" : "http://img840.imageshack.us/img840/4785/fondcontenu.png",
			#"forum.png" : "http://img823.imageshack.us/img823/3816/forumrx.png",
			"header.png" : "http://img823.imageshack.us/img823/5193/headercobb.png",
			"info.png" : "http://img855.imageshack.us/img855/9170/infoyn.png",
			#"inscription.png" : "http://img138.imageshack.us/img138/8840/inscriptionu.png",
			"menu_bas.png" : "http://img339.imageshack.us/img339/7096/menubas.png",
			"menu_fond.png" : "http://img171.imageshack.us/img171/5243/menufond.png",
			"menu_haut.png" : "http://img6.imageshack.us/img6/3766/menuhaut.png",
			#"news.png" : "http://img822.imageshack.us/img822/8745/newsma.png",
			"pied.png" : "http://img577.imageshack.us/img577/2953/pied.png",
			#"plus.png" : "http://img528.imageshack.us/img528/6708/plusrk.png",
			#"rechercher.png" : "http://img138.imageshack.us/img138/9152/rechercherj.png",
			#"tchat.png" : "http://img849.imageshack.us/img849/5558/tchat.png",
			"titre.png" : "http://img208.imageshack.us/img208/1166/titret.png"}
		
		DEBOGUE().trace("ICI", "/... => index, etc")
	
	sys.stdout.write("Interface d'administration à l'adresse ")
	sys.argv = sys.argv[0], str(main.maconf.moi.port + 1)
	monapplication = web.application(urls, globals())  # locals()) ???
	store = web.session.DBStore(web.database(dbn = "sqlite", db = main.maconf.mabdd), 'session')
	__builtin__.session = web.session.Session(monapplication, store, initializer={'utilisateur' : "anonyme"})
	try : monapplication.run()
	except socket.error : pass

