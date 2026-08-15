// src/components/auth/BrandPanel.jsx

export default function BrandPanel() {
  const bars = [40, 65, 30, 80, 50, 90, 45, 70, 35, 60, 85, 40, 55];

  return (
    <div className="relative hidden md:flex md:w-1/2 flex-col justify-between bg-ink text-white p-12 overflow-hidden">
      {/* live indicator */}
      <div className="flex items-center gap-2 font-mono text-xs uppercase tracking-widest text-white/60">
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75" />
          <span className="relative inline-flex h-2 w-2 rounded-full bg-primary" />
        </span>
        Listening
      </div>

      {/* waveform signature */}
      <div className="flex items-end gap-1.5 h-24 my-10" aria-hidden="true">
        {bars.map((h, i) => (
          <span
            key={i}
            className="w-2 rounded-full bg-primary motion-safe:animate-[wave_1.4s_ease-in-out_infinite]"
            style={{
              height: `${h}%`,
              animationDelay: `${i * 0.08}s`,
            }}
          />
        ))}
      </div>

      <div>
        <h1 className="font-display text-3xl font-semibold leading-tight">
          Meet Q
        </h1>
        <p className="mt-3 text-white/60 max-w-sm">
          It joins the call, takes the notes, and hands you the decisions —
          so you don't have to write anything down again.
        </p>
      </div>

      <style>{`
        @keyframes wave {
          0%, 100% { transform: scaleY(0.4); }
          50% { transform: scaleY(1); }
        }
      `}</style>
    </div>
  );
}