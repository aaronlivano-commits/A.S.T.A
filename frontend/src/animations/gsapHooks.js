import { useEffect, useRef } from "react";
import gsap from "gsap";
import {
  createScanlineTimeline,
  createLockOnPulse,
  createTypewriter,
  createPanelBoot,
} from "./scanEffects";

// Runs a looping HUD scan-line animation on the returned ref's element for
// as long as `active` is true. Used by LensScanner's crop overlay and the
// dashboard's idle reticle.
export function useScanline(active = true) {
  const ref = useRef(null);

  useEffect(() => {
    if (!ref.current || !active) return;
    const ctx = gsap.context(() => {
      createScanlineTimeline(ref.current);
    });
    return () => ctx.revert();
  }, [active]);

  return ref;
}

// Fires a one-shot "lock-on" pulse across a set of corner-bracket elements,
// re-triggerable by changing `trigger`.
export function useLockOnPulse(trigger) {
  const ref = useRef(null);

  useEffect(() => {
    if (!ref.current) return;
    const brackets = ref.current.querySelectorAll("[data-bracket]");
    if (brackets.length) createLockOnPulse(brackets);
  }, [trigger]);

  return ref;
}

// Streams text into the target element with a typewriter reveal. Returns a
// ref to attach and an `append(chunk)` function to call as SSE tokens arrive
// from /api/v1/chat/stream.
export function useTypewriter() {
  const ref = useRef(null);
  const controllerRef = useRef(null);

  useEffect(() => {
    if (ref.current) controllerRef.current = createTypewriter(ref.current);
  }, []);

  return {
    ref,
    append: (chunk) => controllerRef.current?.append(chunk),
    reset: () => controllerRef.current?.reset(),
  };
}

// Staggered boot-in for a list of rows when a panel/tab becomes active.
export function usePanelBoot(deps = []) {
  const ref = useRef(null);

  useEffect(() => {
    if (!ref.current) return;
    const rows = ref.current.querySelectorAll("[data-boot-row]");
    if (rows.length) createPanelBoot(rows);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return ref;
}
