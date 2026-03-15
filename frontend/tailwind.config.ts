import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
    './node_modules/@tremor/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        cfo: {
          bg: '#0a0c10',
          surface: '#111318',
          surface2: '#181c24',
          border: '#1e2330',
          accent: '#00e5a0', // runway healthy
          warn: '#ffd166', // runway warning
          danger: '#ff4d4f', // runway critical
        },
      },
      backgroundColor: {
        'cfo-bg': '#0a0c10',
        'cfo-surface': '#111318',
        'cfo-surface2': '#181c24',
      },
      textColor: {
        'cfo-muted': '#8892a4',
        'cfo-accent': '#00e5a0',
      },
      borderColor: {
        'cfo-border': '#1e2330',
      },
    },
  },
  plugins: [],
};

export default config;
