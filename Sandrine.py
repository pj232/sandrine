import os
import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk

# --- GESTION DE LA BASE DE DONNÉES ---
DB_NAME = "historique_genie_civil.db"


def initialiser_bdd():
    """Crée la table dans la base de données si elle n'existe pas."""


conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS calculs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom_projet TEXT,
    b REAL, h REAL, d REAL,
    fck REAL, fyk REAL, med REAL,
    as_calcul REAL, statut TEXT
    )
    """
)
conn.commit()
conn.close()


def sauvegarder_calcul(nom, b, h, d, fck, fyk, med, as_calc, statut):
    """Enregistre un calcul dans le fichier SQLite."""


conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()
cursor.execute(
    """
    INSERT INTO calculs (nom_projet, b, h, d, fck, fyk, med, as_calcul, statut)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
    (nom, b, h, d, fck, fyk, med, as_calc, statut),
)
conn.commit()
conn.close()


def recuperer_historique():
    """Récupère tous les calculs enregistrés."""


conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()
cursor.execute(
    "SELECT id, nom_projet, med, as_calcul, statut FROM calculs ORDER BY id DESC"
)
lignes = cursor.fetchall()
conn.close()
return lignes


def supprimer_calcul(id_calcul):
    """Supprime un enregistrement de l'historique."""


conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()
cursor.execute("DELETE FROM calculs WHERE id = ?", (id_calcul,))
conn.commit()
conn.close()


# --- LOGIQUE DE CALCUL GÉNIE CIVIL ---
def calculer_et_enregistrer():
    try:
        nom_projet = entry_nom.get().strip()


if not nom_projet:
    messagebox.showwarning(
        "Saisie incomplète", "Veuillez donner un nom au projet/poutre."
    )
return

b = float(entry_b.get()) / 100  # cm -> m
h = float(entry_h.get()) / 100  # cm -> m
d = float(entry_d.get()) / 100  # cm -> m
fck = float(entry_fck.get())
fyk = float(entry_fyk.get())
med_knm = float(entry_Med.get())
Med = med_knm / 1000  # kNm -> MNm

# Paramètres Eurocode 2
fcd = fck / 1.5
fyd = fyk / 1.15
mu = Med / (b * (d ** 2) * fcd)
mu_lu = 0.372

if mu > mu_lu:
    messagebox.showwarning(
        "Pivot C",
        f"μ = {mu:.3f} > {mu_lu:.3f}. Section d'acier comprimé requise.",
    )
return

alpha = 1.25 * (1 - (1 - 2 * mu) ** 0.5)
z = d * (1 - 0.4 * alpha)
as_cm2 = (Med / (z * fyd)) * 10000

# Section minimale de non-fragilité
fctm = 0.3 * (fck ** (2 / 3))
as_min = max(0.26 * (fctm / fyk) * b * d * 10000, 0.0013 * b * d * 10000)

as_final = max(as_cm2, as_min)
statut = (
    "Section Min Appliquée"
    if as_min > as_cm2
    else "Calcul Standard Réussi"
)

# Affichage
lbl_as_val.config(text=f"{as_final:.2f} cm²")

# Sauvegarde persistante (fichier .db sur le disque dur)
sauvegarder_calcul(
    nom_projet,
    float(entry_b.get()),
    float(entry_h.get()),
    float(entry_d.get()),
    fck,
    fyk,
    med_knm,
    as_final,
    statut,
)

# Actualiser la vue de l'historique
mettre_a_jour_tableau()
messagebox.showinfo(
    "Succès", "Calcul effectué et enregistré dans la base de données !"
)

except ValueError:
messagebox.showerror(
    "Erreur", "Veuillez entrer des valeurs numériques valides."
)


def mettre_a_jour_tableau():
    """Actualise la liste graphique de l'historique."""


for row in tree.get_children():
    tree.delete(row)
for ligne in recuperer_historique():
# format: id, nom, med, as_calcul, statut
tree.insert(
    "",
    tk.END,
    values=(ligne[0], ligne[1], f"{ligne[2]} kNm", f"{ligne[3]:.2f} cm²", ligne[4]),
)


def action_supprimer():
    selected_item = tree.selection()


if not selected_item:
    messagebox.showwarning(
        "Sélection", "Veuillez sélectionner un calcul à supprimer."
    )
return
item_values = tree.item(selected_item, "values")
id_calcul = item_values[0]
supprimer_calcul(id_calcul)
mettre_a_jour_tableau()

# --- INTERFACE GRAPHIQUE (Tkinter) ---
initialiser_bdd()
root = tk.Tk()
root.title("Dimensionnement Béton Armé avec Base de Données")
root.geometry("850x500")

# Séparation de la fenêtre en deux zones (Gauche: Saisie, Droite: Historique)
paned = ttk.Panedwindow(root, orient=tk.HORIZONTAL)
paned.pack(fill=tk.BOTH, expand=True, padding=10)

frame_saisie = ttk.LabelFrame(paned, text=" Nouveau Calcul ", padding=10)
frame_historique = ttk.LabelFrame(paned, text=" Historique Sauvegardé ", padding=10)
paned.add(frame_saisie, weight=1)
paned.add(frame_historique, weight=2)

# --- Zone Saisie ---
ttk.Label(frame_saisie, text="Nom de la poutre / projet :").grid(
    row=0, column=0, sticky=tk.W, pady=2
)
entry_nom = ttk.Entry(frame_saisie, width=20)
entry_nom.insert(0, "Poutre P1")
entry_nom.grid(row=0, column=1, pady=2)

champs = [
    ("Largeur b [cm] :", "20", "entry_b", 1),
    ("Hauteur h [cm] :", "50", "entry_h", 2),
    ("Hauteur utile d [cm] :", "45", "entry_d", 3),
    ("Béton fck [MPa] :", "25", "entry_fck", 4),
    ("Acier fyk [MPa] :", "500", "entry_fyk", 5),
    ("Moment Med [kNm] :", "150", "entry_Med", 6),
]

for texte, defaut, var_name, r in champs:
    ttk.Label(frame_saisie, text=texte).grid(row=r, column=0, sticky=tk.W, pady=2)
ent = ttk.Entry(frame_saisie, width=20)
ent.insert(0, defaut)
ent.grid(row=r, column=1, pady=2)
globals()[var_name] = ent

btn_calc = ttk.Button(
    frame_saisie, text="Calculer & Sauvegarder", command=calculer_et_enregistrer
)
btn_calc.grid(row=7, column=0, columnspan=2, pady=15)

ttk.Label(
    frame_saisie, text="Section d'acier requise :", font=("Helvetica", 10, "bold")
).grid(row=8, column=0, sticky=tk.W)
lbl_as_val = ttk.Label(
    frame_saisie, text="- cm²", font=("Helvetica", 12, "bold"), foreground="blue"
)
lbl_as_val.grid(row=8, column=1, sticky=tk.E)

# --- Zone Historique (Tableau) ---
colonnes = ("id", "nom", "moment", "acier", "statut")
tree = ttk.Treeview(frame_historique, columns=colonnes, show="headings", height=15)
tree.heading("id", text="ID")
tree.heading("nom", text="Nom Projet")
tree.heading("moment", text="Moment Med")
tree.heading("acier", text="Section As")
tree.heading("statut", text="Note")

tree.column("id", width=40, anchor=tk.CENTER)
tree.column("nom", width=120)
tree.column("moment", width=90, anchor=tk.CENTER)
tree.column("acier", width=90, anchor=tk.CENTER)
tree.column("statut", width=140)
tree.pack(fill=tk.BOTH, expand=True, side=tk.TOP)

btn_suppr = ttk.Button(
    frame_historique, text="Supprimer l'élément sélectionné", command=action_supprimer
)
btn_suppr.pack(pady=10, side=tk.BOTTOM)

# Charger les données existantes à l'allumage
mettre_a_jour_tableau()

root.mainloop()