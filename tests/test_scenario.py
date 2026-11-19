"""Szenario: Erzeuger (Bereiche, Reproduzierbarkeit), Handeingabe (Fehlertexte) und die Kopie des Zufallsgenerators."""

import ast
from pathlib import Path

import numpy as np
import pytest

import mdx_constants as C
import mdx_scenario as S
from mdx_rng import SplitMix64, uniform_block

ROOT = Path(__file__).resolve().parent.parent
RNG_SOURCE = ("ab-test-demo", "abt_rng.py")


def test_rng_copy_is_verbatim_apart_from_the_header():
    folder, original = RNG_SOURCE
    source = ROOT.parent / folder / original
    mine = (ROOT / "mdx_rng.py").read_text(encoding="utf-8").splitlines()
    assert mine[0].startswith(f"# Wörtliche Kopie von {folder}/{original}")
    if not source.exists():
        pytest.skip("Original liegt nicht im Portfolio-Ordner")
    assert mine[1:] == source.read_text(encoding="utf-8").splitlines(), "die Kopie weicht vom Original ab: Änderungen gehören ins Original, danach neu kopieren"


def test_copied_generator_has_the_documented_stream():
    """SplitMix64 mit Seed 0: die bekannten ersten Werte der Konvention (Vigna)."""
    rng = SplitMix64(0)
    assert [rng.next() for _ in range(3)] == [0xE220A8397B1DCDAF, 0x6E789E6AA1B965F4, 0x06C45D188009454F]


def test_block_equals_the_scalar_stream():
    for seed in (0, 1, 35, 2 ** 63 + 5):
        rng = SplitMix64(seed)
        assert np.array_equal(uniform_block(seed, 100), np.array([rng.uniform() for _ in range(100)]))


def test_rng_module_has_no_other_imports_than_numpy_and_math():
    tree = ast.parse((ROOT / "mdx_rng.py").read_text(encoding="utf-8"))
    names = {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    assert names == {"math", "numpy"}


def test_no_module_uses_the_random_modules_of_the_standard_library_or_numpy():
    for path in ROOT.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(a.name != "random" for a in node.names), path.name
            if isinstance(node, ast.ImportFrom):
                assert node.module != "random", path.name
            if isinstance(node, ast.Attribute) and node.attr == "random" and isinstance(node.value, ast.Name) and node.value.id in ("np", "numpy"):
                raise AssertionError(f"numpy.random in {path.name}")


def test_generators_are_deterministic_and_inside_their_ranges():
    for gen in S.generator_keys():
        a = S.make_weights(gen, 12, 35, 3)
        assert a == S.make_weights(gen, 12, 35, 3) and len(a) == 12 and min(a) >= 1
        assert a != S.make_weights(gen, 12, 36, 3) and a != S.make_weights(gen, 12, 35, 4)
        assert S.make_weights(gen, 12, 35, 3, which=1) != a
    for seed in range(20):
        assert all(8 <= x <= 12 for x in S.make_weights("equal", 30, seed))
        assert all(1 <= x <= 20 for x in S.make_weights("uniform", 30, seed))
        assert set(S.make_weights("stepped", 30, seed)) <= {3, 10, 30}


def test_every_generator_value_of_the_stepped_generator_occurs():
    assert set(S.make_weights("stepped", 200, 1)) == {3, 10, 30}


def test_unknown_generator_is_an_error():
    with pytest.raises(ValueError):
        S.make_weights("gibt-es-nicht", 5, 1)


def test_parse_weights_accepts_separators_and_reports_every_kind_of_error():
    assert S.parse_weights("3, 2;1  1") == ((3, 2, 1, 1), None)
    assert S.parse_weights(" 5 5 ")[0] == (5, 5)
    for bad, fragment in (("", "mindestens zwei"), ("   ", "mindestens zwei"), ("3", "Es ist 1 Gewicht angegeben"), ("3, x", "„x“ ist keine ganze Zahl"), ("3, -2", "keine ganze Zahl"),
                          ("3, 2.5", "keine ganze Zahl"), ("3, 0", "mindestens 1"), (", ".join(["1"] * 61), "61 Gewichte"), ("100000, 1", "höchstens 100.000"), ("1," * 2000, "zu lang")):
        weights, error = S.parse_weights(bad)
        assert weights is None and fragment in error, (bad[:20], error)
    assert S.parse_weights(None)[0] is None
    assert S.parse_weights("99999, 1")[0] == (99999, 1)         # Summe genau 100.000: erlaubt
    assert S.parse_weights(", ".join(["1"] * C.N_MAX))[0] == (1,) * C.N_MAX and S.parse_weights("1, 1")[0] == (1, 1)


def test_generators_follow_the_formulas_stated_in_the_readme():
    """README, Methodik: Pareto ⌊3·(1−u)^(−1/α)⌋, lognormal ⌊exp(2 + z)⌋ mit z nach Box–Muller, je mindestens 1; fast gleich 8 bis 12, gleichverteilt 1 bis 20, gestuft 3/10/30."""
    import math

    n, seed = 9, 3
    for gen, alpha in (("pareto12", 1.2), ("pareto25", 2.5)):
        rng = S.stream(gen, n, seed)
        expected = tuple(max(1, math.floor(3 * (1.0 - rng.uniform()) ** (-1.0 / alpha))) for _ in range(n))
        assert S.make_weights(gen, n, seed) == expected
    rng = S.stream("lognormal", n, seed)
    expected = []
    for _ in range(n):
        u1, u2 = 1.0 - rng.uniform(), rng.uniform()
        z = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
        expected.append(max(1, math.floor(math.exp(2.0 + z))))
    assert S.make_weights("lognormal", n, seed) == tuple(expected)
    many = [w for s in range(20) for w in S.make_weights("equal", 10, s)]
    assert min(many) == 8 and max(many) == 12
    many = [w for s in range(20) for w in S.make_weights("uniform", 10, s)]
    assert min(many) >= 1 and max(many) <= 20
    assert {w for s in range(20) for w in S.make_weights("stepped", 10, s)} == {3, 10, 30}
