def test_spike_above_20_percent():
    cost_yesterday = 10.0
    cost_today = 13.0
    if cost_yesterday == 0:
        change_pct = 0
    else:
        change_pct = ((cost_today - cost_yesterday) / cost_yesterday) * 100
    assert change_pct > 20

def test_no_spike_under_20_percent():
    cost_yesterday = 10.0
    cost_today = 10.5
    if cost_yesterday == 0:
        change_pct = 0
    else:
        change_pct = ((cost_today - cost_yesterday) / cost_yesterday) * 100
    assert change_pct < 20

def test_zero_yesterday_no_crash():
    cost_yesterday = 0
    cost_today = 5.0
    if cost_yesterday == 0:
        change_pct = 0
    else:
        change_pct = ((cost_today - cost_yesterday) / cost_yesterday) * 100
    assert change_pct == 0