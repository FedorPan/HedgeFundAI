/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  images: {
    domains: ['localhost', 'hedgefund-ai-lwmjr.ondigitalocean.app'],
  },
  async rewrites() {
    return [
      {
        source: '/api/backend/:path*',
        destination: 'https://hedgefund-ai-lwmjr.ondigitalocean.app/:path*',
      },
    ]
  },
  env: {
    NEXT_PUBLIC_API_URL: 'https://hedgefund-ai-lwmjr.ondigitalocean.app'
  }
}

module.exports = nextConfig 