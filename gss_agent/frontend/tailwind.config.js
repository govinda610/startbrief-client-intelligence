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
                    bg: "#0A192F",       // Deepest Navy
                    card: "#112240",     // Card Surface
                    hover: "#233554",    // Hover State
                    border: "#1E3A8A",   // Subtle Blue Border
                    cyan: "#64FFDA",     // Primary Neon
                    blue: "#00E0FF",     // Secondary Neon
                    slate: "#8892B0",    // Muted Text
                    light: "#E6F1FF",    // Heading Text
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
