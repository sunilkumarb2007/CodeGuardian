import { useEffect, useRef } from 'react'

const TRAIL_LENGTH = 8
const INTERACTIVE = 'a, button, summary, [role="button"], input, select, textarea, label, details'

/**
 * Neon circuit cursor layer: a lime core that tracks the pointer, a ring that
 * lags behind and expands over interactive elements, a click ripple, and a
 * short particle trail. The native cursor art itself comes from CSS
 * (`public/cursors/*.svg`); this only adds motion on top of it.
 */
export function CursorFX() {
  const coreRef = useRef<HTMLDivElement>(null)
  const ringRef = useRef<HTMLDivElement>(null)
  const layerRef = useRef<HTMLDivElement>(null)
  const trailRefs = useRef<HTMLSpanElement[]>([])

  useEffect(() => {
    const fine = window.matchMedia('(pointer: fine)').matches
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (!fine || reduced) return

    const layer = layerRef.current
    const core = coreRef.current
    const ring = ringRef.current
    if (!layer || !core || !ring) return

    layer.dataset.active = 'true'

    const target = { x: window.innerWidth / 2, y: window.innerHeight / 2 }
    const ringPos = { ...target }
    const history: { x: number; y: number }[] = Array.from({ length: TRAIL_LENGTH }, () => ({ ...target }))
    let frame = 0

    const onMove = (event: PointerEvent) => {
      target.x = event.clientX
      target.y = event.clientY
      core.style.transform = `translate3d(${target.x}px, ${target.y}px, 0) translate(-50%, -50%)`
      const hovering = (event.target as Element | null)?.closest?.(INTERACTIVE)
      layer.dataset.hover = hovering ? 'true' : 'false'
    }

    const onDown = () => {
      layer.dataset.press = 'true'
      const ripple = document.createElement('span')
      ripple.className = 'cursor-ripple'
      ripple.style.left = `${target.x}px`
      ripple.style.top = `${target.y}px`
      layer.appendChild(ripple)
      window.setTimeout(() => ripple.remove(), 620)
    }
    const onUp = () => {
      layer.dataset.press = 'false'
    }
    const onLeave = () => {
      layer.dataset.visible = 'false'
    }
    const onEnter = () => {
      layer.dataset.visible = 'true'
    }

    const tick = () => {
      ringPos.x += (target.x - ringPos.x) * 0.18
      ringPos.y += (target.y - ringPos.y) * 0.18
      ring.style.transform = `translate3d(${ringPos.x}px, ${ringPos.y}px, 0) translate(-50%, -50%)`

      history.unshift({ x: target.x, y: target.y })
      history.length = TRAIL_LENGTH
      trailRefs.current.forEach((node, index) => {
        const point = history[index]
        if (!node || !point) return
        node.style.transform = `translate3d(${point.x}px, ${point.y}px, 0) translate(-50%, -50%)`
        node.style.opacity = String(0.32 * (1 - index / TRAIL_LENGTH))
      })
      frame = window.requestAnimationFrame(tick)
    }
    frame = window.requestAnimationFrame(tick)

    window.addEventListener('pointermove', onMove, { passive: true })
    window.addEventListener('pointerdown', onDown, { passive: true })
    window.addEventListener('pointerup', onUp, { passive: true })
    document.addEventListener('pointerleave', onLeave)
    document.addEventListener('pointerenter', onEnter)

    return () => {
      window.cancelAnimationFrame(frame)
      window.removeEventListener('pointermove', onMove)
      window.removeEventListener('pointerdown', onDown)
      window.removeEventListener('pointerup', onUp)
      document.removeEventListener('pointerleave', onLeave)
      document.removeEventListener('pointerenter', onEnter)
      delete layer.dataset.active
    }
  }, [])

  return (
    <div ref={layerRef} className="cursor-layer" data-visible="true" aria-hidden="true">
      {Array.from({ length: TRAIL_LENGTH }, (_, index) => (
        <span
          key={index}
          ref={(node) => {
            if (node) trailRefs.current[index] = node
          }}
          className="cursor-trail"
        />
      ))}
      <div ref={ringRef} className="cursor-ring" />
      <div ref={coreRef} className="cursor-core" />
    </div>
  )
}
