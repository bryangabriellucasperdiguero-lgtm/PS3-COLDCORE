"""
PS3 COLDCORE v0.4
Nucleo termico y pruebas automaticas.

IMPORTANTE:
Esta version solo prueba la logica.
No lee sensores reales ni controla el ventilador.
"""

VERSION = "0.4"


class ThermalController:
    def __init__(
        self,
        warning_temp=75.0,
        critical_temp=85.0,
        hysteresis=3.0
    ):
        if warning_temp >= critical_temp:
            raise ValueError(
                "La temperatura de aviso debe ser menor "
                "que la temperatura critica."
            )

        if hysteresis < 0:
            raise ValueError(
                "La histeresis no puede ser negativa."
            )

        self.warning_temp = warning_temp
        self.critical_temp = critical_temp
        self.hysteresis = hysteresis

        self.warning_active = False
        self.critical_active = False

    def evaluate(self, temperature):
        if temperature is None:
            return {
                "temperature": None,
                "warning": False,
                "critical": False,
                "message": "SIN LECTURA"
            }

        if not isinstance(temperature, (int, float)):
            raise TypeError(
                "La temperatura debe ser un numero."
            )

        if temperature < 0 or temperature > 150:
            return {
                "temperature": temperature,
                "warning": False,
                "critical": False,
                "message": "LECTURA NO VALIDA"
            }

        if temperature >= self.critical_temp:
            self.critical_active = True
            self.warning_active = True

        elif temperature >= self.warning_temp:
            self.warning_active = True
            self.critical_active = False

        elif temperature < (
            self.warning_temp - self.hysteresis
        ):
            self.warning_active = False
            self.critical_active = False

        if self.critical_active:
            message = "ALERTA CRITICA"
        elif self.warning_active:
            message = "ADVERTENCIA TERMICA"
        else:
            message = "ESTADO NORMAL"

        return {
            "temperature": temperature,
            "warning": self.warning_active,
            "critical": self.critical_active,
            "message": message
        }


def run_tests():
    controller = ThermalController()

    tests = [
        ("Temperatura normal", 60, False, False),
        ("Aviso termico", 76, True, False),
        ("Alerta critica", 90, True, True),
        ("Vuelta a normal", 60, False, False)
    ]

    passed = 0

    print("=" * 42)
    print("PS3 COLDCORE v" + VERSION)
    print("PRUEBAS DEL NUCLEO TERMICO")
    print("=" * 42)

    for name, temp, warning, critical in tests:
        result = controller.evaluate(temp)

        success = (
            result["warning"] == warning
            and result["critical"] == critical
        )

        if success:
            passed += 1
            status = "OK"
        else:
            status = "ERROR"

        print(
            "[" + status + "] "
            + name
            + " | "
            + result["message"]
        )

    missing = controller.evaluate(None)

    if missing["message"] == "SIN LECTURA":
        passed += 1
        print("[OK] Deteccion de lectura ausente")
    else:
        print("[ERROR] Deteccion de lectura ausente")

    print("-" * 42)
    print("Resultado:", passed, "de 5 pruebas superadas.")

    if passed == 5:
        print("COLDCORE: TODAS LAS PRUEBAS SUPERADAS")
    else:
        print("COLDCORE: HAY PRUEBAS QUE REVISAR")

    print()
    print("NOTA: no se han leido sensores reales.")
    print("NOTA: no se ha controlado ningun ventilador.")


if __name__ == "__main__":
    run_tests()