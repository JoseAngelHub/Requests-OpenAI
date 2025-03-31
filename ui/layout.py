from core.logic import AppLogic
from tkinter import scrolledtext
import customtkinter as ctk
import threading
import time
ctk.set_appearance_mode("dark") 
ctk.set_default_color_theme("blue")
class LayoutApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Asistente SQL Chatbot")
        self.root.geometry("1000x800")
        self.root.resizable(False, False)
        try:
            self.root.iconbitmap(r"C:\Users\usuario\Documents\code\pdf_alb\jnc.ico")  # Windows
        except:
            icon_image = ctk.CTkImage(file=r"C:\Users\usuario\Documents\code\pdf_alb\jnc.ico")  # macOS / Linux
            self.root.iconphoto(True, icon_image)
        # Configuración del fondo
        # Configurar layout en grid
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=10)
        self.root.grid_rowconfigure(2, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=0)
        self.root.configure(bg="#2C2F33")

        # Encabezado de la aplicación
        header_label = ctk.CTkLabel(root, text="Asistente SQL Chatbot", font=("Helvetica", 30, "bold"))
        header_label.grid(row=0, column=0, columnspan=2, pady=(10, 5))

        # Área de conversación
        self.chat_area = ctk.CTkTextbox(root, width=950, height=600, wrap="word", state="disabled")
        self.chat_area.grid(row=1, column=0, padx=10, pady=(5, 10), columnspan=2)
        self.chat_area.configure(fg_color="#23272A", text_color="#FFFFFF", font=("Arial", 12))
        self.chat_area.tag_config("user", foreground="#A3E635")
        self.chat_area.tag_config("bot", foreground="#1E90FF")

        # Entrada de texto del usuario
        self.entry_box = ctk.CTkEntry(root, width=600, placeholder_text="Escribe tu pregunta aquí...", font=("Arial", 14), fg_color="#7289DA", text_color="#FFFFFF")
        self.entry_box.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="ew")
        self.entry_box.bind("<Return>", self.send_question)

        # Botón de envío
        self.send_button = ctk.CTkButton(root, text="Enviar", command=self.send_question, font=("Arial", 14), fg_color="#FFBF00", hover_color="#FFA500")
        self.send_button.grid(row=2, column=1, padx=10, pady=(0, 10), sticky="ew")
        # Variables de estado
        self.logic_ready = False
        self.logic = None
        self.loading_animation_running = False

        # Mensaje de carga inicial
        self.display_response("", "Cargando el asistente SQL...")

        # Iniciar la carga de AppLogic en segundo plano
        threading.Thread(target=self.initialize_logic).start()

    def display_response(self, question, response_text):
        # Mostrar la pregunta en el área de chat
        self.chat_area.configure(state="normal")
        if question:
            self.chat_area.insert(ctk.END, f"Tú: {question}\n", "user")
        self.chat_area.insert(ctk.END, f"Tú: {question}\n")
        self.chat_area.insert(ctk.END, f"Asistente: {response_text}\n\n")
        self.chat_area.configure(state="disabled")
        self.chat_area.yview(ctk.END)
    def send_question(self, event=None):
        if not self.selected_table:
            self.display_response("Error", "Por favor selecciona una tabla primero.")
            return

        question = self.entry_box.get().strip()
        if not question:
            self.display_response("Error", "Por favor ingresa una pregunta.")
            return

        # Limpiar el campo de entrada
        self.entry_box.delete(0, ctk.END)
        self.send_button.configure(state="disabled")
        self.start_loading_animation()

        # Ejecutar la consulta en segundo plano para evitar bloquear la interfaz
        threading.Thread(target=self.handle_question, args=(question,)).start()

    def initialize_logic(self):
        self.logic = AppLogic() 
        self.logic_ready = True  
        self.loading_animation_running = False  
        self.send_button.configure(text="Enviar") 
        self.display_response("", "Asistente SQL listo para responder tus preguntas.")

    def send_question(self, event=None):
        if not self.logic_ready:
            self.display_response("", "El asistente aún se está cargando. Por favor, espera...")
            return

        question = self.entry_box.get().strip()
        if not question:
            return

        self.entry_box.delete(0, ctk.END)
        self.send_button.configure(state="disabled")
        self.start_loading_animation()

        threading.Thread(target=self.handle_question, args=(question,), daemon=True).start()

    def handle_question(self, question):
        response_text = self.logic.process_q(question)
        self.loading_animation_running = False  # Detiene la animación
        self.display_response(question, response_text)
        self.send_button.configure(state="normal", text="Enviar")

    def start_loading_animation(self):
        if self.loading_animation_running:
            return  # Evita múltiples animaciones
        self.loading_animation_running = True
        threading.Thread(target=self.animate_button, daemon=True).start()

    def animate_button(self):
        animation_frames = ["Enviando.", "Enviando..", "Enviando..."]
        frame_index = 0
        while self.loading_animation_running:
            self.send_button.configure(text=animation_frames[frame_index])
            frame_index = (frame_index + 1) % len(animation_frames)
            time.sleep(0.5)

        