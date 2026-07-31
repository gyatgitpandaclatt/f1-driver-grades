// Renders the LLM's prose sections: paragraphs, `- ` bullet lists, and
// `**bold**` spans. Not a full markdown parser — the narrator's system
// prompt only asks for that limited subset, so a small renderer here avoids
// pulling in a markdown dependency for it.
interface Props {
  text: string;
}

function renderInline(text: string, keyPrefix: string) {
  return text.split(/(\*\*[^*]+\*\*)/g).map((part, i) =>
    part.startsWith("**") && part.endsWith("**") ? (
      <strong key={`${keyPrefix}-${i}`}>{part.slice(2, -2)}</strong>
    ) : (
      <span key={`${keyPrefix}-${i}`}>{part}</span>
    )
  );
}

export default function NarrativeSection({ text }: Props) {
  if (!text.trim()) {
    return <p className="caption">No content generated for this section.</p>;
  }

  const blocks = text.trim().split(/\n\s*\n/);

  return (
    <>
      {blocks.map((block, i) => {
        const lines = block
          .split("\n")
          .map((line) => line.trim())
          .filter(Boolean);
        const isList = lines.length > 0 && lines.every((line) => /^[-*]\s+/.test(line));

        if (isList) {
          return (
            <ul key={i}>
              {lines.map((line, j) => (
                <li key={j}>{renderInline(line.replace(/^[-*]\s+/, ""), `${i}-${j}`)}</li>
              ))}
            </ul>
          );
        }

        return <p key={i}>{renderInline(block.replace(/\n/g, " "), `${i}`)}</p>;
      })}
    </>
  );
}
