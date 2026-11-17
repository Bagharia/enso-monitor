// Client HTTP commun : tout accès réseau du front passe par le dossier api/, et donc par ici.

// En développement : l'API tourne sur le port 8000. Modifiable via VITE_API_BASE_URL.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function getJson<ResponseBody>(
  path: string,
  parameters: Record<string, string>,
  signal?: AbortSignal,
): Promise<ResponseBody> {
  const url = `${API_BASE_URL}/api/v1${path}?${new URLSearchParams(parameters)}`;

  let response: Response;
  try {
    response = await fetch(url, { signal });
  } catch (error) {
    if (signal?.aborted) throw error; // annulation volontaire : pas un problème réseau
    throw new Error("Impossible de contacter l'API : vérifiez qu'elle est lancée.");
  }

  if (!response.ok) {
    // L'API renvoie {"detail": "..."} : on affiche son message s'il est lisible.
    const body: { detail?: unknown } = await response.json().catch(() => ({}));
    const message =
      typeof body.detail === "string" ? body.detail : `Erreur ${response.status} de l'API.`;
    throw new Error(message);
  }
  return (await response.json()) as ResponseBody;
}
