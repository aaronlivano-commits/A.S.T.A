import gsap from "gsap";

// A HUD scan-line sweeping down through a target element (used behind the
// LensScanner's ROI crop box and the hero reticle).
export function createScanlineTimeline(scanLineEl, { duration = 3.2 } = {}) {
  return gsap.timeline({ repeat: -1, yoyo: true }).fromTo(
    scanLineEl,
    { top: "8%", opacity: 0.9 },
    { top: "88%", opacity: 1, duration, ease: "sine.inOut" }
  );
}

// Corner-bracket "lock-on" pulse, played once when a region of interest is
// captured in LensScanner.
export function createLockOnPulse(bracketEls) {
  return gsap.timeline().fromTo(
    bracketEls,
    { scale: 1.4, opacity: 0 },
    { scale: 1, opacity: 1, duration: 0.4, ease: "back.out(3)", stagger: 0.04 }
  );
}

// Typewriter reveal used by ChatWindow while a Gemini response streams in.
// Call `.append(nextChunk)` on the returned controller as new SSE tokens arrive.
export function createTypewriter(targetEl) {
  let full = "";
  targetEl.textContent = "";
  return {
    append(chunk) {
      full += chunk;
      gsap.to(targetEl, {
        duration: Math.max(chunk.length * 0.012, 0.05),
        ease: "none",
        onUpdate: function () {
          const progress = this.progress();
          targetEl.textContent = full.slice(
            0,
            full.length - chunk.length + Math.round(chunk.length * progress)
          );
        },
      });
    },
    reset() {
      full = "";
      targetEl.textContent = "";
    },
  };
}

// Staggered boot-in for a panel's rows (spec sheet lines, topic list items).
export function createPanelBoot(rowEls) {
  return gsap.fromTo(
    rowEls,
    { opacity: 0, x: -8 },
    { opacity: 1, x: 0, duration: 0.3, stagger: 0.05, ease: "power2.out" }
  );
}
