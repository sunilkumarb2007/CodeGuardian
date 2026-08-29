const fs = require('fs');
const path = require('path');

function replaceInFiles(dir) {
  const files = fs.readdirSync(dir);
  for (const file of files) {
    const fullPath = path.join(dir, file);
    const stat = fs.statSync(fullPath);
    if (stat.isDirectory()) {
      replaceInFiles(fullPath);
    } else if (fullPath.endsWith('.tsx') || fullPath.endsWith('.ts')) {
      let content = fs.readFileSync(fullPath, 'utf8');
      
      // bg-[#070A0B] -> bg-ide-base
      // bg-[#0F1518] -> bg-ide-panel
      // border-white/[0.08] -> border-ide-divider
      
      let newContent = content
        .replace(/bg-\[#070A0B\]/g, 'bg-ide-base')
        .replace(/bg-\[#0F1518\]/g, 'bg-ide-panel')
        .replace(/border-white\/\[0\.08\]/g, 'border-ide-divider');
        
      if (newContent !== content) {
        fs.writeFileSync(fullPath, newContent);
        console.log(`Updated ${fullPath}`);
      }
    }
  }
}

replaceInFiles('d:/CodeGuardian/frontend/src');
