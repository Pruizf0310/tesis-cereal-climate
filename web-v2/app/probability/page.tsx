import { ProbabilityAtlas } from '@/components/atlas/probability-atlas';

export const metadata = {
  title: 'Historical hazard probability',
  description: 'Empirical event probabilities during crop growth stages, with annual coverage and reviewed event definitions.'
};

export default function ProbabilityPage() {
  return <ProbabilityAtlas />;
}
