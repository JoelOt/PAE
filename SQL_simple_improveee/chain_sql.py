#moduls langchain
from langchain_core.prompts.chat import ChatPromptTemplate
from langchain_community.utilities import SQLDatabase
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_ollama import OllamaLLM
import re
import sqlite3
import json
import os
import getpass

# Clase chainSQL para generar y ejecutar consultas SQL basadas en preguntas en lenguaje natural
class chainSQL():
    def __init__(self): 
        #mannix/defog-llama3-sqlcoder-8b
        # Inicialización del modelo LLM especificado (en este caso "llama3:8b") para convertir lenguaje natural en SQL
        llm = OllamaLLM(model="llama3:8b")      #model per passar de text - sql
        
        # Configuración de la base de datos: conexión a la base de datos SQLite con los datos de incidencias
        self.db_uri = "sqlite:///BaseDeDatos_v7.db"  #db d'incidencies
        self.db = SQLDatabase.from_uri(self.db_uri)  # Conexión con la base de datos a través de SQLDatabase

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
        \n When you perform a query using a JOIN to relate the Incidences and Alerts tables via the FOREIGN KEY, you should select all columns from both tables, ensuring that all columns from the Alerts table are renamed using the format columnName_Alerts.
        \n If you are required to create a new Alert, INSERT INTO Alerts (start_datetime, Severity, CIs_affected, Description) VALUES (datatime('now', 'localtime'))
        \n If you are required to create a new Incidence, INSERT INTO Incidences (start_datetime, Severity, Impact, CIs_affected, Description, Source) VALUES (datatime('now', 'localtime'))
        \n In the Incidences table, the column Source is a foreign key referencing the ID column in the Alerts table. This means that the value of Source in Incidences must match an existing value in the ID column of Alerts. Therefore, queries must respect this relationship when performing operations between the tables.
        \n There are some examples for diferent types of questions with the response that should be given. The following examples are the same queries for incidents and alerts, except for the table field.: 
        \n How many incidences occurred  betwween 2024-10-15 and 2024-10-25?  --> SELECT COUNT(*) FROM Incidences WHERE start_datetime >= '2024-10-15' AND start_datetime <= '2024-10-25';
        \n How many incidences begin today? --> SELECT COUNT(*) FROM Incidences WHERE start_datetime >= date('now')
        \n How many incidences happened in the last 72 hours --> SELECT COUNT(*) FROM Incidences WHERE start_datetime >= DATETIME('now', '-72 hours');
        \n Is there any incidence with source on the alert 20019? --> SELECT * FROM Incidences WHERE Source = 20019;
        \n Which incidences have their source in some alert? --> SELECT * FROM Incidences WHERE "Source" IN (SELECT "ID" FROM Alerts);
        \n What are the incidences associated with alerts with a severity of 5, including detailed information about both? --> SELECT i.ID AS Incidence_ID, i.start_datetime AS Incidence_Start, i.end_datetime AS Incidence_End, i.Severity AS Incidence_Severity, i.Description AS Incidence_Description, a.ID AS Alert_ID, a.start_datetime AS Alert_Start, a.end_datetime AS Alert_End, a.Severity AS Alert_Severity, a.Description AS Alert_Description FROM Incidences i INNER JOIN Alerts a ON i.Source = a.ID WHERE a.Severity = 5; 
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
                    response = {'err': "permission denied: YOU ARE NOT ALLOWED TO DELETE IN THE DATABASE"}
                    return response, query
                response = self.run_db(query)
                break
            except Exception as e:
                try:
                    query = query.split("sql")[1]
                    query = query.split("```")[0]
                    print("\n\n")
                    print(query)
                    response = self.run_db(query)
                    return response, query
                except:
                    count +=1
                    if(count<5):
                        print("RETRYING QUERY\n")
                    else:
                        print("REPEAT THE QUESTION\n")
                        response = {'err': "I couldn't find information related to that question. Please feel free to ask me another question."}
                        query = "INVALID QUERY"
            
        print("\n\n")
        print(response)
        return response, query
        
    def consulta_simple(self, query):
        try:
            print(query)
            response = self.run_db(query)
        except Exception as e:
            response = str(e)
        return  response

    def run_db(self, query):
        conn = sqlite3.connect('BaseDeDatos_v7.db')
        def dict_factory(cursor, row):
            return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
        conn.row_factory = dict_factory  # Configuración del formato
        cursor = conn.cursor()
        cursor.execute(query)
        response = cursor.fetchall()
        conn.commit()
        return response


    def tester(self, messages):
        question = "Give me the latest 5 alerts"
        response = self.run_chain2(question, messages)
        print(response)