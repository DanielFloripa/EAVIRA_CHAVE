import time

count = 0
start = time.time()
while count < 24531071:
    count = count + 1

elapsed = time.time() - start
print elapsed,count

# O resultado mostra um acrescimo de 2,23 segundos
# >> 2.23299884796 24531071