import { useEffect, useState } from "react";

const STORAGE_KEY = "cti-layout-width";
const DEFAULT_WIDTH = 92;
const MIN_WIDTH = 70;
const MAX_WIDTH = 100;
const STEP = 5;

const clamp = (value) => Math.min(MAX_WIDTH, Math.max(MIN_WIDTH, value));

export function useLayoutWidth() {
  const [width, setWidth] = useState(DEFAULT_WIDTH);

  useEffect(() => {
    const saved = Number(localStorage.getItem(STORAGE_KEY));
    if (Number.isFinite(saved) && saved >= MIN_WIDTH && saved <= MAX_WIDTH) {
      setWidth(saved);
    }
  }, []);

  const updateWidth = (next) => {
    const clamped = clamp(next);
    setWidth(clamped);
    localStorage.setItem(STORAGE_KEY, String(clamped));
  };

  const increase = () => updateWidth(width + STEP);
  const decrease = () => updateWidth(width - STEP);
  const reset = () => updateWidth(DEFAULT_WIDTH);

  return { width, increase, decrease, reset, min: MIN_WIDTH, max: MAX_WIDTH };
}
