import { motion } from "framer-motion";

interface Props {
  onRefresh: () => void;
  refreshing: boolean;
  error: string | null;
}

export default function RefreshButton({ onRefresh, refreshing, error }: Props) {
  return (
    <div>
      <motion.button
        className="refresh-button"
        onClick={onRefresh}
        disabled={refreshing}
        whileHover={refreshing ? undefined : { scale: 1.04 }}
        whileTap={refreshing ? undefined : { scale: 0.96 }}
        transition={{ type: "spring", stiffness: 400, damping: 20 }}
      >
        <motion.span
          animate={refreshing ? { rotate: 360 } : { rotate: 0 }}
          transition={
            refreshing
              ? { repeat: Infinity, ease: "linear", duration: 0.8 }
              : { duration: 0.2 }
          }
          style={{ display: "inline-block", marginRight: 6 }}
        >
          ↻
        </motion.span>
        {refreshing ? "Refreshing…" : "Refresh"}
      </motion.button>
      {error && <div className="refresh-error">{error}</div>}
    </div>
  );
}
