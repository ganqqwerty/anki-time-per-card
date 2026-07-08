import { mount } from "svelte";
import App from "./App.svelte";
import { getInitialState } from "./lib/state";

const target = document.getElementById("app");

if (!target) {
  throw new Error("Missing #app mount point");
}

mount(App, {
  target,
  props: {
    stats: getInitialState()
  }
});
