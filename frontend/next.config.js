/** @type {import('next').NextConfig} */
const path = require('path');

const nextConfig = {
  reactStrictMode: true,
  transpilePackages: [
    '@xyflow/react',
    'framer-motion',
    'recharts',
    'react-markdown',
    'remark-gfm',
    'remark-parse',
    'remark-rehype',
    'rehype-stringify',
    'unified',
    'react-syntax-highlighter',
    'd3',
    'd3-array',
    'd3-scale',
    'd3-shape',
    'd3-color',
    'd3-format',
    'd3-time',
    'd3-interpolate',
  ],
  outputFileTracingRoot: path.join(__dirname, '../../'),
  async rewrites() {
    const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    return [
      {
        source: '/api/:path*',
        destination: `${apiBase}/api/:path*`,
      },
    ];
  },
  webpack: (config) => {
    // Fix "Cannot read properties of undefined (reading 'call')" caused by
    // optional native modules (canvas, encoding) that pdfjs-dist/react-pdf
    // reference but are not installed in a browser context.
    config.resolve.alias = {
      ...config.resolve.alias,
      canvas: false,
      encoding: false,
    };
    return config;
  },
};

module.exports = nextConfig;