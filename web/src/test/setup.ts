// Préparation commune aux tests Vitest.
import "@testing-library/jest-dom/vitest";

// jsdom ne fournit pas ResizeObserver, utilisé par ResponsiveContainer de Recharts.
class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}
globalThis.ResizeObserver = ResizeObserverStub;
