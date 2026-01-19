      {
        source: '/api/:path*',
        // FIX: Remove '/api' from the destination so it matches backend route
        destination: 'http://localhost:8000/:path*', // Proxy to FastAPI
      },
  },
  images: {
    unoptimized: true,
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*', // Proxy to FastAPI
      },
    ]
  },
}

export default nextConfig
