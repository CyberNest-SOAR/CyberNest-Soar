/**
 * Cross-browser clipboard copier utility.
 * Tries the modern navigator.clipboard API first, falling back to a hidden textarea with execCommand.
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  if (!text) return false;

  // 1. Modern browser Clipboard API
  if (navigator.clipboard && typeof navigator.clipboard.writeText === "function") {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch (err) {
      console.warn("navigator.clipboard.writeText failed, falling back to older execCommand method.", err);
    }
  }

  // 2. Fallback method for older browsers or non-secure contexts (HTTP)
  try {
    const textArea = document.createElement("textarea");
    textArea.value = text;
    
    // Prevent scrolling to bottom of screen when appending
    textArea.style.position = "fixed";
    textArea.style.top = "0";
    textArea.style.left = "0";
    textArea.style.width = "2em";
    textArea.style.height = "2em";
    textArea.style.padding = "0";
    textArea.style.border = "none";
    textArea.style.outline = "none";
    textArea.style.boxShadow = "none";
    textArea.style.background = "transparent";
    textArea.style.opacity = "0";

    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    const successful = document.execCommand("copy");
    document.body.removeChild(textArea);
    
    return successful;
  } catch (err) {
    console.error("Clipboard copy fallback also failed:", err);
    return false;
  }
}
