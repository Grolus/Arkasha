from parse_utils import split_with_ignoring

def test_split_with_ignoring():
    cases = [
        ('aa', ['aa']),
        ('aa, aaa', ['aa', ' aaa']),
        ('aa,,a,a', ['aa', '', 'a', 'a']),
        ('aa(aa,aaa,,aa),a,a', ['aa(aa,aaa,,aa)', 'a', 'a']),
        ('aa(a,a,a,a),a,a,[asss,s],a', ['aa(a,a,a,a)', 'a', 'a', '[asss,s]', 'a'])
    ]
    for text, result in cases:
        assert result == split_with_ignoring(text, ',', '()[]')