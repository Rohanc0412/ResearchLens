import { motion, useReducedMotion } from "framer-motion";

export function Spinner() {
  const reduceMotion = useReducedMotion();

  return (
    <motion.span
      className="spinner"
      aria-hidden="true"
      animate={reduceMotion ? undefined : { opacity: [0.55, 1, 0.55], scale: [0.92, 1, 0.92] }}
      transition={{
        duration: 1.1,
        repeat: Number.POSITIVE_INFINITY,
        ease: "easeInOut",
      }}
    />
  );
}
