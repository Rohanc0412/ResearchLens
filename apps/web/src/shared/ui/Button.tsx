import type { ButtonHTMLAttributes, PropsWithChildren } from "react";
import { motion } from "framer-motion";

import { cn } from "../lib/cn";
import { Spinner } from "./Spinner";

type NativeButtonProps = Omit<
  ButtonHTMLAttributes<HTMLButtonElement>,
  "onAnimationStart" | "onAnimationEnd" | "onDrag" | "onDragEnd" | "onDragStart"
>;

type ButtonProps = PropsWithChildren<
  NativeButtonProps & {
    variant?: "primary" | "secondary" | "ghost" | "danger";
    compact?: boolean;
    loading?: boolean;
  }
>;

export function Button({
  children,
  className,
  variant = "secondary",
  compact = false,
  loading = false,
  disabled,
  ...props
}: ButtonProps) {
  return (
    <motion.button
      whileTap={{ scale: disabled ? 1 : 0.98 }}
      transition={{ duration: 0.12 }}
      className={cn(
        "button",
        `button--${variant}`,
        compact && "button--compact",
        className,
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? <Spinner /> : null}
      {children}
    </motion.button>
  );
}
