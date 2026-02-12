/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                nexus: {
                    bg: "#0F172A",       // Slate 900 (Deep Blue/Black)
                    dark: "#020617",     // Slate 950 (Darkest Container)
                    card: "#334155",     // Slate 700 (Lighter Card Surface for distinction)
                    hover: "#475569",    // Slate 600 (Hover State)
                    border: "#475569",   // Slate 600 (Visible Border)
                    cyan: "#22D3EE",     // Cyan 400 (Brighter Neon)
                    blue: "#60A5FA",     // Blue 400 (Brighter Neon)
                    slate: "#CBD5E1",    // Slate 300 (High Contrast Body Text)
                    light: "#FFFFFF",    // Pure White (Headings)
                }
            },
            fontFamily: {
                sans: ['Inter', 'system-ui', 'sans-serif'],
            },
            boxShadow: {
                'neon': '0 0 10px rgba(100, 255, 218, 0.1)',
                'glass': '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
            },
            animation: {
                'fade-in': 'fadeIn 0.5s ease-out',
                'slide-up': 'slideUp 0.5s ease-out',
                'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
            },
            keyframes: {
                fadeIn: {
                    '0%': { opacity: '0' },
                    '100%': { opacity: '1' },
                },
                slideUp: {
                    '0%': { transform: 'translateY(20px)', opacity: '0' },
                    '100%': { transform: 'translateY(0)', opacity: '1' },
                }
            }
        },
    },
    plugins: [],
}
