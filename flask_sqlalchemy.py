"""Lightweight local fallback for Flask-SQLAlchemy in restricted environments."""

from flask import abort


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

    def desc(self):
        return self


class ForeignKey:
    def __init__(self, target):
        self.target = target


class _Query:
    def __init__(self, model_cls):
        self.model_cls = model_cls

    def filter_by(self, **kwargs):
        return self

    def count(self):
        return 0

    def all(self):
        return []

    def first(self):
        return None

    def order_by(self, *args, **kwargs):
        return self

    def limit(self, n):
        return self

    def get_or_404(self, _id):
        abort(404)


class _Session:
    def add(self, obj):
        return None

    def delete(self, obj):
        return None

    def commit(self):
        return None


class _ModelBase:
    query = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.query = _Query(cls)

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class SQLAlchemy:
    Integer = Integer
    String = String
    Text = Text
    DateTime = DateTime
    Float = Float
    Column = Column
    ForeignKey = ForeignKey
    Model = _ModelBase

    def __init__(self, app=None):
        self.app = app
        self.session = _Session()

    def init_app(self, app):
        self.app = app

    def create_all(self):
        return None

    def relationship(self, *args, **kwargs):
        return []
