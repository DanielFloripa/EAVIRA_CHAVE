#!/usr/bin/env python
# -*- coding: utf-8 -*-

import peewee
from model import Author, Book


if __name__ == '__main__':
    try:
        Author.create_table()
    except peewee.OperationalError:
        print 'Tabela Author ja existe'

    try:
        Book.create_table()
    except peewee.OperationalError:
        print 'Tabela Book ja existe!'


# Inserimos um autor de nome "H. G. Wells" na tabela 'Author'
author_1 = Author.create(name='H. G. Wells')

book_1 = {
    'title': 'A Maquina do Tempo',
    'author': author_1,
}

book_2 = {
    'title': 'Guerra dos Mundos',
    'author': author_1,
}

# Inserimos um autor de nome "Julio Verne" na tabela 'Author'
author_2 = Author.create(name='Julio Verne')

book_3 = {
    'title': 'Volta ao Mundo em 80 Dias',
    'author': author_2,
}

book_4 = {
    'title': 'Vinte Mil Leguas Submarinas',
    'author': author_2,
}

books = [book_1, book_2, book_3, book_4]

#Book.create()
# Inserimos os quatro livros na tabela 'Book'
Book.insert_many(books).execute()

#####################################################################
# Consultando dados no banco
book = Book.get(Book.title == "Volta ao Mundo em 80 Dias").get()
print "btitle:", book.title

books = Book.select().join(Author).where(Author.name=='H. G. Wells')

# Exibe a quantidade de registros que corresponde a nossa pesquisa
print books.count()

for book in books:
    print "btitle:", book.title

####################################################################
# Alterando dados no banco
new_author = Author.get(Author.name == 'Julio Verne')
book = Book.get(Book.title=="Vinte Mil Leguas Submarinas")

# Alteramos o autor do livro
book.author = new_author

# Salvamos a alteração no banco
book.save()

exit()

####################################################################
# Deletando dados do banco

# Buscamos o livro que desejamos excluir do banco
book = Book.get(Book.title=="Guerra dos Mundos")

# Excluimos o livro do banco
book.delete_instance()
