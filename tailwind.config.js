/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './apps/**/templates/**/*.html',
    './apps/**/forms.py',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#ffa50010',  // 6% opacity for backgrounds
          100: '#ffa50020', // 12% opacity
          200: '#ffa50030', // 18% opacity
          300: '#ffa50040', // 25% opacity
          400: '#ffa50060', // 37% opacity
          500: '#ffa50094', // Main branding color (approx 58% opacity)
          600: '#ffa50094', // Main branding color
          700: '#ffa500b0', // Slightly more opaque for hover
          800: '#ffa500d0', // Even more opaque
          900: '#ffa500',   // Fully opaque orange
        },
        orange: {
          50: '#ffa50010',
          100: '#ffa50020',
          200: '#ffa50030',
          300: '#ffa50040',
          400: '#ffa50060',
          500: '#ffa50094',
          600: '#ffa50094',
          700: '#ffa500b0',
          800: '#ffa500d0',
          900: '#ffa500',
        },
        brand: {
          dark: '#333333',
        },
        gray: {
          50: '#f9fafb',
          100: '#f3f4f6',
          200: '#e5e7eb',
          300: '#d1d5db',
          400: '#9ca3af',
          500: '#6b7280',
          600: '#4b5563',
          700: '#333333', // Mapping dark gray to branding color
          800: '#333333', // Mapping dark gray to branding color
          900: '#333333', // Mapping dark gray to branding color
        }
      },
    },
  },
  plugins: [],
}
