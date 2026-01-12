/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  // Using API routes instead of rewrites for better error handling
  // See app/api/* for proxy routes to Python backend
}

export default nextConfig
