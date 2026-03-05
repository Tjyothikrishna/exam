"""Lightweight local fallback for Flask-SQLAlchemy in restricted environments."""


class _Type:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


class Integer(_Type):
    pass


class String(_Type):
    pass


class Text(_Type):
    pass


class DateTime(_Type):
    pass


class Float(_Type):
    pass


class Column:
    def __init__(self, _type=None, *args, **kwargs):
        self.type = _type
        self.args = args
        self.kwargs = kwargs


class ForeignKey:
    def __init__(self, target):
        self.target = target


class SQLAlchemy:
    Integer = Integer
    String = String
    Text = Text
    DateTime = DateTime
    Float = Float
    Column = Column
    ForeignKey = ForeignKey

    class Model:
        pass

    def __init__(self, app=None):
        self.app = app

    def init_app(self, app):
        self.app = app

    def create_all(self):
        return None

    def relationship(self, *args, **kwargs):
        return None
