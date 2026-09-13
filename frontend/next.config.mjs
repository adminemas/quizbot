/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',       // Static HTML export -> frontend/out/
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
}

export default nextConfig
