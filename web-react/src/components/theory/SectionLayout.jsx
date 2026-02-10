import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";

function BulletList({ items, dotClassName = "bg-emerald-400" }) {
  if (!items?.length) return null;
  return (
    <ul className="space-y-2 text-sm text-slate-600 dark:text-slate-300">
      {items.map((item) => (
        <li key={item} className="flex gap-2">
          <span className={`mt-1.5 h-1.5 w-1.5 rounded-full ${dotClassName}`}></span>
          <span>{item}</span>
        </li>
      ))}
    </ul>
  );
}

export default function SectionLayout({ data }) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold text-slate-900 dark:text-white">
          {data.title}
        </h2>
        {data.subtitle ? (
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            {data.subtitle}
          </p>
        ) : null}
      </div>

      {data.intro?.map((paragraph) => (
        <p key={paragraph} className="text-sm leading-relaxed text-slate-600 dark:text-slate-300">
          {paragraph}
        </p>
      ))}

      {data.highlights?.length ? (
        <Card className="neon-card rounded-2xl border-slate-200/70 bg-white/70 p-4 shadow-sm dark:border-slate-700/60 dark:bg-slate-900/60">
          <CardHeader>
            <CardTitle className="text-sm">
              {data.highlightsTitle || "Key Points"}
            </CardTitle>
            {data.highlightsSubtitle ? (
              <CardDescription>{data.highlightsSubtitle}</CardDescription>
            ) : null}
          </CardHeader>
          <CardContent className="mt-2">
            <BulletList items={data.highlights} dotClassName="bg-slate-400" />
          </CardContent>
        </Card>
      ) : null}

      {data.sections?.length ? (
        <div className="grid gap-4 md:grid-cols-2">
          {data.sections.map((section) => (
            <Card
              key={section.title}
              className="neon-card rounded-2xl border-slate-200/70 bg-white/70 p-4 shadow-sm dark:border-slate-700/60 dark:bg-slate-900/60"
            >
              <CardHeader>
                <CardTitle className="text-sm">{section.title}</CardTitle>
                {section.subtitle ? (
                  <CardDescription>{section.subtitle}</CardDescription>
                ) : null}
              </CardHeader>
              <CardContent className="mt-2">
                <BulletList items={section.items} dotClassName="bg-emerald-400" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : null}

      {data.images?.length ? (
        <div className="space-y-3">
          <div>
            <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
              Image Suggestions
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Use these visual references to make the documentation feel tangible and analyst friendly.
            </p>
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            {data.images.map((image) => (
              <div
                key={image.title}
                className="neon-card overflow-hidden rounded-2xl border border-slate-200/70 bg-white/80 p-3 text-sm text-slate-600 shadow-sm dark:border-slate-700/60 dark:bg-slate-900/60 dark:text-slate-300"
              >
                <div className="photo-frame overflow-hidden rounded-xl border border-slate-200/70 bg-white dark:border-slate-700/60 dark:bg-slate-950">
                  <img
                    src={image.src}
                    alt={image.title}
                    loading="lazy"
                    className="photo-image h-40 w-full object-cover"
                  />
                </div>
                <div className="mt-3 space-y-1">
                  <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                    {image.title}
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    {image.caption}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}
