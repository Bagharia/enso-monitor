// Mention de la source des données (exigence du sujet : source visible).
import { formatDate } from "../format";
import type { SourceResponse } from "../types";

interface SourceNoteProps {
  source: SourceResponse;
  indexName: string;
}

export function SourceNote({ source, indexName }: SourceNoteProps) {
  return (
    <p className="source-note">
      Source : {source.provider}, {indexName} —{" "}
      <a href={source.url} target="_blank" rel="noreferrer">
        fichier de données
      </a>{" "}
      extrait le {formatDate(source.extracted_on)}.
    </p>
  );
}
