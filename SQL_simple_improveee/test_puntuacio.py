from backendHistory import Backend 
import pdfplumber
from sacrebleu.metrics import BLEU

b = Backend()
bleu = BLEU() 

with open("./test_preguntes.txt", "r") as test_pregs:  
    tPreguntes = test_pregs.read()

with open("./test_respostesCorrectes.txt", "r") as test_rc:  
    tRespostaCorrecte = test_rc.read()

preguntes = tPreguntes.split("\n\n")
respostesCorrectes = tRespostaCorrecte.split("\n\n")

respostes = []
mitja = 0

for preg in preguntes:
    resp = b.preguntaSQL(preg)
    #print(resp + "\n\n\n")
    respostes.append(resp)
    
for i in range(len(respostes)):
    a=respostes[i]
    b=[respostesCorrectes[i]]
    nota = bleu.sentence_score(a, b)
    nota = str(nota).split(" ")
    print("La nota de la pregunta número " + str(i) + " tiene una nota de similitud de:" + nota[2] + "%\n")
    mitja += float(nota[2])

mitja = mitja/len(respostes)
print("\nResultat final: " +str(mitja)+"%\n\n")
   
with open("./test_compare.txt", "w") as test_c:    
    for i in range(len(preguntes)):    
        test_c.write(str(i) + ". Pregunta: " + preguntes[i] + "\nResposta: \n" + respostes[i] + "\n\nResposta Correcte:\n" + respostesCorrectes[i] + "\n\n\n")
