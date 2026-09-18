import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";

import { DEFAULT_FILTERS, useUniverseStore } from "../../state/universeStore";
import { Filters } from "./Filters";

beforeEach(() => {
  useUniverseStore.setState({ filters: DEFAULT_FILTERS });
});

describe("Filters", () => {
  it("toggles a filter chip on click", async () => {
    const user = userEvent.setup();
    render(<Filters />);
    const chip = screen.getByRole("button", { name: "Numeric" });
    expect(chip).toHaveAttribute("aria-pressed", "false");

    await user.click(chip);
    expect(chip).toHaveAttribute("aria-pressed", "true");
    expect(useUniverseStore.getState().filters.numeric).toBe(true);
  });

  it("shows a Clear action only when a filter is active, and it resets every filter", async () => {
    const user = userEvent.setup();
    render(<Filters />);
    expect(screen.queryByText("Clear")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Has missing data" }));
    expect(screen.getByText("Clear")).toBeInTheDocument();

    await user.click(screen.getByText("Clear"));
    expect(useUniverseStore.getState().filters).toEqual(DEFAULT_FILTERS);
    expect(screen.queryByText("Clear")).not.toBeInTheDocument();
  });
});
