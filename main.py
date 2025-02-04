# -*- coding: utf-8 -*-
#--------------------------------------------------------------------------------------------------#
#---------------------------------------------[Import]---------------------------------------------#
#--------------------------------------------------------------------------------------------------#

from PIL import ImageTk                  # Utilisé pour manipuler des images dans l'interface graphique
import PIL.Image                         # Utilisé pour manipuler des images dans l'interface graphique
import os                                # Permet d'effectuer des opérations de système de fichiers
from os import listdir                   # Permet de lister le contenu d'un dossier
import shutil                            # Permet d'effectuer des opérations de système de fichiers
import pandas as pd                      # Utilisé pour la manipulation de données et l'analyse
from tkinter import *                    # Utilisé pour créer l'interface graphique de l'application
from tkinter import filedialog, ttk, messagebox      # Permet de sélectionner des fichiers/dossiers via une boîte de dialogue
import sqlite3                           # Permet d'interagir avec une base de données SQLite
from io import BytesIO                   # Permet de travailler avec des octets en mémoire
from reportlab.pdfgen import canvas      # Utilisé pour générer des fichiers PDF
import threading                         # Utilisé pour exécuter des tâches en arrière-plan
import csv                               # Permet de lire les fichier csv
import requests                          # Permet d'éffectuer des requête
from pokemontcgsdk import Card, Set      # Permet davoir accès au donner des cartes pokemon

#-----------------------------------------------------------------------------------------------------#
#---------------------------------------------[Variables]---------------------------------------------#
#-----------------------------------------------------------------------------------------------------#
blocks_csv = pd.read_csv("ne_pas_toucher/blocks.csv") # Chargement du fichier CSV des blocs
File_Picture = "ne_pas_toucher/Images/" # Chemin relatif vers le dossier d'images

connection = sqlite3.connect("ne_pas_toucher/coll_api.db")
cursor = connection.cursor()
rows = cursor.execute("SELECT * FROM Collection").fetchall()

col_list, listeidcards, listeidcol = {}, {}, {}
block_list, download_list, lot_file = [], [], []
vstop, preview = False, False
lot_window, L_5, classeur_window = None, None, None

for row in rows:
	block_list.append((row[0], row[1], row[4]))
	col_list[row[1]] = (row[2], row[3])
	listeidcards[row[1]] = row[5]
	if listeidcards[row[1]] in [None, ""]:
		if col_list[row[1]][1] != "None":
			liste_id_card2 = Card.where(q=f"set.id:{col_list[row[1]][0]}", orderBy="number")
			liste_id_card2 += Card.where(q=f"set.id:{col_list[row[1]][1]}", orderBy="number")
		else:
			liste_id_card2 = Card.where(q=f"set.id:{col_list[row[1]][0]}", orderBy="number")
		liste_id_card = []
		for i in liste_id_card2:
			liste_id_card.append(i.id)
		listeidcards[row[1]] = " ".join(liste_id_card)

		sql = "UPDATE Collection SET idcards = ? WHERE name = ?"
		value = (listeidcards[row[1]], row[1])
		cursor.execute(sql, value)
		connection.commit()
	if row[6] == None or row[6] == "":
		listeidcol[row[1]] = []
	else:
		listeidcol[row[1]] = row[6].split()
connection.commit()
connection.close()

#----------------------------------------------------------------------------------------------------#
#---------------------------------------------[Fonction]---------------------------------------------#
#----------------------------------------------------------------------------------------------------#

def on_closing():
	connection = sqlite3.connect("ne_pas_toucher/coll_api.db")
	cursor = connection.cursor()
	sql = "UPDATE Collection SET idcol = ? WHERE name = ?"
	for cle,valeur in listeidcol.items():
		valeur = " ".join(valeur)
		value = (valeur, cle)
		cursor.execute(sql, value)
	connection.commit()
	connection.close()

	window.destroy()

def delete_window(element):
    for widget in element.winfo_children():
        widget.grid_remove()

def center(element):
	eval_ = element.nametowidget('.').eval
	eval_('tk::PlaceWindow %s center' % element)

def create_directory_if_not_exists(directory_path):
    if not os.path.isdir(directory_path):
        os.makedir(directory_path)

def test_supr_window(element):
	try:
		element.destroy()
	except:
		pass

def frame_create(fenetre, y, x, fond=None, px=None, py=None, hlbg=None, hltn=None, h=None, w=None, rel=None, bw=None):
	frame = Frame(fenetre, bg=fond, highlightbackground=hlbg, highlightthickness=hltn, height=h, width=w, relief=rel, borderwidth=bw)
	frame.grid(row=y, column=x, padx=px, pady=py)
	return frame

def button_create(fenetre, y, x, txt=None, im=None, cmd=None, px=None, py=None, fond=None, pol=None, h=None, w=None):
	button = Button(fenetre, text=txt, image=im, bg=fond, font=pol, height=h, width=w, command=cmd)
	button.grid(row=y, column=x, padx=px, pady=py)
	return button

def Cpreview(event):
	global preview
	preview = not preview

# Définition de la fonction pour gérer la sélection d'un élément
def sel(event):
	if not action_lever:
	    # Utilisation des variables globales pour stocker l'état précédent et le texte de l'élément sélectionné
		global old_bg, text, repertoire, B_lot

	    # Parcours tous les boutons de la liste et leur donne une couleur de fond par défaut
		for button in bc_list:
			button.config(bg="#D4D4D4") 

	    # Définit la couleur de fond du bouton sélectionné sur une couleur différente pour le mettre en évidence
		event.widget.config(bg="#7E7E7E")
		old_bg = event.widget["bg"]
		text = event.widget["text"]
		col_name["text"] = text

		if action == "d_one":
			B_lot = button_create(F_g, 4, 0, txt="Card Choice", pol=("Courier", 10))
			B_lot.bind("<Button-1>", lot)
		else:
			B_lot = button_create(F_g, 4, 0, im=image_list["valider"], cmd=download_start, px=10, py=10)

	    # Stocke le répertoire de téléchargement correspondant à l'élément sélectionné
		repertoire = f"Download/{text}/"

		test_supr_window(lot_window)

def charge_img(idcarte, colname):
	info = idcarte.split("-")
	url = f"https://images.pokemontcg.io/{info[0]}/{info[1]}.png"
	response = requests.get(url)
	im = PIL.Image.open(BytesIO(response.content))
	im = im.resize((93, 132))
	if idcarte not in listeidcol[colname]:
		im = im.convert("L")
	photo = ImageTk.PhotoImage(im)
	return photo

def add_col(event, card_id, pos, col, butt):
	if not action_lever:
		global photocardliste
		if card_id != "":
			if card_id in listeidcol[col]:
				listeidcol[col].remove(card_id)
			else:
				listeidcol[col].append(card_id)
			photocardliste[pos]=charge_img(card_id, col)
			butt.config(image=photocardliste[pos])

def add_colM(event, card_id, pos, col, butt):
	if not action_lever:
		global photocardliste
		for i in range(len(card_id)):
			if card_id[i] != "":
				if card_id[i] in listeidcol[col]:
					listeidcol[col].remove(card_id[i])
				else:
					listeidcol[col].append(card_id[i])
				photocardliste[pos[i]]=charge_img(card_id[i], col)
				butt[i].config(image=photocardliste[pos[i]])

def classeur(event, p, col):
	if not action_lever:
		global classeur_window, photocardliste, text_clas, buttonliste, cardid, photo, nb
		test_supr_window(classeur_window)
		test_supr_window(lot_window)
		classeur_window = Toplevel(window)
		classeur_window.resizable(False, False)
		F_info = frame_create(classeur_window, 0, 0, px=10, py=10)
		F_page = frame_create(classeur_window, 1, 0, px=10, py=10)

		F_p1 = frame_create(F_page, 0, 1, px=10, py=10, hlbg="black", hltn=1)
		F_p2 = frame_create(F_page, 0, 2, px=10, py=10, hlbg="black", hltn=1)

		text_clas = col
		buttonliste = []
		cardid = listeidcards[text_clas].split()
		nb=0

		Label(F_info, text=text_clas).grid(row=0, column=0)
		dimi = col_list[text_clas]
		photo = PhotoImage(file= f"ne_pas_toucher/Images/logo/{dimi[0]}.png")
		Label(F_info, image=photo).grid(row=0, column=1)

		def tache2(nb,i):
			global photocardliste
			photocardliste[nb] = image_list["vide"] if i<9 or i-9>len(cardid)-1 else charge_img(cardid[i-9], text_clas)
			try:
				buttonliste[nb].config(image=photocardliste[nb])
			except:
				pass
		tache02 = threading.Thread(target=tache2)
		photocardliste = ["" for i in range(18)]
		lbk = [7, 8, 9, 4, 5, 6, 1, 2, 3]
		multi_add1, multi_add2 = [], []
		multi_but1, multi_but2 = [], []
		multi_pos1, multi_pos2 = [], []
		for i in range(p*9, (p+2)*9, 1):
			cardidtest = "" if i<9 or i-9>len(cardid)-1 else cardid[i-9]
			clas = button_create(F_p1 if i < (p+1)*9 else F_p2, i//3 if i < (p+1)*9 else (i-9)//3, i%3, im=image_list["vide"])
			clas.bind("<Button-1>", lambda event, cardid=cardidtest, pos=nb, col=text_clas, butt=clas:add_col(event, cardid, pos, col, butt))
			classeur_window.bind(lbk[nb] if nb<9 else f"<Control-KeyPress-{lbk[nb-9]}>", lambda event, cardid=cardidtest, pos=nb, col=text_clas, butt=clas:add_col(event, cardid, pos, col, butt))
			buttonliste.append(clas)
			tache02 = threading.Thread(target=tache2, args=(nb,i))
			tache02.start()
			if nb<9:
				multi_add1.append(cardidtest)
				multi_but1.append(clas)
				multi_pos1.append(nb)
			else:
				multi_add2.append(cardidtest)
				multi_but2.append(clas)
				multi_pos2.append(nb)
			nb += 1
		classeur_window.bind("<KeyPress-+>", lambda event, cardid=multi_add1, pos=multi_pos1, col=text_clas, butt=multi_but1:add_colM(event, cardid, pos, col, butt))
		classeur_window.bind("<Control-KeyPress-+>", lambda event, cardid=multi_add2, pos=multi_pos2, col=text_clas, butt=multi_but2:add_colM(event, cardid, pos, col, butt))
		if p-2 < 0 and (p+2)*9 <= len(cardid):
			button_create(F_page, 0, 3, im=image_list["FD"], cmd=lambda text=text_clas, page=p+2:classeur(text, page, text_clas))
			classeur_window.bind("<Right>", lambda text=text_clas, page=p+2:classeur(text, page, text_clas))
			button_create(F_page, 0, 0, im=image_list["FR"])
		elif (p+1)*9 > len(cardid) and p-2 >= 0:
			button_create(F_page, 0, 0, im=image_list["FG"], cmd=lambda text=text_clas, page=p-2:classeur(text, page, text_clas))
			classeur_window.bind("<Left>", lambda text=text_clas, page=p-2:classeur(text, page, text_clas))
			button_create(F_page, 0, 3, im=image_list["FR"])
		else:
			button_create(F_page, 0, 0, im=image_list["FG"], cmd=lambda text=text_clas, page=p-2:classeur(text, page, text_clas))
			classeur_window.bind("<Left>", lambda text=text_clas, page=p-2:classeur(text, page, text_clas))
			button_create(F_page, 0, 3, im=image_list["FD"], cmd=lambda text=text_clas, page=p+2:classeur(text, page, text_clas))
			classeur_window.bind("<Right>", lambda text=text_clas, page=p+2:classeur(text, page, text_clas))
		center(classeur_window)

# Définition de la fonction pour gérer le passage de la souris sur un widget
def on_enter(event):
    global old_bg
    old_bg = event.widget["bg"]
    event.widget.config(bg="#B5B5B5")

# Définition de la fonction pour gérer le départ de la souris d'un widget
def on_leave(event):
    event.widget.config(bg=old_bg)

# Définition de la fonction pour sélectionner une collection
def selectB(event=None):
	if not action_lever:
		# Récupère l'élément sélectionné dans la liste Li_1
		global photo_list, bc_list
		photo_list = []
		bc_list = []
		selB = block_choice.get()
	    
		# Supprime tous les widgets du F_4
		delete_window(F_4)

	    # Crée un tableau de chaque collection de ce bloc
		blocktemp = [col for col in block_list if col[0] == selB]

		for i, col in enumerate(blocktemp, start=1):
			dimi = col_list[col[1]][0]
			if not os.path.isfile(f"ne_pas_toucher/Images/logo/{dimi}.png"):
				url = Set.find(dimi).images.symbol
				response = requests.get(url)
				im = PIL.Image.open(BytesIO(response.content))
				im = im.resize((25, 25))
				im.save(f"ne_pas_toucher/Images/logo/{dimi}.png", "png")

			photo = PhotoImage(file= f"ne_pas_toucher/Images/logo/{dimi}.png")
			photo_list.append(photo)
			bc = button_create(F_4, (i-1)//4, (i-1)%4, im=photo, txt=col[1], w=25, h=25, fond="#D4D4D4")
			bc.bind("<Button-1>", sel)
			bc.bind("<Button-3>", lambda event, page=0, col=col[1]:classeur(event, page, col))
			bc.bind("<Enter>", on_enter)
			bc.bind("<Leave>", on_leave)
			bc_list.append(bc)

def stop(event):
	global vstop
	vstop = True

def actionf():
	global action_lever
	action_lever = False

def sel_lot(event, card_id):
	if not action_lever:
		global old_bg, lot_file, photo
		t1, t2 = card_id in lot_file, card_id in listeidcol[text]
		if t1:
			bg_color = "#44BE33" if t2 else "#D4D4D4"
			lot_file.remove(card_id)
		else:
			bg_color = "#225F19" if t2 else "#7E7E7E"
			lot_file.append(card_id)

		if view_check.get() == 1:
			if lot_ac == "D":
				info = card_id.split("-")
				url = f"https://images.pokemontcg.io/{info[0]}/{info[1]}.png"
				response = requests.get(url)
				im = PIL.Image.open(BytesIO(response.content))
				im = im.resize((185, 262))
				photo = ImageTk.PhotoImage(im)

			elif lot_ac == "R":
				photo = PhotoImage(file = f"Download/{file}/{card_id}.png")

			L_vislot["image"] = photo
			center(lot_window)
		event.widget.config(bg=bg_color)
		old_bg = event.widget["bg"]

def select_all_not_card():
	if not action_lever:
		global lot_file
		lot_file = []
		for ele in F_lot.winfo_children():
			if ele["bg"] == "#225F19":
				ele["bg"] = "#44BE33"
			elif ele["bg"] == "#D4D4D4":
				ele["bg"] = "#7E7E7E"
		templisteid = listeidcards[text]
		templisteid = templisteid.split()
		for tempidcard in templisteid:
			if tempidcard not in listeidcol[text]:
				lot_file.append(tempidcard)

def lot(event):
	if not action_lever:
		global lot_window, lot_file, L_vislot, lot_ac, view_check, F_lot
		lot_ac = "D"
		test_supr_window(lot_window)
		test_supr_window(classeur_window)

		lot_window = Toplevel(window)
		lot_window.resizable(False, False)
		lot_file = []
		F_lot = frame_create(lot_window, 0, 0, px=5, py=5, rel="sunken", bw=5)
		F_vv = frame_create(lot_window, 1, 0, px=5, py=5)

		liste_id_card = listeidcards[text].split()

		for i, idcard in enumerate(liste_id_card):
			bg_color = "#44BE33" if idcard in listeidcol[text] else "#D4D4D4"
			BuNum = button_create(F_lot, i//16, i%16, txt=idcard.split("-")[1], h=2, w=4, fond=bg_color)
			BuNum.bind("<Button-1>", lambda event, cardid=idcard:sel_lot(event, cardid))
			BuNum.bind("<Enter>", on_enter)
			BuNum.bind("<Leave>", on_leave)

		B_valider = button_create(F_vv, 0, 0, im=image_list["valider"], px=10, py=10, cmd=download_start)

		view_check = IntVar()
		B_view = Checkbutton(F_vv, text="Card preview", variable=view_check)
		B_view.grid(row=0, column=1, padx=10, pady=10)
		B_view.bind("<Button-1>", Cpreview)
		B_view.select() if preview == True else B_view.deselect()

		B_sel = button_create(F_vv, 1, 1, txt="select", cmd=select_all_not_card)

		L_vislot = Label(lot_window, image="")
		L_vislot.grid(row=0, column=1)
		center(lot_window)

def download_card(card_l, repertoire_old):
	L_5.config(text="En cours ...")
	if not os.path.isfile(repertoire_old + card_l + ".png"):
		try:
			url = Card.find(card_l).images.small
			response = requests.get(url)
			im = PIL.Image.open(BytesIO(response.content))
			im = im.resize((185, 262))
			im.save(repertoire_old + card_l + ".png", "png")
		except:
			shutil.copy("ne_pas_toucher/Images/dos.png", repertoire_old + card_l + ".png")

def download_start():
	if not action_lever:
		global L_5, tache01, vstop, lot_file, lot_old
		vstop = False
		lot_old = lot_file
		lot_file = []
		B_lot.grid_remove()

		test_supr_window(L_5)
		test_supr_window(lot_window)

		L_5 = Label(F_g, text="En cours ...", font=("Courier", 10))
		L_5.grid(row=5, column=0)
		B_8 = button_create(F_g, 6, 0, txt="stop", pol=("Courier", 10))
		B_8.bind("<Button-1>", stop)
		def tache():
			global lot_old, action_lever
			action_lever = True
			dimi = col_list[text][0]
			repertoire_old = repertoire
			if not os.path.exists(repertoire_old) and lot_old != []:
				os.mkdir(repertoire_old)

			if action == "d_all":
				listeID = Card.where(q=f"set.id:{dimi}")
				if col_list[text][1] != "None":
					dimi2 = col_list[text][1]
					listeID += Card.where(q=f"set.id:{dimi2}")
				lot_old = [card.id for card in listeID]
			for text_card in lot_old:
				if vstop:
					break
				download_card(text_card, repertoire_old)

			L_5.config(text="Terminer")
			B_8.destroy()
			B_lot.grid()
			actionf()
		tache01 = threading.Thread(target=tache)
		tache01.start()

# Définition de la fonction pour suprimer une colection ou une à plusieurs cartes
def remove_start(event):
	if not action_lever:
		global lot_window, lot_file, file, lot_ac, L_vislot, view_check
		# Désactive le bouton pour éviter les clics multiples
		event.widget.config(state='disabled')
	    
		# Récupère le nom du fichier sélectionné
		file = Li_2.get(Li_2.curselection()[0])

	    # Vérifie si l'action est de supprimer tous les fichiers ou seulement un fichier
		if action == "r_all":
			# Supprime le répertoire et tous ses fichiers
			shutil.rmtree(f"Download/{file}")
			remove("r_all")
		else:
			# Demande à l'utilisateur de sélectionner un ou plusieurs fichiers à supprimer
			lot_ac = "R"
			test_supr_window(lot_window)

			lot_window = Toplevel(window)
			lot_window.resizable(False, False)
			lot_file = []
			F_lot = frame_create(lot_window, 0, 0, rel="sunken", bw=5, px=5, py=5)
			F_vv = frame_create(lot_window, 1, 0, px=5, py=5)
			for i, name_file in enumerate(os.listdir(f"Download/{file}")):

				nom_fichier, extansion = os.path.splitext(name_file)

				BuNum = button_create(F_lot, i//16, i%16, txt=nom_fichier.split("-")[1], h=2, w=4, fond="#D4D4D4")
				BuNum.bind("<Button-1>", lambda event, cardid=nom_fichier:sel_lot(event, cardid))
				BuNum.bind("<Enter>", on_enter)
				BuNum.bind("<Leave>", on_leave)

			B_valider = button_create(F_vv, 0, 0, im=image_list["valider"], px=10, py=10)
			B_valider.bind("<Button-1>", remove_lot)
			view_check = IntVar()
			B_view = Checkbutton(F_vv, text="Card preview", variable=view_check)
			B_view.grid(row=0, column=1, padx=10, pady=10)
			B_view.bind("<Button-1>", Cpreview)
			B_view.select() if preview == True else B_view.deselect()
			L_vislot = Label(lot_window, image="")
			L_vislot.grid(row=0, column=1)
			center(lot_window)

def remove_lot(self):
	if not action_lever:
		global lot_file
		for fichier in lot_file:
			os.remove(f"Download/{file}/{fichier}.png")
		# Si le répertoire est vide, le supprime également
		if len(os.listdir(f"Download/{file}")) == 0:
			shutil.rmtree(f"Download/{file}")
		lot_file = []
		lot_window.destroy()
		remove("r_one")

def compile_start(event):
	if not action_lever:
		file = Li_3.get(Li_3.curselection()[0])

		card_list = []
		x = 0
		y = 524
	    
		file_liste = listdir(f"Download/{file}")

		c = canvas.Canvas("Download/" + file +".pdf")
		i = 0
		while i <= (len(file_liste)-1):
			for y in range(524, -262, -262):
				for x in range(0, 555, 185):
					if i <= (len(file_liste)-1):
						repertoire = "Download/" + file + "/" + str(file_liste[i])
						c.drawImage(repertoire, x, y)
						i += 1

			c.showPage()
		c.save()

		shutil.rmtree("Download/" + file)
		pdf("pdfd")

def pdfsupr_start(event):
	if not action_lever:
		file = Li_3.get(Li_3.curselection()[0])
		os.remove(f"Download/{file}")
		pdf("pdfr")

def pdf(action):
	if not action_lever:
		global Li_3
		delete_window(F_g)

		label_text = "Remove\nPdf" if action == "pdfr" else "Compile in\nPdf"
		L_8 = Label(F_g, text=label_text, font=("Courier", 20))
		L_8.grid(row=0, column=0, padx=10, pady=10)

		files = listdir("Download/")
		if action == "pdfr":
			pdf_list = [file_name for file_name in files if file_name[-3:] == "pdf"]
		else:
			pdf_list = [file_name for file_name in files if file_name[-3:] != "pdf"]

		Li_3 = Listbox(F_g, borderwidth=4)
		Li_3.grid(row=1, column=0, padx=15, pady=15)

		if not pdf_list:
			L_7 = Label(F_g, text="No File")
			L_7.grid(row=1, column=0, padx=10, pady=10)
		else:
			pair = True
			for i, file_name in enumerate(pdf_list):
				Li_3.insert(str(i), file_name)
				Li_3.itemconfig(i, {"bg": "#C6C6C6" if pair else "#FFFFFF"})
				pair = not pair
			Li_3.select_set(0)

			B_6 = button_create(F_g, 2, 0, im=image_list["valider"], px=10, py=10)
			if action == "pdfd":
				B_6.bind("<Button-1>", compile_start)
			else:
				B_6.bind("<Button-1>", pdfsupr_start)

#----------------------------------------------------------------------------------------------------#
#----------------------------------------[Fonction graphique]----------------------------------------#
#----------------------------------------------------------------------------------------------------#

def download(ac):
	if not action_lever:
		global F_4, action, F_g, block_choice, text, col_name
		action = ac
		text = ""
		delete_window(F_g)
		act = "One" if ac == "d_one" else "All"

		Label(F_g, text=f"Download\n{act}", font=("Courier", 20)).grid(row=0, column=0, padx=10, pady=10)
		F_5 = frame_create(F_g, 3, 0)

		block = [blocks_csv.loc[i, "Blocks"] for i in range(len(blocks_csv.axes[0]))]
		block_choice = StringVar()
		C_1 = ttk.Combobox(F_g, textvariable=block_choice, values=block)
		C_1.grid(row=1, column=0, padx=10, pady=10)
		C_1.bind('<<ComboboxSelected>>', selectB)
		C_1.current(0)

		F_3 = frame_create(F_g, 2, 0, px=15, py=15)

		F_4 = frame_create(F_3, 0, 0)
		col_name = Label(F_3, text="")
		col_name.grid(row=1, column=0)
		selectB()

def remove(ac):
	if not action_lever:
		global Li_2, action
		action = ac
		delete_window(F_g)
		act = "One" if ac == "r_one" else "All"

		Label(F_g, text=f"Remove\n{act}", font=("Courier", 20)).grid(row=0, column=0, padx=10, pady=10)
		Li_2 = Listbox(F_g, borderwidth=4)
		Li_2.grid(row=1, column=0, padx=15, pady=15)

		if listdir("Download/") == []:
			Label(F_g, text="No File").grid(row=1, column=0)
		else:
			pair = True
			nb_file = 0
			for file in listdir("Download/"):
				if file[-3:] != "pdf":
					nb_file += 1
					Li_2.insert(str(nb_file-1), file)
					color = "#C6C6C6" if pair else "#FFFFFF" #| Alterne les couleur dans la liste en gris et blanc
					Li_2.itemconfig(nb_file-1, {"bg": color})  #|
					pair = not pair
			Li_2.select_set(0)
			if nb_file == 0:
				Label(F_g, text="No File").grid(row=1, column=0)
			else:
				B_6 = button_create(F_g, 2, 0, im=image_list["valider"], px=10, py=10)
				B_6 = Button(F_g, image=image_list["valider"])
				B_6.grid(row=2, column=0, padx=10, pady=10)
				B_6.bind("<Button-1>", remove_start)

def menu():
	delete_window(window)
	global F_g, F_verif, L_verif, Li_verif, action_lever
	action_lever = False
	F_menu = frame_create(window, 0, 0, "#C1C1C1")
	F_All = frame_create(window, 1, 0)
	F_option = frame_create(F_All, 1, 0)

	F_dow_rem = frame_create(F_option, 0, 0)
	F_dow = frame_create(F_dow_rem, 0, 0, "#C1C1C1", 15, 15)
	F_rem = frame_create(F_dow_rem, 0, 1, "#C1C1C1", 15, 15)

	L_dow = Label(F_dow, text="Download", font=("Courier", 20)).grid(row=0, column=0, padx=10, pady=10)
	B_dowA = button_create(F_dow, 1, 0, im=image_list["All"], txt="", cmd=lambda action="d_all":download(action), px=10, py=10)
	B_dowO = button_create(F_dow, 2, 0, im=image_list["One"], txt="", cmd=lambda action="d_one":download(action), px=10, py=10)

	L_rem = Label(F_rem, text="Remove", font=("Courier", 20)).grid(row=0, column=0, padx=10, pady=10)
	B_remA = button_create(F_rem, 1, 0, im=image_list["All"], txt="", cmd=lambda action="r_all":remove(action), px=10, py=10)
	B_remA = button_create(F_rem, 2, 0, im=image_list["One"], txt="", cmd=lambda action="r_one":remove(action), px=10, py=10)

	F_pdf = frame_create(F_option, 1, 0)
	B_pdfd = button_create(F_pdf, 0, 0, im=image_list["Pdfd"], fond="#C1C1C1", cmd=lambda action="pdfd":pdf(action), px=10, py=10)
	B_pdfr = button_create(F_pdf, 0, 1, im=image_list["Pdfr"], fond="#C1C1C1", cmd=lambda action="pdfr":pdf(action), px=10, py=10)

	F_ac = frame_create(F_All, 1, 1, px=15, py=15, hlbg="black", hltn=1, h=550, w=250)
	F_ac.grid_propagate(False)
	F_ac.grid_rowconfigure(1, weight=0)
	F_ac.grid_columnconfigure(1, weight=1)
	F_g = frame_create(F_ac, 1, 1, px=15, py=15)

#-----------------------------------------------------------------------------------------------------#
#-----------------------------------------[Création Interface]----------------------------------------#
#-----------------------------------------------------------------------------------------------------#
if os.path.isdir("ne_pas_toucher"):
	if os.path.isdir("ne_pas_toucher/images"):

		create_directory_if_not_exists("Download")
		create_directory_if_not_exists("ne_pas_toucher/Images/logo")

		window = Tk() #| Création de l'interface

		window.title("Card Downloader") #| Paramètre de l'interface
		window.resizable(False, False)  #|
		window.protocol("WM_DELETE_WINDOW", on_closing)

		image_list = {}
		name_image = ("All", "One", "Pdfd", "Pdfr", "valider", "close", "vide", "FG", "FD", "FR")
		for i in name_image:
			image_list[i] = PhotoImage(file = File_Picture + f"{i}.png")

		menu()

		center(window)

		window.mainloop()