import { Composition } from "remotion";
import { TwitterBotVideo } from "./TwitterBotVideo";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="TwitterBotPromo"
        component={TwitterBotVideo}
        durationInFrames={300}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          title: "Twitter Monitor Bot",
          subtitle: "Route tweets to Discord automatically",
        }}
      />
    </>
  );
};
