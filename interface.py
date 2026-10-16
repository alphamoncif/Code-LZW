"""
Interface graphique Tkinter pour le projet n°2 — Compression LZW.
Cette interface permet de visualiser interactivement :
  1. La trace d'exécution pas à pas
  2. Les codes compressés générés
  3. Le dictionnaire final (initiales vs générées avec couleur)
  4. Le décodage et la vérification de l'intégrité de la chaîne

Elle utilise exclusivement les fonctions métier définies dans `lzw.py`.
"""

import sys

# Gestion pédagogique de l'absence potentielle de Tkinter
try:
    import tkinter as tk
    from tkinter import ttk
    from tkinter import messagebox
except ImportError:
    print(
        "Erreur : La bibliothèque Tkinter n'est pas installée sur votre système Python.\n"
        "- Sur Linux (Ubuntu/Debian) : exécutez 'sudo apt install python3-tk'\n"
        "- Sur Fedora/RHEL : exécutez 'sudo dnf install python3-tkinter'\n"
        "- Sur Windows/macOS : réinstallez Python en cochant la case 'tcl/tk and IDLE'."
    )
    sys.exit(1)

from lzw import valider_entree, compresser_lzw, decompresser_lzw
from decompression_lzw import parser_chaine_codes, decompresser_lzw_detaille


class ApplicationLZW:
    """Classe gérant la fenêtre et les interactions de l'interface graphique LZW."""

    def __init__(self, racine: tk.Tk):
        self.racine = racine
        self.racine.title("Projet n°2 — Visualisation interactive LZW")
        self.racine.geometry("1020x800")
        self.racine.minsize(850, 650)

        # Style TTK
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self._configurer_styles()

        # Construction des éléments de l'interface
        self._construire_interface()

    def _configurer_styles(self):
        """Configure les polices et couleurs des composants ttk."""
        self.style.configure("TLabel", font=("Helvetica", 10))
        self.style.configure("TButton", font=("Helvetica", 10, "bold"))
        self.style.configure("Treeview.Heading", font=("Helvetica", 9, "bold"))
        self.style.configure("Treeview", font=("Consolas", 9), rowheight=22)

    def _construire_interface(self):
        """Met en place la disposition globale des panneaux et widgets."""
        # --- 1. En-tête et Titre ---
        cadre_titre = ttk.Frame(self.racine, padding="10 10 10 5")
        cadre_titre.pack(fill=tk.X)

        label_titre = ttk.Label(
            cadre_titre,
            text="Compression & Décompression LZW (Alphabet {a, b, c})",
            font=("Helvetica", 14, "bold"),
            foreground="#1e3a8a",
        )
        label_titre.pack(anchor=tk.W)

        label_sous_titre = ttk.Label(
            cadre_titre,
            text="Convention initiale : 0 → 'a' | 1 → 'b' | 2 → 'c'. Nouveaux codes consécutifs dès 3.",
            font=("Helvetica", 9, "italic"),
            foreground="#4b5563",
        )
        label_sous_titre.pack(anchor=tk.W, pady=(2, 0))

        # --- 2. Zone de Saisie et Boutons d'Action ---
        cadre_saisie = ttk.LabelFrame(self.racine, text=" Entrée utilisateur ", padding=10)
        cadre_saisie.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(cadre_saisie, text="Chaîne à compresser :", font=("Helvetica", 10, "bold")).pack(
            side=tk.LEFT, padx=(0, 8)
        )

        self.var_entree = tk.StringVar(value="ababc")
        self.champ_entree = ttk.Entry(cadre_saisie, textvariable=self.var_entree, font=("Consolas", 11), width=35)
        self.champ_entree.pack(side=tk.LEFT, padx=(0, 10))
        self.champ_entree.bind("<Return>", lambda event: self.action_compresser())

        self.btn_compresser = ttk.Button(
            cadre_saisie, text="▶ Compresser", command=self.action_compresser
        )
        self.btn_compresser.pack(side=tk.LEFT, padx=(0, 6))

        self.btn_effacer = ttk.Button(
            cadre_saisie, text="✕ Effacer", command=self.action_effacer
        )
        self.btn_effacer.pack(side=tk.LEFT)

        # Label d'erreur (rouge, masqué par défaut)
        self.label_erreur = tk.Label(
            cadre_saisie,
            text="",
            font=("Helvetica", 9, "bold"),
            fg="#dc2626",
            wraplength=400,
            justify=tk.LEFT,
        )
        self.label_erreur.pack(side=tk.LEFT, padx=(15, 0))

        # --- 3. Zone Centrale (Onglets ou Grille d'Affichage) ---
        panneau_onglets = ttk.Notebook(self.racine)
        panneau_onglets.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Onglet 1 : Trace de compression
        onglet_trace = ttk.Frame(panneau_onglets, padding=5)
        panneau_onglets.add(onglet_trace, text="1. Trace de compression")
        self._creer_vue_trace(onglet_trace)

        # Onglet 2 : Synthèse complète (Codes, Dictionnaire final & Décodage)
        onglet_synthese = ttk.Frame(panneau_onglets, padding=5)
        panneau_onglets.add(onglet_synthese, text="2. Dictionnaire & Décodage")
        self._creer_vue_synthese(onglet_synthese)

        # Onglet 3 : Décompression autonome de codes
        onglet_decomp = ttk.Frame(panneau_onglets, padding=5)
        panneau_onglets.add(onglet_decomp, text="3. Décompression autonome")
        self._creer_vue_decompression(onglet_decomp)
        self.derniers_codes = []

        # --- 4. Barre d'état en bas ---
        self.cadre_statut = ttk.Frame(self.racine, padding="8 4 8 8")
        self.cadre_statut.pack(fill=tk.X)

        self.label_statut = tk.Label(
            self.cadre_statut,
            text="Prêt. Saisissez une chaîne et cliquez sur 'Compresser'.",
            font=("Helvetica", 9),
            anchor=tk.W,
        )
        self.label_statut.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _creer_vue_trace(self, parent):
        """Crée le tableau Treeview affichant la trace détaillée étape par étape."""
        colonnes = ("k", "w", "wk", "dans_dico", "code_emis", "nouvel_ajout", "action")
        self.arbre_trace = ttk.Treeview(parent, columns=colonnes, show="headings", selectmode="browse")

        self.arbre_trace.heading("k", text="Car. k")
        self.arbre_trace.heading("w", text="w")
        self.arbre_trace.heading("wk", text="wk")
        self.arbre_trace.heading("dans_dico", text="Dans dico ?")
        self.arbre_trace.heading("code_emis", text="Code émis")
        self.arbre_trace.heading("nouvel_ajout", text="Ajout dictionnaire")
        self.arbre_trace.heading("action", text="Action effectuée")

        self.arbre_trace.column("k", width=70, anchor=tk.CENTER)
        self.arbre_trace.column("w", width=80, anchor=tk.CENTER)
        self.arbre_trace.column("wk", width=80, anchor=tk.CENTER)
        self.arbre_trace.column("dans_dico", width=95, anchor=tk.CENTER)
        self.arbre_trace.column("code_emis", width=95, anchor=tk.CENTER)
        self.arbre_trace.column("nouvel_ajout", width=140, anchor=tk.CENTER)
        self.arbre_trace.column("action", width=340, anchor=tk.W)

        scroll_y = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.arbre_trace.yview)
        scroll_x = ttk.Scrollbar(parent, orient=tk.HORIZONTAL, command=self.arbre_trace.xview)
        self.arbre_trace.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.arbre_trace.pack(fill=tk.BOTH, expand=True)

    def _creer_vue_synthese(self, parent):
        """Crée l'affichage des codes, du dictionnaire final et du décodage."""
        # Cadre supérieur : Codes compressés
        cadre_codes = ttk.LabelFrame(parent, text=" Codes compressés émis ", padding=8)
        cadre_codes.pack(fill=tk.X, pady=(0, 6))

        self.var_codes_texte = tk.StringVar(value="Aucune compression effectuée.")
        label_codes = ttk.Label(
            cadre_codes,
            textvariable=self.var_codes_texte,
            font=("Consolas", 11, "bold"),
            foreground="#1e40af",
        )
        label_codes.pack(anchor=tk.W)

        # Séparation en deux colonnes : Dictionnaire final (gauche) & Décodage (droite)
        cadre_deux_colonnes = ttk.Frame(parent)
        cadre_deux_colonnes.pack(fill=tk.BOTH, expand=True)

        # --- Colonne Gauche : Dictionnaire Final ---
        colonne_gauche = ttk.LabelFrame(cadre_deux_colonnes, text=" Dictionnaire final généré ", padding=6)
        colonne_gauche.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 4))

        self.arbre_dico = ttk.Treeview(
            colonne_gauche, columns=("code", "chaine", "type"), show="headings", selectmode="browse"
        )
        self.arbre_dico.heading("code", text="Code")
        self.arbre_dico.heading("chaine", text="Sous-chaîne")
        self.arbre_dico.heading("type", text="Type")

        self.arbre_dico.column("code", width=65, anchor=tk.CENTER)
        self.arbre_dico.column("chaine", width=110, anchor=tk.CENTER)
        self.arbre_dico.column("type", width=100, anchor=tk.CENTER)

        # Configuration des tags de couleurs pour différencier Initiale vs Générée
        self.arbre_dico.tag_configure("initiale", background="#f0fdf4")  # Vert très pâle
        self.arbre_dico.tag_configure("generee", background="#eff6ff")   # Bleu très pâle

        scroll_dico = ttk.Scrollbar(colonne_gauche, orient=tk.VERTICAL, command=self.arbre_dico.yview)
        self.arbre_dico.configure(yscrollcommand=scroll_dico.set)
        scroll_dico.pack(side=tk.RIGHT, fill=tk.Y)
        self.arbre_dico.pack(fill=tk.BOTH, expand=True)

        # --- Colonne Droite : Décodage et Vérification ---
        colonne_droite = ttk.LabelFrame(cadre_deux_colonnes, text=" Décodage LZW (Remplacement des codes) ", padding=6)
        colonne_droite.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(4, 0))

        self.arbre_decomp = ttk.Treeview(
            colonne_droite, columns=("pos", "code", "sub"), show="headings", selectmode="browse"
        )
        self.arbre_decomp.heading("pos", text="Pos.")
        self.arbre_decomp.heading("code", text="Code reçu")
        self.arbre_decomp.heading("sub", text="Sous-chaîne associée")

        self.arbre_decomp.column("pos", width=55, anchor=tk.CENTER)
        self.arbre_decomp.column("code", width=85, anchor=tk.CENTER)
        self.arbre_decomp.column("sub", width=150, anchor=tk.CENTER)

        scroll_decomp = ttk.Scrollbar(colonne_droite, orient=tk.VERTICAL, command=self.arbre_decomp.yview)
        self.arbre_decomp.configure(yscrollcommand=scroll_decomp.set)
        scroll_decomp.pack(side=tk.RIGHT, fill=tk.Y)
        self.arbre_decomp.pack(fill=tk.BOTH, expand=True)

        # Zone inférieure de vérification
        cadre_verif = ttk.Frame(colonne_droite, padding=4)
        cadre_verif.pack(fill=tk.X, pady=(6, 0))

        self.var_texte_reconstruit = tk.StringVar(value="Chaîne reconstruite : -")
        ttk.Label(cadre_verif, textvariable=self.var_texte_reconstruit, font=("Consolas", 10)).pack(anchor=tk.W)

        self.label_verif = tk.Label(
            cadre_verif, text="En attente de calcul", font=("Helvetica", 10, "bold"), fg="#6b7280"
        )
        self.label_verif.pack(anchor=tk.W, pady=(2, 0))

    def action_compresser(self):
        """Déclenche la validation, la compression et la décompression via lzw.py."""
        # Réinitialisation du message d'erreur
        self.label_erreur.config(text="")

        chaine_brute = self.var_entree.get().strip()

        # 1. Validation de l'entrée via la fonction métier de lzw.py
        try:
            chaine_validee = valider_entree(chaine_brute)
        except ValueError as err:
            self.label_erreur.config(text=f"⚠️ {err}")
            self.label_statut.config(text="Erreur lors de la validation de la saisie.", fg="#dc2626")
            return

        # 2. Compression via lzw.compresser_lzw
        codes, dico_comp, trace = compresser_lzw(chaine_validee)

        # 3. Décompression via lzw.decompresser_lzw
        texte_reconstruit, correspondances, dico_decomp = decompresser_lzw(codes)

        # --- 4. Remplissage des données dans l'interface ---
        # A. Trace
        for row in self.arbre_trace.get_children():
            self.arbre_trace.delete(row)

        for etape in trace:
            k_str = etape.k if etape.k != "(fin)" else "(fin)"
            w_str = f"'{etape.w}'" if etape.w else "''"
            wk_str = f"'{etape.wk}'" if etape.wk != "-" else "-"
            dans_dico_str = "Oui" if etape.dans_dico else "Non"
            code_str = str(etape.code_emis) if etape.code_emis is not None else "-"
            ajout_str = (
                f"{etape.nouvelle_entree[0]} : '{etape.nouvelle_entree[1]}'"
                if etape.nouvelle_entree
                else "-"
            )

            self.arbre_trace.insert(
                "",
                tk.END,
                values=(k_str, w_str, wk_str, dans_dico_str, code_str, ajout_str, etape.action),
            )

        # B. Codes compressés
        self.var_codes_texte.set(f"Codes compressés : {codes}")

        # C. Dictionnaire final (avec mise en couleur)
        for row in self.arbre_dico.get_children():
            self.arbre_dico.delete(row)

        entrees_triees = sorted(dico_comp.items(), key=lambda item: item[1])
        for sous_chaine, code in entrees_triees:
            if code < 3:
                tag = "initiale"
                type_str = "Initiale"
            else:
                tag = "generee"
                type_str = "Générée"

            self.arbre_dico.insert(
                "", tk.END, values=(code, repr(sous_chaine), type_str), tags=(tag,)
            )

        # D. Décodage
        for row in self.arbre_decomp.get_children():
            self.arbre_decomp.delete(row)

        for idx, (code, sub) in enumerate(correspondances, start=1):
            self.arbre_decomp.insert("", tk.END, values=(idx, code, repr(sub)))

        self.var_texte_reconstruit.set(f"Chaîne reconstruite : '{texte_reconstruit}'")

        # E. Vérification finale
        if texte_reconstruit == chaine_validee:
            self.label_verif.config(
                text="[OK] Verification reussie (reconstruction exacte sans perte)",
                fg="#16a34a",
            )
            self.label_statut.config(
                text=f"Succès : {len(chaine_validee)} caractères compressés en {len(codes)} codes.",
                fg="#15803d",
            )
        else:
            self.label_verif.config(
                text="[ECHEC] Echec de la verification (chaines differentes)",
                fg="#dc2626",
            )
            self.label_statut.config(
                text="Erreur critique : divergence lors de la décompression !",
                fg="#dc2626",
            )

        self.derniers_codes = codes

    def _creer_vue_decompression(self, parent):
        """Crée l'onglet interactif pour la décompression autonome d'une suite de codes."""
        # Barre de saisie des codes
        cadre_saisie = ttk.LabelFrame(parent, text=" Saisie de la séquence de codes compressés ", padding=8)
        cadre_saisie.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(cadre_saisie, text="Codes (ex: 0, 3, 1, 0, 2, 5) :", font=("Helvetica", 10, "bold")).pack(
            side=tk.LEFT, padx=(0, 8)
        )

        self.var_codes_entree = tk.StringVar(value="0, 3, 1, 0, 2, 5")
        self.champ_codes = ttk.Entry(
            cadre_saisie, textvariable=self.var_codes_entree, font=("Consolas", 11), width=30
        )
        self.champ_codes.pack(side=tk.LEFT, padx=(0, 8))
        self.champ_codes.bind("<Return>", lambda event: self.action_decompresser_autonome())

        self.btn_decompresser = ttk.Button(
            cadre_saisie, text="▶ Décompresser", command=self.action_decompresser_autonome
        )
        self.btn_decompresser.pack(side=tk.LEFT, padx=(0, 6))

        self.btn_recuperer = ttk.Button(
            cadre_saisie, text="📋 Codes de compression", command=self.action_recuperer_codes
        )
        self.btn_recuperer.pack(side=tk.LEFT, padx=(0, 6))

        self.btn_effacer_decomp = ttk.Button(
            cadre_saisie, text="✕ Effacer", command=self.action_effacer_decomp
        )
        self.btn_effacer_decomp.pack(side=tk.LEFT)

        # Message d'erreur
        self.label_erreur_decomp = tk.Label(
            cadre_saisie,
            text="",
            font=("Helvetica", 9, "bold"),
            fg="#dc2626",
            wraplength=350,
            justify=tk.LEFT,
        )
        self.label_erreur_decomp.pack(side=tk.LEFT, padx=(12, 0))

        # Cadre central à 2 colonnes : Dictionnaire généré (gauche) & Trace de décompression (droite)
        cadre_colonnes = ttk.Frame(parent)
        cadre_colonnes.pack(fill=tk.BOTH, expand=True)

        # Colonne gauche : Dictionnaire généré
        cadre_dico = ttk.LabelFrame(cadre_colonnes, text=" Dictionnaire généré au fil de l'eau ", padding=6)
        cadre_dico.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 4))

        self.arbre_dico_decomp = ttk.Treeview(
            cadre_dico, columns=("code", "chaine", "type"), show="headings", selectmode="browse"
        )
        self.arbre_dico_decomp.heading("code", text="Code")
        self.arbre_dico_decomp.heading("chaine", text="Sous-chaîne")
        self.arbre_dico_decomp.heading("type", text="Type")

        self.arbre_dico_decomp.column("code", width=60, anchor=tk.CENTER)
        self.arbre_dico_decomp.column("chaine", width=110, anchor=tk.CENTER)
        self.arbre_dico_decomp.column("type", width=110, anchor=tk.CENTER)

        self.arbre_dico_decomp.tag_configure("initiale", background="#f0fdf4")
        self.arbre_dico_decomp.tag_configure("generee", background="#eff6ff")

        scroll_dico = ttk.Scrollbar(cadre_dico, orient=tk.VERTICAL, command=self.arbre_dico_decomp.yview)
        self.arbre_dico_decomp.configure(yscrollcommand=scroll_dico.set)
        scroll_dico.pack(side=tk.RIGHT, fill=tk.Y)
        self.arbre_dico_decomp.pack(fill=tk.BOTH, expand=True)

        # Colonne droite : Trace détaillée de décompression
        cadre_trace = ttk.LabelFrame(cadre_colonnes, text=" Trace pédagogique de la décompression ", padding=6)
        cadre_trace.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(4, 0))

        colonnes_trace = ("etape", "code", "dans_dico", "sub", "ajout", "action")
        self.arbre_trace_decomp = ttk.Treeview(
            cadre_trace, columns=colonnes_trace, show="headings", selectmode="browse"
        )
        self.arbre_trace_decomp.heading("etape", text="Étape")
        self.arbre_trace_decomp.heading("code", text="Code")
        self.arbre_trace_decomp.heading("dans_dico", text="Dans dico ?")
        self.arbre_trace_decomp.heading("sub", text="Sous-chaîne")
        self.arbre_trace_decomp.heading("ajout", text="Ajout dico")
        self.arbre_trace_decomp.heading("action", text="Action effectuée")

        self.arbre_trace_decomp.column("etape", width=55, anchor=tk.CENTER)
        self.arbre_trace_decomp.column("code", width=55, anchor=tk.CENTER)
        self.arbre_trace_decomp.column("dans_dico", width=95, anchor=tk.CENTER)
        self.arbre_trace_decomp.column("sub", width=95, anchor=tk.CENTER)
        self.arbre_trace_decomp.column("ajout", width=120, anchor=tk.CENTER)
        self.arbre_trace_decomp.column("action", width=250, anchor=tk.W)

        scroll_trace_y = ttk.Scrollbar(cadre_trace, orient=tk.VERTICAL, command=self.arbre_trace_decomp.yview)
        scroll_trace_x = ttk.Scrollbar(cadre_trace, orient=tk.HORIZONTAL, command=self.arbre_trace_decomp.xview)
        self.arbre_trace_decomp.configure(yscrollcommand=scroll_trace_y.set, xscrollcommand=scroll_trace_x.set)
        scroll_trace_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_trace_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.arbre_trace_decomp.pack(fill=tk.BOTH, expand=True)

        # Zone inférieure de résultat
        cadre_resultat = ttk.Frame(parent, padding=6)
        cadre_resultat.pack(fill=tk.X, pady=(6, 0))

        self.var_resultat_decomp = tk.StringVar(value="Chaîne décompressée : -")
        ttk.Label(
            cadre_resultat, textvariable=self.var_resultat_decomp, font=("Consolas", 11, "bold"), foreground="#1e3a8a"
        ).pack(anchor=tk.W)

        self.label_statut_decomp = tk.Label(
            cadre_resultat, text="En attente de décompression.", font=("Helvetica", 9, "italic"), fg="#6b7280"
        )
        self.label_statut_decomp.pack(anchor=tk.W, pady=(2, 0))

    def action_decompresser_autonome(self):
        """Déclenche le parsing et la décompression de la séquence de codes saisie."""
        self.label_erreur_decomp.config(text="")
        saisie = self.var_codes_entree.get().strip()

        try:
            codes = parser_chaine_codes(saisie)
        except ValueError as err:
            self.label_erreur_decomp.config(text=f"⚠️ {err}")
            self.label_statut.config(text="Erreur dans la saisie des codes.", fg="#dc2626")
            return

        try:
            chaine, correspondances, dico, trace = decompresser_lzw_detaille(codes)
        except ValueError as err:
            self.label_erreur_decomp.config(text=f"⚠️ {err}")
            self.label_statut.config(text="Erreur lors de la décompression.", fg="#dc2626")
            return

        # 1. Remplissage du dictionnaire généré
        for row in self.arbre_dico_decomp.get_children():
            self.arbre_dico_decomp.delete(row)

        for code in sorted(dico.keys()):
            if code < 3:
                tag = "initiale"
                type_str = "Initiale"
            else:
                tag = "generee"
                type_str = "Générée"
            self.arbre_dico_decomp.insert(
                "", tk.END, values=(code, repr(dico[code]), type_str), tags=(tag,)
            )

        # 2. Remplissage de la trace
        for row in self.arbre_trace_decomp.get_children():
            self.arbre_trace_decomp.delete(row)

        for etape in trace:
            code_str = str(etape.code)
            dans_dico_str = "Spécial" if etape.cas_special else ("Oui" if etape.dans_dico else "Non")
            sub_str = repr(etape.sous_chaine_emise)
            ajout_str = (
                f"{etape.ajout_dictionnaire[0]} : {repr(etape.ajout_dictionnaire[1])}"
                if etape.ajout_dictionnaire
                else "-"
            )
            self.arbre_trace_decomp.insert(
                "",
                tk.END,
                values=(etape.etape, code_str, dans_dico_str, sub_str, ajout_str, etape.action),
            )

        # 3. Résultat
        self.var_resultat_decomp.set(f"Chaîne décompressée : '{chaine}'")
        self.label_statut_decomp.config(
            text=f"Succès : {len(codes)} codes décompressés en {len(chaine)} caractères. Dictionnaire : {len(dico)} entrées.",
            fg="#15803d",
        )
        self.label_statut.config(
            text=f"Décompression réussie : chaîne '{chaine}' ({len(chaine)} car.)", fg="#15803d"
        )

    def action_recuperer_codes(self):
        """Récupère les codes générés par la compression dans l'onglet 1/2."""
        if hasattr(self, "derniers_codes") and self.derniers_codes:
            chaine_codes = ", ".join(str(c) for c in self.derniers_codes)
            self.var_codes_entree.set(chaine_codes)
            self.label_erreur_decomp.config(text="")
            self.label_statut_decomp.config(text="Codes récupérés depuis la dernière compression.", fg="#1e3a8a")
        else:
            self.label_erreur_decomp.config(text="Aucune compression préalable effectuée.")

    def action_effacer_decomp(self):
        """Efface les champs et tableaux de la décompression autonome."""
        self.var_codes_entree.set("")
        self.label_erreur_decomp.config(text="")
        self.var_resultat_decomp.set("Chaîne décompressée : -")
        self.label_statut_decomp.config(text="Champs réinitialisés.", fg="#6b7280")
        for row in self.arbre_dico_decomp.get_children():
            self.arbre_dico_decomp.delete(row)
        for row in self.arbre_trace_decomp.get_children():
            self.arbre_trace_decomp.delete(row)
        self.champ_codes.focus_set()

    def action_effacer(self):
        """Réinitialise les champs de saisie et les tableaux."""
        self.var_entree.set("")
        self.label_erreur.config(text="")
        self.var_codes_texte.set("Aucune compression effectuée.")
        self.var_texte_reconstruit.set("Chaîne reconstruite : -")
        self.label_verif.config(text="En attente de calcul", fg="#6b7280")
        self.label_statut.config(text="Champs réinitialisés.", fg="#374151")

        for row in self.arbre_trace.get_children():
            self.arbre_trace.delete(row)
        for row in self.arbre_dico.get_children():
            self.arbre_dico.delete(row)
        for row in self.arbre_decomp.get_children():
            self.arbre_decomp.delete(row)

        self.champ_entree.focus_set()


def lancer_interface():
    """Fonction principale pour instancier et exécuter l'application Tkinter."""
    fenetre = tk.Tk()
    ApplicationLZW(fenetre)
    fenetre.mainloop()


if __name__ == "__main__":
    lancer_interface()
