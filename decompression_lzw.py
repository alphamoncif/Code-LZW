"""
Projet — Décompression LZW (Lempel-Ziv-Welch)
Alphabet restreint : {'a', 'b', 'c'}

Convention initiale du dictionnaire :
  0 -> 'a'
  1 -> 'b'
  2 -> 'c'
Les nouveaux codes sont attribués successivement à partir de 3.

Ce script :
  1. Lit en entrée une séquence de codes générée par la compression LZW.
  2. Décompresse la séquence en restituant la chaîne de caractères correspondante.
  3. Reconstruit et visualise le dictionnaire généré au fil de l'eau.
  4. Fournit une trace pédagogique détaillée pas-à-pas (avec gestion du cas spécial cScSc).
"""

import sys
import re
from typing import List, Dict, Tuple, NamedTuple, Optional

ALPHABET_VALIDE = {'a', 'b', 'c'}


class EtapeDecompression(NamedTuple):
    """Représente une étape élémentaire de la trace de décompression."""
    etape: int
    code: int
    dans_dico: bool
    cas_special: bool
    sous_chaine_emise: str
    ajout_dictionnaire: Optional[Tuple[int, str]]
    chaine_cumulee: str
    action: str


def initialiser_dictionnaire_decompression() -> Dict[int, str]:
    """
    Initialise le dictionnaire de base pour la décompression avec l'alphabet {'a', 'b', 'c'}.
    Mapping : code -> sous-chaîne.
    """
    return {0: 'a', 1: 'b', 2: 'c'}


def parser_chaine_codes(chaine_brute: str) -> List[int]:
    """
    Convertit une chaîne représentant une séquence de codes en une liste d'entiers.
    Supporte de multiples formats de saisie :
      - Liste Python : "[0, 3, 1, 0, 2, 5]" ou "Codes compressés : [0, 3, 1, 0, 2, 5]"
      - Séparé par virgules : "0, 3, 1, 0, 2, 5" ou "0,3,1,0,2,5"
      - Séparé par espaces : "0 3 1 0 2 5"
      - Séparé par points-virgules : "0; 3; 1; 0; 2; 5"

    Lève ValueError avec un message explicite en cas d'entrée vide ou invalide.
    """
    if not chaine_brute or not chaine_brute.strip():
        raise ValueError("Erreur de saisie : la chaîne de codes en entrée ne peut pas être vide.")

    texte = chaine_brute.strip()

    # Si l'utilisateur colle une ligne contenant des crochets [ ... ], on extrait l'intérieur
    match_crochets = re.search(r"\[(.*?)\]", texte)
    if match_crochets:
        texte = match_crochets.group(1).strip()
    else:
        # Enlever d'éventuelles parenthèses
        if texte.startswith("(") and texte.endswith(")"):
            texte = texte[1:-1].strip()

    if not texte:
        raise ValueError("Erreur de saisie : aucun code trouvé dans la séquence fournie.")

    # Découpage par virgules, points-virgules ou espaces
    morceaux = re.split(r"[,;\s]+", texte)
    codes: List[int] = []
    erreurs: List[str] = []

    for piece in morceaux:
        piece = piece.strip()
        if not piece:
            continue
        try:
            val = int(piece)
            if val < 0:
                erreurs.append(f"code négatif interdit ({val})")
            else:
                codes.append(val)
        except ValueError:
            erreurs.append(f"élément non entier '{piece}'")

    if erreurs:
        raise ValueError(
            f"Erreur de syntaxe dans les codes : {', '.join(erreurs)}. "
            f"Veuillez fournir uniquement des entiers positifs ou nuls."
        )

    if not codes:
        raise ValueError("Erreur de saisie : aucun code numérique valide n'a été extrait.")

    return codes


def decompresser_lzw_detaille(
    codes: List[int],
) -> Tuple[str, List[Tuple[int, str]], Dict[int, str], List[EtapeDecompression]]:
    """
    Décompresse une séquence de codes LZW et construit une trace pédagogique détaillée.

    Algorithme :
      1. Initialiser le dictionnaire avec 0->'a', 1->'b', 2->'c'. Prochain code = 3.
      2. Lire le premier code. Il doit appartenir au dictionnaire initial.
         Émettre sa sous-chaîne associée w = dico[premier_code].
      3. Pour chaque code suivant :
         a. Si code est dans le dictionnaire :
            entree = dico[code]
         b. Sinon si code == prochain_code (Cas spécial cScSc) :
            entree = w + w[0]
         c. Sinon (code inconnu non consécutif) :
            Erreur (code invalide).
         d. Émettre entree.
         e. Ajouter au dictionnaire : dico[prochain_code] = w + entree[0].
         f. prochain_code += 1.
         g. w = entree.

    Retourne :
      - texte_reconstruit : chaîne finale décodée
      - correspondances : liste des tuples (code, sous-chaîne associée)
      - dictionnaire_final : dictionnaire code -> sous-chaîne reconstitué
      - trace : liste d'EtapeDecompression pour analyse et affichage pédagogique
    """
    if not codes:
        raise ValueError("Erreur : la liste de codes à décompresser est vide.")

    dico = initialiser_dictionnaire_decompression()
    prochain_code = 3
    trace: List[EtapeDecompression] = []

    # 1. Traitement du premier code
    premier_code = codes[0]
    if premier_code not in dico:
        raise ValueError(
            f"Code initial invalide : {premier_code}. "
            f"Le premier code doit appartenir au dictionnaire initial (0, 1 ou 2 pour 'a', 'b', 'c')."
        )

    w = dico[premier_code]
    resultats: List[str] = [w]
    correspondances: List[Tuple[int, str]] = [(premier_code, w)]
    chaine_cumulee = w

    trace.append(
        EtapeDecompression(
            etape=1,
            code=premier_code,
            dans_dico=True,
            cas_special=False,
            sous_chaine_emise=w,
            ajout_dictionnaire=None,
            chaine_cumulee=chaine_cumulee,
            action=f"Premier code : émettre '{w}', initialiser w = '{w}'",
        )
    )

    # 2. Traitement des codes suivants
    for idx, code in enumerate(codes[1:], start=2):
        cas_special = False

        if code in dico:
            entree = dico[code]
            dans_dico = True
            action_desc = f"Code connu : émettre '{entree}'"
        elif code == prochain_code:
            # Cas spécial : le compresseur a émis un code qui vient juste d'être créé
            # et que le décompresseur n'a pas encore ajouté à son dictionnaire.
            # Cela arrive pour les répétitions comme 'aaa', 'aaaaaa', 'abababab'.
            # La règle mathématique démontre que la chaîne est alors égale à w + w[0].
            entree = w + w[0]
            dans_dico = False
            cas_special = True
            action_desc = f"Cas spécial (code == {prochain_code}) : émettre w + w[0] = '{entree}'"
        else:
            raise ValueError(
                f"Code LZW invalide détecté à la position {idx} (code={code}). "
                f"Ce code n'est ni présent dans le dictionnaire courant (0 à {prochain_code - 1}), "
                f"ni égal au prochain code attendu ({prochain_code})."
            )

        resultats.append(entree)
        correspondances.append((code, entree))
        chaine_cumulee += entree

        # Ajout de la nouvelle chaîne au dictionnaire : w + premier caractère de l'entrée actuelle
        nouveau_motif = w + entree[0]
        dico[prochain_code] = nouveau_motif
        nouvel_ajout = (prochain_code, nouveau_motif)

        action_complete = f"{action_desc}, ajouter {prochain_code} : '{nouveau_motif}', w devient '{entree}'"

        trace.append(
            EtapeDecompression(
                etape=idx,
                code=code,
                dans_dico=dans_dico,
                cas_special=cas_special,
                sous_chaine_emise=entree,
                ajout_dictionnaire=nouvel_ajout,
                chaine_cumulee=chaine_cumulee,
                action=action_complete,
            )
        )

        prochain_code += 1
        w = entree

    texte_reconstruit = "".join(resultats)

    # Vérification que la chaîne décompressée respecte bien l'alphabet {a, b, c}
    caracteres_hors_alphabet = set(texte_reconstruit) - ALPHABET_VALIDE
    if caracteres_hors_alphabet:
        raise ValueError(
            f"Anomalie de décompression : des caractères hors alphabet ont été générés : "
            f"{caracteres_hors_alphabet}"
        )

    return texte_reconstruit, correspondances, dico, trace


def afficher_trace_decompression(trace: List[EtapeDecompression]) -> None:
    """Affiche la trace d'exécution détaillée de la décompression sous forme tabulaire."""
    print("\n" + "=" * 110)
    print("TRACE PÉDAGOGIQUE DE LA DÉCOMPRESSION LZW")
    print("=" * 110)
    header = (
        f"{'Étape':<6} | {'Code':<6} | {'Dans dico ?':<14} | {'Sous-chaîne':<13} | "
        f"{'Ajout dictionnaire':<20} | {'Chaîne cumulée':<20} | {'Action'}"
    )
    print(header)
    print("-" * 110)

    for etape in trace:
        code_str = str(etape.code)
        if etape.cas_special:
            dans_dico_str = "Non (Spécial)"
        elif etape.dans_dico:
            dans_dico_str = "Oui"
        else:
            dans_dico_str = "Non"

        sub_str = repr(etape.sous_chaine_emise)
        ajout_str = (
            f"{etape.ajout_dictionnaire[0]} : {repr(etape.ajout_dictionnaire[1])}"
            if etape.ajout_dictionnaire
            else "-"
        )
        cumul_str = repr(etape.chaine_cumulee)
        if len(cumul_str) > 18:
            cumul_str = cumul_str[:15] + "...'"

        print(
            f"{etape.etape:<6} | {code_str:<6} | {dans_dico_str:<14} | {sub_str:<13} | "
            f"{ajout_str:<20} | {cumul_str:<20} | {etape.action}"
        )

    print("-" * 110)


def afficher_dictionnaire_decompression(dico: Dict[int, str]) -> None:
    """
    Affiche le dictionnaire reconstruit au fil de l'eau par le décodeur LZW.
    Distingue clairement les entrées initiales des entrées générées.
    """
    print("\n" + "=" * 60)
    print("DICTIONNAIRE RECONSTRUIT (GÉNÉRÉ LORS DE LA DÉCOMPRESSION)")
    print("=" * 60)
    print(f"{'Code':<8} | {'Sous-chaîne':<18} | {'Type'}")
    print("-" * 60)

    for code in sorted(dico.keys()):
        sous_chaine = dico[code]
        if code < 3:
            type_str = "Initiale"
        else:
            type_str = "Générée (Reconstruite)"
        print(f"{code:<8} | {repr(sous_chaine):<18} | {type_str}")

    print("-" * 60)


def afficher_correspondances(correspondances: List[Tuple[int, str]]) -> None:
    """Affiche le tableau associant chaque code reçu à la sous-chaîne qu'il représente."""
    print("\n" + "=" * 60)
    print("CORRESPONDANCE CODES -> SOUS-CHAÎNES DÉCODÉES")
    print("=" * 60)
    print(f"{'Position':<10} | {'Code':<8} | {'Sous-chaîne correspondante'}")
    print("-" * 60)

    for idx, (code, sub) in enumerate(correspondances, start=1):
        print(f"{idx:<10} | {code:<8} | {repr(sub)}")

    print("-" * 60)


def afficher_bilan(codes: List[int], chaine: str, dico: Dict[int, str]) -> None:
    """Affiche le récapitulatif complet de la décompression avec statistiques."""
    nb_initiales = sum(1 for c in dico if c < 3)
    nb_generees = sum(1 for c in dico if c >= 3)

    print("\n" + "=" * 65)
    print("RÉSULTAT FINAL DE LA DÉCOMPRESSION")
    print("=" * 65)
    print(f"Codes reçus en entrée     : {codes}")
    print(f"Chaîne décompressée       : '{chaine}'")
    print(f"Nombre de codes traités   : {len(codes)}")
    print(f"Longueur chaîne obtenue   : {len(chaine)} caractère(s)")
    print(f"Taille dictionnaire final : {len(dico)} entrées ({nb_initiales} initiales, {nb_generees} générées)")
    print("Statut                    : SUCCÈS (Décompression intègre et conforme)")
    print("=" * 65)


def main() -> None:
    """Point d'entrée principal interactif et CLI pour la décompression LZW."""
    # Assure un affichage correct des caractères accentués sous tous terminaux
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("=" * 70)
    print("       Projet — Décompression LZW (Lempel-Ziv-Welch)")
    print("=" * 70)
    print("Alphabet autorisé : {'a', 'b', 'c'}")
    print("Dictionnaire initial : 0 -> 'a', 1 -> 'b', 2 -> 'c'")
    print("Nouveaux codes générés successivement à partir de 3.")
    print("Formats de saisie acceptés : [0, 3, 1, 0, 2, 5] ou 0, 3, 1, 0, 2, 5 ou 0 3 1 0 2 5")
    print("=" * 70)

    codes: List[int] = []

    # Vérification si des arguments ont été passés en ligne de commande
    if len(sys.argv) > 1:
        argument_brut = " ".join(sys.argv[1:])
        try:
            codes = parser_chaine_codes(argument_brut)
            print(f"\nCodes reçus en argument : {codes}")
        except ValueError as err:
            print(f"\nArgument invalide : {err}")
            codes = []

    # Saisie interactive si aucun argument valide n'a été fourni
    while not codes:
        try:
            saisie = input("\nVeuillez entrer la séquence de codes compressés : ").strip()
            codes = parser_chaine_codes(saisie)
        except ValueError as err:
            print(err)
            print("Veuillez recommencer la saisie.")

    # Exécution de la décompression avec trace détaillée
    try:
        texte_reconstruit, correspondances, dico_reconstruit, trace = decompresser_lzw_detaille(codes)
    except ValueError as err:
        print(f"\nErreur durant la décompression : {err}")
        sys.exit(1)

    # 1. Affichage de la trace étape par étape
    afficher_trace_decompression(trace)

    # 2. Affichage de la correspondance des codes
    afficher_correspondances(correspondances)

    # 3. Visualisation du dictionnaire généré
    afficher_dictionnaire_decompression(dico_reconstruit)

    # 4. Bilan final
    afficher_bilan(codes, texte_reconstruit, dico_reconstruit)


if __name__ == "__main__":
    main()
