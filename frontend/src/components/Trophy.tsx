// A podium cup, coloured by the era (silver in the 2000s, gold on the
// ground-effect podiums). The bubbles are champagne: only the refuelling era
// shows them, see index.css.
export default function Trophy({ size = 20 }: { size?: number }) {
  return (
    <span className="trophy" aria-label="S grade" role="img">
      <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true">
        <path
          fill="currentColor"
          d="M7 3h10v3h3a1 1 0 0 1 1 1c0 3-2 5-4.4 5.4A5 5 0 0 1 13 15.9V18h3v3H8v-3h3v-2.1a5 5 0 0 1-3.6-3.5C5 12 3 10 3 7a1 1 0 0 1 1-1h3V3Zm10 5v2.3c1-.4 1.8-1.2 2-2.3h-2ZM5 8c.2 1.1 1 1.9 2 2.3V8H5Z"
        />
      </svg>
      <i className="bubble" />
      <i className="bubble" />
      <i className="bubble" />
    </span>
  );
}
