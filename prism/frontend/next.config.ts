import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  turbopack: {
    /** Pin workspace root when multiple lockfiles exist (avoids wrong inferred root). */
    root: path.resolve(process.cwd()),
  },
};

export default nextConfig;
