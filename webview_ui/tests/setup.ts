import { afterEach } from "vitest";

afterEach(() => {
  delete window.__INITIAL_STATE__;
  document.body.innerHTML = "";
});
