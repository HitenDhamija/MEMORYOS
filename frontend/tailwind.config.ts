import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: ['class'],
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Apple Action Blue
        'apple-blue': '#0066cc',
        'apple-blue-focus': '#0071e3',
        'apple-blue-dark': '#2997ff',
        // Apple Surfaces
        'apple-canvas': '#ffffff',
        'apple-parchment': '#f5f5f7',
        'apple-pearl': '#fafafc',
        'apple-tile-1': '#272729',
        'apple-tile-2': '#2a2a2c',
        'apple-tile-3': '#252527',
        'apple-black': '#000000',
        'apple-chip': '#d2d2d7',
        // Apple Text
        'apple-ink': '#1d1d1f',
        'apple-body': '#1d1d1f',
        'apple-body-dark': '#ffffff',
        'apple-muted': '#cccccc',
        'apple-ink-80': '#333333',
        'apple-ink-48': '#7a7a7a',
        // Apple Borders
        'apple-divider': '#f0f0f0',
        'apple-hairline': '#e0e0e0',
      },
      fontFamily: {
        'sf-display': ['"SF Pro Display"', 'system-ui', '-apple-system', 'sans-serif'],
        'sf-text': ['"SF Pro Text"', 'system-ui', '-apple-system', 'sans-serif'],
      },
      borderRadius: {
        'apple-none': '0px',
        'apple-xs': '5px',
        'apple-sm': '8px',
        'apple-md': '11px',
        'apple-lg': '18px',
        'apple-pill': '9999px',
      },
      spacing: {
        'apple-xxs': '4px',
        'apple-xs': '8px',
        'apple-sm': '12px',
        'apple-md': '17px',
        'apple-lg': '24px',
        'apple-xl': '32px',
        'apple-2xl': '48px',
        'apple-section': '80px',
      },
      fontSize: {
        'apple-hero': ['56px', { lineHeight: '1.07', letterSpacing: '-0.28px', fontWeight: '600' }],
        'apple-display-lg': ['40px', { lineHeight: '1.10', letterSpacing: '0', fontWeight: '600' }],
        'apple-display-md': ['34px', { lineHeight: '1.47', letterSpacing: '-0.374px', fontWeight: '600' }],
        'apple-lead': ['28px', { lineHeight: '1.14', letterSpacing: '0.196px', fontWeight: '400' }],
        'apple-lead-airy': ['24px', { lineHeight: '1.5', letterSpacing: '0', fontWeight: '300' }],
        'apple-tagline': ['21px', { lineHeight: '1.19', letterSpacing: '0.231px', fontWeight: '600' }],
        'apple-body-strong': ['17px', { lineHeight: '1.24', letterSpacing: '-0.374px', fontWeight: '600' }],
        'apple-body': ['17px', { lineHeight: '1.47', letterSpacing: '-0.374px', fontWeight: '400' }],
        'apple-dense-link': ['17px', { lineHeight: '2.41', letterSpacing: '0', fontWeight: '400' }],
        'apple-caption': ['14px', { lineHeight: '1.43', letterSpacing: '-0.224px', fontWeight: '400' }],
        'apple-caption-strong': ['14px', { lineHeight: '1.29', letterSpacing: '-0.224px', fontWeight: '600' }],
        'apple-btn-lg': ['18px', { lineHeight: '1.0', letterSpacing: '0', fontWeight: '300' }],
        'apple-btn-utility': ['14px', { lineHeight: '1.29', letterSpacing: '-0.224px', fontWeight: '400' }],
        'apple-fine-print': ['12px', { lineHeight: '1.0', letterSpacing: '-0.12px', fontWeight: '400' }],
        'apple-micro': ['10px', { lineHeight: '1.3', letterSpacing: '-0.08px', fontWeight: '400' }],
        'apple-nav': ['12px', { lineHeight: '1.0', letterSpacing: '-0.12px', fontWeight: '400' }],
      },
      animation: {
        'slide-down': 'slideDown 0.3s ease-out',
        'slide-in': 'slideIn 0.3s ease-out',
        'fade-in': 'fadeIn 0.6s ease-out',
        'fade-in-up': 'fadeInUp 0.6s ease-out',
        'scale-in': 'scaleIn 0.3s ease-out',
      },
      keyframes: {
        slideDown: {
          'from': { opacity: '0', transform: 'translateY(-10px)' },
          'to': { opacity: '1', transform: 'translateY(0)' },
        },
        slideIn: {
          'from': { opacity: '0', transform: 'translateX(-10px)' },
          'to': { opacity: '1', transform: 'translateX(0)' },
        },
        fadeIn: {
          'from': { opacity: '0' },
          'to': { opacity: '1' },
        },
        fadeInUp: {
          'from': { opacity: '0', transform: 'translateY(20px)' },
          'to': { opacity: '1', transform: 'translateY(0)' },
        },
        scaleIn: {
          'from': { opacity: '0', transform: 'scale(0.95)' },
          'to': { opacity: '1', transform: 'scale(1)' },
        },
      },
    },
  },
  plugins: [],
};

export default config;
