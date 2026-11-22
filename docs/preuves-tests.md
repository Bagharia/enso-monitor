# Preuves d'exécution des tests

- Date : 22/11/2026
- Commit testé : `9e8402f` (`git rev-parse --short HEAD`)
- Commandes : `pytest -v` (dans `backend/`) et `npm test -- --reporter=verbose` (dans `web/`)
- Résultat : **17 passed** (Python) et **7 passed** (front), code de sortie 0 pour les deux.

Les sorties ci-dessous sont copiées telles quelles, sans retouche.

## Les 3 tests minimaux exigés par le sujet

| Exigence | Fichier | Résultat |
|---|---|---|
| Données | `backend/tests/test_transform.py` | 3 passed |
| API : route filtrée par période + entrée invalide | `backend/tests/test_api.py` | 4 passed |
| Front : changer la période met à jour les valeurs | `web/src/App.test.tsx` | 2 passed |

Tests concernés, tels qu'ils apparaissent dans les sorties :
- Données : `test_removes_identical_duplicates_and_invalid_rows`,
  `test_conflicting_values_exclude_the_season`, `test_period_date_is_center_month_of_season`.
- API, route filtrée : `test_returns_observations_within_period` ; entrées invalides :
  `test_rejects_period_with_end_before_start`, `test_rejects_invalid_date_format`
  (le 4e test du fichier, `test_returns_404_when_index_has_no_import_run`, est un bonus).
- Front : `updates displayed values when the period changes` (le 2e test du fichier,
  `shows the API error and reloads the values on retry`, est un bonus).

Les autres tests (règle des épisodes, chargement en base, base indisponible, comparaison,
graduations) vont au-delà du minimum demandé ; ils figurent aussi dans les sorties.

## Backend : `pytest -v`

```text
============================= test session starts ==============================
platform darwin -- Python 3.12.16, pytest-9.2.0, pluggy-1.7.0 -- /Users/alexis/Documents/Code/Projet hetic/enso-monitor/backend/.venv/bin/python3.12
cachedir: .pytest_cache
rootdir: /Users/alexis/Documents/Code/Projet hetic/enso-monitor/backend
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.16.0
collecting ... collected 17 items

tests/test_api.py::test_returns_observations_within_period PASSED        [  5%]
tests/test_api.py::test_rejects_period_with_end_before_start PASSED      [ 11%]
tests/test_api.py::test_rejects_invalid_date_format PASSED               [ 17%]
tests/test_api.py::test_returns_404_when_index_has_no_import_run PASSED  [ 23%]
tests/test_api_database_unavailable.py::test_returns_503_when_database_is_unreachable PASSED [ 29%]
tests/test_api_episodes.py::test_returns_el_nino_episodes PASSED         [ 35%]
tests/test_api_episodes.py::test_rejects_unknown_phase PASSED            [ 41%]
tests/test_episodes.py::test_detects_episode_of_at_least_five_consecutive_seasons PASSED [ 47%]
tests/test_episodes.py::test_ignores_run_shorter_than_five_seasons PASSED [ 52%]
tests/test_episodes.py::test_missing_season_splits_the_run PASSED        [ 58%]
tests/test_episodes.py::test_episode_reaching_end_of_series_is_ongoing PASSED [ 64%]
tests/test_episodes.py::test_la_nina_peak_is_the_lowest_value PASSED     [ 70%]
tests/test_load.py::test_second_identical_import_inserts_nothing PASSED  [ 76%]
tests/test_load.py::test_revised_value_is_updated_and_traced PASSED      [ 82%]
tests/test_transform.py::test_removes_identical_duplicates_and_invalid_rows PASSED [ 88%]
tests/test_transform.py::test_conflicting_values_exclude_the_season PASSED [ 94%]
tests/test_transform.py::test_period_date_is_center_month_of_season PASSED [100%]

=============================== warnings summary ===============================
.venv/lib/python3.12/site-packages/fastapi/testclient.py:1
  /Users/alexis/Documents/Code/Projet hetic/enso-monitor/backend/.venv/lib/python3.12/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 17 passed, 1 warning in 0.81s =========================
```

## Front : `npm test -- --reporter=verbose`

```text

> enso-monitor-web@0.0.0 test
> vitest run --reporter=verbose


 RUN  v5.1.0 /Users/alexis/Documents/Code/Projet hetic/enso-monitor/web

 ✓ src/chartAxis.test.ts > rounds the axis limit up to the next step 1ms
 ✓ src/chartAxis.test.ts > ticks every step, including zero and both thresholds 0ms
 ✓ src/episodeComparison.test.ts > labels an episode spanning two years 1ms
 ✓ src/episodeComparison.test.ts > states comparable peaks, longer duration and the limits 3ms
 ✓ src/episodeComparison.test.ts > mentions an ongoing episode 0ms
 ✓ src/App.test.tsx > updates displayed values when the period changes 100ms
 ✓ src/App.test.tsx > shows the API error and reloads the values on retry 35ms

 Test Files  3 passed (3)
      Tests  7 passed (7)
   Start at  18:51:25
   Duration  1.24s (environment 67%, import 13%, setup 13%, tests 5%, transform 2%)
```
