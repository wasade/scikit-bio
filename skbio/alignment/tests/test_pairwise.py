# ----------------------------------------------------------------------------
# Copyright (c) 2013--, scikit-bio development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# ----------------------------------------------------------------------------

from __future__ import absolute_import, division, print_function

from unittest import TestCase, main
import warnings

import numpy as np

from skbio import Protein, DNA, BiologicalSequence, Alignment
from skbio.alignment import (
    global_pairwise_align_protein, local_pairwise_align_protein,
    global_pairwise_align_nucleotide, local_pairwise_align_nucleotide)
from skbio.alignment._pairwise import (
    _make_nt_substitution_matrix, _init_matrices_sw, _init_matrices_nw,
    _compute_score_and_traceback_matrices, _traceback, _first_largest,
    _get_seq_id, _compute_substitution_score)


class PairwiseAlignmentTests(TestCase):
    """
        Note: In the high-level tests, the expected results were derived with
        assistance from the EMBOSS web server:
        http://www.ebi.ac.uk/Tools/psa/emboss_needle/
        http://www.ebi.ac.uk/Tools/psa/emboss_water/
        In some cases, placement of non-gap characters surrounded by gap
        characters are slighly different between scikit-bio and the EMBOSS
        server. These differences arise from arbitrary implementation
        differences, and always result in the same score (which tells us that
        the alignments are equivalent). In cases where the expected results
        included here differ from those generated by the EMBOSS server, I note
        the EMBOSS result as a comment below the expected value.

    """

    def test_make_nt_substitution_matrix(self):
        expected = {'A': {'A':  1, 'C': -2, 'G': -2, 'T': -2},
                    'C': {'A': -2, 'C':  1, 'G': -2, 'T': -2},
                    'G': {'A': -2, 'C': -2, 'G':  1, 'T': -2},
                    'T': {'A': -2, 'C': -2, 'G': -2, 'T':  1}}
        self.assertEqual(_make_nt_substitution_matrix(1, -2), expected)

        expected = {'A': {'A':  5, 'C': -4, 'G': -4, 'T': -4},
                    'C': {'A': -4, 'C':  5, 'G': -4, 'T': -4},
                    'G': {'A': -4, 'C': -4, 'G':  5, 'T': -4},
                    'T': {'A': -4, 'C': -4, 'G': -4, 'T':  5}}
        self.assertEqual(_make_nt_substitution_matrix(5, -4), expected)

    def test_global_pairwise_align_protein(self):
        expected = ("HEAGAWGHEE-", "---PAW-HEAE", 23.0)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            actual = global_pairwise_align_protein(
                "HEAGAWGHEE", "PAWHEAE", gap_open_penalty=10.,
                gap_extend_penalty=5.)
        self.assertEqual(str(actual[0]), expected[0])
        self.assertEqual(str(actual[1]), expected[1])
        self.assertEqual(actual.score(), expected[2])
        self.assertEqual(actual.start_end_positions(), [(0, 9), (0, 6)])
        self.assertEqual(actual.ids(), list('01'))

        expected = ("HEAGAWGHE-E", "---PAW-HEAE", 30.0)
        # EMBOSS result: P---AW-HEAE
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            actual = global_pairwise_align_protein(
                "HEAGAWGHEE", "PAWHEAE", gap_open_penalty=5.,
                gap_extend_penalty=0.5)
        self.assertEqual(str(actual[0]), expected[0])
        self.assertEqual(str(actual[1]), expected[1])
        self.assertEqual(actual.score(), expected[2])
        self.assertEqual(actual.start_end_positions(), [(0, 9), (0, 6)])
        self.assertEqual(actual.ids(), list('01'))

        # Protein (rather than str) as input
        expected = ("HEAGAWGHEE-", "---PAW-HEAE", 23.0)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            actual = global_pairwise_align_protein(
                Protein("HEAGAWGHEE", "s1"), Protein("PAWHEAE", "s2"),
                gap_open_penalty=10., gap_extend_penalty=5.)
        self.assertEqual(str(actual[0]), expected[0])
        self.assertEqual(str(actual[1]), expected[1])
        self.assertEqual(actual.score(), expected[2])
        self.assertEqual(actual.start_end_positions(), [(0, 9), (0, 6)])
        self.assertEqual(actual.ids(), ["s1", "s2"])

        # One Alignment and one Protein as input
        expected = ("HEAGAWGHEE-", "---PAW-HEAE", 23.0)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            actual = global_pairwise_align_protein(
                Alignment([Protein("HEAGAWGHEE", "s1")]),
                Protein("PAWHEAE", "s2"),
                gap_open_penalty=10., gap_extend_penalty=5.)
        self.assertEqual(str(actual[0]), expected[0])
        self.assertEqual(str(actual[1]), expected[1])
        self.assertEqual(actual.score(), expected[2])
        self.assertEqual(actual.start_end_positions(), [(0, 9), (0, 6)])
        self.assertEqual(actual.ids(), ["s1", "s2"])

        # One single-sequence alignment as input and one double-sequence
        # alignment as input. Score confirmed manually.
        expected = ("HEAGAWGHEE-", "HDAGAWGHDE-", "---PAW-HEAE", 21.0)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            actual = global_pairwise_align_protein(
                Alignment([Protein("HEAGAWGHEE", "s1"),
                           Protein("HDAGAWGHDE", "s2")]),
                Alignment([Protein("PAWHEAE", "s3")]),
                gap_open_penalty=10., gap_extend_penalty=5.)
        self.assertEqual(str(actual[0]), expected[0])
        self.assertEqual(str(actual[1]), expected[1])
        self.assertEqual(str(actual[2]), expected[2])
        self.assertEqual(actual.score(), expected[3])
        self.assertEqual(actual.start_end_positions(), [(0, 9), (0, 6)])
        self.assertEqual(actual.ids(), ["s1", "s2", "s3"])

        # ids are provided if they're not passed in
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            actual = global_pairwise_align_protein(
                Protein("HEAGAWGHEE"), Protein("PAWHEAE"),
                gap_open_penalty=10., gap_extend_penalty=5.)
        self.assertEqual(actual.ids(), list('01'))

        # TypeError on invalid input
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.assertRaises(TypeError, global_pairwise_align_protein,
                              42, "HEAGAWGHEE")
            self.assertRaises(TypeError, global_pairwise_align_protein,
                              "HEAGAWGHEE", 42)

    def test_global_pairwise_align_protein_penalize_terminal_gaps(self):
        expected = ("HEAGAWGHEE", "---PAWHEAE", 1.0)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            actual = global_pairwise_align_protein(
                "HEAGAWGHEE", "PAWHEAE", gap_open_penalty=10.,
                gap_extend_penalty=5., penalize_terminal_gaps=True)
        self.assertEqual(str(actual[0]), expected[0])
        self.assertEqual(str(actual[1]), expected[1])
        self.assertEqual(actual.score(), expected[2])
        self.assertEqual(actual.start_end_positions(), [(0, 9), (0, 6)])
        self.assertEqual(actual.ids(), list('01'))

    def test_global_pairwise_align_nucleotide_penalize_terminal_gaps(self):
        # in these tests one sequence is about 3x the length of the other.
        # we toggle penalize_terminal_gaps to confirm that it results in
        # different alignments and alignment scores.
        seq1 = "ACCGTGGACCGTTAGGATTGGACCCAAGGTTG"
        seq2 = "T"*25 + "ACCGTGGACCGTAGGATTGGACCAAGGTTA" + "A"*25

        aln1 = ("-------------------------ACCGTGGACCGTTAGGA"
                "TTGGACCCAAGGTTG-------------------------")
        aln2 = ("TTTTTTTTTTTTTTTTTTTTTTTTTACCGTGGACCGT-AGGA"
                "TTGGACC-AAGGTTAAAAAAAAAAAAAAAAAAAAAAAAAA")
        expected = (aln1, aln2, 131.0)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            actual = global_pairwise_align_nucleotide(
                seq1, seq2, gap_open_penalty=5., gap_extend_penalty=0.5,
                match_score=5, mismatch_score=-4, penalize_terminal_gaps=False)
        self.assertEqual(str(actual[0]), expected[0])
        self.assertEqual(str(actual[1]), expected[1])
        self.assertEqual(actual.score(), expected[2])

        aln1 = ("-------------------------ACCGTGGACCGTTAGGA"
                "TTGGACCCAAGGTT-------------------------G")
        aln2 = ("TTTTTTTTTTTTTTTTTTTTTTTTTACCGTGGACCGT-AGGA"
                "TTGGACC-AAGGTTAAAAAAAAAAAAAAAAAAAAAAAAAA")
        expected = (aln1, aln2, 97.0)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            actual = global_pairwise_align_nucleotide(
                seq1, seq2, gap_open_penalty=5., gap_extend_penalty=0.5,
                match_score=5, mismatch_score=-4, penalize_terminal_gaps=True)
        self.assertEqual(str(actual[0]), expected[0])
        self.assertEqual(str(actual[1]), expected[1])
        self.assertEqual(actual.score(), expected[2])

    def test_local_pairwise_align_protein(self):
        expected = ("AWGHE", "AW-HE", 26.0, 4, 1)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            actual = local_pairwise_align_protein(
                "HEAGAWGHEE", "PAWHEAE", gap_open_penalty=10.,
                gap_extend_penalty=5.)
        self.assertEqual(str(actual[0]), expected[0])
        self.assertEqual(str(actual[1]), expected[1])
        self.assertEqual(actual.score(), expected[2])
        self.assertEqual(actual.start_end_positions(), [(4, 8), (1, 4)])
        self.assertEqual(actual.ids(), list('01'))

        expected = ("AWGHE-E", "AW-HEAE", 32.0, 4, 1)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            actual = local_pairwise_align_protein(
                "HEAGAWGHEE", "PAWHEAE", gap_open_penalty=5.,
                gap_extend_penalty=0.5)
        self.assertEqual(str(actual[0]), expected[0])
        self.assertEqual(str(actual[1]), expected[1])
        self.assertEqual(actual.score(), expected[2])
        self.assertEqual(actual.start_end_positions(), [(4, 9), (1, 6)])
        self.assertEqual(actual.ids(), list('01'))

        expected = ("AWGHE", "AW-HE", 26.0, 4, 1)
        # Protein (rather than str) as input
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            actual = local_pairwise_align_protein(
                Protein("HEAGAWGHEE", "s1"), Protein("PAWHEAE", "s2"),
                gap_open_penalty=10., gap_extend_penalty=5.)
        self.assertEqual(str(actual[0]), expected[0])
        self.assertEqual(str(actual[1]), expected[1])
        self.assertEqual(actual.score(), expected[2])
        self.assertEqual(actual.start_end_positions(), [(4, 8), (1, 4)])
        self.assertEqual(actual.ids(), ["s1", "s2"])

        # Fails when either input is passed as an Alignment
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.assertRaises(TypeError, local_pairwise_align_protein,
                              Alignment([Protein("HEAGAWGHEE", "s1")]),
                              Protein("PAWHEAE", "s2"), gap_open_penalty=10.,
                              gap_extend_penalty=5.)
            self.assertRaises(TypeError, local_pairwise_align_protein,
                              Protein("HEAGAWGHEE", "s1"),
                              Alignment([Protein("PAWHEAE", "s2")]),
                              gap_open_penalty=10., gap_extend_penalty=5.)

        # ids are provided if they're not passed in
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            actual = local_pairwise_align_protein(
                Protein("HEAGAWGHEE"), Protein("PAWHEAE"),
                gap_open_penalty=10., gap_extend_penalty=5.)
        self.assertEqual(actual.ids(), list('01'))

        # TypeError on invalid input
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.assertRaises(TypeError, local_pairwise_align_protein,
                              42, "HEAGAWGHEE")
            self.assertRaises(TypeError, local_pairwise_align_protein,
                              "HEAGAWGHEE", 42)

    def test_global_pairwise_align_nucleotide(self):
        expected = ("G-ACCTTGACCAGGTACC", "GAACTTTGAC---GTAAC", 41.0, 0, 0)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            actual = global_pairwise_align_nucleotide(
                "GACCTTGACCAGGTACC", "GAACTTTGACGTAAC", gap_open_penalty=5.,
                gap_extend_penalty=0.5, match_score=5, mismatch_score=-4)
        self.assertEqual(str(actual[0]), expected[0])
        self.assertEqual(str(actual[1]), expected[1])
        self.assertEqual(actual.score(), expected[2])
        self.assertEqual(actual.start_end_positions(), [(0, 16), (0, 14)])
        self.assertEqual(actual.ids(), list('01'))

        expected = ("-GACCTTGACCAGGTACC", "GAACTTTGAC---GTAAC", 32.0, 0, 0)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            actual = global_pairwise_align_nucleotide(
                "GACCTTGACCAGGTACC", "GAACTTTGACGTAAC", gap_open_penalty=10.,
                gap_extend_penalty=0.5, match_score=5, mismatch_score=-4)
        self.assertEqual(str(actual[0]), expected[0])
        self.assertEqual(str(actual[1]), expected[1])
        self.assertEqual(actual.score(), expected[2])
        self.assertEqual(actual.start_end_positions(), [(0, 16), (0, 14)])
        self.assertEqual(actual.ids(), list('01'))

        # DNA (rather than str) as input
        expected = ("-GACCTTGACCAGGTACC", "GAACTTTGAC---GTAAC", 32.0, 0, 0)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            actual = global_pairwise_align_nucleotide(
                DNA("GACCTTGACCAGGTACC", "s1"), DNA("GAACTTTGACGTAAC", "s2"),
                gap_open_penalty=10., gap_extend_penalty=0.5, match_score=5,
                mismatch_score=-4)
        self.assertEqual(str(actual[0]), expected[0])
        self.assertEqual(str(actual[1]), expected[1])
        self.assertEqual(actual.score(), expected[2])
        self.assertEqual(actual.start_end_positions(), [(0, 16), (0, 14)])
        self.assertEqual(actual.ids(), ["s1", "s2"])

        # Align one DNA sequence and one Alignment, score computed manually
        expected = ("-GACCTTGACCAGGTACC", "-GACCATGACCAGGTACC",
                    "GAACTTTGAC---GTAAC", 27.5, 0, 0)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            actual = global_pairwise_align_nucleotide(
                Alignment([DNA("GACCTTGACCAGGTACC", "s1"),
                           DNA("GACCATGACCAGGTACC", "s2")]),
                DNA("GAACTTTGACGTAAC", "s3"),
                gap_open_penalty=10., gap_extend_penalty=0.5, match_score=5,
                mismatch_score=-4)
        self.assertEqual(str(actual[0]), expected[0])
        self.assertEqual(str(actual[1]), expected[1])
        self.assertEqual(str(actual[2]), expected[2])
        self.assertEqual(actual.score(), expected[3])
        self.assertEqual(actual.start_end_positions(), [(0, 16), (0, 14)])
        self.assertEqual(actual.ids(), ["s1", "s2", "s3"])

        # ids are provided if they're not passed in
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            actual = global_pairwise_align_nucleotide(
                DNA("GACCTTGACCAGGTACC"), DNA("GAACTTTGACGTAAC"),
                gap_open_penalty=10., gap_extend_penalty=0.5, match_score=5,
                mismatch_score=-4)
        self.assertEqual(actual.ids(), list('01'))

        # TypeError on invalid input
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.assertRaises(TypeError, global_pairwise_align_nucleotide,
                              42, "HEAGAWGHEE")
            self.assertRaises(TypeError, global_pairwise_align_nucleotide,
                              "HEAGAWGHEE", 42)

    def test_local_pairwise_align_nucleotide(self):
        expected = ("ACCTTGACCAGGTACC", "ACTTTGAC---GTAAC", 41.0, 1, 2)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            actual = local_pairwise_align_nucleotide(
                "GACCTTGACCAGGTACC", "GAACTTTGACGTAAC", gap_open_penalty=5.,
                gap_extend_penalty=0.5, match_score=5, mismatch_score=-4)
        self.assertEqual(str(actual[0]), expected[0])
        self.assertEqual(str(actual[1]), expected[1])
        self.assertEqual(actual.score(), expected[2])
        self.assertEqual(actual.start_end_positions(), [(1, 16), (2, 14)])
        self.assertEqual(actual.ids(), list('01'))

        expected = ("ACCTTGAC", "ACTTTGAC", 31.0, 1, 2)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            actual = local_pairwise_align_nucleotide(
                "GACCTTGACCAGGTACC", "GAACTTTGACGTAAC", gap_open_penalty=10.,
                gap_extend_penalty=5., match_score=5, mismatch_score=-4)
        self.assertEqual(str(actual[0]), expected[0])
        self.assertEqual(str(actual[1]), expected[1])
        self.assertEqual(actual.score(), expected[2])
        self.assertEqual(actual.start_end_positions(), [(1, 8), (2, 9)])
        self.assertEqual(actual.ids(), list('01'))

        # DNA (rather than str) as input
        expected = ("ACCTTGAC", "ACTTTGAC", 31.0, 1, 2)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            actual = local_pairwise_align_nucleotide(
                DNA("GACCTTGACCAGGTACC", "s1"), DNA("GAACTTTGACGTAAC", "s2"),
                gap_open_penalty=10., gap_extend_penalty=5., match_score=5,
                mismatch_score=-4)
        self.assertEqual(str(actual[0]), expected[0])
        self.assertEqual(str(actual[1]), expected[1])
        self.assertEqual(actual.score(), expected[2])
        self.assertEqual(actual.start_end_positions(), [(1, 8), (2, 9)])
        self.assertEqual(actual.ids(), ["s1", "s2"])

        # Fails when either input is passed as an Alignment
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.assertRaises(TypeError, local_pairwise_align_nucleotide,
                              Alignment([DNA("GACCTTGACCAGGTACC", "s1")]),
                              DNA("GAACTTTGACGTAAC", "s2"),
                              gap_open_penalty=10., gap_extend_penalty=5.,
                              match_score=5, mismatch_score=-4)
            self.assertRaises(TypeError, local_pairwise_align_nucleotide,
                              DNA("GACCTTGACCAGGTACC", "s1"),
                              Alignment([DNA("GAACTTTGACGTAAC", "s2")]),
                              gap_open_penalty=10., gap_extend_penalty=5.,
                              match_score=5, mismatch_score=-4)

        # ids are provided if they're not passed in
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            actual = local_pairwise_align_nucleotide(
                DNA("GACCTTGACCAGGTACC"), DNA("GAACTTTGACGTAAC"),
                gap_open_penalty=10., gap_extend_penalty=5., match_score=5,
                mismatch_score=-4)
        self.assertEqual(actual.ids(), list('01'))

        # TypeError on invalid input
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.assertRaises(TypeError, local_pairwise_align_nucleotide,
                              42, "HEAGAWGHEE")
            self.assertRaises(TypeError, local_pairwise_align_nucleotide,
                              "HEAGAWGHEE", 42)

    def test_nucleotide_aligners_use_substitution_matrices(self):
        alt_sub = _make_nt_substitution_matrix(10, -10)
        # alternate substitution matrix yields different alignment (the
        # aligned sequences and the scores are different) with local alignment
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            actual_no_sub = local_pairwise_align_nucleotide(
                "GACCTTGACCAGGTACC", "GAACTTTGACGTAAC", gap_open_penalty=10.,
                gap_extend_penalty=5., match_score=5, mismatch_score=-4)
            actual_alt_sub = local_pairwise_align_nucleotide(
                "GACCTTGACCAGGTACC", "GAACTTTGACGTAAC", gap_open_penalty=10.,
                gap_extend_penalty=5., match_score=5, mismatch_score=-4,
                substitution_matrix=alt_sub)
        self.assertNotEqual(str(actual_no_sub[0]), str(actual_alt_sub[0]))
        self.assertNotEqual(str(actual_no_sub[1]), str(actual_alt_sub[1]))
        self.assertNotEqual(actual_no_sub.score(),
                            actual_alt_sub.score())

        # alternate substitution matrix yields different alignment (the
        # aligned sequences and the scores are different) with global alignment
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            actual_no_sub = local_pairwise_align_nucleotide(
                "GACCTTGACCAGGTACC", "GAACTTTGACGTAAC", gap_open_penalty=10.,
                gap_extend_penalty=5., match_score=5, mismatch_score=-4)
            actual_alt_sub = global_pairwise_align_nucleotide(
                "GACCTTGACCAGGTACC", "GAACTTTGACGTAAC", gap_open_penalty=10.,
                gap_extend_penalty=5., match_score=5, mismatch_score=-4,
                substitution_matrix=alt_sub)
        self.assertNotEqual(str(actual_no_sub[0]), str(actual_alt_sub[0]))
        self.assertNotEqual(str(actual_no_sub[1]), str(actual_alt_sub[1]))
        self.assertNotEqual(actual_no_sub.score(),
                            actual_alt_sub.score())

    def test_init_matrices_sw(self):
        expected_score_m = np.zeros((5, 4))
        expected_tback_m = [[0, 0, 0, 0],
                            [0, -1, -1, -1],
                            [0, -1, -1, -1],
                            [0, -1, -1, -1],
                            [0, -1, -1, -1]]
        actual_score_m, actual_tback_m = _init_matrices_sw(
            Alignment([DNA('AAA')]), Alignment([DNA('AAAA')]), 5, 2)
        np.testing.assert_array_equal(actual_score_m, expected_score_m)
        np.testing.assert_array_equal(actual_tback_m, expected_tback_m)

    def test_init_matrices_nw(self):
        expected_score_m = [[0, -5, -7, -9],
                            [-5, 0, 0, 0],
                            [-7, 0, 0, 0],
                            [-9, 0, 0, 0],
                            [-11, 0, 0, 0]]
        expected_tback_m = [[0, 3, 3, 3],
                            [2, -1, -1, -1],
                            [2, -1, -1, -1],
                            [2, -1, -1, -1],
                            [2, -1, -1, -1]]
        actual_score_m, actual_tback_m = _init_matrices_nw(
            Alignment([DNA('AAA')]), Alignment([DNA('AAAA')]), 5, 2)
        np.testing.assert_array_equal(actual_score_m, expected_score_m)
        np.testing.assert_array_equal(actual_tback_m, expected_tback_m)

    def test_compute_substitution_score(self):
        # these results were computed manually
        subs_m = _make_nt_substitution_matrix(5, -4)
        self.assertEqual(
            _compute_substitution_score(['A'], ['A'], subs_m, 0), 5.0)
        self.assertEqual(
            _compute_substitution_score(['A', 'A'], ['A'], subs_m, 0), 5.0)
        self.assertEqual(
            _compute_substitution_score(['A', 'C'], ['A'], subs_m, 0), 0.5)
        self.assertEqual(
            _compute_substitution_score(['A', 'C'], ['A', 'C'], subs_m, 0),
            0.5)
        self.assertEqual(
            _compute_substitution_score(['A', 'A'], ['A', '-'], subs_m, 0),
            2.5)
        self.assertEqual(
            _compute_substitution_score(['A', 'A'], ['A', '-'], subs_m, 1), 3)

        # alt subs_m
        subs_m = _make_nt_substitution_matrix(1, -2)
        self.assertEqual(
            _compute_substitution_score(['A', 'A'], ['A', '-'], subs_m, 0),
            0.5)

    def test_compute_score_and_traceback_matrices(self):
        # these results were computed manually
        expected_score_m = [[0, -5, -7, -9],
                            [-5, 2, -3, -5],
                            [-7, -3, 4, -1],
                            [-9, -5, -1, 6],
                            [-11, -7, -3, 1]]
        expected_tback_m = [[0, 3, 3, 3],
                            [2, 1, 3, 3],
                            [2, 2, 1, 3],
                            [2, 2, 2, 1],
                            [2, 2, 2, 2]]
        m = _make_nt_substitution_matrix(2, -1)
        actual_score_m, actual_tback_m = _compute_score_and_traceback_matrices(
            Alignment([DNA('ACG')]),
            Alignment([DNA('ACGT')]), 5, 2, m)
        np.testing.assert_array_equal(actual_score_m, expected_score_m)
        np.testing.assert_array_equal(actual_tback_m, expected_tback_m)

        # different sequences
        # these results were computed manually
        expected_score_m = [[0, -5, -7, -9],
                            [-5, 2, -3, -5],
                            [-7, -3, 4, -1],
                            [-9, -5, -1, 3],
                            [-11, -7, -3, -2]]
        expected_tback_m = [[0, 3, 3, 3],
                            [2, 1, 3, 3],
                            [2, 2, 1, 3],
                            [2, 2, 2, 1],
                            [2, 2, 2, 1]]
        m = _make_nt_substitution_matrix(2, -1)
        actual_score_m, actual_tback_m = _compute_score_and_traceback_matrices(
            Alignment([DNA('ACC')]),
            Alignment([DNA('ACGT')]), 5, 2, m)
        np.testing.assert_array_equal(actual_score_m, expected_score_m)
        np.testing.assert_array_equal(actual_tback_m, expected_tback_m)

        # four sequences provided in two alignments
        # these results were computed manually
        expected_score_m = [[0, -5, -7, -9],
                            [-5, 2, -3, -5],
                            [-7, -3, 4, -1],
                            [-9, -5, -1, 3],
                            [-11, -7, -3, -2]]
        expected_tback_m = [[0, 3, 3, 3],
                            [2, 1, 3, 3],
                            [2, 2, 1, 3],
                            [2, 2, 2, 1],
                            [2, 2, 2, 1]]
        m = _make_nt_substitution_matrix(2, -1)
        actual_score_m, actual_tback_m = _compute_score_and_traceback_matrices(
            Alignment([DNA('ACC', 's1'), DNA('ACC', 's2')]),
            Alignment([DNA('ACGT', 's3'), DNA('ACGT', 's4')]), 5, 2, m)
        np.testing.assert_array_equal(actual_score_m, expected_score_m)
        np.testing.assert_array_equal(actual_tback_m, expected_tback_m)

    def test_compute_score_and_traceback_matrices_invalid(self):
        # if the sequence contains a character that is not in the
        # substitution matrix, an informative error should be raised
        m = _make_nt_substitution_matrix(2, -1)
        self.assertRaises(ValueError, _compute_score_and_traceback_matrices,
                          Alignment([DNA('AWG')]),
                          Alignment([DNA('ACGT')]), 5, 2, m)

    def test_traceback(self):
        score_m = [[0, -5, -7, -9],
                   [-5, 2, -3, -5],
                   [-7, -3, 4, -1],
                   [-9, -5, -1, 6],
                   [-11, -7, -3, 1]]
        score_m = np.array(score_m)
        tback_m = [[0, 3, 3, 3],
                   [2, 1, 3, 3],
                   [2, 2, 1, 3],
                   [2, 2, 2, 1],
                   [2, 2, 2, 2]]
        tback_m = np.array(tback_m)
        # start at bottom-right
        expected = ([BiologicalSequence("ACG-")],
                    [BiologicalSequence("ACGT")], 1, 0, 0)
        actual = _traceback(tback_m, score_m, Alignment([DNA('ACG')]),
                            Alignment([DNA('ACGT')]), 4, 3)
        self.assertEqual(actual, expected)

        # four sequences in two alignments
        score_m = [[0, -5, -7, -9],
                   [-5, 2, -3, -5],
                   [-7, -3, 4, -1],
                   [-9, -5, -1, 6],
                   [-11, -7, -3, 1]]
        score_m = np.array(score_m)
        tback_m = [[0, 3, 3, 3],
                   [2, 1, 3, 3],
                   [2, 2, 1, 3],
                   [2, 2, 2, 1],
                   [2, 2, 2, 2]]
        tback_m = np.array(tback_m)
        # start at bottom-right
        expected = ([BiologicalSequence("ACG-"), BiologicalSequence("ACG-")],
                    [BiologicalSequence("ACGT"), BiologicalSequence("ACGT")],
                    1, 0, 0)
        actual = _traceback(tback_m, score_m,
                            Alignment([DNA('ACG', 's1'), DNA('ACG', 's2')]),
                            Alignment([DNA('ACGT', 's3'), DNA('ACGT', 's4')]),
                            4, 3)
        self.assertEqual(actual, expected)

        # start at highest-score
        expected = ([BiologicalSequence("ACG")],
                    [BiologicalSequence("ACG")], 6, 0, 0)
        actual = _traceback(tback_m, score_m, Alignment([DNA('ACG')]),
                            Alignment([DNA('ACGT')]), 3, 3)
        self.assertEqual(actual, expected)

        # terminate traceback before top-right
        tback_m = [[0, 3, 3, 3],
                   [2, 1, 3, 3],
                   [2, 2, 0, 3],
                   [2, 2, 2, 1],
                   [2, 2, 2, 2]]
        tback_m = np.array(tback_m)
        expected = ("G", "G", 6, 2, 2)
        expected = ([BiologicalSequence("G")],
                    [BiologicalSequence("G")], 6, 2, 2)
        actual = _traceback(tback_m, score_m, Alignment([DNA('ACG')]),
                            Alignment([DNA('ACGT')]), 3, 3)
        self.assertEqual(actual, expected)

    def test_get_seq_id(self):
        self.assertEqual(_get_seq_id("AAA", "hello"), "hello")
        self.assertEqual(_get_seq_id(DNA("AAA"), "hello"), "hello")
        self.assertEqual(_get_seq_id(DNA("AAA", "s1"), "hello"), "s1")

    def test_first_largest(self):
        l = [(5, 'a'), (5, 'b'), (5, 'c')]
        self.assertEqual(_first_largest(l), (5, 'a'))
        l = [(5, 'c'), (5, 'b'), (5, 'a')]
        self.assertEqual(_first_largest(l), (5, 'c'))
        l = [(5, 'c'), (6, 'b'), (5, 'a')]
        self.assertEqual(_first_largest(l), (6, 'b'))
        # works for more than three entries
        l = [(5, 'c'), (6, 'b'), (5, 'a'), (7, 'd')]
        self.assertEqual(_first_largest(l), (7, 'd'))
        # Note that max([(5, 'a'), (5, 'c')]) == max([(5, 'c'), (5, 'a')])
        # but for the purposes needed here, we want the max to be the same
        # regardless of what the second item in the tuple is.

if __name__ == "__main__":
    main()
