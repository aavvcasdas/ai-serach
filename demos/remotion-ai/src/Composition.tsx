import { CalculateMetadataFunction, Composition } from "remotion";
import { AiExplainer } from "./AiExplainer";

type Props = {};

const calculateMetadata: CalculateMetadataFunction<Props> = () => {
  return {};
};

export const MyComposition = () => {
  return (
    <Composition
      id="AiExplainer"
      component={AiExplainer}
      durationInFrames={300}
      fps={30}
      width={1920}
      height={1080}
      calculateMetadata={calculateMetadata}
    />
  );
};

export const MyComponent = AiExplainer;
