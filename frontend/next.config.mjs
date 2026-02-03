/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  // Note: Do not proxy all /api routes. App Router handlers live under app/api.
  // If you need a proxy, add a narrow rewrite for a specific path instead of /api/:path*.
}


export default nextConfig
