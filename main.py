import tkinter as tk
from tkinter import ttk
from datetime import datetime
import random
import csv
from pathlib import Path

# ==================================================
# PS3 COLDCORE v0.2
# Prototipo para PC: TODAS las lecturas son simuladas.
# No controla ni monitoriza una PS3 real.
# ==================================================

BG = "#10151c"
PANEL = "#1b2530"
TEXT = "#e8f0f7"
ACCENT = "#42d9c3"
WARNING = "#f2c879"

CARPETA = Path(__file__).resolve().parent
ARCHIVO_CSV = CARPETA / "coldcore_historial.csv"

temperatura_cell = 54.0
temperatura_rsx = 57.0
velocidad_ventilador = 32
modo = None
historial = []
ultimo_modo = "BALANCE"

# ---------------- Ventana principal ----------------

root = tk.Tk()
root.title("PS3 COLDCORE | Thermal Dashboard v0.2")
root.geometry("900x650")
root.minsize(720, 540)
root.configure(bg=BG)

modo = tk.StringVar(value="BALANCE")

style = ttk.Style()
style.theme_use("clam")
style.configure(
    "TCombobox",
    fieldbackground=PANEL,
    background=PANEL,
    foreground=TEXT
)

# ---------------- Funciones de interfaz ----------------

def crear_panel(parent, titulo, valor_inicial):
    panel = tk.Frame(parent, bg=PANEL, padx=18, pady=14)

    tk.Label(
        panel,
        text=titulo,
        bg=PANEL,
        fg="#9aabba",
        font=("Segoe UI", 11)
    ).pack(anchor="w")

    valor = tk.Label(
        panel,
        text=valor_inicial,
        bg=PANEL,
        fg=ACCENT,
        font=("Segoe UI", 25, "bold")
    )
    valor.pack(anchor="w", pady=(8, 0))

    return panel, valor


def escribir_registro(mensaje):
    hora = datetime.now().strftime("%H:%M:%S")

    registro.configure(state="normal")
    registro.insert("end", f"[{hora}] {mensaje}\n")
    registro.see("end")
    registro.configure(state="disabled")


# ---------------- Guardar muestras ----------------

def guardar_muestra():
    muestra = {
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "cell": round(temperatura_cell, 1),
        "rsx": round(temperatura_rsx, 1),
        "ventilador": velocidad_ventilador,
        "modo": modo.get()
    }

    historial.append(muestra)

    escribir_registro(
        f"Muestra guardada: Cell {muestra['cell']} °C, "
        f"RSX {muestra['rsx']} °C, "
        f"ventilador {muestra['ventilador']} % (simulados)"
    )


def exportar_historial():
    if not historial:
        escribir_registro(
            "No hay muestras guardadas. Pulsa primero «Guardar muestra»."
        )
        return

    try:
        with open(
            ARCHIVO_CSV,
            "w",
            newline="",
            encoding="utf-8-sig"
        ) as archivo:
            escritor = csv.writer(archivo)

            escritor.writerow([
                "Fecha y hora",
                "Temperatura Cell (C)",
                "Temperatura RSX (C)",
                "Ventilador (%)",
                "Modo",
                "Tipo de datos"
            ])

            for muestra in historial:
                escritor.writerow([
                    muestra["fecha"],
                    muestra["cell"],
                    muestra["rsx"],
                    muestra["ventilador"],
                    muestra["modo"],
                    "SIMULADOS"
                ])

        escribir_registro(
            f"Exportación correcta: {ARCHIVO_CSV.name}"
        )
        escribir_registro(
            f"Ubicación: {ARCHIVO_CSV}"
        )

    except OSError as error:
        escribir_registro(f"Error al exportar: {error}")


# ---------------- Modos de interfaz ----------------

def cambiar_modo(event=None):
    escribir_registro(
        f"Modo seleccionado: {modo.get()} "
        "(solo afecta al prototipo)"
    )
    estado.config(text=f"Modo de simulación: {modo.get()}")


# ---------------- Simulación térmica ----------------

def actualizar():
    global temperatura_cell
    global temperatura_rsx
    global velocidad_ventilador

    # Datos ficticios para probar la interfaz.
    temperatura_cell = max(
        40.0,
        min(80.0, temperatura_cell + random.uniform(-0.8, 0.8))
    )

    temperatura_rsx = max(
        40.0,
        min(80.0, temperatura_rsx + random.uniform(-0.8, 0.8))
    )

    velocidad_ventilador = max(
        20,
        min(75, velocidad_ventilador + random.randint(-2, 2))
    )

    label_cell.config(text=f"{temperatura_cell:.1f} °C*")
    label_rsx.config(text=f"{temperatura_rsx:.1f} °C*")
    label_fan.config(text=f"{velocidad_ventilador} %*")

    root.after(2000, actualizar)


# ---------------- Construcción de la interfaz ----------------

header = tk.Frame(root, bg=BG, padx=24, pady=20)
header.pack(fill="x")

tk.Label(
    header,
    text="PS3 COLDCORE",
    bg=BG,
    fg=ACCENT,
    font=("Segoe UI", 24, "bold")
).pack(anchor="w")

tk.Label(
    header,
    text="THERMAL CONTROL CENTER | PROTOTIPO 0.2",
    bg=BG,
    fg=TEXT,
    font=("Segoe UI", 10)
).pack(anchor="w", pady=(4, 0))

tk.Label(
    header,
    text="MODO SIMULACIÓN: NO CONECTADO A LA PS3",
    bg=BG,
    fg=WARNING,
    font=("Segoe UI", 10, "bold")
).pack(anchor="w", pady=(8, 0))

# Tarjetas térmicas

cards = tk.Frame(root, bg=BG, padx=24)
cards.pack(fill="x")

panel_cell, label_cell = crear_panel(cards, "CELL · CPU", "54.0 °C*")
panel_rsx, label_rsx = crear_panel(cards, "RSX · GPU", "57.0 °C*")
panel_fan, label_fan = crear_panel(cards, "VENTILADOR", "32 %*")

for panel in (panel_cell, panel_rsx, panel_fan):
    panel.pack(
        side="left",
        fill="both",
        expand=True,
        padx=(0, 10)
    )

tk.Label(
    root,
    text="* Valores generados aleatoriamente; no son mediciones reales.",
    bg=BG,
    fg="#9aabba",
    font=("Segoe UI", 9)
).pack(anchor="w", padx=24, pady=(8, 0))

# Controles

controls = tk.Frame(root, bg=BG, padx=24, pady=16)
controls.pack(fill="x")

tk.Label(
    controls,
    text="MODO DE OPERACIÓN",
    bg=BG,
    fg=TEXT,
    font=("Segoe UI", 11, "bold")
).pack(anchor="w")

selector = ttk.Combobox(
    controls,
    textvariable=modo,
    values=("ECO", "BALANCE", "RENDIMIENTO"),
    state="readonly",
    width=22
)
selector.pack(anchor="w", pady=8)
selector.bind("<<ComboboxSelected>>", cambiar_modo)

estado = tk.Label(
    controls,
    text="Simulación activa",
    bg=BG,
    fg=WARNING,
    font=("Segoe UI", 10)
)
estado.pack(anchor="w", pady=(0, 8))

botones = tk.Frame(controls, bg=BG)
botones.pack(anchor="w")

tk.Button(
    botones,
    text="Guardar muestra",
    command=guardar_muestra,
    bg=ACCENT,
    fg=BG,
    activebackground="#70f0dc",
    relief="flat",
    padx=12,
    pady=7,
    font=("Segoe UI", 10, "bold")
).pack(side="left", padx=(0, 8))

tk.Button(
    botones,
    text="Exportar historial CSV",
    command=exportar_historial,
    bg=PANEL,
    fg=TEXT,
    activebackground="#293846",
    relief="flat",
    padx=12,
    pady=7,
    font=("Segoe UI", 10)
).pack(side="left")

# Registro de actividad

log_frame = tk.Frame(root, bg=BG, padx=24, pady=8)
log_frame.pack(fill="both", expand=True)

tk.Label(
    log_frame,
    text="REGISTRO DE SESIÓN",
    bg=BG,
    fg=TEXT,
    font=("Segoe UI", 11, "bold")
).pack(anchor="w", pady=(0, 8))

registro = tk.Text(
    log_frame,
    height=7,
    bg=PANEL,
    fg=TEXT,
    insertbackground=TEXT,
    relief="flat",
    font=("Consolas", 9),
    state="disabled"
)
registro.pack(fill="both", expand=True)

# ---------------- Inicio ----------------

escribir_registro("PS3 COLDCORE v0.2 iniciado.")
escribir_registro("Las lecturas térmicas son simuladas.")
escribir_registro("Guarda muestras y expórtalas a CSV.")

actualizar()
root.mainloop()
