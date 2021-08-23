import logging


def setup_log():
    logging.basicConfig(
        level=logging.INFO,
        datefmt="%d.%m.%y %I:%M:%S %p",
        format="[ %(asctime)s ]  %(name)-11s  |  %(levelname)-7s  |  %(message)s",
    )
    for name, lvl in (
        ("pyrogram", "WARNING"),
        ("pyrogram.parser.html", "ERROR"),
        ("pyrogram.session.session", "ERROR"),
    ):
        logging.getLogger(name).setLevel(getattr(logging, lvl))
