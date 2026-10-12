"""
PS3 COLDCORE v0.6
Sistema modular de adquisicion de datos.

SIMULATION: genera datos ficticios.
REAL: requiere una fuente real validada.
OFFLINE: no presenta temperaturas inventadas.

Esta version NO controla el ventilador de la PS3.
"""

import csv
import random
import tkinter as tk

from collections import deque
from dataclasses import dataclass
from datetime import datetime
from tkinter import ttk, filedialog, messagebox


VERSION = "0.6"
INTERVAL_MS = 2000
MAX_POINTS = 60
CSV_FILE = "coldcore_historial.csv"


# ==================================================
# MODELOS DE DATOS
# ==================================================

@dataclass
class TemperatureReading:
    timestamp: str
    cell: float = None
    rsx: float = None
    source: str = "OFFLINE"
    valid: bool = False
    message: str = "Sin datos"


@dataclass
class ThermalConfig:
    warning_temp: float = 75.0
    critical_temp: float = 85.0
    hysteresis: float = 3.0


@dataclass
class ThermalStatus:
    temperature: float = None
    warning: bool = False
    critical: bool = False
    message: str = "SIN LECTURA"


# ==================================================
# FUENTES DE DATOS
# ==================================================

class SimulationSource:
    """Fuente de prueba. Nunca produce datos reales."""

    def __init__(self):
        self.cell = 60.0
        self.rsx = 58.0

    def read(self, profile):
        targets = {
            "ECO": (55.0, 53.0),
            "BALANCE": (65.0, 62.0),
            "RENDIMIENTO": (73.0, 69.0)
        }

        target_cell, target_rsx = targets[profile]

        self.cell += (target_cell - self.cell) * 0.15
        self.rsx += (target_rsx - self.rsx) * 0.15

        self.cell += random.uniform(-0.8, 0.8)
        self.rsx += random.uniform(-0.8, 0.8)

        return TemperatureReading(
            timestamp=datetime.now().isoformat(
                timespec="seconds"
            ),
            cell=round(self.cell, 1),
            rsx=round(self.rsx, 1),
            source="SIMULATION",
            valid=True,
            message="SIMULACION: datos ficticios"
        )


class RealDataSource:
    """
    Adaptador reservado para una fuente real validada.

    No inventa valores ni se conecta por su cuenta.
    Hasta implementar un protocolo compatible, devuelve
    un estado sin datos.
    """

    def read(self, profile=None):
        return TemperatureReading(
            timestamp=datetime.now().isoformat(
                timespec="seconds"
            ),
            source="REAL",
            valid=False,
            message="Fuente real no configurada"
        )


class OfflineSource:
    """Fuente sin conexión."""

    def read(self, profile=None):
        return TemperatureReading(
            timestamp=datetime.now().isoformat(
                timespec="seconds"
            ),
            source="OFFLINE",
            valid=False,
            message="Sin conexion a una fuente de datos"
        )


# ==================================================
# NUCLEO TERMICO
# ==================================================

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
            raise ValueError(
                "La histeresis no puede ser negativa."
            )

    def evaluate(self, temperature):
        if temperature is None:
            self.warning_active = False
            self.critical_active = False

            return ThermalStatus(
                message="SIN LECTURA"
            )

        if not isinstance(temperature, (int, float)):
            raise TypeError(
                "La temperatura debe ser numerica."
            )

        if not 0 <= temperature <= 150:
            return ThermalStatus(
                temperature=temperature,
                message="LECTURA NO VALIDA"
            )

        if temperature >= self.config.critical_temp:
            self.critical_active = True
            self.warning_active = True

        elif temperature >= self.config.warning_temp:
            self.critical_active = False
            self.warning_active = True

        elif temperature < (
            self.config.warning_temp - self.config.hysteresis
        ):
            self.critical_active = False
            self.warning_active = False

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
# APLICACION PRINCIPAL
# ==================================================

class ColdcoreApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PS3 COLDCORE v" + VERSION)
        self.root.geometry("920x720")
        self.root.minsize(680, 560)

        self.simulation = SimulationSource()
        self.real_source = RealDataSource()
        self.offline_source = OfflineSource()

        self.controller_cell = ThermalController()
        self.controller_rsx = ThermalController()

        self.history = deque(maxlen=MAX_POINTS)
        self.running = True
        self.after_id = None

        self.profile = tk.StringVar(value="BALANCE")
        self.mode = tk.StringVar(value="SIMULATION")

        self.cell_text = tk.StringVar(value="CELL: -- °C")
        self.rsx_text = tk.StringVar(value="RSX: -- °C")
        self.status_text = tk.StringVar(value="Esperando datos...")
        self.source_text = tk.StringVar(value="Fuente: SIMULACION")

        self.build_interface()
        self.root.after(300, self.update_data)

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
                 " | ADQUISICION MODULAR DE DATOS",
            foreground="#c07800"
        ).pack(anchor="w", pady=(0, 10))

        modes = ttk.Frame(main)
        modes.pack(fill="x", pady=5)

        ttk.Label(modes, text="Fuente:").pack(side="left")

        ttk.Combobox(
            modes,
            textvariable=self.mode,
            values=["SIMULATION", "REAL", "OFFLINE"],
            state="readonly",
            width=16
        ).pack(side="left", padx=8)

        ttk.Label(modes, text="Perfil:").pack(
            side="left", padx=(12, 0)
        )

        ttk.Combobox(
            modes,
            textvariable=self.profile,
            values=["ECO", "BALANCE", "RENDIMIENTO"],
            state="readonly",
            width=16
        ).pack(side="left", padx=8)

        ttk.Label(
            main,
            textvariable=self.source_text
        ).pack(anchor="w", pady=5)

        readings = ttk.Frame(main)
        readings.pack(fill="x", pady=8)

        ttk.Label(
            readings,
            textvariable=self.cell_text,
            font=("Segoe UI", 16, "bold")
        ).pack(side="left", padx=(0, 25))

        ttk.Label(
            readings,
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
            text="Historial de temperaturas"
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

        ttk.Button(
            controls,
            text="Actualizar ahora",
            command=self.update_data
        ).pack(side="left")

        ttk.Button(
            controls,
            text="Exportar CSV",
            command=self.export_history
        ).pack(side="right")

        self.sample_label = ttk.Label(
            main,
            text="Muestras: 0"
        )
        self.sample_label.pack(anchor="w")

        ttk.Label(
            main,
            text="El modo REAL no funcionara hasta conectar "
                 "una fuente compatible y validada.",
            foreground="#c07800",
            wraplength=780
        ).pack(anchor="w", pady=(5, 0))

    # ==============================================
    # ADQUISICION
    # ==============================================

    def get_source(self):
        mode = self.mode.get()

        if mode == "SIMULATION":
            return self.simulation

        if mode == "REAL":
            return self.real_source

        return self.offline_source

    def update_data(self):
        if not self.running:
            return

        try:
            source = self.get_source()

            if self.mode.get() == "SIMULATION":
                reading = source.read(self.profile.get())
            else:
                reading = source.read()

            self.source_text.set(
                "Fuente: {} | {}".format(
                    reading.source,
                    reading.message
                )
            )

            if not reading.valid:
                self.cell_text.set("CELL: SIN DATOS")
                self.rsx_text.set("RSX: SIN DATOS")
                self.status_text.set(
                    "Sin lecturas verificadas"
                )

            else:
                cell_status = self.controller_cell.evaluate(
                    reading.cell
                )
                rsx_status = self.controller_rsx.evaluate(
                    reading.rsx
                )

                self.cell_text.set(
                    "CELL: {:.1f} °C".format(reading.cell)
                )
                self.rsx_text.set(
                    "RSX: {:.1f} °C".format(reading.rsx)
                )

                if (
                    cell_status.critical
                    or rsx_status.critical
                ):
                    status = "ALERTA CRITICA"
                elif (
                    cell_status.warning
                    or rsx_status.warning
                ):
                    status = "ADVERTENCIA TERMICA"
                else:
                    status = "Estado normal"

                if reading.source == "SIMULATION":
                    status += " — SIMULADO"

                self.status_text.set(status)

                sample = {
                    "time": reading.timestamp,
                    "cell": reading.cell,
                    "rsx": reading.rsx,
                    "profile": self.profile.get(),
                    "source": reading.source
                }

                self.history.append(sample)
                self.save_sample(sample)

            self.sample_label.config(
                text="Muestras validas en memoria: {}".format(
                    len(self.history)
                )
            )

            self.draw_chart()

        except Exception as error:
            self.status_text.set(
                "Error de adquisicion: " + str(error)
            )

        self.after_id = self.root.after(
            INTERVAL_MS,
            self.update_data
        )

    # ==============================================
    # CSV
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
                        "fuente"
                    ])

                writer.writerow([
                    sample["time"],
                    sample["cell"],
                    sample["rsx"],
                    sample["profile"],
                    sample["source"]
                ])

        except OSError as error:
            self.status_text.set(
                "Error guardando CSV: " + str(error)
            )

    def export_history(self):
        if not self.history:
            messagebox.showinfo(
                "COLDCORE",
                "No hay muestras validas para exportar."
            )
            return

        path = filedialog.asksaveasfilename(
            title="Exportar historial",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile="coldcore_historial.csv"
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
                    "fuente"
                ])

                for sample in self.history:
                    writer.writerow([
                        sample["time"],
                        sample["cell"],
                        sample["rsx"],
                        sample["profile"],
                        sample["source"]
                    ])

            messagebox.showinfo(
                "COLDCORE",
                "Exportacion completada."
            )

        except OSError as error:
            messagebox.showerror(
                "Error",
                str(error)
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

        samples = list(self.history)

        if len(samples) < 2:
            self.chart.create_text(
                width / 2,
                height / 2,
                text="Esperando muestras validas...",
                fill="white"
            )
            return

        xs = [
            left + i * (right - left) / (len(samples) - 1)
            for i in range(len(samples))
        ]

        for key, color in [
            ("cell", "#ff765e"),
            ("rsx", "#55c8ff")
        ]:
            coords = []

            for i, sample in enumerate(samples):
                coords.extend([
                    xs[i],
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
