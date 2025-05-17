import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        serif: ['Playfair Display Variable', 'serif'],
      },
      colors: {
        white: '#FFFFFF',           // White (unchanged name)
        mountbattenPink: '#464F51', // Mountbatten pink (replaces outerSpace)
        smokyBlack: '#000009',      // Smoky black (replaces black)
        beige: '#F5F5DC',           // Beige (kept as is)
        dukeBlue: '#0d2847',        // Duke blue (replaces navy)
        trueBlue: '#edf2f7',        // True Blue (replaces lightBlue)
      },
    },
  },
  plugins: [],
}

export default config 