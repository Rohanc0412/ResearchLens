import { motion } from "framer-motion";

type WaveTextProps = {
  text: string;
  duration: number;
  className?: string;
};

export function WaveText({ text, duration, className }: WaveTextProps) {
  const chars = text.split("");
  return (
    <span className={className}>
      {chars.map((char, index) => {
        if (char === " ") return <span key={index}>&nbsp;</span>;
        const delay = -(duration * (1 - index / chars.length));
        return (
          <motion.span
            key={index}
            style={{ display: "inline-block" }}
            animate={{ opacity: [1, 0.75, 0.2, 0.75, 1] }}
            transition={{ duration, ease: "easeInOut", repeat: Infinity, delay }}
          >
            {char}
          </motion.span>
        );
      })}
    </span>
  );
}
