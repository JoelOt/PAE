#moduls langchain
from langchain_core.prompts.chat import ChatPromptTemplate
from langchain_community.utilities import SQLDatabase
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_ollama import OllamaLLM
import re
import sqlite3
from langchain_core.messages import HumanMessage, AIMessage
import pandas as pd
import json

# Clase chainSQL para generar y ejecutar consultas SQL basadas en preguntas en lenguaje natural
class chainSQL():
    def __init__(self): 
        #mannix/defog-llama3-sqlcoder-8b
        # Inicialización del modelo LLM especificado (en este caso "llama3:8b") para convertir lenguaje natural en SQL
        llm = OllamaLLM(model="llama3:8b")      #model per passar de text - sql
        
        # Configuración de la base de datos: conexión a la base de datos SQLite con los datos de incidencias
        db_uri = "sqlite:///BaseDeDatos_v6.db"  #db d'incidencies
        self.db = SQLDatabase.from_uri(db_uri)  # Conexión con la base de datos a través de SQLDatabase

        #platilla amb instruccions per generar la sentencia sql
        template = """  
        You are a SQLite3 expert. Given an input question, just create a syntactically correct SQLite3 query to run without other text or symbols:
        \n Pay attention you have two tables. You have to use the correct table: Incidences or Alerts. 
        \n An incidence or an alert is active if the end_datetime is NULL
        \n You only have to use the Source cell if the question is relating Incidences and Alerts
        \n Incidents may or may not be preceded by an alert. In the case where there is a previous alert, the Source cell contains the ID of that alert. 
        \n If the incident is not preceded by any alert (unexpected), the Source cell is NULL. The Source cell only relates incidents preceded by alerts, nothing more.
        \n Pay attention to use only the column names you can see in the tables below. Be careful to not query for columns that do not exist. Pay attention to which column is in which table
        \n Pay attention to use datetime(\'now\') function to get the current date, if the question involves "today".
        \n Pay attention not to use the function INTERVAL.
        \n There are some examples for diferent types of questions with the response that should be given. The following examples are the same queries for incidents and alerts, except for the table field.: 
        \n How many incidences occurred  betwween 2024-10-15 and 2024-10-25?  --> SELECT COUNT(*) FROM Incidences WHERE start_datetime >= '2024-10-15' AND start_datetime <= '2024-10-25';
        \n How many incidences begin today? --> SELECT COUNT(*) FROM Incidences WHERE start_datetime >= date('now')
        \n How many incidences happened in the last 72 hours --> SELECT COUNT(*) FROM Incidences WHERE start_datetime >= DATETIME('now', '-72 hours');
        \n Is there any incidence with source on the alert 20019? --> SELECT * FROM Incidences WHERE Source = 20019;
        \n Which incidences have their source in some alert? --> SELECT * FROM Incidences WHERE "Source" IN (SELECT "ID" FROM Alerts);
        \n Use the following format (Pay attention to only give the SQLite3 query, without any extra text or symbol):        
        \n\n Question:{question}
        \n If needed, take into account the previous messages of the conversation: {messages}
        \n Only use the following tables: {schema}
        """
        
        # Creación de un prompt basado en la plantilla anterior, para que el LLM genere la consulta SQL
        prompt = ChatPromptTemplate.from_template(template)

        # Configuración de una cadena de procesamiento que conecta la pregunta con el esquema de la base de datos y el LLM
        self.sql_chain = (
            RunnablePassthrough.assign(schema = self.get_schema)
            | prompt
            | llm.bind(stop=["\nSQL Result:"])
            | StrOutputParser()
        )
        
    # Método para acceder a la cadena de procesamiento desde `fullChain`)
    def getChain(self): #perque es pugui cridar desde fullChain
        return self.sql_chain
    
    def get_schema(self,_): #passa el esquema de les taules de la db i els camps de cada taula
        return self.db.get_table_info()
        
    def run_chain2(self, question, messages):
        count = 0
        query = None
        for count in range(5):
            try:
                print(messages)
                query = self.sql_chain.invoke({"question": question, 
                                               "messages": messages})
                
                print("\n")
                print(query)
                print("\n")
                if re.search(r"(?=.*DELETE)", query):
                    response = "[YOU ARE NOT ALLOWED TO DELETE IN THE DATABASE]" 
                    return response, query
                response = self.db.run(query)
                print(response + '\n')
                print("\n")
                break
            except Exception as e:
                count +=1
                if(count<5):
                    print("RETRYING QUERY\n")
                else:
                    print("REPEAT THE QUESTION\n")
                    response = "[REPEAT THE QUESTION]"
                    query = "INVALID QUERY"

        print("\n\n")
        print(response)
        return response, query
        
    def consulta_simple(self, query):
        try:
            print(query)
            response = self.db.run(query)
        except Exception as e:
            response = str(e)
        return  response





    def tester(self, messages):
        question = "Give me the latest 5 alerts"
        response = self.run_chain2(question, messages)
        print(response)
   
if __name__ == "__main__":
    messages = []
    ChainSQL = chainSQL()
    ChainSQL.tester(messages)


#context 
#insert mirar