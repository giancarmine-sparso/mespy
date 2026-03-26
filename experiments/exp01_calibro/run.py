from pathlib import Path
import sys


# Aggiunge la root del repository al path per usare `from scripts ...`
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.stats_utils import covariance, standard_deviation, variance


def main():
    print("Import dei moduli riuscito.")
    print("Funzioni disponibili:", variance.__name__, covariance.__name__, standard_deviation.__name__)


if __name__ == "__main__":
    main()
