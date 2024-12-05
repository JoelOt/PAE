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

if "messages" not in st.session_state:
    st.session_state.messages = []

if "first_message" not in st.session_state:
    st.session_state.first_message = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if isinstance(message["content"], str):
            st.markdown(message["content"])
        else:
            st.dataframe(message["content"])

if st.session_state.first_message:
    with st.chat_message("assistant"):
        st.markdown("Bienvenido a tu assistente InfraX, en que puedo ayudarte?")

    st.session_state.messages.append({"role":"assistant","content":"Bienvenido a tu assistente InfraX, en que puedo ayudarte?"})
    st.session_state.first_message=False

if prompt:= st.chat_input ("¿cómo puedo ayudarte?"):
    with st.chat_message("user"):
        st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        
    #Implementacion del algoritmo de IA
    #insts = pregunta(prompt) #funcio q li pasa la pregunta
    #res = get_response(insts,intents) #funcio q retorna la resposta
    
    
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
    st.session_state.messages.clear()  # Limpia el historial de mensajes
    st.session_state.first_message = True  # Restablece la primera interacción
    st.write("La conversación ha terminado.")
    # Puedes agregar un mensaje o acción adicional si lo deseas.
    
