import { redirect } from "next/navigation";

/** Legacy sidebar URL — dashboard layout lives under /dashboard. */
export default function PatientsLegacyRedirect() {
  redirect("/dashboard/patients");
}
