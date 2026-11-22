// Tests front : changer la période actualise les valeurs ; une erreur d'API peut être réessayée.
import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, test, vi } from "vitest";

import { App } from "./App";
import type {
  EpisodeListResponse,
  ObservationListResponse,
  ObservationResponse,
  SourceResponse,
} from "./types";

// Valeurs réelles du fichier NOAA RONI (extraction du 14/11/2026).
const OBSERVATIONS: ObservationResponse[] = [
  { season: "NDJ", year: 1997, period_date: "1997-12-01", value: 2.28 },
  { season: "NDJ", year: 2015, period_date: "2015-12-01", value: 2.25 },
];

const SOURCE: SourceResponse = {
  provider: "NOAA Climate Prediction Center",
  url: "https://www.cpc.ncep.noaa.gov/data/indices/RONI.ascii.txt",
  extracted_on: "2026-11-14",
};

// Fausse API : renvoie seulement les observations comprises dans la période demandée.
// La route des épisodes n'est pas l'objet de ce test : elle renvoie une liste vide.
function fakeApi(url: string): Response {
  const { pathname, searchParams: parameters } = new URL(url);
  if (pathname.endsWith("/episodes")) {
    const emptyEpisodes: EpisodeListResponse = {
      index_code: "RONI",
      unit: "°C",
      source: SOURCE,
      phase: "el_nino",
      episode_threshold: 0.5,
      min_episode_seasons: 5,
      episodes: [],
    };
    return new Response(JSON.stringify(emptyEpisodes), { status: 200 });
  }
  const start = parameters.get("start") ?? "";
  const end = parameters.get("end") ?? "";
  const observations = OBSERVATIONS.filter(
    (observation) => observation.period_date >= start && observation.period_date <= end,
  );
  const body: ObservationListResponse = {
    index_code: "RONI",
    index_name: "Relative Oceanic Niño Index",
    unit: "°C",
    source: SOURCE,
    start,
    end,
    count: observations.length,
    observations,
  };
  return new Response(JSON.stringify(body), { status: 200 });
}

afterEach(() => {
  cleanup(); // retire la page rendue par le test précédent
  vi.unstubAllGlobals();
});

test("updates displayed values when the period changes", async () => {
  const fetchMock = vi.fn(async (url: string) => fakeApi(url));
  vi.stubGlobal("fetch", fetchMock);
  const user = userEvent.setup();
  render(<App />);

  // Période par défaut (1950 → année en cours) : les deux valeurs sont affichées.
  const table = await screen.findByRole("table");
  expect(within(table).getAllByRole("row")).toHaveLength(3); // en-tête + 2 valeurs

  // L'utilisateur choisit 2010 comme année de début.
  await user.selectOptions(screen.getByLabelText("De"), "2010");

  // L'API est rappelée avec la nouvelle période, et seule la valeur de 2015 reste.
  expect(fetchMock).toHaveBeenLastCalledWith(
    expect.stringContaining("start=2010-01-01"),
    expect.anything(),
  );
  const updatedTable = await screen.findByRole("table");
  await vi.waitFor(() => expect(within(updatedTable).getAllByRole("row")).toHaveLength(2));
  expect(within(updatedTable).getByText("2015")).toBeInTheDocument();
  expect(within(updatedTable).queryByText("1997")).not.toBeInTheDocument();
});

test("shows the API error and reloads the values on retry", async () => {
  // 1re demande d'observations : l'API répond 503 (base arrêtée). Ensuite : réponse normale.
  let isDatabaseDown = true;
  const fetchMock = vi.fn(async (url: string) => {
    if (isDatabaseDown && url.includes("/observations")) {
      isDatabaseDown = false;
      const detail = "Base de données indisponible : réessayez dans quelques instants.";
      return new Response(JSON.stringify({ detail }), { status: 503 });
    }
    return fakeApi(url);
  });
  vi.stubGlobal("fetch", fetchMock);
  const user = userEvent.setup();
  render(<App />);

  // Le message de l'API est affiché, avec un bouton pour réessayer.
  const [alert] = await screen.findAllByRole("alert");
  expect(alert).toHaveTextContent("Base de données indisponible");

  await user.click(within(alert).getByRole("button", { name: "Réessayer" }));

  // La même période est redemandée, et les valeurs s'affichent.
  const table = await screen.findByRole("table");
  expect(within(table).getAllByRole("row")).toHaveLength(3);
});
