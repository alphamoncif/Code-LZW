"""
Tests unitaires pour le script de décompression LZW (decompression_lzw.py).
Couvre :
  - Le parsing robuste des chaînes de codes (formats variés, crochets, virgules, espaces)
  - La gestion des erreurs de parsing (entrées vides, lettres, négatifs)
  - La décompression exacte de toutes les séquences canoniques de l'alphabet {a, b, c}
  - Le test dédié du cas spécial cScSc (ex: [0, 3] -> aaa, [0, 3, 4] -> aaaaaa)
  - La détection des codes invalides (premier code inconnu, saut de code supérieur à prochain_code)
  - L'intégrité du dictionnaire généré lors de la décompression
"""

import unittest
from decompression_lzw import (
    parser_chaine_codes,
    decompresser_lzw_detaille,
    initialiser_dictionnaire_decompression,
)


class TestDecompressionLZW(unittest.TestCase):

    def test_parser_formats_valides(self):
        """Vérifie que différents formats textuels de codes sont correctement parsés."""
        cas = [
            ("[0, 3, 1, 0, 2, 5]", [0, 3, 1, 0, 2, 5]),
            ("0, 3, 1, 0, 2, 5", [0, 3, 1, 0, 2, 5]),
            ("0,3,1,0,2,5", [0, 3, 1, 0, 2, 5]),
            ("0 3 1 0 2 5", [0, 3, 1, 0, 2, 5]),
            ("(0, 3, 1, 0, 2, 5)", [0, 3, 1, 0, 2, 5]),
            ("0; 3; 1; 0; 2; 5", [0, 3, 1, 0, 2, 5]),
            ("Codes compressés : [0, 3, 1, 0, 2, 5]", [0, 3, 1, 0, 2, 5]),
            (" [ 0 , 1 , 2 ] ", [0, 1, 2]),
        ]
        for texte, attendu in cas:
            with self.subTest(texte=texte):
                self.assertEqual(parser_chaine_codes(texte), attendu)

    def test_parser_formats_invalides(self):
        """Vérifie que les chaînes mal formées lèvent une exception ValueError."""
        cas_invalides = [
            "",
            "   ",
            "[]",
            "[  ]",
            "0, a, 2",
            "0, -3, 1",
            "abc",
            "None",
        ]
        for texte in cas_invalides:
            with self.subTest(texte=texte):
                with self.assertRaises(ValueError):
                    parser_chaine_codes(texte)

    def test_decompresser_sequences_canoniques(self):
        """
        Vérifie la décompression des codes standards et l'exactitude de la chaîne reconstruite.
        """
        cas_tests = [
            ([0], "a"),
            ([1], "b"),
            ([2], "c"),
            ([0, 0], "aa"),
            ([0, 3], "aaa"),
            ([0, 1, 2], "abc"),
            ([0, 1, 3, 2], "ababc"),
            ([0, 3, 1, 0, 2, 5], "aaabacba"),
            ([0, 1, 3, 5, 1], "abababab"),
            ([0, 3, 4], "aaaaaa"),
        ]

        for codes, attendu in cas_tests:
            with self.subTest(codes=codes):
                texte, correspondances, dico, trace = decompresser_lzw_detaille(codes)
                self.assertEqual(texte, attendu)
                self.assertEqual(len(correspondances), len(codes))
                self.assertEqual(len(trace), len(codes))

    def test_dictionnaire_reconstruit(self):
        """
        Vérifie que le dictionnaire reconstruit au fil de la décompression
        contient les entrées initiales et les nouvelles entrées générées.
        """
        codes = [0, 3, 1, 0, 2, 5]  # Décompresse 'aaabacba'
        _, _, dico, _ = decompresser_lzw_detaille(codes)

        # Entrées initiales
        self.assertEqual(dico[0], "a")
        self.assertEqual(dico[1], "b")
        self.assertEqual(dico[2], "c")

        # Entrées générées consécutives
        self.assertEqual(dico[3], "aa")
        self.assertEqual(dico[4], "aab")
        self.assertEqual(dico[5], "ba")
        self.assertEqual(dico[6], "ac")
        self.assertEqual(dico[7], "cb")

    def test_cas_special_decompression(self):
        """
        Vérifie spécifiquement le cas où code == prochain_code (cas cScSc).
        """
        # [0, 3] -> 'aaa' : 3 n'est pas encore dans le dictionnaire au moment de la lecture
        texte, _, dico, trace = decompresser_lzw_detaille([0, 3])
        self.assertEqual(texte, "aaa")
        self.assertTrue(trace[1].cas_special)
        self.assertEqual(dico[3], "aa")

        # [0, 3, 4] -> 'aaaaaa'
        texte2, _, dico2, trace2 = decompresser_lzw_detaille([0, 3, 4])
        self.assertEqual(texte2, "aaaaaa")
        self.assertTrue(trace2[1].cas_special)
        self.assertTrue(trace2[2].cas_special)

    def test_erreurs_codes_invalides(self):
        """Vérifie que les codes incompatibles avec le dictionnaire lèvent ValueError."""
        # 1. Liste vide
        with self.assertRaises(ValueError):
            decompresser_lzw_detaille([])

        # 2. Premier code n'appartenant pas à l'alphabet initial {0, 1, 2}
        with self.assertRaises(ValueError) as ctx_premier:
            decompresser_lzw_detaille([3])
        self.assertIn("initial", str(ctx_premier.exception).lower())

        with self.assertRaises(ValueError):
            decompresser_lzw_detaille([9])

        # 3. Saut de code invalide (prochain attendu 3, code reçu 5)
        with self.assertRaises(ValueError) as ctx_saut:
            decompresser_lzw_detaille([0, 5])
        self.assertIn("invalide", str(ctx_saut.exception).lower())


if __name__ == "__main__":
    unittest.main()
