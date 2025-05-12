import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        'white': '#FFFFFF',
        'ash-gray': '#9DB5B2',
        'outer-space': '#464F51',
        'black': '#000009',
        'light-cyan': '#DAF0EE',
        'snow-drift': '#FAF9F6',
        'beige': '#F5F5DC',
      },
      fontFamily: {
        'inter': ['Inter', 'system-ui', 'sans-serif'],
        'playfair': ['Playfair Display Variable', 'serif'],
        'raleway': ['Raleway Variable', 'sans-serif'],
      },
    },
  },
  plugins: [],
}

export default config 