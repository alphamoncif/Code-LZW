"""
Projet n°2 — Compression LZW (Lempel-Ziv-Welch)
Alphabet restreint : {'a', 'b', 'c'}
Convention initiale :
  0 -> 'a'
  1 -> 'b'
  2 -> 'c'
Les nouveaux codes sont attribués successivement à partir de 3.
"""

import sys
from typing import List, Dict, Tuple, NamedTuple, Optional

ALPHABET_VALIDE = {'a', 'b', 'c'}


class EtapeTrace(NamedTuple):
    k: str
    w: str
    wk: str
    dans_dico: bool
    action: str
    code_emis: Optional[int]
    nouvelle_entree: Optional[Tuple[int, str]]


def valider_entree(texte: str) -> str:
    """
    Valide que la chaîne n'est pas vide et ne contient que les caractères de l'alphabet {'a', 'b', 'c'}.
    Lève ValueError avec un message explicite citant les caractères fautifs si invalide.
    Retourne la chaîne originale non modifiée si valide.
    """
    if not texte:
        raise ValueError("Erreur de saisie : la chaîne d'entrée ne peut pas être vide.")

    caracteres_fautifs = sorted(list({char for char in texte if char not in ALPHABET_VALIDE}))
    if caracteres_fautifs:
        caracteres_str = ", ".join(repr(c) for c in caracteres_fautifs)
        raise ValueError(
            f"Erreur de saisie : caractères non autorisés détectés : {caracteres_str}. "
            f"Seuls les caractères 'a', 'b' et 'c' sont acceptés."
        )

    return texte


def initialiser_dictionnaire_compression() -> Dict[str, int]:
    """
    Initialise le dictionnaire pour la compression avec l'alphabet {'a', 'b', 'c'}.
    Mapping : sous-chaîne -> code.
    """
    return {'a': 0, 'b': 1, 'c': 2}


def initialiser_dictionnaire_decompression() -> Dict[int, str]:
    """
    Initialise le dictionnaire pour la décompression avec l'alphabet {'a', 'b', 'c'}.
    Mapping : code -> sous-chaîne.
    """
    return {0: 'a', 1: 'b', 2: 'c'}


def compresser_lzw(texte: str) -> Tuple[List[int], Dict[str, int], List[EtapeTrace]]:
    """
    Exécute la compression LZW classique sur la chaîne `texte`.
    Retourne:
      - codes : liste des codes générés
      - dictionnaire_final : dictionnaire sous-chaîne -> code final
      - trace : liste d'étapes détaillées (EtapeTrace) pour affichage pédagogique
    """
    valider_entree(texte)

    dico = initialiser_dictionnaire_compression()
    prochain_code = 3
    codes: List[int] = []
    trace: List[EtapeTrace] = []

    w = ""
    for k in texte:
        wk = w + k
        if wk in dico:
            trace.append(
                EtapeTrace(
                    k=k,
                    w=w,
                    wk=wk,
                    dans_dico=True,
                    action=f"w devient '{wk}'",
                    code_emis=None,
                    nouvelle_entree=None,
                )
            )
            w = wk
        else:
            code_emis = dico[w]
            codes.append(code_emis)
            dico[wk] = prochain_code
            nouvelle_entree = (prochain_code, wk)
            trace.append(
                EtapeTrace(
                    k=k,
                    w=w,
                    wk=wk,
                    dans_dico=False,
                    action=f"Émettre {code_emis}, ajouter '{wk}' -> {prochain_code}, w devient '{k}'",
                    code_emis=code_emis,
                    nouvelle_entree=nouvelle_entree,
                )
            )
            prochain_code += 1
            w = k

    # Émission finale si w n'est pas vide
    if w:
        code_final = dico[w]
        codes.append(code_final)
        trace.append(
            EtapeTrace(
                k="(fin)",
                w=w,
                wk="-",
                dans_dico=True,
                action=f"Fin de chaîne : émettre le code de w ('{w}')",
                code_emis=code_final,
                nouvelle_entree=None,
            )
        )

    return codes, dico, trace


def decompresser_lzw(codes: List[int]) -> Tuple[str, List[Tuple[int, str]], Dict[int, str]]:
    """
    Décompresse une séquence de codes LZW.
    Reconstruit son propre dictionnaire au fur et à mesure de la lecture des codes.
    Gère le cas spécial où le code reçu est égal au prochain code libre (code == prochain_code).

    Retourne:
      - texte_reconstruit : chaîne de caractères décodée
      - correspondances : liste des paires (code, sous_chaine) décodées
      - dictionnaire_final : dictionnaire code -> sous-chaîne reconstruit côté décodeur
    """
    if not codes:
        return "", [], initialiser_dictionnaire_decompression()

    dico = initialiser_dictionnaire_decompression()
    prochain_code = 3

    premier_code = codes[0]
    if premier_code not in dico:
        raise ValueError(
            f"Code initial invalide lors de la décompression : {premier_code}. "
            f"Les codes initiaux valides sont 0, 1 ou 2."
        )

    w = dico[premier_code]
    resultats = [w]
    correspondances: List[Tuple[int, str]] = [(premier_code, w)]

    for code in codes[1:]:
        if code in dico:
            entree = dico[code]
        elif code == prochain_code:
            # Cas spécial : le code reçu est égal au prochain code qui doit être ajouté.
            # Cela arrive lorsque l'émetteur a codé une séquence commençant par le même caractère
            # que le motif précédent (ex: 'w + w[0]').
            entree = w + w[0]
        else:
            raise ValueError(
                f"Code LZW invalide détecté : {code}. "
                f"Ce code n'est ni dans le dictionnaire existant (codes 0 à {prochain_code - 1}), "
                f"ni égal au prochain code attendu ({prochain_code})."
            )

        resultats.append(entree)
        correspondances.append((code, entree))

        # Reconstitution progressive du dictionnaire côté décodeur
        dico[prochain_code] = w + entree[0]
        prochain_code += 1

        w = entree

    return "".join(resultats), correspondances, dico


def afficher_trace(trace: List[EtapeTrace]) -> None:
    """Affiche la trace détaillée de la compression sous forme de tableau formaté."""
    print("\n" + "=" * 95)
    print("TRACE PÉDAGOGIQUE DE LA COMPRESSION")
    print("=" * 95)
    header = (
        f"{'Car. k':<8} | {'w':<8} | {'wk':<8} | {'Dans dico ?':<12} | "
        f"{'Code émis':<10} | {'Ajout dictionnaire':<20} | {'Action'}"
    )
    print(header)
    print("-" * 95)

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

        print(
            f"{k_str:<8} | {w_str:<8} | {wk_str:<8} | {dans_dico_str:<12} | "
            f"{code_str:<10} | {ajout_str:<20} | {etape.action}"
        )
    print("-" * 95)


def afficher_dictionnaire(dico: Dict[str, int]) -> None:
    """
    Affiche le dictionnaire final de compression trié par code croissant.
    Colonnes : Code | Sous-chaîne | Type (Initiale ou Générée).
    """
    print("\n" + "=" * 55)
    print("DICTIONNAIRE FINAL")
    print("=" * 55)
    print(f"{'Code':<8} | {'Sous-chaîne':<15} | {'Type'}")
    print("-" * 55)

    # Inverser pour trier par code croissant
    entrees_triees = sorted(dico.items(), key=lambda item: item[1])
    for sous_chaine, code in entrees_triees:
        type_entree = "Initiale" if code < 3 else "Générée"
        print(f"{code:<8} | {repr(sous_chaine):<15} | {type_entree}")
    print("-" * 55)


def afficher_correspondances(correspondances: List[Tuple[int, str]]) -> None:
    """Affiche le remplacement des codes par les sous-chaînes décodées."""
    print("\n" + "=" * 55)
    print("CORRESPONDANCE CODES -> SOUS-CHAÎNES DÉCODÉES")
    print("=" * 55)
    print(f"{'Position':<10} | {'Code':<8} | {'Sous-chaîne correspondante'}")
    print("-" * 55)
    for idx, (code, sub) in enumerate(correspondances, start=1):
        print(f"{idx:<10} | {code:<8} | {repr(sub)}")
    print("-" * 55)


def main() -> None:
    """Point d'entrée principal interactif et CLI."""
    # Assure un affichage correct des caractères accentués sous tous terminaux
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("=" * 65)
    print("       Projet n°2 — Compression LZW (Lempel-Ziv-Welch)")
    print("=" * 65)
    print("Alphabet autorisé : {'a', 'b', 'c'}")
    print("Dictionnaire initial : 0 -> 'a', 1 -> 'b', 2 -> 'c'")
    print("Les nouveaux codes sont attribués successivement à partir de 3.")
    print("=" * 65)

    texte_source = ""
    # Gestion de l'argument CLI ou saisie interactive
    if len(sys.argv) > 1:
        candidat = sys.argv[1]
        try:
            texte_source = valider_entree(candidat)
            print(f"\nChaîne fournie en ligne de commande : '{texte_source}'")
        except ValueError as err:
            print(f"\nArgument invalide : {err}")
            texte_source = ""

    while not texte_source:
        try:
            saisie = input("\nVeuillez entrer une chaîne à compresser (ex: ababc) : ").strip()
            texte_source = valider_entree(saisie)
        except ValueError as err:
            print(err)
            print("Veuillez recommencer la saisie.")

    # 1. Compression LZW
    codes, dico_comp, trace = compresser_lzw(texte_source)

    # 2. Affichage de la trace pédagogique
    afficher_trace(trace)

    # 3. Affichage des codes compressés
    print(f"\nCodes compressés : {codes}")

    # 4. Affichage du dictionnaire final
    afficher_dictionnaire(dico_comp)

    # 5. Décompression LZW (reconstruction autonome du dictionnaire)
    chaine_reconstruite, correspondances, dico_decomp = decompresser_lzw(codes)

    # 6. Affichage correspondance codes -> sous-chaînes
    afficher_correspondances(correspondances)

    # 7. Affichage et vérification finale
    print("\n" + "=" * 55)
    print("RÉSULTAT DE LA VÉRIFICATION")
    print("=" * 55)
    print(f"Chaîne d'origine    : '{texte_source}'")
    print(f"Chaîne reconstruite : '{chaine_reconstruite}'")
    if chaine_reconstruite == texte_source:
        print("Vérification : SUCCÈS (La chaîne reconstruite est rigoureusement identique à l'entrée).")
    else:
        print("Vérification : ÉCHEC (Divergence détectée entre l'entrée et la sortie !)")
    print("=" * 55)


if __name__ == "__main__":
    main()
