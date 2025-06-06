"""src/tests/test_streamlit_app.py"""

from streamlit.testing.v1 import AppTest


def test_title():
    at = AppTest.from_file("../streamlit_app.py").run()
    at.run()
    assert not at.exception
    assert at.title.values[0] == "Example streamlit app. Hello!"


def test_page():
    at = AppTest.from_file("../pages/my_page.py").run()
    at.run()
    assert not at.exception
    assert at.title.values[0] == "Example page"
