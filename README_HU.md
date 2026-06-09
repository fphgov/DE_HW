# DE házi feladat

## Mi ez a repo?

Ez egy lokális Airflow fejlesztői környezet. Elő van készítve, hogy az infrastruktúrával ne kelljen foglalkozni — koncentrálj a DAG-ok írására és az adatmérnöki logikára. Bármit megváltoztathatsz, ami nem tetszik.

A repo tartalmaz:

- **Apache Airflow 2.10.4** Dockerben futtatva (webserver + scheduler + Postgres metaadatbázis)
- **`packages/template_package`** — egy Python csomag, ami szerkeszthető módban van telepítve Airflow-ba. Ide kerüljön az újrafelhasználható logika (DB kapcsolatok, transzformációk, segédfüggvények stb.), és a DAG-okból importálható
- **`dags/`** — DAG fájlok; minden ide kerülő `.py` fájlt automatikusan felvesz az Airflow (volume-mount, nincs szükség újraépítésre)

---

## Előfeltételek

- [Docker](https://docs.docker.com/get-docker/) + [Docker Compose](https://docs.docker.com/compose/install/)
- [Poetry](https://python-poetry.org/docs/#installation) (lokális fejlesztéshez és csomagok hozzáadásához)

---

## Első indítás

```bash
docker compose up --build
```

Ez felépíti az image-t, inicializálja az Airflow adatbázist, létrehozza az admin felhasználót, és elindítja az összes szolgáltatást. Kódváltozás nélküli újraindításhoz elég:

```bash
docker compose up
```

---

## Airflow UI

Futás közben elérhető: **http://localhost:8081**

| Felhasználónév | Jelszó  |
|----------------|---------|
| `admin`        | `admin` |

---

## Projekt struktúra

```
.
├── dags/                         # A DAG fájlok ide kerülnek
│   └── example_dag.py
├── packages/
│   └── template_package/         # Az újrafelhasználható Python csomag
│       ├── pyproject.toml        # Függőségek definíciója (ezt szerkeszd)
│       ├── requirements.txt      # Auto-generált — NE szerkeszd kézzel
│       └── template_package/     # A tényleges Python forráskód
├── Dockerfile
├── docker-compose.yml
└── update_requirementy.sh        # Requirements.txt biztonságos újragenerálása
```

---

## DAG-ok írása

A DAG-ok volume-mountolva vannak — hozz létre egy `.py` fájlt a `dags/` mappában, és az Airflow másodperceken belül felveszi. **Nincs szükség újraépítésre.**

A `template_package`-ből való importálás DAG-ban:

```python
from template_package.example_module import my_function
```

A `template_package` **szerkeszthető módban** (editable install) van telepítve a konténerekben, így a forrásfájlok változásai azonnal érvényesülnek újraépítés nélkül.

---

## Python függőség hozzáadása

> ⚠️ Mindig ebben a sorrendben kövesd a lépéseket. A `requirements.txt`-t **ne szerkeszd kézzel**.

```bash
# 1. Csomag hozzáadása Poetry-vel (frissíti a pyproject.toml-t és a poetry.lock-ot)
cd packages/template_package
poetry add <csomagnév>

# 2. Vissza a repo gyökerére, requirements.txt újragenerálása
cd ../..
bash update_requirementy.sh

# 3. Docker image újraépítése az új csomag telepítéséhez
docker compose build --no-cache
docker compose up
```

**Miért kell a script?** A `requirements.txt`-t a `pip-compile` generálja az Airflow constraint fájl felhasználásával. Ez garantálja, hogy az új függőség kompatibilis az Airflow saját pinned verzióival — ha nem az, a script jól látható hibával áll le, mielőtt bármi eltörne.

---

## Requirements frissítése (új csomag hozzáadása nélkül)

Ha kézzel szerkesztetted a `pyproject.toml`-t, vagy upstream változásokat húztál be:

```bash
bash update_requirementy.sh
docker compose build --no-cache
docker compose up
```

---

## Tesztek futtatása

```bash
cd packages/template_package
poetry install          # dev függőségek lokális telepítése
poetry run pytest
```

---

## Leállítás és takarítás

```bash
# Konténerek leállítása (adatok megmaradnak)
docker compose down

# Leállítás és az összes adat törlése (Postgres volume is)
docker compose down -v
```

---

## Függőségkezelés — hogyan működik

A `requirements.txt` **nem** egy sima pip requirements fájl, és **nem** `poetry export`-tal generált. A `pip-compile` állítja elő az [Airflow 2.10.4 constraint fájl](https://raw.githubusercontent.com/apache/airflow/constraints-2.10.4/constraints-3.12.txt) felhasználásával.

Ez azt jelenti:
- Minden pinned verzió garantáltan kompatibilis az Airflow-val
- A `requirements.txt` kommentjei megmutatják, miért éppen az adott verzió lett választva
- A `bash update_requirementy.sh` futtatása mindig biztonságos — ütközés esetén jól látható hibával leáll, ahelyett hogy csendben törött image-t hozna létre
