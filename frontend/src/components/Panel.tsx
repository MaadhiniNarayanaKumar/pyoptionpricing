export default function Panel({ title, subtitle, loading, error, children }: {
  title: string;
  subtitle?: string;
  loading?: boolean;
  error?: string;
  children?: React.ReactNode;
}) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <header className="mb-3">
        <h2 className="text-base font-semibold text-slate-900">{title}</h2>
        {subtitle && <p className="text-sm text-slate-500">{subtitle}</p>}
      </header>
      {error ? (
        <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
      ) : loading ? (
        <p className="py-10 text-center text-sm text-slate-500">Loading…</p>
      ) : (
        children
      )}
    </section>
  );
}
