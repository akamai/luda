from src.clustering import swalign


def test_align():
    match = 1
    mismatch = -1
    scoring = swalign.NucleotideScoringMatrix(match, mismatch)

    sw = swalign.LocalAlignment(scoring, gap_penalty=-1)
    assert sw.align('/mal/xxx/a.php', '/mal/a.php') == 6
