import { useEffect } from "react";

type Handlers = {
  onNewBranch: () => void;
  onRunSelected: () => void;
  onCompare: () => void;
  onMergeSelected: () => void;
  onShowShortcuts: () => void;
};

const isEditableTarget = (target: EventTarget | null) => {
  if (!(target instanceof HTMLElement)) return false;
  const tag = target.tagName;
  return (
    tag === "INPUT" ||
    tag === "TEXTAREA" ||
    target.isContentEditable
  );
};

/**
 * Single-letter shortcuts. Skipped while the user is in an input or
 * contentEditable, and while a modifier (cmd/ctrl/alt) is held — those go to
 * the OS or the editor.
 */
export function useKeyboardShortcuts(h: Handlers) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      if (isEditableTarget(e.target)) return;

      switch (e.key) {
        case "n":
        case "N":
          e.preventDefault();
          h.onNewBranch();
          break;
        case "r":
        case "R":
          e.preventDefault();
          h.onRunSelected();
          break;
        case "c":
        case "C":
          e.preventDefault();
          h.onCompare();
          break;
        case "m":
        case "M":
          e.preventDefault();
          h.onMergeSelected();
          break;
        case "?":
          e.preventDefault();
          h.onShowShortcuts();
          break;
      }
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [h]);
}
