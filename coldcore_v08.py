import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
import random
import time
from datetime import datetime
from collections import deque


APP_NAME = "PS3 COLDCORE v0.8"

WARNING_TEMP = 75.0
CRITICAL_TEMP = 85.0

LOG_FILE = "coldcore_log.csv"


class ColdcoreApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("900x760")
        self.root.minsize(720, 650)

        self.profile = tk.StringVar(value="BALANCE")
        self.mode = tk.StringVar(value="AUTOMATICO")
        self.fan_value = tk.IntVar(value=40)

        self.cell_temp = 60.0
        self.rsx_temp = 58.0
        self.fan_applied = 40
        self.history_cell = deque(maxlen=100)
        self.history_rsx = deque(maxlen=100)

        self.running = True

        self.create_log()
        self.build_interface()
        self.update_display()

        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def create_log(self):
        try:
            with open(LOG_FILE, "a", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                if file.tell() == 0:
                    writer.writerow([
                        "fecha_hora",
                        "fuente",
                        "perfil",
                        "cell_c",
                        "rsx_c",
                        "ventilador_simulado_pct",
                        "estado"
                    ])
        except OSError as error:
            print("No se pudo crear el registro:", error)

    def build_interface(self):
        main = ttk.Frame(self.root, padding=12)
        main.pack(fill="both", expand=True)

        ttk.Label(
            main,
            text=APP_NAME,
            font=("Segoe UI", 20, "bold")
        ).pack(anchor="w")

        ttk.Label(
            main,
            text="Monitor térmico y banco de pruebas para PC",
        ).pack(anchor="w", pady=(0, 10))

        warning = ttk.Label(
            main,
            text=(
                "MODO SIMULACIÓN: no conectado a la PS3. "
                "El control del ventilador no actúa sobre hardware."
            ),
            foreground="#b45309",
            wraplength=850
        )
        warning.pack(anchor="w", pady=(0, 10))

        # Temperaturas
        temps = ttk.LabelFrame(main, text="Temperaturas simuladas", padding=10)
        temps.pack(fill="x", pady=5)

        temp_row = ttk.Frame(temps)
        temp_row.pack(fill="x")

        self.cell_label = ttk.Label(
            temp_row, text="CELL: -- °C", font=("Segoe UI", 15, "bold")
        )
        self.cell_label.pack(side="left", padx=(0, 30))

        self.rsx_label = ttk.Label(
            temp_row, text="RSX: -- °C", font=("Segoe UI", 15, "bold")
        )
        self.rsx_label.pack(side="left")

        self.status_label = ttk.Label(
            temps, text="Estado: iniciando..."
        )
        self.status_label.pack(anchor="w", pady=(8, 0))

        # Perfiles
        profile_frame = ttk.LabelFrame(main, text="Perfil térmico", padding=10)
        profile_frame.pack(fill="x", pady=5)

        ttk.Label(profile_frame, text="Perfil:").pack(side="left")

        profile_select = ttk.Combobox(
            profile_frame,
            textvariable=self.profile,
            values=["ECO", "BALANCE", "RENDIMIENTO"],
            state="readonly",
            width=18
        )
        profile_select.pack(side="left", padx=10)

        ttk.Label(
            profile_frame,
            text="Solo cambia el objetivo de la simulación."
        ).pack(side="left")

        # Ventilador
        fan_frame = ttk.LabelFrame(
            main, text="Control manual del ventilador (simulación)", padding=10
        )
        fan_frame.pack(fill="x", pady=5)

        mode_row = ttk.Frame(fan_frame)
        mode_row.pack(fill="x")

        ttk.Label(mode_row, text="Modo:").pack(side="left")

        ttk.Radiobutton(
            mode_row,
            text="Automático simulado",
            variable=self.mode,
            value="AUTOMATICO",
            command=self.mode_changed
        ).pack(side="left", padx=8)

        ttk.Radiobutton(
            mode_row,
            text="Manual simulado",
            variable=self.mode,
            value="MANUAL",
            command=self.mode_changed
        ).pack(side="left", padx=8)

        self.fan_label = ttk.Label(
            fan_frame,
            text="Velocidad simulada: 40%"
        )
        self.fan_label.pack(anchor="w", pady=(10, 0))

        self.fan_slider = ttk.Scale(
            fan_frame,
            from_=20,
            to=100,
            orient="horizontal",
            command=self.slider_changed
        )
        self.fan_slider.set(40)
        self.fan_slider.pack(fill="x", pady=5)

        fan_buttons = ttk.Frame(fan_frame)
        fan_buttons.pack(fill="x", pady=(5, 0))

        self.apply_button = ttk.Button(
            fan_buttons,
            text="Aplicar velocidad simulada",
            command=self.apply_manual_fan
        )
        self.apply_button.pack(side="left")

        ttk.Button(
            fan_buttons,
            text="Volver a automático",
            command=self.return_to_auto
        ).pack(side="left", padx=8)

        self.fan_status = ttk.Label(
            fan_frame,
            text="Ventilador real: sin conexión"
        )
        self.fan_status.pack(anchor="w", pady=(8, 0))

        # Gráfica
        graph_frame = ttk.LabelFrame(
            main, text="Historial de temperaturas simuladas", padding=8
        )
        graph_frame.pack(fill="both", expand=True, pady=5)

        self.canvas = tk.Canvas(
            graph_frame,
            height=180,
            background="#151922",
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda event: self.draw_graph())

        # Botones de herramientas
        actions = ttk.Frame(main)
        actions.pack(fill="x", pady=5)

        ttk.Button(
            actions,
            text="Registrar lectura",
            command=self.record_reading
        ).pack(side="left")

        ttk.Button(
            actions,
            text="Exportar CSV",
            command=self.export_csv
        ).pack(side="left", padx=8)

        ttk.Button(
            actions,
            text="Prueba de alertas",
            command=self.test_alerts
        ).pack(side="left")

        ttk.Button(
            actions,
            text="Salir",
            command=self.close
        ).pack(side="right")

    def slider_changed(self, value):
        value = int(float(value))
        self.fan_label.config(
            text="Velocidad simulada: {}%".format(value)
        )

    def mode_changed(self):
        if self.mode.get() == "AUTOMATICO":
            self.fan_status.config(
                text="Modo automático de simulación activo."
            )
        else:
            self.fan_status.config(
                text="Modo manual de simulación. No controla la PS3."
            )

    def apply_manual_fan(self):
        if self.mode.get() != "MANUAL":
            messagebox.showinfo(
                "Modo automático",
                "Selecciona primero 'Manual simulado'."
            )
            return

        self.fan_applied = int(float(self.fan_slider.get()))
        self.fan_status.config(
            text=(
                "Valor simulado aplicado: {}%. "
                "Ventilador real: sin conexión."
            ).format(self.fan_applied)
        )

    def return_to_auto(self):
        self.mode.set("AUTOMATICO")
        self.mode_changed()

    def simulate_temperatures(self):
        profile = self.profile.get()

        targets = {
            "ECO": (55.0, 53.0),
            "BALANCE": (65.0, 62.0),
            "RENDIMIENTO": (73.0, 69.0)
        }

        target_cell, target_rsx = targets[profile]

        self.cell_temp += (target_cell - self.cell_temp) * 0.15
        self.rsx_temp += (target_rsx - self.rsx_temp) * 0.15

        self.cell_temp += random.uniform(-0.8, 0.8)
        self.rsx_temp += random.uniform(-0.8, 0.8)

        self.cell_temp = max(25.0, min(100.0, self.cell_temp))
        self.rsx_temp = max(25.0, min(100.0, self.rsx_temp))

        self.history_cell.append(self.cell_temp)
        self.history_rsx.append(self.rsx_temp)

    def get_status(self):
        hottest = max(self.cell_temp, self.rsx_temp)

        if hottest >= CRITICAL_TEMP:
            return "CRÍTICO: temperatura simulada muy elevada"

        if hottest >= WARNING_TEMP:
            return "ALERTA: temperatura simulada elevada"

        return "NORMAL: datos de simulación"

    def update_display(self):
        if not self.running:
            return

        self.simulate_temperatures()

        self.cell_label.config(
            text="CELL: {:.1f} °C".format(self.cell_temp)
        )
        self.rsx_label.config(
            text="RSX: {:.1f} °C".format(self.rsx_temp)
        )

        self.status_label.config(text="Estado: " + self.get_status())

        if self.mode.get() == "AUTOMATICO":
            # Solo estimación visual para esta demostración.
            hottest = max(self.cell_temp, self.rsx_temp)
            simulated_fan = int(
                max(25, min(90, 25 + (hottest - 50) * 1.5))
            )
            self.fan_label.config(
                text="Velocidad automática simulada: {}%".format(
                    simulated_fan
                )
            )

        self.draw_graph()
        self.log_reading()
        self.root.after(1500, self.update_display)

    def draw_graph(self):
        canvas = self.canvas
        canvas.delete("all")

        width = canvas.winfo_width()
        height = canvas.winfo_height()

        if width < 100 or height < 80:
            return

        left, right = 45, width - 15
        top, bottom = 15, height - 25

        for temp in (40, 50, 60, 70, 80, 90):
            y = bottom - (temp - 30) / 70 * (bottom - top)
            canvas.create_line(
                left, y, right, y, fill="#343b48"
            )
            canvas.create_text(
                25, y, text=str(temp), fill="#cbd5e1"
            )

        def draw_series(values, color):
            if len(values) < 2:
                return

            points = []
            for index, value in enumerate(values):
                x = left + index / max(1, len(values) - 1) * (
                    right - left
                )
                y = bottom - (value - 30) / 70 * (bottom - top)
                points.extend([x, y])

            canvas.create_line(
                *points, fill=color, width=2, smooth=True
            )

        draw_series(list(self.history_cell), "#38bdf8")
        draw_series(list(self.history_rsx), "#f59e0b")

        canvas.create_text(
            left + 40, height - 10,
            text="CELL", fill="#38bdf8"
        )
        canvas.create_text(
            left + 110, height - 10,
            text="RSX", fill="#f59e0b"
        )

    def log_reading(self):
        try:
            with open(LOG_FILE, "a", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow([
                    datetime.now().isoformat(timespec="seconds"),
                    "SIMULATION",
                    self.profile.get(),
                    round(self.cell_temp, 1),
                    round(self.rsx_temp, 1),
                    self.fan_applied,
                    self.get_status()
                ])
        except OSError:
            self.status_label.config(
                text="Aviso: no se pudo escribir el registro CSV."
            )

    def record_reading(self):
        self.log_reading()
        messagebox.showinfo(
            "Registro",
            "Lectura simulada registrada en " + LOG_FILE
        )

    def export_csv(self):
        filename = filedialog.asksaveasfilename(
            title="Exportar historial",
            defaultextension=".csv",
            filetypes=[("Archivos CSV", "*.csv")]
        )

        if not filename:
            return

        try:
            with open(LOG_FILE, "r", newline="", encoding="utf-8") as source:
                data = source.read()

            with open(filename, "w", newline="", encoding="utf-8") as dest:
                dest.write(data)

            messagebox.showinfo(
                "Exportación completada",
                "Historial exportado correctamente."
            )
        except OSError as error:
            messagebox.showerror(
                "Error al exportar",
                str(error)
            )

    def test_alerts(self):
        messagebox.showinfo(
            "Prueba de alertas",
            "Umbral de aviso: {} °C\n"
            "Umbral crítico: {} °C\n\n"
            "Son umbrales configurables de prueba, no límites "
            "oficiales de Sony.".format(WARNING_TEMP, CRITICAL_TEMP)
        )

    def close(self):
        self.running = False
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ColdcoreApp(root)
    root.mainloop()

