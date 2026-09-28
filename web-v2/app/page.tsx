import { redirect } from "next/navigation";

export const metadata = {
  title: "Crop calendars, hazards and thresholds",
  description:
    "Regional crop calendars, phenological stages, reviewed climate hazards and their thresholds."
};

export default function ExplorerPage() {
  redirect('/risk');
}
