import { motion } from "framer-motion";

export function TypingIndicator() {
  return (
    <div className="typing-indicator" role="status" aria-label="Assistant is typing">
      <span className="visually-hidden">Assistant is typing</span>
      {[0, 1, 2].map((index) => (
        <motion.div
          key={index}
          className="typing-indicator__dot"
          animate={{ y: [0, -6, 0] }}
          transition={{
            duration: 0.6,
            repeat: Infinity,
            ease: "easeInOut",
            delay: index * 0.15,
          }}
          aria-hidden="true"
        />
      ))}
    </div>
  );
}
