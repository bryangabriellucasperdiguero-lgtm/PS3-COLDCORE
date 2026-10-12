import math
import time
import unittest


# PS3 COLDCORE v0.7
# Núcleo de seguridad térmica.
# No lee temperaturas reales ni controla el ventilador.

WARNING_TEMP = 75.0
CRITICAL_TEMP = 85.0
HYSTERESIS = 3.0
MAX_READING_AGE = 10.0


def valid_temperature(value):
    """Comprueba que una temperatura sea un número válido."""
    if isinstance(value, bool):
        return False

    if not isinstance(value, (int, float)):
        return False

    if not math.isfinite(value):
        return False

    return 0.0 <= value <= 120.0


class ThermalSafety:

    def __init__(self):
        self.previous_level = "NORMAL"

    def evaluate(self, cell, rsx, timestamp, source="SIMULATION",
                 valid=True, now=None):

        if now is None:
            now = time.time()

        # Los datos simulados nunca autorizan acciones sobre hardware.
        if source != "REAL":
            return {
                "level": "NO_REAL_DATA",
                "message": "Fuente no real. Sin acciones sobre la consola.",
                "allow_automatic_action": False
            }

        if not valid:
            return {
                "level": "INVALID",
                "message": "La fuente indica una lectura inválida.",
                "allow_automatic_action": False
            }

        if not isinstance(timestamp, (int, float)):
            return {
                "level": "INVALID",
                "message": "Marca de tiempo inválida.",
                "allow_automatic_action": False
            }

        if not math.isfinite(timestamp):
            return {
                "level": "INVALID",
                "message": "Marca de tiempo no válida.",
                "allow_automatic_action": False
            }

        age = now - timestamp

        if age < -2:
            return {
                "level": "INVALID",
                "message": "La lectura tiene una fecha futura.",
                "allow_automatic_action": False
            }

        if age > MAX_READING_AGE:
            return {
                "level": "STALE",
                "message": "La lectura está demasiado antigua.",
                "allow_automatic_action": False
            }

        if not valid_temperature(cell):
            return {
                "level": "INVALID",
                "message": "Temperatura CELL inválida.",
                "allow_automatic_action": False
            }

        if not valid_temperature(rsx):
            return {
                "level": "INVALID",
                "message": "Temperatura RSX inválida.",
                "allow_automatic_action": False
            }

        hottest = max(cell, rsx)

        if hottest >= CRITICAL_TEMP:
            self.previous_level = "CRITICAL"
            return {
                "level": "CRITICAL",
                "message": "Temperatura crítica. Revisa la consola.",
                "allow_automatic_action": False
            }

        if hottest >= WARNING_TEMP:
            self.previous_level = "WARNING"
            return {
                "level": "WARNING",
                "message": "Temperatura elevada.",
                "allow_automatic_action": False
            }

        # Evita quitar la alerta inmediatamente al bajar la temperatura.
        if self.previous_level == "CRITICAL":
            if hottest > CRITICAL_TEMP - HYSTERESIS:
                return {
                    "level": "WARNING",
                    "message": "Descendiendo desde temperatura crítica.",
                    "allow_automatic_action": False
                }

        if self.previous_level in ("WARNING", "CRITICAL"):
            if hottest > WARNING_TEMP - HYSTERESIS:
                self.previous_level = "WARNING"
                return {
                    "level": "WARNING",
                    "message": "La temperatura está bajando.",
                    "allow_automatic_action": False
                }

        self.previous_level = "NORMAL"

        return {
            "level": "NORMAL",
            "message": "Lecturas dentro de los límites configurados.",
            "allow_automatic_action": False
        }


# --------------------------------------------------
# PRUEBAS AUTOMÁTICAS
# --------------------------------------------------

class TestColdcore(unittest.TestCase):

    def setUp(self):
        self.safety = ThermalSafety()
        self.now = 1000.0

    def check(self, cell=60, rsx=60, age=0,
              source="REAL", valid=True):
        return self.safety.evaluate(
            cell=cell,
            rsx=rsx,
            timestamp=self.now - age,
            source=source,
            valid=valid,
            now=self.now
        )

    def test_normal(self):
        self.assertEqual(
            self.check()["level"], "NORMAL"
        )

    def test_warning(self):
        self.assertEqual(
            self.check(cell=75)["level"], "WARNING"
        )

    def test_critical(self):
        self.assertEqual(
            self.check(rsx=85)["level"], "CRITICAL"
        )

    def test_invalid_temperature(self):
        self.assertEqual(
            self.check(cell=None)["level"], "INVALID"
        )

    def test_nan_temperature(self):
        self.assertEqual(
            self.check(cell=float("nan"))["level"], "INVALID"
        )

    def test_infinite_temperature(self):
        self.assertEqual(
            self.check(rsx=float("inf"))["level"], "INVALID"
        )

    def test_old_reading(self):
        self.assertEqual(
            self.check(age=20)["level"], "STALE"
        )

    def test_simulated_source(self):
        result = self.check(source="SIMULATION")
        self.assertEqual(result["level"], "NO_REAL_DATA")
        self.assertFalse(result["allow_automatic_action"])

    def test_invalid_reading_flag(self):
        self.assertEqual(
            self.check(valid=False)["level"], "INVALID"
        )

    def test_boolean_temperature(self):
        self.assertEqual(
            self.check(cell=True)["level"], "INVALID"
        )


if __name__ == "__main__":
    print("================================")
    print(" PS3 COLDCORE v0.7")
    print(" Pruebas de seguridad térmica")
    print("================================")

    unittest.main(verbosity=2)

