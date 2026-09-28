import { ProbabilityAtlas } from "@/components/atlas/probability-atlas";

export const metadata = {
  title: "Hazard occurrence atlas",
  description:
    "Explore how climate variability shapes rice, maize, wheat and soybean systems across the world."
};

export default function ExplorerPage() {
  return <ProbabilityAtlas />;
}
