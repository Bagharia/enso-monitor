// Page principale : filtre de période, puis courbe, tableau et source selon l'état du chargement.
import { useState } from "react";

import { EpisodeComparison } from "./components/EpisodeComparison";
import { ObservationChart } from "./components/ObservationChart";
import { ObservationTable } from "./components/ObservationTable";
import { PeriodFilter } from "./components/PeriodFilter";
import { SourceNote } from "./components/SourceNote";
import { useEpisodes } from "./hooks/useEpisodes";
import { useObservations } from "./hooks/useObservations";
import type { Period } from "./types";

// Années proposées dans le filtre (à ne pas confondre avec MIN_YEAR / MAX_YEAR de l'ETL,
// qui sont des bornes de validation) : la série RONI commence en 1950.
const FIRST_YEAR = 1950;
const LATEST_YEAR = new Date().getFullYear();

export function App() {
  const [period, setPeriod] = useState<Period>({ startYear: FIRST_YEAR, endYear: LATEST_YEAR });
  const { state: observationsState, retry: retryObservations } = useObservations(period);
  const { state: episodesState, retry: retryEpisodes } = useEpisodes("el_nino");

  return (
    <main>
      <header>
        <h1>ENSO Monitor</h1>
        <p>Suivi d'El Niño et de La Niña avec l'indice NOAA RONI.</p>
      </header>

      <PeriodFilter
        period={period}
        minYear={FIRST_YEAR}
        maxYear={LATEST_YEAR}
        onChange={setPeriod}
      />

      {/* aria-live : le lecteur d'écran annonce le changement d'état (chargement, erreur…) */}
      <section aria-live="polite" aria-busy={observationsState.status === "loading"}>
        {observationsState.status === "loading" && <p>Chargement des données…</p>}

        {observationsState.status === "error" && (
          <div role="alert" className="error">
            <p>{observationsState.message}</p>
            <button type="button" onClick={retryObservations}>
              Réessayer
            </button>
          </div>
        )}

        {observationsState.status === "success" &&
          (observationsState.data.count === 0 ? (
            <p>Aucune valeur sur cette période.</p>
          ) : (
            <>
              <ObservationChart
                observations={observationsState.data.observations}
                indexCode={observationsState.data.index_code}
                unit={observationsState.data.unit}
              />
              <ObservationTable
                observations={observationsState.data.observations}
                unit={observationsState.data.unit}
              />
              <SourceNote
                source={observationsState.data.source}
                indexName={observationsState.data.index_name}
              />
            </>
          ))}
      </section>

      <div aria-live="polite" aria-busy={episodesState.status === "loading"}>
        {episodesState.status === "loading" && <p>Chargement des épisodes…</p>}
        {episodesState.status === "error" && (
          <div role="alert" className="error">
            <p>{episodesState.message}</p>
            <button type="button" onClick={retryEpisodes}>
              Réessayer
            </button>
          </div>
        )}
        {episodesState.status === "success" && (
          <EpisodeComparison episodeList={episodesState.data} />
        )}
      </div>
    </main>
  );
}
