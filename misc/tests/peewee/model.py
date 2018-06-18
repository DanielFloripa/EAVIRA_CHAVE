#!/usr/bin/env python
# -*- coding: utf-8 -*-

import peewee

db = peewee.SqliteDatabase('codigo_avulso.db')

class Author(peewee.Model):
    """
    Classe que representa a tabela Author
    """

    # A tabela possui apenas o campo 'name', que
    # receberá o nome do autor
    name = peewee.CharField()

    class Meta:
        # Indica em qual banco de dados a tabela
        # 'author' sera criada (obrigatorio). Neste caso,
        # utilizamos o banco 'codigo_avulso.db' criado anteriormente.
        database = db


class Book(peewee.Model):
    """
    Classe que representa a tabela Book
    """

    # A tabela possui apenas o campo 'title', que
    # receberá o nome do livro
    title = peewee.CharField()

    # Chave estrangeira para a tabela Author
    author = peewee.ForeignKeyField(Author)

    class Meta:
        # Indica em qual banco de dados a tabela
        # 'author' sera criada (obrigatorio). Neste caso,
        # utilizamos o banco 'codigo_avulso.db' criado anteriormente.
        database = db
