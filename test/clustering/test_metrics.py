from src.clustering.metrics import get_sw_distance
from src.clustering.metrics import longest_sub


def test_get_sw_distance():
    distance = get_sw_distance(match=1, mismatch=-1, gap_penalty=-1)
    assert distance('/mal/xxx/a.php', '/mal/a.php') == 6


def test_longest_sub():
    a = 'myurl/abigfolder/home'
    b = 'abigfolder/akamai'
    assert longest_sub(a, b) == 1
