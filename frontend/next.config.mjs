/** @type {import('next').NextConfig} */
const nextConfig = {
  // Tremor v3 requires transpilation in Next.js 14 App Router
  transpilePackages: ["@tremor/react"],
  // Static export for Amplify manual deployment
  output: "export",
  // Required for Amplify static hosting - ensures correct asset paths
  trailingSlash: true,
  // Disable image optimization (not supported in static export)
  images: { unoptimized: true },
};

export default nextConfig;
