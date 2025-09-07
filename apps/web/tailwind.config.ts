import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        background: '#0a0b0d',
        foreground: '#e4e4e7',
        card: '#111215',
        'card-hover': '#1a1b1f',
        border: '#27272a',
        primary: '#00ff88',
        'primary-dim': '#00cc6a',
        danger: '#ff3b3b',
        'danger-dim': '#cc2e2e',
        warning: '#ffaa00',
        'warning-dim': '#cc8800',
        accent: '#00d4ff',
        'accent-dim': '#00a8cc',
        'text-primary': '#ffffff',
        'text-secondary': '#a1a1aa',
        'text-tertiary': '#71717a',
        success: '#10b981',
      },
    },
  },
  plugins: [],
}
export default config
