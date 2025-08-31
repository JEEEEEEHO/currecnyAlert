import { render, screen } from "@testing-library/react";
import Home from "./Home";
import { vi } from "vitest";
import * as client from "../api/client";

vi.spyOn(client.default, "get").mockResolvedValue({
  data: { base:"USD", target:"KRW", current_rate:1300, avg_3y:1350, status:"LOW", last_updated:"2025-01-01T00:00:00Z", source:"test" }
});

test("renders current rate and avg", async () => {
  render(<Home />);
  expect(await screen.findByText("현재 환율")).toBeInTheDocument();
  expect(await screen.findByText("3년 평균")).toBeInTheDocument();
});
