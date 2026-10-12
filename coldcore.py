import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
import random
from datetime import datetime
from collections import deque

VERSION = "0.3"
INTERVAL_MS = 2000
MAX_POINTS = 60

# DATOS SIMULADOS: no son temperaturas reales de la PS3.
cell_temp = 65.0
rsx_temp = 62.0

history = deque(maxlen=MAX_POINTS)
running = True
csv_file = "coldcore_historial.csv"

root = tk.Tk()
root.title(f"PS3 COLDCORE v{VERSION}")
root.geometry("850x650")
root.minsize(650, 520)

style = ttk.Style()
style.configure("Title.TLabel", font=("Segoe UI", 20, "bold"))
style.configure("Temp.TLabel", font=("Segoe UI", 15, "bold"))

main = ttk.Frame(root, padding=16)
main.pack(fill="both", expand=True)

ttk.Label(
    main, text="PS3 COLDCORE",
    style="Title.TLabel"
).pack(anchor="w")

ttk.Label(
    main,
    text="Prototipo para PC | MODO SIMULACIÓN",
    foreground="#c07800"
).pack(anchor="w", pady=(0, 12))

# Temperaturas simuladas
cards = ttk.Frame(main)
cards.pack(fill="x", pady=5)

cell_label = ttk.Label(
    cards, text="CELL: -- °C",
    style="Temp.TLabel"
)
cell_label.pack(side="left", padx=(0, 30))

rsx_label = ttk.Label(
    cards, text="RSX: -- °C",
    style="Temp.TLabel"
)
rsx_label.pack(side="left")

status_label = ttk.Label(
    main, text="Estado: iniciando simulación..."
)
status_label.pack(anchor="w", pady=8)

# Gráfica
ttk.Label(
    main, text="Historial térmico (últimas 60 muestras)"
).pack(anchor="w", pady=(8, 4))

chart = tk.Canvas(
    main,
    height=300,
    background="#171b22",
    highlightthickness=1,
    highlightbackground="#444a55"
)
chart.pack(fill="both", expand=True)

# Controles
controls = ttk.Frame(main)
controls.pack(fill="x", pady=12)

profile = tk.StringVar(value="BALANCE")

ttk.Label(controls, text="Perfil:").pack(side="left")

profile_box = ttk.Combobox(
    controls,
    textvariable=profile,
    values=["ECO", "BALANCE", "RENDIMIENTO"],
    state="readonly",
    width=16
)
profile_box.pack(side="left", padx=8)

sample_label = ttk.Label(controls, text="Muestras: 0")
sample_label.pack(side="left", padx=12)


def draw_chart():
    chart.delete("all")

    width = chart.winfo_width()
    height = chart.winfo_height()

    if width < 100 or height < 100:
        return

    left, right = 48, width - 15
    top, bottom = 20, height - 35

    # Escala fija de 30 a 100 °C
    min_temp, max_temp = 30, 100

    def y_position(temp):
        return bottom - (
            (temp - min_temp) / (max_temp - min_temp)
        ) * (bottom - top)

    # Líneas horizontales y etiquetas
    for temp in range(30, 101, 10):
        y = y_position(temp)
        chart.create_line(
            left, y, right, y,
            fill="#343b46"
        )
        chart.create_text(
            left - 8, y,
            text=str(temp),
            fill="#c8ced8",
            anchor="e"
        )

    chart.create_text(
        8, 8, text="°C",
        fill="#c8ced8", anchor="nw"
    )

    if len(history) < 2:
        chart.create_text(
            width / 2, height / 2,
            text="Esperando muestras...",
            fill="white"
        )
        return

    points_x = [
        left + i * (right - left) / (len(history) - 1)
        for i in range(len(history))
    ]

    for key, color in [
        ("cell", "#ff765e"),
        ("rsx", "#55c8ff")
    ]:
        coordinates = []

        for i, sample in enumerate(history):
            coordinates.extend([
                points_x[i],
                y_position(sample[key])
            ])

        chart.create_line(
            *coordinates,
            fill=color,
            width=2,
            smooth=False
        )

    chart.create_text(
        right - 95, top + 5,
        text="CELL",
        fill="#ff765e",
        anchor="w"
    )
    chart.create_text(
        right - 95, top + 23,
        text="RSX",
        fill="#55c8ff",
        anchor="w"
    )


def save_sample(sample):
    file_exists = False

    try:
        with open(csv_file, "r", newline="", encoding="utf-8"):
            file_exists = True
    except FileNotFoundError:
        pass

    with open(csv_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow([
                "fecha_hora",
                "CELL_C_simulada",
                "RSX_C_simulada",
                "perfil"
            ])

        writer.writerow([
            sample["time"],
            sample["cell"],
            sample["rsx"],
            sample["profile"]
        ])


def export_history():
    if not history:
        messagebox.showinfo(
            "COLDCORE",
            "Todavía no hay muestras para exportar."
        )
        return

    path = filedialog.asksaveasfilename(
        title="Exportar historial",
        defaultextension=".csv",
        filetypes=[("Archivo CSV", "*.csv")],
        initialfile="coldcore_historial.csv"
    )

    if not path:
        return

    try:
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow([
                "fecha_hora",
                "CELL_C_simulada",
                "RSX_C_simulada",
                "perfil"
            ])

            for sample in history:
                writer.writerow([
                    sample["time"],
                    sample["cell"],
                    sample["rsx"],
                    sample["profile"]
                ])

        messagebox.showinfo(
            "COLDCORE",
            f"Historial exportado correctamente:\n{path}"
        )
    except OSError as error:
        messagebox.showerror(
            "Error al exportar", str(error)
        )


def update():
    global cell_temp, rsx_temp

    if not running:
        return

    selected = profile.get()

    # Solo cambia el comportamiento de la simulación.
    # No controla el ventilador de la consola.
    if selected == "ECO":
        target_cell, target_rsx = 58, 56
    elif selected == "RENDIMIENTO":
        target_cell, target_rsx = 72, 68
    else:
        target_cell, target_rsx = 65, 62

    cell_temp += (target_cell - cell_temp) * 0.15
    rsx_temp += (target_rsx - rsx_temp) * 0.15

    cell_temp += random.uniform(-0.8, 0.8)
    rsx_temp += random.uniform(-0.8, 0.8)

    sample = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "cell": round(cell_temp, 1),
        "rsx": round(rsx_temp, 1),
        "profile": selected
    }

    history.append(sample)

    cell_label.config(
        text=f"CELL: {sample['cell']:.1f} °C"
    )
    rsx_label.config(
        text=f"RSX: {sample['rsx']:.1f} °C"
    )

    status_label.config(
        text=f"Estado: simulación activa | Perfil {selected}"
    )

    sample_label.config(
        text=f"Muestras: {len(history)}"
    )

    try:
        save_sample(sample)
    except OSError as error:
        status_label.config(
            text=f"No se pudo guardar el CSV: {error}"
        )

    draw_chart()
    root.after(INTERVAL_MS, update)


ttk.Button(
    controls,
    text="Exportar CSV",
    command=export_history
).pack(side="right")

chart.bind("<Configure>", lambda event: draw_chart())

def close_app():
    global running
    running = False
    root.destroy()

root.protocol("WM_DELETE_WINDOW", close_app)

root.after(500, update)
root.mainloop()
