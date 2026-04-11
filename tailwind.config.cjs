const { spawnSync } = require('child_process');
const path = require('path');

function crispyTailwindTemplates() {
  const r = spawnSync(
    'python3',
    [
      '-c',
      "import importlib.util as u, pathlib as p; s=u.find_spec('crispy_tailwind'); print(p.Path(s.origin).parent / 'templates' if s and s.origin else '', end='')",
    ],
    { encoding: 'utf8' },
  );
  const dir = (r.stdout || '').trim();
  if (!dir) return [];
  return [path.join(dir, '**', '*.html')];
}

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./templates/**/*.html', ...crispyTailwindTemplates()],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        soft: '0 2px 15px -3px rgb(0 0 0 / 0.06), 0 10px 20px -5px rgb(0 0 0 / 0.04)',
        lift: '0 10px 40px -10px rgb(15 118 110 / 0.25)',
      },
    },
  },
  plugins: [],
};
