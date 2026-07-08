import { describe, expect, it } from "vitest";
import { formatCount, formatDateLabel, formatDurationMs } from "../src/lib/format";

describe("formatDurationMs", () => {
  it("formats zero and invalid durations", () => {
    expect(formatDurationMs(0)).toBe("0s");
    expect(formatDurationMs(Number.NaN)).toBe("0s");
  });

  it("formats sub-minute durations", () => {
    expect(formatDurationMs(7500)).toBe("7.5s");
    expect(formatDurationMs(12000)).toBe("12s");
  });

  it("formats minute durations", () => {
    expect(formatDurationMs(65000)).toBe("1m 05s");
  });
});

describe("formatCount", () => {
  it("formats positive counts", () => {
    expect(formatCount(1234)).toBe("1,234");
  });
});

describe("formatDateLabel", () => {
  it("labels today's date", () => {
    expect(formatDateLabel("2026-07-08")).toBe("Today, 2026-07-08");
  });
});
