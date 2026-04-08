type PlaceholderCardProps = {
  title: string;
  body: string;
};

export function PlaceholderCard({ title, body }: PlaceholderCardProps) {
  return (
    <section aria-label={title}>
      <h2>{title}</h2>
      <p>{body}</p>
    </section>
  );
}

