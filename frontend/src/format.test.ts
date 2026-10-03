import { describe, it, expect } from "vitest";
import { formatINR, formatLakh, formatDate, daysLeftLabel } from "./format";

describe("formatINR", () => {
  it("formats positive numbers", () => {
    expect(formatINR(180000)).toBe("₹1,80,000");
  });
  it("formats negative numbers", () => {
    expect(formatINR(-180000)).toBe("-₹1,80,000");
  });
  it("formats zero", () => {
    expect(formatINR(0)).toBe("₹0");
  });
});

describe("formatLakh", () => {
  it("formats crores", () => {
    expect(formatLakh(15000000)).toBe("₹1.50 Cr");
  });
  it("formats lakhs", () => {
    expect(formatLakh(180000)).toBe("₹1.8 L");
  });
  it("formats hundreds", () => {
    expect(formatLakh(500)).toBe("₹500");
  });
});

describe("formatDate", () => {
  it("formats string dates", () => {
    expect(formatDate("2026-10-18")).toMatch(/Oct 2026/);
  });
});

describe("daysLeftLabel", () => {
  it("formats days left", () => {
    expect(daysLeftLabel(5)).toBe("5 days left");
    expect(daysLeftLabel(0)).toBe("due today");
    expect(daysLeftLabel(-2)).toBe("2 days overdue");
    expect(daysLeftLabel(null)).toBe("");
  });
});
