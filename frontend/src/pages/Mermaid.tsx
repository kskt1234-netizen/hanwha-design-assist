import { useEffect, useRef, useState } from "react";
import mermaid from "mermaid";

mermaid.initialize({ startOnLoad: false, theme: "default", suppressErrorRendering: true, er: { useMaxWidth: false } });
let seq = 0;

export default function Mermaid({ code }: { code: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    if (!code.trim()) return;
    mermaid
      .render(`mermaid-${++seq}`, code)
      .then(({ svg }) => {
        if (!cancelled && ref.current) {
          ref.current.innerHTML = svg;
          setError(null);
        }
      })
      .catch((e) => !cancelled && setError(String(e?.message ?? e)));
    return () => {
      cancelled = true;
    };
  }, [code]);

  return (
    <>
      {error && <pre style={{ color: "crimson", whiteSpace: "pre-wrap" }}>{error}</pre>}
      <div ref={ref} style={{ overflow: "auto" }} />
    </>
  );
}
