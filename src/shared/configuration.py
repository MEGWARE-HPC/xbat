logger_name = "root"
app_name = ""
build = "dev"
demo = False

config = {}


def set_config(c):
    global config
    config = c


def get_config():
    return config


def set_logger(name):
    global logger_name
    logger_name = name


def get_logger():
    return logger_name


def set_app(name):
    global app_name
    app_name = name


def get_app():
    return app_name


def set_build(b):
    global build
    build = b


def get_build():
    return build


def set_demo(d):
    global demo
    demo = d


def get_demo():
    return demo
