# Importaciones necesarias para el modelo de lenguaje y manejo de mensajes
from langchain_ollama import OllamaLLM
from langchain_core.messages import HumanMessage, AIMessage
#altres moduls
from chain_sql import chainSQL
import re
import pandas as pd
# La clase Backend sirve como interfaz para manejar preguntas y respuestas
class Backend:
    def __init__(self):
        # Inicializar el modelo de lenguaje
        self.llm = OllamaLLM(model="llama3:8b")#, top_k= 50, top_p=0.8, temperature=0.2
        self.messages = []
        self.chainSQL = chainSQL()

    def preguntaSQL(self,input):
        if(len(self.messages)>1):
            self.messages.pop(0)
            print("\n memory pop \n")
        
        self.messages.append(HumanMessage(content=input))
        [sql_response, query] = self.chainSQL.run_chain2(input, self.messages) # Obtener respuesta SQL de la base de datos usando la pregunta de entrada
        response = self.modificar_sortida(sql_response, query)
        #response = self.mod_sortida(sql_response)
        self.messages.append(AIMessage(content="GENERATED QUERY: " + query))
        return response
    
    
    def modificar_sortida(self, sql_response, query):
        print(sql_response)
        print("\n\n")

        if "Incidences" in query:
            table = "incidences"
        elif "Alerts" in query:
            table = "alerts"
        elif "Changes" in query:
            table = "changes"
        else:
            table = "Delete"
        
        if query.startswith("SELECT"):
            if("COUNT" in query ):
                try:
                    response = "There are " + str(sql_response[0]['COUNT(*)']) + " " + table +" that match with your question."
                except:
                    response = self.maquetarLlistes(sql_response)
            else:
                response = self.maquetarLlistes(sql_response)
                
        elif query.startswith("UPDATE"):
            aux = re.search(r"WHERE(.*)", query).group(1).strip()  #busca el where a la query sql i es queda amb tot lo posterior
            comprovador = "SELECT * FROM " + table + " WHERE " + aux  
            sql_response = self.chainSQL.consulta_simple(query=comprovador)  #executa la consulta a la db
            response = self.maquetarLlistes(sql_response)
            
        elif query.startswith("DELETE"):
            response = str(sql_response['err'])
           
        elif query.startswith("INSERT"):
            aux = "SELECT * FROM " + table.upper() + " ORDER BY ID DESC LIMIT 1"
            sql_response = self.chainSQL.consulta_simple(query=aux)
            response = self.maquetarLlistes(sql_response)            

        else :
            response="I couldn't find information related to that question. Please feel free to ask me another question." 
        return response
            
            
    def maquetarLlistes(self, sql_response):
        df = pd.json_normalize(sql_response) #retorna un dataframe agafant els camps del json
        return df
              
    def genInsert(self, resp):
        query = "INSERT INTO Incidences (start_datetime, Severity, Impact, CIs_affected, Description, AlertSource, ChangeSource) VALUES (datetime('now', 'localtime'), " + str(resp[0]) + ", " + str(resp[1]) + ", 'BANCO-SRV-" + str(resp[2]) + "', '" + str(resp[3]) + "', " + str(resp[4]) + ", " + str(resp[5]) +");"
        resp = self.chainSQL.consulta_simple(query=query)
        return resp
        