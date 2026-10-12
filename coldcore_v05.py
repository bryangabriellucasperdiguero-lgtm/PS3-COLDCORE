"""
PS3 COLDCORE v0.5
Aplicacion unificada de monitorizacion termica.

Incluye:
- Interfaz grafica
- Grafica de temperaturas
- Perfiles ECO, BALANCE y RENDIMIENTO
- Alertas termicas con histeresis
- Historial CSV
- Exportacion de muestras
- Pruebas automaticas

IMPORTANTE:
Las temperaturas son simuladas.
No controla el ventilador ni lee sensores de la PS3.
"""

import csv
import random
import tkinter as tk

from collections import deque
from dataclasses import dataclass
from datetime import datetime
from tkinter import ttk, filedialog, messagebox


VERSION = "0.5"
INTERVAL_MS = 2000
MAX_POINTS = 60
CSV_FILE = "coldcore_historial.csv"


# ==================================================
# NUCLEO TERMICO
# ==================================================

@dataclass
class ThermalConfig:
    warning_temp: float = 75.0
    critical_temp: float = 85.0
    hysteresis: float = 3.0


@dataclass
class ThermalStatus:
    temperature: float
    warning: bool
    critical: bool
    message: str


class ThermalController:
    def __init__(self, config=None):
        self.config = config or ThermalConfig()
        self.warning_active = False
        self.critical_active = False

        if self.config.warning_temp >= self.config.critical_temp:
            raise ValueError(
                "El umbral de aviso debe ser inferior "
                "al umbral critico."
            )

        if self.config.hysteresis < 0:
            raise ValueError("La histeresis no puede ser negativa.")

    def evaluate(self, temperature):
        if temperature is None:
            return ThermalStatus(
                temperature=None,
                warning=False,
                critical=False,
                message="SIN LECTURA"
            )

        if not isinstance(temperature, (int, float)):
            raise TypeError("La temperatura debe ser numerica.")

        if not 0 <= temperature <= 150:
            return ThermalStatus(
                temperature=temperature,
                warning=False,
                critical=False,
                message="LECTURA NO VALIDA"
            )

        if temperature >= self.config.critical_temp:
            self.critical_active = True
            self.warning_active = True

        elif temperature >= self.config.warning_temp:
            self.warning_active = True
            self.critical_active = False

        elif temperature < (
            self.config.warning_temp - self.config.hysteresis
        ):
            self.warning_active = False
            self.critical_active = False

        if self.critical_active:
            message = "ALERTA CRITICA"
        elif self.warning_active:
            message = "ADVERTENCIA TERMICA"
        else:
            message = "ESTADO NORMAL"

        return ThermalStatus(
            temperature=temperature,
            warning=self.warning_active,
            critical=self.critical_active,
            message=message
        )


# ==================================================
# APLICACION
# ==================================================

class ColdcoreApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PS3 COLDCORE v" + VERSION)
        self.root.geometry("900x700")
        self.root.minsize(680, 560)

        self.controller_cell = ThermalController()
        self.controller_rsx = ThermalController()

        self.cell_temp = 60.0
        self.rsx_temp = 58.0

        self.history = deque(maxlen=MAX_POINTS)
        self.running = True
        self.after_id = None

        self.profile = tk.StringVar(value="BALANCE")
        self.mode_text = tk.StringVar(value="SIMULACION ACTIVA")
        self.cell_text = tk.StringVar(value="CELL: -- °C")
        self.rsx_text = tk.StringVar(value="RSX: -- °C")
        self.status_text = tk.StringVar(value="Iniciando...")

        self.build_interface()
        self.root.after(300, self.update_simulation)

    def build_interface(self):
        main = ttk.Frame(self.root, padding=14)
        main.pack(fill="both", expand=True)

        ttk.Label(
            main,
            text="PS3 COLDCORE",
            font=("Segoe UI", 22, "bold")
        ).pack(anchor="w")

        ttk.Label(
            main,
            text="Version " + VERSION +
                 " | DATOS SIMULADOS, NO REALES",
            foreground="#c07800"
        ).pack(anchor="w", pady=(0, 12))

        cards = ttk.Frame(main)
        cards.pack(fill="x", pady=5)

        ttk.Label(
            cards,
            textvariable=self.cell_text,
            font=("Segoe UI", 16, "bold")
        ).pack(side="left", padx=(0, 25))

        ttk.Label(
            cards,
            textvariable=self.rsx_text,
            font=("Segoe UI", 16, "bold")
        ).pack(side="left")

        ttk.Label(
            main,
            textvariable=self.status_text,
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", pady=8)

        ttk.Label(
            main,
            text="Historial termico — ultimas 60 muestras"
        ).pack(anchor="w", pady=(8, 4))

        self.chart = tk.Canvas(
            main,
            height=300,
            background="#171b22",
            highlightthickness=1,
            highlightbackground="#444a55"
        )
        self.chart.pack(fill="both", expand=True)
        self.chart.bind(
            "<Configure>",
            lambda event: self.draw_chart()
        )

        controls = ttk.Frame(main)
        controls.pack(fill="x", pady=12)

        ttk.Label(controls, text="Perfil:").pack(side="left")

        self.profile_box = ttk.Combobox(
            controls,
            textvariable=self.profile,
            values=["ECO", "BALANCE", "RENDIMIENTO"],
            state="readonly",
            width=15
        )
        self.profile_box.pack(side="left", padx=8)

        ttk.Button(
            controls,
            text="Exportar CSV",
            command=self.export_history
        ).pack(side="right", padx=(5, 0))

        ttk.Button(
            controls,
            text="Prueba del nucleo",
            command=self.run_self_test
        ).pack(side="right")

        self.sample_text = ttk.Label(
            main,
            text="Muestras: 0"
        )
        self.sample_text.pack(anchor="w")

        ttk.Label(
            main,
            text="Los perfiles solo afectan a la simulacion.",
            foreground="#c07800"
        ).pack(anchor="w", pady=(5, 0))

    # ==============================================
    # SIMULACION
    # ==============================================

    def update_simulation(self):
        if not self.running:
            return

        profile = self.profile.get()

        targets = {
            "ECO": (55.0, 53.0),
            "BALANCE": (65.0, 62.0),
            "RENDIMIENTO": (73.0, 69.0)
        }

        target_cell, target_rsx = targets[profile]

        self.cell_temp += (
            target_cell - self.cell_temp
        ) * 0.15

        self.rsx_temp += (
            target_rsx - self.rsx_temp
        ) * 0.15

        self.cell_temp += random.uniform(-0.8, 0.8)
        self.rsx_temp += random.uniform(-0.8, 0.8)

        cell = round(self.cell_temp, 1)
        rsx = round(self.rsx_temp, 1)

        cell_status = self.controller_cell.evaluate(cell)
        rsx_status = self.controller_rsx.evaluate(rsx)

        messages = [
            cell_status.message,
            rsx_status.message
        ]

        if "ALERTA CRITICA" in messages:
            status = "ALERTA CRITICA — DATOS SIMULADOS"
        elif "ADVERTENCIA TERMICA" in messages:
            status = "ADVERTENCIA — DATOS SIMULADOS"
        else:
            status = "Estado normal — datos simulados"

        self.cell_text.set("CELL: {:.1f} °C".format(cell))
        self.rsx_text.set("RSX: {:.1f} °C".format(rsx))
        self.status_text.set(status)

        sample = {
            "time": datetime.now().isoformat(timespec="seconds"),
            "cell": cell,
            "rsx": rsx,
            "profile": profile,
            "mode": "SIMULACION"
        }

        self.history.append(sample)
        self.save_sample(sample)

        self.sample_text.config(
            text="Muestras en memoria: {}".format(len(self.history))
        )

        self.draw_chart()
        self.after_id = self.root.after(
            INTERVAL_MS,
            self.update_simulation
        )

    # ==============================================
    # HISTORIAL CSV
    # ==============================================

    def save_sample(self, sample):
        try:
            with open(
                CSV_FILE,
                "a",
                newline="",
                encoding="utf-8"
            ) as file:
                writer = csv.writer(file)

                if file.tell() == 0:
                    writer.writerow([
                        "fecha_hora",
                        "CELL_C",
                        "RSX_C",
                        "perfil",
                        "modo"
                    ])

                writer.writerow([
                    sample["time"],
                    sample["cell"],
                    sample["rsx"],
                    sample["profile"],
                    sample["mode"]
                ])

        except OSError as error:
            self.status_text.set(
                "Error guardando CSV: " + str(error)
            )

    def export_history(self):
        if not self.history:
            messagebox.showinfo(
                "COLDCORE",
                "No hay muestras para exportar."
            )
            return

        path = filedialog.asksaveasfilename(
            title="Exportar historial",
            defaultextension=".csv",
            filetypes=[("Archivos CSV", "*.csv")],
            initialfile="coldcore_exportacion.csv"
        )

        if not path:
            return

        try:
            with open(
                path,
                "w",
                newline="",
                encoding="utf-8-sig"
            ) as file:
                writer = csv.writer(file)
                writer.writerow([
                    "fecha_hora",
                    "CELL_C",
                    "RSX_C",
                    "perfil",
                    "modo"
                ])

                for sample in self.history:
                    writer.writerow([
                        sample["time"],
                        sample["cell"],
                        sample["rsx"],
                        sample["profile"],
                        sample["mode"]
                    ])

            messagebox.showinfo(
                "COLDCORE",
                "Historial exportado correctamente."
            )

        except OSError as error:
            messagebox.showerror(
                "Error",
                "No se pudo exportar:\n" + str(error)
            )

    # ==============================================
    # GRAFICA
    # ==============================================

    def draw_chart(self):
        if not hasattr(self, "chart"):
            return

        self.chart.delete("all")

        width = self.chart.winfo_width()
        height = self.chart.winfo_height()

        if width < 100 or height < 100:
            return

        left, right = 48, width - 15
        top, bottom = 20, height - 35

        def y_position(temp):
            return bottom - (
                (temp - 30) / 70
            ) * (bottom - top)

        for temp in range(30, 101, 10):
            y = y_position(temp)

            self.chart.create_line(
                left, y, right, y,
                fill="#343b46"
            )

            self.chart.create_text(
                left - 8, y,
                text=str(temp),
                fill="#c8ced8",
                anchor="e"
            )

        if len(self.history) < 2:
            self.chart.create_text(
                width / 2,
                height / 2,
                text="Recopilando muestras...",
                fill="white"
            )
            return

        samples = list(self.history)

        xs = [
            left + i * (right - left) / (len(samples) - 1)
            for i in range(len(samples))
        ]

        for key, color in [
            ("cell", "#ff765e"),
            ("rsx", "#55c8ff")
        ]:
            coords = []

            for index, sample in enumerate(samples):
                coords.extend([
                    xs[index],
                    y_position(sample[key])
                ])

            self.chart.create_line(
                *coords,
                fill=color,
                width=2
            )

        self.chart.create_text(
            right - 80, top + 5,
            text="CELL",
            fill="#ff765e"
        )

        self.chart.create_text(
            right - 80, top + 23,
            text="RSX",
            fill="#55c8ff"
        )

    # ==============================================
    # PRUEBAS AUTOMATICAS
    # ==============================================

    def run_self_test(self):
        tests = [
            ("Normal", 60, False, False),
            ("Aviso", 76, True, False),
            ("Critica", 90, True, True)
        ]

        passed = 0
        lines = []

        for name, temperature, warning, critical in tests:
            controller = ThermalController()
            result = controller.evaluate(temperature)

            success = (
                result.warning == warning
                and result.critical == critical
            )

            if success:
                passed += 1

            lines.append(
                "{}: {}".format(
                    name,
                    "OK" if success else "ERROR"
                )
            )

        missing = ThermalController().evaluate(None)

        if missing.message == "SIN LECTURA":
            passed += 1
            lines.append("Sin lectura: OK")
        else:
            lines.append("Sin lectura: ERROR")

        messagebox.showinfo(
            "Pruebas de COLDCORE",
            "\n".join(lines)
            + "\n\nResultado: {}/4 pruebas".format(passed)
        )

    # ==============================================
    # CIERRE
    # ==============================================

    def close(self):
        self.running = False

        if self.after_id is not None:
            self.root.after_cancel(self.after_id)

        self.root.destroy()


def main():
    root = tk.Tk()
    app = ColdcoreApp(root)
    root.protocol("WM_DELETE_WINDOW", app.close)
    root.mainloop()


if __name__ == "__main__":
    main()
