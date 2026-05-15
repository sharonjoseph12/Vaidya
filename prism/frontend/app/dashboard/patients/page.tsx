"use client";

import Link from "next/link";
import PatientQueue from "@/components/dashboard/PatientQueue";

export default function PatientsPage() {
  return (
    <div className="p-6 md:p-10 space-y-8 max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white mb-2">Patients</h1>
          <p className="text-gray-400">Queue, registration, and recent records.</p>
        </div>
        <Link
          href="/patient/new"
          className="inline-flex items-center justify-center px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-xl text-sm font-medium transition w-fit"
        >
          + Register patient
        </Link>
      </div>
      <PatientQueue />
    </div>
  );
}
