from MySQL import db

banco = db({'host':"neosed.net",    # your host, usually localhost
            'user':"username",         # your username
            'passwd':"password",  # your password
            'db':"neosed"})


teste = banco.executarConsulta("select * from aluno")

for item in teste:
    print(item['ra'], item['nome'], item['nascimento'])  