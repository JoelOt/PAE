from backendHistory import Backend 
import pdfplumber


b = Backend()

with open("./test_preguntes.txt", "r") as test_pregs:  
    tPreguntes = test_pregs.read()

preguntes = tPreguntes.split("\n\n")


respostes = []
mitja = 0

for preg in preguntes:
    resp = b.preguntaSQL(preg)
    #print(resp + "\n\n\n")
    respostes.append(resp)
       
with open("./test_resultat.txt", "w") as test_c:    
    for i in range(len(preguntes)):    
        test_c.write(str(i) + ". Pregunta: " + preguntes[i] + "\nResposta: \n" + str(respostes[i])+"\n\n\n")
