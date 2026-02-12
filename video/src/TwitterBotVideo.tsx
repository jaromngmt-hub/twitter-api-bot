import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
} from "remotion";

// Title Card Component
const TitleCard: React.FC<{ title: string; subtitle: string; frame: number }> = ({
  title,
  subtitle,
  frame,
}) => {
  const titleOpacity = interpolate(frame, [0, 30], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  
  const titleY = interpolate(frame, [0, 40], [50, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const subtitleOpacity = interpolate(frame, [20, 50], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        background: "linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: "system-ui, -apple-system, sans-serif",
      }}
    >
      {/* Animated background circles */}
      <div
        style={{
          position: "absolute",
          width: "600px",
          height: "600px",
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(29,161,242,0.1) 0%, transparent 70%)",
          top: "10%",
          left: "10%",
          transform: `translateX(${Math.sin(frame * 0.02) * 20}px)`,
        }}
      />
      <div
        style={{
          position: "absolute",
          width: "400px",
          height: "400px",
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(88,101,242,0.1) 0%, transparent 70%)",
          bottom: "10%",
          right: "10%",
          transform: `translateY(${Math.cos(frame * 0.02) * 20}px)`,
        }}
      />

      {/* Twitter Bird Icon */}
      <div
        style={{
          fontSize: "80px",
          marginBottom: "20px",
          opacity: titleOpacity,
          transform: `translateY(${titleY}px)`,
        }}
      >
        🐦
      </div>

      {/* Title */}
      <h1
        style={{
          fontSize: "72px",
          fontWeight: "bold",
          color: "#ffffff",
          margin: 0,
          textShadow: "0 4px 20px rgba(0,0,0,0.3)",
          opacity: titleOpacity,
          transform: `translateY(${titleY}px)`,
        }}
      >
        {title}
      </h1>

      {/* Subtitle */}
      <p
        style={{
          fontSize: "28px",
          color: "#a0a0a0",
          marginTop: "20px",
          opacity: subtitleOpacity,
        }}
      >
        {subtitle}
      </p>

      {/* Arrow down indicator */}
      <div
        style={{
          position: "absolute",
          bottom: "50px",
          fontSize: "40px",
          opacity: interpolate(frame, [40, 70], [0, 1]),
        }}
      >
        ⬇️
      </div>
    </AbsoluteFill>
  );
};

// Features Section
const FeaturesSection: React.FC<{ frame: number; startFrame: number }> = ({
  frame,
  startFrame,
}) => {
  const progress = frame - startFrame;

  const features = [
    { icon: "📊", title: "Channel Management", desc: "Organize users into Discord channels" },
    { icon: "👤", title: "User Monitoring", desc: "Track multiple Twitter accounts" },
    { icon: "⏰", title: "Auto Scheduling", desc: "Runs every 5 minutes automatically" },
    { icon: "🔔", title: "Instant Notifications", desc: "Get tweets delivered to Discord instantly" },
  ];

  return (
    <AbsoluteFill
      style={{
        background: "linear-gradient(135deg, #0f0f23 0%, #1a1a3e 100%)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        paddingTop: "100px",
        fontFamily: "system-ui, -apple-system, sans-serif",
      }}
    >
      <h2
        style={{
          fontSize: "48px",
          color: "#ffffff",
          marginBottom: "60px",
          opacity: interpolate(progress, [0, 20], [0, 1]),
          transform: `translateY(${interpolate(progress, [0, 20], [30, 0])}px)`,
        }}
      >
        Key Features
      </h2>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(2, 1fr)",
          gap: "40px",
          maxWidth: "1200px",
          padding: "0 40px",
        }}
      >
        {features.map((feature, i) => {
          const delay = i * 10;
          const opacity = interpolate(progress, [delay, delay + 20], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });
          const y = interpolate(progress, [delay, delay + 20], [50, 0], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          });

          return (
            <div
              key={i}
              style={{
                background: "rgba(255,255,255,0.05)",
                borderRadius: "20px",
                padding: "40px",
                border: "1px solid rgba(255,255,255,0.1)",
                opacity,
                transform: `translateY(${y}px)`,
              }}
            >
              <div style={{ fontSize: "48px", marginBottom: "15px" }}>{feature.icon}</div>
              <h3 style={{ fontSize: "24px", color: "#fff", margin: "0 0 10px 0" }}>
                {feature.title}
              </h3>
              <p style={{ fontSize: "18px", color: "#888", margin: 0 }}>{feature.desc}</p>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

// CLI Demo Section
const CLIDemoSection: React.FC<{ frame: number; startFrame: number }> = ({
  frame,
  startFrame,
}) => {
  const progress = frame - startFrame;

  const commands = [
    { cmd: "python main.py init", output: "✓ Database initialized" },
    { cmd: "python main.py channel create alerts <webhook>", output: "✓ Created channel 'alerts'" },
    { cmd: "python main.py user add @elonmusk alerts", output: "✓ Added @elonmusk" },
    { cmd: "python main.py run", output: "Starting Twitter Monitor Bot..." },
  ];

  return (
    <AbsoluteFill
      style={{
        background: "linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        paddingTop: "80px",
        fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
      }}
    >
      <h2
        style={{
          fontSize: "42px",
          color: "#ffffff",
          marginBottom: "40px",
          fontFamily: "system-ui, -apple-system, sans-serif",
          opacity: interpolate(progress, [0, 20], [0, 1]),
        }}
      >
        Simple CLI Interface
      </h2>

      <div
        style={{
          background: "#0d1117",
          borderRadius: "16px",
          padding: "30px",
          width: "900px",
          border: "1px solid #30363d",
          boxShadow: "0 20px 60px rgba(0,0,0,0.5)",
        }}
      >
        {/* Terminal header */}
        <div style={{ display: "flex", gap: "8px", marginBottom: "20px" }}>
          <div style={{ width: "12px", height: "12px", borderRadius: "50%", background: "#ff5f56" }} />
          <div style={{ width: "12px", height: "12px", borderRadius: "50%", background: "#ffbd2e" }} />
          <div style={{ width: "12px", height: "12px", borderRadius: "50%", background: "#27c93f" }} />
        </div>

        {/* Terminal content */}
        <div style={{ display: "flex", flexDirection: "column", gap: "15px" }}>
          {commands.map((item, i) => {
            const delay = i * 25;
            const visible = progress > delay;
            const typedChars = Math.max(0, progress - delay);
            const displayedCmd = item.cmd.slice(0, Math.floor(typedChars / 2));
            const showOutput = progress > delay + item.cmd.length * 0.5 + 10;

            return visible ? (
              <div key={i}>
                <div style={{ color: "#7ee787", fontSize: "16px" }}>
                  <span style={{ color: "#58a6ff" }}>❯</span> {displayedCmd}
                  {typedChars < item.cmd.length * 2 && (
                    <span style={{ opacity: 0.7 }}>▊</span>
                  )}
                </div>
                {showOutput && (
                  <div
                    style={{
                      color: "#a5d6ff",
                      fontSize: "14px",
                      marginTop: "5px",
                      marginLeft: "20px",
                      opacity: interpolate(progress, [delay + 30, delay + 40], [0, 1]),
                    }}
                  >
                    {item.output}
                  </div>
                )}
              </div>
            ) : null;
          })}
        </div>
      </div>

      {/* Discord webhook visualization */}
      <div
        style={{
          marginTop: "40px",
          display: "flex",
          alignItems: "center",
          gap: "20px",
          opacity: interpolate(progress, [100, 120], [0, 1]),
        }}
      >
        <div style={{ fontSize: "40px" }}>🐦</div>
        <div
          style={{
            width: "100px",
            height: "4px",
            background: "linear-gradient(90deg, #1da1f2, #5865f2)",
            borderRadius: "2px",
          }}
        />
        <div style={{ fontSize: "40px" }}>💬</div>
      </div>
    </AbsoluteFill>
  );
};

// Final CTA Section
const CTASection: React.FC<{ frame: number; startFrame: number }> = ({
  frame,
  startFrame,
}) => {
  const progress = frame - startFrame;

  return (
    <AbsoluteFill
      style={{
        background: "linear-gradient(135deg, #0f3460 0%, #16213e 50%, #1a1a2e 100%)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: "system-ui, -apple-system, sans-serif",
      }}
    >
      <div
        style={{
          fontSize: "100px",
          marginBottom: "30px",
          opacity: interpolate(progress, [0, 20], [0, 1]),
          transform: `scale(${interpolate(progress, [0, 30], [0.5, 1])})`,
        }}
      >
        🚀
      </div>

      <h2
        style={{
          fontSize: "56px",
          color: "#ffffff",
          margin: 0,
          opacity: interpolate(progress, [10, 30], [0, 1]),
        }}
      >
        Get Started Today
      </h2>

      <p
        style={{
          fontSize: "24px",
          color: "#a0a0a0",
          marginTop: "20px",
          opacity: interpolate(progress, [20, 40], [0, 1]),
        }}
      >
        Monitor Twitter. Notify Discord. Simple.
      </p>

      <div
        style={{
          marginTop: "50px",
          padding: "20px 50px",
          background: "linear-gradient(90deg, #1da1f2, #5865f2)",
          borderRadius: "50px",
          fontSize: "24px",
          fontWeight: "bold",
          color: "#fff",
          opacity: interpolate(progress, [40, 60], [0, 1]),
          transform: `translateY(${interpolate(progress, [40, 60], [30, 0])}px)`,
          boxShadow: "0 10px 40px rgba(29,161,242,0.4)",
        }}
      >
        pip install -r requirements.txt
      </div>

      <div
        style={{
          marginTop: "30px",
          fontSize: "16px",
          color: "#666",
          opacity: interpolate(progress, [60, 80], [0, 1]),
        }}
      >
        Python • SQLite • Asyncio • Discord Webhooks
      </div>
    </AbsoluteFill>
  );
};

// Main Video Component
export const TwitterBotVideo: React.FC<{
  title: string;
  subtitle: string;
}> = ({ title, subtitle }) => {
  const frame = useCurrentFrame();

  // Scene timing (in frames at 30fps)
  // Scene 1: Title (0-90 frames = 3s)
  // Scene 2: Features (90-180 frames = 3s)
  // Scene 3: CLI Demo (180-240 frames = 2s)
  // Scene 4: CTA (240-300 frames = 2s)

  return (
    <AbsoluteFill>
      {frame < 90 && <TitleCard title={title} subtitle={subtitle} frame={frame} />}
      {frame >= 90 && frame < 180 && <FeaturesSection frame={frame} startFrame={90} />}
      {frame >= 180 && frame < 240 && <CLIDemoSection frame={frame} startFrame={180} />}
      {frame >= 240 && <CTASection frame={frame} startFrame={240} />}
    </AbsoluteFill>
  );
};
