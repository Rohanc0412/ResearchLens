import type { SVGProps } from "react";

type IconProps = SVGProps<SVGSVGElement>;

export function ShieldCheckIcon(props: IconProps) {
  return (
    <svg fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" viewBox="0 0 24 24" {...props}>
      <path d="M12 3.5 6.5 5.6v5.55c0 3.6 2.15 6.85 5.5 8.35 3.35-1.5 5.5-4.75 5.5-8.35V5.6L12 3.5Z" />
      <path d="m9.5 12.25 1.6 1.6 3.4-3.7" />
    </svg>
  );
}

export function ShieldOffIcon(props: IconProps) {
  return (
    <svg fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" viewBox="0 0 24 24" {...props}>
      <path d="M12 3.5 6.5 5.6v5.55c0 3.6 2.15 6.85 5.5 8.35 3.35-1.5 5.5-4.75 5.5-8.35V5.6L12 3.5Z" />
      <path d="m8.25 8.25 7.5 7.5" />
    </svg>
  );
}

export function CheckCircleIcon(props: IconProps) {
  return (
    <svg fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" viewBox="0 0 24 24" {...props}>
      <circle cx="12" cy="12" r="8.5" />
      <path d="m8.9 12.2 2.05 2.05 4.15-4.45" />
    </svg>
  );
}

export function CopyIcon(props: IconProps) {
  return (
    <svg fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" viewBox="0 0 24 24" {...props}>
      <rect height="10" rx="1.5" width="10" x="9" y="9" />
      <path d="M6 15.25H5.5A1.5 1.5 0 0 1 4 13.75v-8.5a1.5 1.5 0 0 1 1.5-1.5H14a1.5 1.5 0 0 1 1.5 1.5v.5" />
    </svg>
  );
}
