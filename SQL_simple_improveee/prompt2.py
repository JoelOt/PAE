from backendHistory import Backend


def prompt():

    back = Backend()
    while True:
        msg = ""
        msg = input(">> ")

            
        

        # Salir del bucle si el usuario escribe 'salir' o 'exit'
        if msg.lower() in ["salir", "exit"]:
            print("Saliendo de la conversación.")
            #back.finalitzar()
            break

        response = back.preguntaSQL(msg)
        print(response)
        
if __name__ == "__main__":
    prompt()