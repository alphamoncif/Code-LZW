"""
Tests unitaires pour le projet n°2 — Compression LZW.
Couvre :
  - Validation des entrées (rejet chaînes vides, caractères hors alphabet)
  - Compression et décompression des chaînes de test obligatoires :
    a, b, c, aa, aaa, abc, ababc, abcabcabc, aaabccab, abababab
  - Propriétés structurelles du dictionnaire et des codes émis
  - Test dédié du cas spécial du décodeur (ex: [0, 3] -> aaa, [0, 3, 4] -> aaaaaa)
  - Détection et rejet des codes invalides lors de la décompression
"""

import unittest
from lzw import (
    valider_entree,
    compresser_lzw,
    decompresser_lzw,
    initialiser_dictionnaire_compression,
    initialiser_dictionnaire_decompression,
)


class TestLZW(unittest.TestCase):

    def test_valider_entree_valide(self):
        """Vérifie que les chaînes valides sont retournées intactes."""
        chaines_valides = [
            "a", "b", "c", "aa", "aaa", "abc", "ababc",
            "abcabcabc", "aaabccab", "abababab"
        ]
        for s in chaines_valides:
            self.assertEqual(valider_entree(s), s)

    def test_valider_entree_invalide(self):
        """Vérifie que ValueError est levée avec un message explicite pour les entrées invalides."""
        # Chaîne vide
        with self.assertRaises(ValueError) as ctx_vide:
            valider_entree("")
        self.assertIn("vide", str(ctx_vide.exception).lower())

        # Caractères interdits
        cas_invalides = [
            ("abcd", ["d"]),
            ("ABC", ["A", "B", "C"]),
            ("ab c", [" "]),
            ("123", ["1", "2", "3"]),
            ("a#b!c", ["!", "#"]),
        ]
        for texte, fautifs in cas_invalides:
            with self.assertRaises(ValueError) as ctx:
                valider_entree(texte)
            msg = str(ctx.exception)
            for f in fautifs:
                self.assertIn(repr(f), msg)

    def test_compression_decompression_chaines_obligatoires(self):
        """
        Vérifie pour chaque chaîne de test obligatoire :
          1. La compression s'exécute sans erreur.
          2. Le dictionnaire initial contient bien 0: 'a', 1: 'b', 2: 'c'.
          3. Les nouveaux codes sont consécutifs à partir de 3.
          4. Le décodage restitue exactement la chaîne d'origine.
          5. Chaque code émis est valide pour le décodeur.
        """
        chaines = [
            "a", "b", "c", "aa", "aaa", "abc", "ababc",
            "abcabcabc", "aaabccab", "abababab"
        ]

        for s in chaines:
            with self.subTest(chaine=s):
                codes, dico_comp, trace = compresser_lzw(s)

                # Dictionnaire initial présent
                self.assertEqual(dico_comp["a"], 0)
                self.assertEqual(dico_comp["b"], 1)
                self.assertEqual(dico_comp["c"], 2)

                # Nouveaux codes consécutifs à partir de 3
                valeurs_codes = sorted(dico_comp.values())
                expected_codes = list(range(len(valeurs_codes)))
                self.assertEqual(valeurs_codes, expected_codes)

                # Décompression et égalité parfaite
                texte_reconstruit, correspondances, dico_decomp = decompresser_lzw(codes)
                self.assertEqual(texte_reconstruit, s)

                # Les correspondances doivent correspondre aux codes émis
                codes_reconstruits = [code for code, _ in correspondances]
                self.assertEqual(codes_reconstruits, codes)

    def test_cas_special_decompression(self):
        """
        Test dédié du cas spécial de décompression (code == prochain_code):
          - [0, 3] -> aaa (0='a', 3='aa')
          - [0, 3, 4] -> aaaaaa
          - [0, 1, 3, 5, 1] -> abababab
        """
        # [0, 3]
        texte1, _, _ = decompresser_lzw([0, 3])
        self.assertEqual(texte1, "aaa")

        # [0, 3, 4]
        texte2, _, _ = decompresser_lzw([0, 3, 4])
        self.assertEqual(texte2, "aaaaaa")

        # [0, 1, 3, 5, 1]
        texte3, _, _ = decompresser_lzw([0, 1, 3, 5, 1])
        self.assertEqual(texte3, "abababab")

        # Vérification croisée avec la compression
        self.assertEqual(compresser_lzw("aaa")[0], [0, 3])
        self.assertEqual(compresser_lzw("aaaaaa")[0], [0, 3, 4])
        self.assertEqual(compresser_lzw("abababab")[0], [0, 1, 3, 5, 1])

    def test_code_invalide_decompresser(self):
        """Vérifie qu'un code hors dictionnaire et différent de prochain_code lève ValueError."""
        # Code initial invalide
        with self.assertRaises(ValueError) as ctx_init:
            decompresser_lzw([5])
        self.assertIn("invalide", str(ctx_init.exception).lower())

        # Code suivant trop grand (prochain code attendu = 3, on envoie 7)
        with self.assertRaises(ValueError) as ctx_saut:
            decompresser_lzw([0, 7])
        self.assertIn("7", str(ctx_saut.exception))


if __name__ == "__main__":
    unittest.main()
