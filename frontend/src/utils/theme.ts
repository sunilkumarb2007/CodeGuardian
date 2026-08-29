export type ThemeMode = 'dark' | 'light' | 'system'

export function getStoredTheme(): ThemeMode {
  const saved = localStorage.getItem('codeguardian-theme') as ThemeMode | null
  if (saved === 'dark' || saved === 'light' || saved === 'system') return saved
  return 'dark'
}

export function applyTheme(mode: ThemeMode): void {
  localStorage.setItem('codeguardian-theme', mode)
  const root = document.documentElement
  
  let effectiveTheme = mode
  if (mode === 'system') {
    effectiveTheme = window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark'
  }

  if (effectiveTheme === 'light') {
    root.classList.add('theme-light')
    root.classList.remove('theme-dark')
    root.style.colorScheme = 'light'
  } else {
    root.classList.add('theme-dark')
    root.classList.remove('theme-light')
    root.style.colorScheme = 'dark'
  }
}

export function initTheme(): void {
  const theme = getStoredTheme()
  applyTheme(theme)
  
  // Listen for system theme changes if set to system
  window.matchMedia('(prefers-color-scheme: light)').addEventListener('change', () => {
    if (getStoredTheme() === 'system') {
      applyTheme('system')
    }
  })
}
