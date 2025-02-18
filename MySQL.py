import mysql.connector

class db:
    def __init__(self, credenciais):
        self.cred = credenciais

    def executarConsultaVetor(self, sql):
        database = mysql.connector.connect(host=self.cred['host'],
                                   user=self.cred['user'],
                                   passwd=self.cred['passwd'],
                                   db=self.cred['db'])
        
        cur = database.cursor()

        cur.execute(sql)

        result = [item[0] for item in cur.fetchall()]

        database.close()

        return result        

    def executarConsulta(self, sql):
        database = mysql.connector.connect(host=self.cred['host'],
                                   user=self.cred['user'],
                                   passwd=self.cred['passwd'],
                                   db=self.cred['db'])
        
        cur = database.cursor(dictionary=True)

        cur.execute(sql)

        result = [dict(row) for row in cur.fetchall()]
        
        #for row in cur.fetchall():
            #print(row)

        database.close()

        return result
    
    def inserirNovaTurma(self, turma):   
        
        sql = "INSERT INTO turma VALUES(" + str(turma.values()).replace("'", '').replace('"', "'")[13:-2] + ")"

        try:
            database = mysql.connector.connect(host=self.cred['host'], user=self.cred['user'], passwd=self.cred['passwd'], db=self.cred['db'])
        
            cur = database.cursor()
            cur.execute(sql)
            database.commit()

            database.close()
            return True
        except Exception as error:
            print("An exception occurred:", error) # An exception occurred: division by zero
            return False
        
    def inserirNovaTurmaIf(self, turma, vinculos):   
        
        sql = "INSERT INTO turma_if VALUES(" + str(turma.values()).replace("'", '').replace('"', "'")[13:-2] + ")"

        try:
            database = mysql.connector.connect(host=self.cred['host'], user=self.cred['user'], passwd=self.cred['passwd'], db=self.cred['db'])
        
            cur = database.cursor()

            cur.execute('DELETE FROM vinculo_if WHERE num_classe_if = %s' % turma['num_classe'])
            #database.commit()
            cur.execute(sql)

            for item in vinculos:
                cur.execute('INSERT INTO vinculo_if VALUES(%s, %s)' % (turma['num_classe'], item))

            database.commit()
            database.close()
            return True
        except Exception as error:
            print("An exception occurred:", error) # An exception occurred: division by zero
            return False        
        
    def alterarTurma(self, turma):
        sql = 'UPDATE TURMA SET '

        for key, value in turma.items():
            if (key != 'num_classe'):
                sql += '%s = %s, ' % (key, value)

        sql = sql[:-2] + ' WHERE num_classe = %s' % turma['num_classe']
        
        try:
            database = mysql.connector.connect(host=self.cred['host'], user=self.cred['user'], passwd=self.cred['passwd'], db=self.cred['db'])
        
            cur = database.cursor()
            cur.execute(sql)
            database.commit()

            database.close()
            return True
        except Exception as error:
            print("An exception occurred:", error) # An exception occurred: division by zero
            return False
        
    def alterarTurmaIf(self, turma, vinculos):
        sql = 'UPDATE turma_if SET '

        for key, value in turma.items():
            if (key != 'num_classe'):
                sql += '%s = %s, ' % (key, value)

        sql = sql[:-2] + ' WHERE num_classe = %s' % turma['num_classe']
        
        try:
            database = mysql.connector.connect(host=self.cred['host'], user=self.cred['user'], passwd=self.cred['passwd'], db=self.cred['db'])
        
            cur = database.cursor()

            cur.execute('DELETE FROM vinculo_if WHERE num_classe_if = %s' % turma['num_classe'])
            #database.commit()
            cur.execute(sql)

            for item in vinculos:
                cur.execute('INSERT INTO vinculo_if VALUES(%s, %s)' % (turma['num_classe'], item))

            database.commit()
            database.close()
            return True
        except Exception as error:
            print("An exception occurred:", error) # An exception occurred: division by zero
            return False        
        
    def salvarVinculoProfs(self, info):
        try:
            database = mysql.connector.connect(host=self.cred['host'], user=self.cred['user'], passwd=self.cred['passwd'], db=self.cred['db'])
            cur = database.cursor()

            cur.execute('DELETE FROM vinculo_turma_prof WHERE id_turma = %s' % info['num_classe'])
            database.commit()

            for item in info['profs']:
                sql = "INSERT INTO vinculo_turma_prof VALUES(%s, %s)" % (info['num_classe'], item)
                cur.execute(sql)


            database.commit()
            database.close()
            return True
        except Exception as error:
            print("An exception occurred:", error) # An exception occurred: division by zero
            return False        

    def salvarMedias(self, info):
        try:
            database = mysql.connector.connect(host=self.cred['host'], user=self.cred['user'], passwd=self.cred['passwd'], db=self.cred['db'])
            cur = database.cursor()


            cur.execute('DELETE FROM conceito_final WHERE num_classe = %s' % info['num_classe'])
            database.commit()            

            for item in info['notas']:
                sql = "INSERT INTO conceito_final VALUES(%s, %s, %s, '%s')" % (info['num_classe'], item['ra'], item['disc'], item['M'])
                cur.execute(sql)

            database.commit()
            database.close()
            return True
        except Exception as error:
            print("An exception occurred:", error) # An exception occurred: division by zero
            return False          

    def salvarNotas(self, info):
        try:
            database = mysql.connector.connect(host=self.cred['host'], user=self.cred['user'], passwd=self.cred['passwd'], db=self.cred['db'])
            cur = database.cursor()

            cur.execute('DELETE FROM vinculo_prof_disc WHERE num_classe = %s and bimestre = %s' % (info['num_classe'], info['bim']))
            database.commit()

            for item in info['vinculo']:
                sql = "INSERT INTO vinculo_prof_disc VALUES(%s, %s, %s, %s, %s)" % (info['num_classe'], item['prof'], info['bim'], item['disc'], item['AD'])
                cur.execute(sql)


            cur.execute('DELETE FROM notas WHERE num_classe = %s and bimestre = %s' % (info['num_classe'], info['bim']))
            database.commit()            

            for item in info['notas']:
                sql = "INSERT INTO notas VALUES(%s, %s, %s, %s, '%s', %s, %s)" % (info['bim'], info['num_classe'], item['ra'], item['disc'], item['N'], item['F'], item['AC'])
                cur.execute(sql)

            database.commit()
            database.close()
            return True
        except Exception as error:
            print("An exception occurred:", error) # An exception occurred: division by zero
            return False  

    def importarDadosTurma(self, turma):

        try:
            database = mysql.connector.connect(host=self.cred['host'], user=self.cred['user'], passwd=self.cred['passwd'], db=self.cred['db'])
            cur = database.cursor()

            if turma[0]['serie'] == "0":
                #print('to aqui')
                cur.execute('DELETE FROM vinculo_alunos_if WHERE num_classe_if = %s' % turma[0]['num_classe'])
                database.commit()

                for item in turma:
                    sql = "INSERT INTO aluno(ra, digito_ra, rm, nome, nascimento, sexo, rg, cpf) VALUES(%s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE rm=%s, nome=%s, nascimento=%s, sexo=%s, rg=%s, cpf=%s" % (item['ra'], item['digito'], item['rm'], item['nome'], item['nascimento'], item['sexo'], item['rg'], item['cpf'].replace(".", "").replace("-", ""), item['rm'], item['nome'], item['nascimento'], item['sexo'], item['rg'], item['cpf'].replace(".", "").replace("-", ""))                    
                    cur.execute(sql)

                    sql = "INSERT INTO vinculo_alunos_if VALUES(%s, %s, %s, %s, %s, %s)" % (item['ra'], item['num_classe'], item['num_chamada'], item['matricula'], item['fim_mat'], item['situacao'])
                    cur.execute(sql)

            else:
                cur.execute('DELETE FROM vinculo_alunos_turmas WHERE num_classe = %s' % turma[0]['num_classe'])
                database.commit()

                for item in turma:
                    sql = "INSERT INTO aluno(ra, digito_ra, rm, nome, nascimento, sexo, rg, cpf) VALUES(%s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE rm=%s, nome=%s, nascimento=%s, sexo=%s, rg=%s, cpf=%s" % (item['ra'], item['digito'], item['rm'], item['nome'], item['nascimento'], item['sexo'], item['rg'], item['cpf'].replace(".", "").replace("-", ""), item['rm'], item['nome'], item['nascimento'], item['sexo'], item['rg'], item['cpf'].replace(".", "").replace("-", ""))                
                    cur.execute(sql)

                    sql = "INSERT INTO vinculo_alunos_turmas VALUES(%s, %s, %s, %s, %s, %s, %s)" % (item['ra'], item['num_classe'], item['num_chamada'], item['serie'], item['matricula'], item['fim_mat'], item['situacao'])
                    cur.execute(sql)

            database.commit()
            database.close()
            return True
        except Exception as error:
            print("An exception occurred:", error) # An exception occurred: division by zero
            return False


    def executeBasicSQL(self, sql):
        try:
            database = mysql.connector.connect(host=self.cred['host'], user=self.cred['user'], passwd=self.cred['passwd'], db=self.cred['db'])
            cur = database.cursor()
            cur.execute(sql)
            database.commit()
            database.close()
            return True

        except Exception as error:
            print("An exception occurred:", error) # An exception occurred: division by zero
            return False     


    def insertOrUpdate(self, dados, tabela):
            
        try:
            database = mysql.connector.connect(host=self.cred['host'], user=self.cred['user'], passwd=self.cred['passwd'], db=self.cred['db'])
            cur = database.cursor()

            keys = ""
            data = ""
            update = ""

            for item in dados:
                keys += "%s, " % item
                data += "%s, " % dados[item]

                if item != 'codigo_disciplina':
                    update += "%s=%s, " % (item, dados[item])

            sql = "INSERT INTO " + tabela + " (" + keys[:-2] + ") VALUES(" + data[:-2] + ") ON DUPLICATE KEY UPDATE " + update[:-2]

            print(sql)

            cur.execute(sql)
            database.commit()
            database.close()

            return True

        except Exception as error:
            print("An exception occurred:", error) # An exception occurred: division by zero
            return False            


    def salvarDificuldades(self, lista):
        
        num_classe = lista[0]['num_classe']
        bimestre = lista[0]['bimestre']

        try:
            database = mysql.connector.connect(host=self.cred['host'], user=self.cred['user'], passwd=self.cred['passwd'], db=self.cred['db'])
            cur = database.cursor()        

            cur.execute('DELETE FROM alunos_dificuldades WHERE num_classe = %s and bimestre = %s' % (num_classe, bimestre))
            database.commit()

            for item in lista:
                cur.execute('INSERT INTO alunos_dificuldades VALUES(%s, %s, %s, %s)' % (item['ra'], item['item'], item['bimestre'], item['num_classe']))

            database.commit()

            return True

        except Exception as error:
            print("An exception occurred:", error) # An exception occurred: division by zero
            return False            
        

    def inserirEvento(self, data_inicial, data_final, evento, descricao, instancia):
        try:

            if descricao == '':
                descricao = 'null'
            else:
                descricao = "'" + descricao + "'"

            database = mysql.connector.connect(host=self.cred['host'], user=self.cred['user'], passwd=self.cred['passwd'], db=self.cred['db'])
            cur = database.cursor()        

            # remover dados conflitantes
            cur.execute('SET SQL_SAFE_UPDATES = 0')
            cur.execute("DELETE FROM eventos_calendario WHERE (data_inicial BETWEEN '%s' AND '%s') and instancia_calendario = %s" % (data_inicial, data_final, instancia))
            cur.execute("DELETE FROM eventos_calendario WHERE (data_final BETWEEN '%s' AND '%s') and instancia_calendario = %s" % (data_inicial, data_final, instancia))
            print("DELETE FROM eventos_calendario WHERE (data_final BETWEEN '%s' AND '%s') and instancia_calendario = %s" % (data_inicial, data_final, instancia))
            cur.execute('SET SQL_SAFE_UPDATES = 1;')
            cur.execute("INSERT INTO eventos_calendario VALUES('%s', '%s', %s, %s, %s)" % (data_inicial, data_final, evento, descricao, instancia))

            database.commit()

            return True

        except Exception as error:
            print("An exception occurred:", error) # An exception occurred: division by zero
            return False
        

    def inserirQuadro(self, cpf, quadro, outras_ue):
        try:

            database = mysql.connector.connect(host=self.cred['host'], user=self.cred['user'], passwd=self.cred['passwd'], db=self.cred['db'])
            cur = database.cursor()        

            print("DELETE FROM horario_livro_ponto WHERE cpf_professor = %s" % cpf)

            # remover dados conflitantes
            cur.execute('SET SQL_SAFE_UPDATES = 0')
            cur.execute("DELETE FROM horario_livro_ponto WHERE cpf_professor = %s" % cpf)
            cur.execute('SET SQL_SAFE_UPDATES = 1')


            for item in quadro:

                seg = "'" + item['seg'] + "'" if item['seg'] != '' else 'null'
                ter = "'" + item['ter'] + "'" if item['ter'] != '' else 'null'
                qua = "'" + item['qua'] + "'" if item['qua'] != '' else 'null'
                qui = "'" + item['qui'] + "'" if item['qui'] != '' else 'null'
                sex = "'" + item['sex'] + "'" if item['sex'] != '' else 'null'
                sab = "'" + item['sab'] + "'" if item['sab'] != '' else 'null'
                dom = "'" + item['dom'] + "'" if item['dom'] != '' else 'null'

                cur.execute("INSERT INTO horario_livro_ponto VALUES(%s, %s, '%s', '%s', %s, %s, %s, %s, %s, %s, %s)" % (cpf, item['periodo'], item['inicio'], item['fim'], seg, ter, qua, qui, sex, sab, dom))


            if outras_ue:
                # remover dados conflitantes
                cur.execute('SET SQL_SAFE_UPDATES = 0')
                cur.execute("DELETE FROM aulas_outra_ue_livro_ponto WHERE cpf_professor = %s" % cpf)
                cur.execute('SET SQL_SAFE_UPDATES = 1')

                for key in outras_ue:
                    cur.execute("INSERT INTO aulas_outra_ue_livro_ponto VALUES(%s, '%s', %s)" % (cpf, key, outras_ue[key]))

            database.commit()

            return True

        except Exception as error:
            print("An exception occurred:", error) # An exception occurred: division by zero
            return False
        

    def inserirAfastamentos(self, cpf, lista):
        try:

            database = mysql.connector.connect(host=self.cred['host'], user=self.cred['user'], passwd=self.cred['passwd'], db=self.cred['db'])
            cur = database.cursor()        

            # remover dados conflitantes
            cur.execute('SET SQL_SAFE_UPDATES = 0')
            cur.execute("DELETE FROM afastamentos_ponto_adm WHERE cpf = %s" % cpf)
            cur.execute('SET SQL_SAFE_UPDATES = 1')


            for item in lista:
                cur.execute("INSERT INTO afastamentos_ponto_adm VALUES(%s, '%s', '%s', '%s')" % (cpf, item['inicio'], item['fim'], item['desc']))

            database.commit()

            return True

        except Exception as error:
            print("An exception occurred:", error) # An exception occurred: division by zero
            return False 

    def alterarMatriz(self, lista):
        num_classe = lista[0]['num_classe']
        
        try:

            database = mysql.connector.connect(host=self.cred['host'], user=self.cred['user'], passwd=self.cred['passwd'], db=self.cred['db'])
            cur = database.cursor()        

            # remover dados conflitantes
            cur.execute('SET SQL_SAFE_UPDATES = 0')
            cur.execute("DELETE FROM matriz_curricular WHERE num_classe = %s" % num_classe)
            cur.execute('SET SQL_SAFE_UPDATES = 1')


            for item in lista:
                cur.execute(f"INSERT INTO matriz_curricular VALUES({item['num_classe']}, {item['disc']}, {item['area']}, {item['tipo']}, {item['qtd']}, {item['minutos']})")

            database.commit()

            return True

        except Exception as error:
            print("An exception occurred:", error) # An exception occurred: division by zero
            return False
        
    def alterarGrade(self, num_classe, lista):

        print(num_classe)
        print(lista)

        try:

            database = mysql.connector.connect(host=self.cred['host'], user=self.cred['user'], passwd=self.cred['passwd'], db=self.cred['db'])
            cur = database.cursor()        

            # remover dados conflitantes
            cur.execute('SET SQL_SAFE_UPDATES = 0')
            cur.execute("DELETE FROM grade WHERE num_classe = %s" % num_classe)
            cur.execute('SET SQL_SAFE_UPDATES = 1')

            pos = 1

            for item in lista:
                cur.execute(f"INSERT INTO grade VALUES({num_classe}, {pos}, 2, {item['Seg']})")
                cur.execute(f"INSERT INTO grade VALUES({num_classe}, {pos}, 3, {item['Ter']})")
                cur.execute(f"INSERT INTO grade VALUES({num_classe}, {pos}, 4, {item['Qua']})")
                cur.execute(f"INSERT INTO grade VALUES({num_classe}, {pos}, 5, {item['Qui']})")
                cur.execute(f"INSERT INTO grade VALUES({num_classe}, {pos}, 6, {item['Sex']})")
                pos += 1

            database.commit()

            return True

        except Exception as error:
            print("An exception occurred:", error) # An exception occurred: division by zero
            return False