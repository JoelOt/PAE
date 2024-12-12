from sqlalchemy import Insert
import streamlit as st
from backendHistory import Backend
#Para ejecutarlo usamos streamlit run interfazstreamlit.py

#importamos nustros chats
#from backend/prompt
st.set_page_config(layout="wide")

if 'backend' not in st.session_state:
    st.session_state.backend = Backend()

b = st.session_state.backend

#titol almb imatge
icon_path = "infraicon.jpg"
col1, col2 = st.columns([1, 5])  # Ajusta los pesos según sea necesario

with col1:
    st.image(icon_path, width=100)  # Muestra el ícono con el ancho deseado

with col2:
    st.title("InfraX") 

# Inicializar el estado
if "messages" not in st.session_state:
    st.session_state.messages = []

if "first_message" not in st.session_state:
    st.session_state.first_message = True

if "additional_questions" not in st.session_state:
    st.session_state.additional_questions = []
    st.session_state.responses = []
    st.session_state.asking_additional = False
    st.session_state.current_question_index = 0

# Mostrar mensajes anteriores
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if isinstance(message["content"], str):
            st.markdown(message["content"])
        else:
            st.dataframe(message["content"])

# Mensaje de bienvenida
if st.session_state.first_message:
    with st.chat_message("assistant"):
        st.markdown("Bienvenido a tu asistente InfraX, ¿en qué puedo ayudarte?")
    st.session_state.messages.append({"role": "assistant", "content": "Bienvenido a tu asistente InfraX, ¿en qué puedo ayudarte?"})
    st.session_state.first_message = False

# Entrada del usuario
if prompt := st.chat_input("Escribe aquí tu mensaje:"):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Si estamos en el modo de preguntas adicionales
    if st.session_state.asking_additional:
        # Guardar la respuesta del usuario
        st.session_state.responses.append(prompt)

        # Pasar a la siguiente pregunta
        st.session_state.current_question_index += 1
        if st.session_state.current_question_index < len(st.session_state.additional_questions):
            next_question = st.session_state.additional_questions[st.session_state.current_question_index]
            with st.chat_message("assistant"):
                st.markdown(next_question)
            st.session_state.messages.append({"role": "assistant", "content": next_question})
        else:
            # Si ya se han respondido todas las preguntas
            st.session_state.asking_additional = False
            with st.chat_message("assistant"):
                st.markdown("Thank you for your answers! Upadting database...")
            st.session_state.messages.append({"role": "assistant", "content": "Thank you for your answers! Upadting database..."})
            
            # Ejecutar código con las respuestas
            column_count = st.session_state.responses[1]
            values = st.session_state.responses[2]
            
            # Generar y mostrar un ejemplo de código
            code_result = b.genInsert(st.session_state.responses)
            with st.chat_message("assistant"):
                st.markdown(f"Ejecutando el código:\n```sql\n{code_result}\n```")
            st.session_state.messages.append({"role": "assistant", "content": f"Ejecutando el código:\n```sql\n{code_result}\n```"})
    else:
        # Verificar si la entrada contiene "insert" para activar el flujo de preguntas adicionales
        if "insert" in prompt.lower():
            st.session_state.asking_additional = True
            st.session_state.additional_questions = [
                "Give me the Severity of the incidence that you want to insert (1 to 5)",
                "Give me the Impact of the incidence that you want to insert (0/1)",
                "Which is the number of the server afected? (BANCO-SERV-?)?",
                "Give me description of the incidence that you want to include ",
                "Give me the ID of the alert that is related to this incidence (if there is no alerts related to it write NULL)",
                "Give me the ID of the change that is related to this incidence (if there is no changes related to it write NULL)"
            ]
            st.session_state.responses = []
            st.session_state.current_question_index = 0

            # Hacer la primera pregunta
            first_question = st.session_state.additional_questions[st.session_state.current_question_index]
            with st.chat_message("assistant"):
                st.markdown(first_question)
            st.session_state.messages.append({"role": "assistant", "content": first_question})
        else:
            # Respuesta normal
            with st.chat_message("assistant"):
                msg = b.preguntaSQL(prompt)
                if isinstance(msg, str):
                    st.markdown(msg)
                else:
                    st.dataframe(msg)
            st.session_state.messages.append({"role": "assistant", "content": msg})

# Botón para finalizar la conversación
if st.button("Finalizar conversación"):
    b.finalitzar()
    st.session_state.messages.clear()
    st.session_state.first_message = True
    st.session_state.asking_additional = False
    st.session_state.current_question_index = 0
    st.session_state.responses = []
    st.write("La conversación ha terminado.")
