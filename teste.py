cpf = "%08d" % 49087779

print(cpf)

result = '%s.%s.%s-%s' % (cpf[:2], cpf[2:5], cpf[5:8], cpf[8:])

print(result)