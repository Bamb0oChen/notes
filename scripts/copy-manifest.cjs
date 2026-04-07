const fs = require('fs');
const path = require('path');

const distDir = path.resolve(__dirname, '..', 'dist');
const source = path.join(distDir, '.vite', 'manifest.json');
const target = path.join(distDir, 'manifest.json');

if (fs.existsSync(source)) {
  fs.copyFileSync(source, target);
  console.log('Copied manifest to dist/manifest.json');
} else {
  console.warn('Manifest not found at', source);
}
