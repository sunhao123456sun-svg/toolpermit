from importlib.resources import files


def index_html() -> str:
    return files("toolpermit_ui_spike.assets").joinpath("index.html").read_text(encoding="utf-8")

