interface Props {
  label?: string
}

export default function RobotLoading({ label = 'AIが考えています' }: Props) {
  return (
    <div className="flex flex-col items-center gap-4 py-8">
      <style>{`
        @keyframes robotFloat {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-10px); }
        }
        @keyframes eyeBlink {
          0%, 88%, 100% { transform: scaleY(1); }
          92% { transform: scaleY(0.08); }
        }
        @keyframes antennaPulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.35; transform: scale(0.65); }
        }
        @keyframes thinkDot {
          0%, 80%, 100% { opacity: 0.2; transform: translateY(0); }
          40% { opacity: 1; transform: translateY(-4px); }
        }
        .robot-float { animation: robotFloat 2s ease-in-out infinite; }
        .robot-eye-l {
          animation: eyeBlink 3s ease-in-out infinite;
          transform-box: fill-box;
          transform-origin: center;
        }
        .robot-eye-r {
          animation: eyeBlink 3s ease-in-out infinite 0.12s;
          transform-box: fill-box;
          transform-origin: center;
        }
        .robot-antenna-dot {
          animation: antennaPulse 1s ease-in-out infinite;
          transform-box: fill-box;
          transform-origin: center;
        }
        .tdot1 { animation: thinkDot 1.2s ease-in-out infinite 0s; }
        .tdot2 { animation: thinkDot 1.2s ease-in-out infinite 0.2s; }
        .tdot3 { animation: thinkDot 1.2s ease-in-out infinite 0.4s; }
      `}</style>
      <div className="robot-float">
        <svg width="72" height="84" viewBox="0 0 72 84" fill="none" xmlns="http://www.w3.org/2000/svg">
          <line x1="36" y1="5" x2="36" y2="15" stroke="hsl(var(--primary))" strokeWidth="2.5" strokeLinecap="round" />
          <circle cx="36" cy="5" r="4.5" fill="hsl(var(--primary))" className="robot-antenna-dot" />
          <rect x="8" y="15" width="56" height="40" rx="10" fill="hsl(var(--muted))" stroke="hsl(var(--primary))" strokeWidth="2" />
          <circle cx="24" cy="33" r="8" fill="white" />
          <circle cx="24" cy="33" r="5" fill="hsl(var(--primary))" className="robot-eye-l" />
          <circle cx="26.5" cy="30.5" r="1.5" fill="white" />
          <circle cx="48" cy="33" r="8" fill="white" />
          <circle cx="48" cy="33" r="5" fill="hsl(var(--primary))" className="robot-eye-r" />
          <circle cx="50.5" cy="30.5" r="1.5" fill="white" />
          <path d="M 22 47 Q 36 56 50 47" stroke="hsl(var(--primary))" strokeWidth="2.5" strokeLinecap="round" />
          <rect x="14" y="57" width="44" height="26" rx="8" fill="hsl(var(--muted))" stroke="hsl(var(--primary))" strokeWidth="2" />
          <circle cx="36" cy="70" r="6" fill="hsl(var(--primary))" opacity="0.35" />
          <circle cx="36" cy="70" r="3" fill="hsl(var(--primary))" opacity="0.7" />
        </svg>
      </div>
      <div className="flex items-center gap-1.5">
        <span className="text-sm text-muted-foreground">{label}</span>
        <div className="flex gap-1 mt-0.5">
          <span className="tdot1 inline-block w-1.5 h-1.5 rounded-full bg-primary" />
          <span className="tdot2 inline-block w-1.5 h-1.5 rounded-full bg-primary" />
          <span className="tdot3 inline-block w-1.5 h-1.5 rounded-full bg-primary" />
        </div>
      </div>
    </div>
  )
}
