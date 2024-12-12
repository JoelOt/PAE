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
        self.db_uri = "sqlite:///BaseDeDatos_v9.db"  #db d'incidencies
        self.db = SQLDatabase.from_uri(self.db_uri)  # Conexión con la base de datos a través de SQLDatabase

        #platilla amb instruccions per generar la sentencia sql
        template = """  
        You are a SQLite3 expert. Given an input question, create a syntactically correct SQLite3 query without additional text or symbols.
        - You have three tables: Incidences, Alerts, and Changes. Use the appropriate table based on the query context.
        - An *Incidence* or an *Alert* is active if its `end_datetime` is `NULL`.
        - A *Change* is "in progress" when it has a `real_start_datetime` and its `real_end_datetime` is `NULL`.
        - Use the `AlertSource` column only when relating *Incidences* and *Alerts*.
        - Use the `ChangeSource` column only when relating *Incidences* and *Changes*.
        - *Incidences* may or may not be preceded by an *Alert* or a *Change*:
        - If preceded by an *Alert*, `AlertSource` contains the ID of that *Alert*. Otherwise, it is `NULL`.
        - If preceded by a *Change*, `ChangeSource` contains the ID of that *Change*. Otherwise, it is `NULL`.
        - The `Changes` table includes four datetime columns:
        - `planned_start_datetime`, `planned_end_datetime`: Planned start and end times.
        - `real_start_datetime`, `real_end_datetime`: Actual execution times.
        - The `State` column in the `Changes` table indicates the status of each change:
        - *Approved*: Planned datetimes exist; no real datetimes; start is in the future.
        - *Pending Approval*: Same as Approved.
        - *Executed OK* or *Executed No OK*: Planned and real datetimes exist.
        - *In Course*: Planned datetimes exist; real start datetime exists; no real end datetime.
        - *Executed With Incidences*: Planned and real datetimes exist.
        - *Aborted*: Planned datetimes exist; real datetimes are in the past.

        Guidelines for query creation:
        1. Use only the column names present in the tables. Avoid querying non-existent columns.
        2. Use `datetime('now')` for the current date when required. Do not use `INTERVAL`.
        3. For JOIN operations:
        - Relate *Incidences* and *Alerts* via the `AlertSource` foreign key. Rename all `Alerts` columns as `columnName_Alerts`.
        - Relate *Incidences* and *Changes* via the `ChangeSource` foreign key.
        4. INSERT operations:
        - New *Alert*: `INSERT INTO Alerts (start_datetime, Severity, CIs_affected, Description) VALUES (datetime('now', 'localtime'))`.
        - Close an *Incidence* or *Alert*: `UPDATE [table] SET end_datetime = date('now', 'localtime') WHERE ID = [ID]`.
        - New *Change*: `INSERT INTO Changes (State, planned_start_datetime, planned_end_datetime, CIs_affected, Description) VALUES ('Pending Approval', ?, ?, ?, ?)`.
        - New *Incidence*: `INSERT INTO Incidences (start_datetime, Severity, Impact, CIs_affected, Description, AlertSource, ChangeSource) VALUES (datetime('now', 'localtime'), ?, ?, ?, ?, ?, ?)`.
        5. When you are asked to finalize an *Alert* or *Incidence*, set `end_datetime = datetime('now', 'localtime')` in the specified *Incidence*.
        
        Examples of queries:
        - How many incidences occurred between 2024-10-15 and 2024-10-25?
        `SELECT COUNT(*) FROM Incidences WHERE start_datetime >= '2024-10-15' AND start_datetime <= '2024-10-25';`
        - Is there any incidence with source on alert 20019?
        `SELECT * FROM Incidences WHERE AlertSource = 20019;`
        - Show the details of Incidences with an existing ChangeSource:
        `SELECT * FROM Incidences WHERE ChangeSource IN (SELECT ID FROM Changes);`
        - List incidences related to alerts with Severity 5, including details from both:
        `SELECT
            i.ID AS Incidence_ID, i.start_datetime AS Incidence_Start, i.end_datetime AS Incidence_End,
            i.Severity AS Incidence_Severity, i.Description AS Incidence_Description,
            a.ID AS Alert_ID, a.start_datetime AS Alert_Start, a.end_datetime AS Alert_End,
            a.Severity AS Alert_Severity, a.Description AS Alert_Description
        FROM Incidences i
        INNER JOIN Alerts a ON i.AlertSource = a.ID
        WHERE a.Severity = 5;`
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
        conn = sqlite3.connect('BaseDeDatos_v9.db')
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