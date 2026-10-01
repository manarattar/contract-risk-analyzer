import PropTypes from 'prop-types';
import { BANDS } from "../theme";

const TICKS = Array.from({ length: 11 }, (_, i) => i * 10);

/**
 * The overall score drawn to scale on a 0-100 ruler with the three risk bands
 * behind it. Takes one or more markers, so the compare view can show A and B
 * on the same scale.
 */
export default function RiskRuler({ markers }) {
  return (
    <div className="pt-7 pb-1">
      <div className="relative h-9">
        {/* bands */}
        <div className="absolute inset-0 flex overflow-hidden rounded-[2px] border border-rule">
          {BANDS.map((b) => (
            <div key={b.level} className={`${b.soft} flex items-end px-1.5 pb-0.5`} style={{ width: `${b.to - b.from}%` }}>
              <span className={`text-[10.5px] font-semibold uppercase tracking-[0.08em] ${b.text}`}>{b.level}</span>
            </div>
          ))}
        </div>

        {/* ticks */}
        {TICKS.map((t) => (
          <span
            key={t}
            className={`absolute top-0 w-px bg-ink-3 ${t % 50 === 0 ? "h-3" : "h-1.5"}`}
            style={{ left: `${t}%` }}
          />
        ))}

        {/* markers */}
        {markers.map((m) => (
          <div key={m.label || "score"} className="absolute -top-7 bottom-0 flex flex-col items-center" style={{ left: `${m.score}%`, transform: "translateX(-50%)" }}>
            <span className={`num whitespace-nowrap rounded-[2px] px-1 text-[12px] font-semibold leading-5 text-sheet ${m.tone || "bg-ink"}`}>
              {m.label ? `${m.label} ${m.score}` : m.score}
            </span>
            <span className={`w-0.5 flex-1 ${m.tone || "bg-ink"}`} />
          </div>
        ))}
      </div>
      <div className="num relative mt-1 h-4 text-[11px] text-ink-3">
        {[0, 35, 70, 100].map((t) => (
          <span key={t} className="absolute" style={{ left: `${t}%`, transform: t === 0 ? "none" : t === 100 ? "translateX(-100%)" : "translateX(-50%)" }}>
            {t}
          </span>
        ))}
      </div>
    </div>
  );
}

RiskRuler.propTypes = {
  markers: PropTypes.arrayOf(PropTypes.shape({ score: PropTypes.number, label: PropTypes.string, tone: PropTypes.string })),
};
