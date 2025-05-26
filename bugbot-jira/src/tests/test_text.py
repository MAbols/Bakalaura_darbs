from bugbot.preprocess import clean_freeform, split_sentences


def test_cleaner_basic():
    raw = "  OMG 😱 Page CRASHED!!!   "
    assert clean_freeform(raw) == "omg :face_screaming_in_fear: page crashed!!!"


def test_sentence_split():
    txt = "Step 1: open app. Step 2: click ✅."
    assert split_sentences(txt) == ["Step 1: open app.", "Step 2: click ✅."]
