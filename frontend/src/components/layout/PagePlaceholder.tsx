import PageHeader from './PageHeader';

interface PagePlaceholderProps {
  title: string;
  description: string;
}

export default function PagePlaceholder({ title, description }: PagePlaceholderProps) {
  return (
    <div>
      <PageHeader title={title} isActive={false} lastUpdate="--:--" showStatus={false} />
      <main className="flex-1 px-8 pt-7 pb-10">
        <section className="rounded-lg border border-border bg-white p-6 shadow-sm">
          <h2 className="m-0 text-lg font-bold text-text-dark">{title}</h2>
          <p className="mt-2 max-w-2xl text-sm text-text-muted">{description}</p>
        </section>
      </main>
    </div>
  );
}
