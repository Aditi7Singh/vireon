/** @type {import('next').NextConfig} */
const nextConfig = {
  // Tremor v3 requires transpilation in Next.js 14 App Router
  transpilePackages: ["@tremor/react"],
};

export default nextConfig;
