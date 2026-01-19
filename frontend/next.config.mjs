/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        // CORRECT: Maps '/api/trade/execute' -> 'http://localhost:8000/trade/execute'
        destination: 'http://localhost:8000/:path*',
      },
    ]
  },
}

export default nextConfig
