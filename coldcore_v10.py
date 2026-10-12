import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from collections import deque
from datetime import datetime
import random
import time
import csv
import os
import shutil

APP_NAME = "PS3 COLDCORE v1.0"
LOG_FILE = "coldcore_log.csv"

WARNING_TEMP = 75.0
CRITICAL_TEMP = 85.0
HISTORY_SIZE = 100

PROFILES = {
    "ECO": {
        "cell": 55.0,
        "rsx": 53.0,
        "description": (
            "ECO\n\n"
            "Objetivo: una simulación de funcionamiento tranquilo.\n\n"
            "- Representa temperaturas objetivo más bajas.\n"
            "- Simula un uso moderado.\n"
            "- Es útil para probar un perfil conservador.\n\n"
            "Importante: no reduce el consumo ni la temperatura "
            "real de tu PS3 en esta versión."
        )
    },
    "BALANCEADO": {
        "cell": 65.0,
        "rsx": 62.0,
        "description": (
            "BALANCEADO\n\n"
            "Objetivo: equilibrio entre uso moderado y rendimiento.\n\n"
            "- Representa una carga intermedia.\n"
            "- Usa objetivos térmicos simulados intermedios.\n"
            "- Es el perfil predeterminado para las pruebas.\n\n"
            "Importante: no modifica el hardware de tu PS3."
        )
    },
    "RENDIMIENTO": {
        "cell": 73.0,
        "rsx": 69.0,
        "description": (
            "RENDIMIENTO\n\n"
            "Objetivo: representar una carga de trabajo más intensa.\n\n"
            "- Simula temperaturas objetivo más altas.\n"
            "- Sirve para probar las alertas con una carga ficticia.\n"
            "- No aumenta los FPS ni la potencia de la consola.\n\n"
            "Importante: los valores son simulados, no mediciones reales."
        )
    }
}


class ColdcoreApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("1020x850")
        self.root.minsize(780, 650)

        self.running = True
        self.source = tk.StringVar(value="SIMULACION")
        self.profile = tk.StringVar(value="BALANCEADO")
        self.fan_mode = tk.StringVar(value="AUTOMATICO")

        self.cell_temp = 60.0
        self.rsx_temp = 58.0
        self.simulated_fan = 40

        self.cell_history = deque(maxlen=HISTORY_SIZE)
        self.rsx_history = deque(maxlen=HISTORY_SIZE)
        self.last_log_time = 0.0

        self.prepare_log()
        self.build_interface()
        self.update_profile_description()
        self.change_source()
        self.update_display()

        self.root.protocol("WM_DELETE_WINDOW", self.close)

    # ---------------- HISTORIAL ----------------

    def prepare_log(self):
        if not os.path.exists(LOG_FILE) or os.path.getsize(LOG_FILE) == 0:
            try:
                with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
                    csv.writer(f).writerow([
                        "fecha_hora", "conexion", "fuente", "perfil",
                        "cell_c", "rsx_c", "modo_ventilador",
                        "velocidad_simulada_pct", "estado"
                    ])
            except OSError as error:
                print("Error creando historial:", error)

    def log_reading(self):
        simulated = self.source.get() == "SIMULACION"

        row = [
            datetime.now().isoformat(timespec="seconds"),
            self.source.get(),
            "SIMULACION" if simulated else "SIN_ADAPTADOR_REAL",
            self.profile.get(),
            round(self.cell_temp, 1) if simulated else "",
            round(self.rsx_temp, 1) if simulated else "",
            self.fan_mode.get(),
            self.simulated_fan if simulated else "",
            self.get_thermal_status() if simulated else "SIN_LECTURAS_REALES"
        ]

        try:
            with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(row)
        except OSError as error:
            self.connection_info.config(
                text="Error guardando historial: " + str(error)
            )

    # ---------------- INTERFAZ ----------------

    def build_interface(self):
        container = ttk.Frame(self.root, padding=10)
        container.pack(fill="both", expand=True)

        ttk.Label(
            container, text=APP_NAME,
            font=("Segoe UI", 21, "bold")
        ).pack(anchor="w")

        self.notebook = ttk.Notebook(container)
        self.notebook.pack(fill="both", expand=True, pady=10)

        self.monitor_tab = ttk.Frame(self.notebook, padding=10)
        self.guide_tab = ttk.Frame(self.notebook, padding=10)

        self.notebook.add(self.monitor_tab, text="Monitor")
        self.notebook.add(self.guide_tab, text="Guía e historial")

        self.build_monitor()
        self.build_guide()

    def build_monitor(self):
        tab = self.monitor_tab

        # Conexión
        connection = ttk.LabelFrame(
            tab, text="Conexión con la consola", padding=10
        )
        connection.pack(fill="x", pady=4)

        row = ttk.Frame(connection)
        row.pack(fill="x")

        ttk.Label(row, text="Estado:").pack(side="left")

        self.source_combo = ttk.Combobox(
            row, textvariable=self.source,
            values=["SIMULACION", "CONECTADO", "DESCONECTADO"],
            state="readonly", width=18
        )
        self.source_combo.pack(side="left", padx=8)
        self.source_combo.bind(
            "<<ComboboxSelected>>", self.change_source
        )

        self.connection_badge = ttk.Label(row, text="SIMULACIÓN")
        self.connection_badge.pack(side="left", padx=8)

        self.connection_info = ttk.Label(
            connection, text="", wraplength=850
        )
        self.connection_info.pack(anchor="w", pady=(8, 0))

        # Temperaturas
        temperatures = ttk.LabelFrame(
            tab, text="Temperaturas", padding=10
        )
        temperatures.pack(fill="x", pady=4)

        row = ttk.Frame(temperatures)
        row.pack(fill="x")

        self.cell_label = ttk.Label(
            row, text="CELL: -- °C",
            font=("Segoe UI", 17, "bold")
        )
        self.cell_label.pack(side="left", padx=(0, 30))

        self.rsx_label = ttk.Label(
            row, text="RSX: -- °C",
            font=("Segoe UI", 17, "bold")
        )
        self.rsx_label.pack(side="left")

        self.thermal_status = ttk.Label(
            temperatures, text="Estado térmico: esperando datos"
        )
        self.thermal_status.pack(anchor="w", pady=(8, 0))

        # Perfiles y explicación dinámica
        profiles = ttk.LabelFrame(
            tab, text="Perfiles térmicos", padding=10
        )
        profiles.pack(fill="x", pady=4)

        row = ttk.Frame(profiles)
        row.pack(fill="x")

        ttk.Label(row, text="Selecciona un perfil:").pack(side="left")

        self.profile_combo = ttk.Combobox(
            row, textvariable=self.profile,
            values=["ECO", "BALANCEADO", "RENDIMIENTO"],
            state="readonly", width=18
        )
        self.profile_combo.pack(side="left", padx=10)
        self.profile_combo.bind(
            "<<ComboboxSelected>>", self.profile_changed
        )

        self.profile_description = ttk.Label(
            profiles, text="", justify="left",
            wraplength=850
        )
        self.profile_description.pack(
            anchor="w", fill="x", pady=(10, 0)
        )

        # Ventilador
        fan = ttk.LabelFrame(
            tab, text="Control manual del ventilador (simulación)",
            padding=10
        )
        fan.pack(fill="x", pady=4)

        row = ttk.Frame(fan)
        row.pack(fill="x")

        ttk.Radiobutton(
            row, text="Automático",
            variable=self.fan_mode, value="AUTOMATICO",
            command=self.fan_mode_changed
        ).pack(side="left", padx=(0, 12))

        ttk.Radiobutton(
            row, text="Manual",
            variable=self.fan_mode, value="MANUAL",
            command=self.fan_mode_changed
        ).pack(side="left")

        self.fan_label = ttk.Label(
            fan, text="Velocidad simulada: 40%"
        )
        self.fan_label.pack(anchor="w", pady=(8, 0))

        self.fan_slider = ttk.Scale(
            fan, from_=20, to=100,
            orient="horizontal", command=self.slider_changed
        )
        self.fan_slider.set(40)
        self.fan_slider.pack(fill="x", pady=5)

        row = ttk.Frame(fan)
        row.pack(fill="x")

        self.apply_fan_button = ttk.Button(
            row, text="Aplicar valor simulado",
            command=self.apply_fan
        )
        self.apply_fan_button.pack(side="left")

        ttk.Button(
            row, text="Volver a automático",
            command=self.return_to_auto
        ).pack(side="left", padx=8)

        self.fan_info = ttk.Label(
            fan, text="Ventilador real: sin conexión"
        )
        self.fan_info.pack(anchor="w", pady=(8, 0))

        # Gráfica
        graph = ttk.LabelFrame(
            tab, text="Gráfica térmica", padding=5
        )
        graph.pack(fill="both", expand=True, pady=4)

        self.canvas = tk.Canvas(
            graph, height=150, background="#171b24",
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind(
            "<Configure>", lambda event: self.draw_graph()
        )

        row = ttk.Frame(tab)
        row.pack(fill="x", pady=5)

        ttk.Button(
            row, text="Registrar ahora",
            command=self.register_now
        ).pack(side="left")

        ttk.Button(
            row, text="Exportar historial CSV",
            command=self.export_csv
        ).pack(side="left", padx=8)

    def build_guide(self):
        tab = self.guide_tab

        ttk.Label(
            tab, text="Guía e historial",
            font=("Segoe UI", 16, "bold")
        ).pack(anchor="w")

        ttk.Label(
            tab,
            text="Consulta el significado de los datos de COLDCORE.",
            wraplength=850
        ).pack(anchor="w", pady=5)

        table = ttk.Treeview(
            tab, columns=("name", "meaning"),
            show="headings", height=13
        )
        table.heading("name", text="Concepto")
        table.heading("meaning", text="Significado")
        table.column("name", width=190)
        table.column("meaning", width=650)
        table.pack(fill="both", expand=True, pady=5)

        rows = [
            ("CELL", "Procesador principal de la PS3. Temperatura simulada en esta versión."),
            ("RSX", "Procesador gráfico de la PS3. Temperatura simulada en esta versión."),
            ("ECO", "Simula objetivos térmicos más bajos y una carga moderada."),
            ("BALANCEADO", "Simula una carga intermedia y sirve como perfil predeterminado."),
            ("RENDIMIENTO", "Simula una carga más intensa y objetivos térmicos más altos."),
            ("SIMULACION", "Genera datos ficticios en el ordenador."),
            ("CONECTADO", "Estado seleccionado en la interfaz; no confirma una conexión física."),
            ("DESCONECTADO", "Oculta las lecturas y bloquea el control simulado del ventilador."),
            ("AVISO", "Una lectura simulada ha alcanzado el umbral de aviso."),
            ("CRITICO", "Una lectura simulada ha alcanzado el umbral crítico."),
            ("CSV", "Archivo de texto tabular que registra fecha, perfil, temperaturas y estado."),
            ("Ventilador %", "Porcentaje de demostración; no son RPM reales.")
        ]

        for name, meaning in rows:
            table.insert("", "end", values=(name, meaning))

        ttk.Label(
            tab,
            text="Historial: " + os.path.abspath(LOG_FILE),
            wraplength=850
        ).pack(anchor="w", pady=5)

    # ---------------- PERFILES ----------------

    def profile_changed(self, event=None):
        self.update_profile_description()

    def update_profile_description(self):
        selected = self.profile.get()
        profile = PROFILES[selected]
        self.profile_description.config(
            text=profile["description"]
        )

    # ---------------- CONEXIÓN ----------------

    def change_source(self, event=None):
        mode = self.source.get()

        if mode == "SIMULACION":
            self.connection_badge.config(text="SIMULACIÓN")
            self.connection_info.config(
                text="Datos ficticios generados en el PC; no proceden de la PS3."
            )
            self.fan_info.config(
                text="Ventilador real: sin conexión. Solo simulación."
            )
            self.apply_fan_button.config(state="normal")
        elif mode == "CONECTADO":
            self.connection_badge.config(text="NO VERIFICADO")
            self.connection_info.config(
                text="Adaptador real pendiente. No hay temperaturas verificadas."
            )
            self.fan_info.config(
                text="Control real bloqueado: no existe adaptador configurado."
            )
            self.apply_fan_button.config(state="disabled")
        else:
            self.connection_badge.config(text="DESCONECTADO")
            self.connection_info.config(
                text="Sin conexión. No se generan temperaturas ni se envían órdenes."
            )
            self.fan_info.config(text="Ventilador real: desconectado.")
            self.apply_fan_button.config(state="disabled")

        self.update_data_visibility()

    def update_data_visibility(self):
        if self.source.get() != "SIMULACION":
            self.cell_label.config(text="CELL: -- °C")
            self.rsx_label.config(text="RSX: -- °C")
            self.thermal_status.config(
                text="Estado térmico: sin lecturas reales"
            )
            self.fan_label.config(
                text="Velocidad del ventilador: no disponible"
            )
            self.draw_graph()

    # ---------------- SIMULACIÓN ----------------

    def simulate_temperatures(self):
        profile = PROFILES[self.profile.get()]
        target_cell = profile["cell"]
        target_rsx = profile["rsx"]

        self.cell_temp += (target_cell - self.cell_temp) * 0.15
        self.rsx_temp += (target_rsx - self.rsx_temp) * 0.15

        self.cell_temp += random.uniform(-0.8, 0.8)
        self.rsx_temp += random.uniform(-0.8, 0.8)

        self.cell_temp = max(25, min(100, self.cell_temp))
        self.rsx_temp = max(25, min(100, self.rsx_temp))

        self.cell_history.append(self.cell_temp)
        self.rsx_history.append(self.rsx_temp)

    def get_thermal_status(self):
        hottest = max(self.cell_temp, self.rsx_temp)
        if hottest >= CRITICAL_TEMP:
            return "CRITICO"
        if hottest >= WARNING_TEMP:
            return "AVISO"
        return "NORMAL"

    def update_display(self):
        if not self.running:
            return

        if self.source.get() == "SIMULACION":
            self.simulate_temperatures()

            self.cell_label.config(
                text="CELL: {:.1f} °C".format(self.cell_temp)
            )
            self.rsx_label.config(
                text="RSX: {:.1f} °C".format(self.rsx_temp)
            )

            status = self.get_thermal_status()
            self.thermal_status.config(
                text="Estado térmico: " + status
            )

            if self.fan_mode.get() == "AUTOMATICO":
                hottest = max(self.cell_temp, self.rsx_temp)
                self.simulated_fan = int(
                    max(25, min(90, 25 + (hottest - 50) * 1.5))
                )
                self.fan_label.config(
                    text="Velocidad automática simulada: {}%".format(
                        self.simulated_fan
                    )
                )

            self.draw_graph()

            now = time.time()
            if now - self.last_log_time >= 5:
                self.log_reading()
                self.last_log_time = now
        else:
            self.update_data_visibility()

        self.root.after(1500, self.update_display)

    # ---------------- VENTILADOR ----------------

    def slider_changed(self, value):
        self.fan_label.config(
            text="Velocidad simulada seleccionada: {}%".format(
                int(float(value))
            )
        )

    def fan_mode_changed(self):
        self.fan_info.config(
            text=(
                "Modo manual simulado."
                if self.fan_mode.get() == "MANUAL"
                else "Modo automático simulado."
            ) + " No controla el hardware."
        )

    def apply_fan(self):
        if self.source.get() != "SIMULACION":
            messagebox.showwarning(
                "Control bloqueado",
                "No hay adaptador real configurado."
            )
            return

        if self.fan_mode.get() != "MANUAL":
            messagebox.showinfo(
                "Modo automático",
                "Selecciona primero el modo manual."
            )
            return

        self.simulated_fan = int(float(self.fan_slider.get()))
        self.fan_label.config(
            text="Velocidad manual simulada: {}%".format(
                self.simulated_fan
            )
        )
        self.fan_info.config(
            text="Valor simulado aplicado. El ventilador físico no cambia."
        )

    def return_to_auto(self):
        self.fan_mode.set("AUTOMATICO")
        self.fan_mode_changed()

    # ---------------- GRÁFICA ----------------

    def draw_graph(self):
        canvas = self.canvas
        canvas.delete("all")

        if self.source.get() != "SIMULACION":
            canvas.create_text(
                max(100, canvas.winfo_width() // 2),
                max(50, canvas.winfo_height() // 2),
                text="Sin lecturas reales",
                fill="#e2e8f0"
            )
            return

        width = canvas.winfo_width()
        height = canvas.winfo_height()
        if width < 100 or height < 70:
            return

        left, right = 45, width - 15
        top, bottom = 15, height - 25

        for temp in (30, 40, 50, 60, 70, 80, 90, 100):
            y = bottom - (temp - 30) / 70 * (bottom - top)
            canvas.create_line(left, y, right, y, fill="#343b48")
            canvas.create_text(23, y, text=str(temp), fill="#cbd5e1")

        def draw_series(values, color):
            if len(values) < 2:
                return
            points = []
            for i, value in enumerate(values):
                x = left + i / max(1, len(values) - 1) * (right - left)
                y = bottom - (value - 30) / 70 * (bottom - top)
                points.extend([x, y])
            canvas.create_line(*points, fill=color, width=2, smooth=True)

        draw_series(list(self.cell_history), "#38bdf8")
        draw_series(list(self.rsx_history), "#f59e0b")

        canvas.create_text(left + 35, height - 10, text="CELL", fill="#38bdf8")
        canvas.create_text(left + 100, height - 10, text="RSX", fill="#f59e0b")

    # ---------------- ARCHIVOS ----------------

    def register_now(self):
        self.log_reading()
        messagebox.showinfo(
            "Historial",
            "Se ha guardado el estado actual, si el archivo está disponible."
        )

    def export_csv(self):
        if not os.path.exists(LOG_FILE):
            messagebox.showwarning("Historial", "No existe historial todavía.")
            return

        filename = filedialog.asksaveasfilename(
            title="Exportar historial",
            defaultextension=".csv",
            filetypes=[("Archivo CSV", "*.csv")]
        )
        if not filename:
            return

        try:
            shutil.copyfile(LOG_FILE, filename)
            messagebox.showinfo("Exportación", "Historial exportado correctamente.")
        except OSError as error:
            messagebox.showerror("Error", str(error))

    def close(self):
        self.running = False
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ColdcoreApp(root)
    root.mainloop()