from smoothing import LavaSmoother


def test_smoothing_triggers_on_k():
    sm = LavaSmoother(k_consecutive=3)
    triggered = []
    for i in range(5):
        sm.next_frame()
        trig = sm.observe(1, 'left', 2, 3, True)
        triggered.append(trig)
    assert triggered == [False, False, True, False, False]


def test_smoothing_resets_on_non_lava():
    sm = LavaSmoother(k_consecutive=2)
    sm.next_frame(); assert sm.observe(1, 'left', 1, 1, True) is False
    sm.next_frame(); assert sm.observe(1, 'left', 1, 1, False) is False
    sm.next_frame(); assert sm.observe(1, 'left', 1, 1, True) is False
    sm.next_frame(); assert sm.observe(1, 'left', 1, 1, True) is True 