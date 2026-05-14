/**
 * Dark mode styles for Watson Orchestrate chat widget
 * Uses CSS custom properties for easy theming
 */

// CSS custom properties for theming
const CSS_VARIABLES = `
  :root {
    --wxo-bg-primary: #161616;
    --wxo-bg-secondary: #262626;
    --wxo-bg-tertiary: #393939;
    --wxo-text-primary: #f4f4f4;
    --wxo-text-secondary: #8d8d8d;
    --wxo-border: #393939;
  }
`;

// Main dark mode styles
export const DARK_MODE_STYLES = `
  ${CSS_VARIABLES}

  /* Dark backgrounds */
  #wxo-container,
  #wxo-container [class*="App"],
  #wxo-container [class*="Container"],
  #wxo-container [class*="Wrapper"],
  #wxo-container [class*="Panel"],
  #wxo-container [class*="messages"],
  #wxo-container [class*="Messages"],
  #wxo-container [class*="scroller"],
  #wxo-container .cds--content {
    background-color: var(--wxo-bg-primary) !important;
  }

  /* Header bar */
  #wxo-container [class*="header"],
  #wxo-container [class*="Header"] {
    background-color: var(--wxo-bg-secondary) !important;
    color: var(--wxo-text-primary) !important;
    border-bottom: 1px solid var(--wxo-border) !important;
  }

  /* Footer / input bar */
  #wxo-container nav,
  #wxo-container [class*="footer"],
  #wxo-container [class*="Footer"],
  #wxo-container [class*="bar"],
  #wxo-container [class*="Bar"] {
    background-color: var(--wxo-bg-secondary) !important;
    color: var(--wxo-text-primary) !important;
  }

  /* Text inputs */
  #wxo-container input,
  #wxo-container textarea,
  #wxo-container [class*="text-area"],
  #wxo-container [class*="TextArea"] {
    background-color: var(--wxo-bg-tertiary) !important;
    color: var(--wxo-text-primary) !important;
    caret-color: var(--wxo-text-primary) !important;
  }

  #wxo-container input::placeholder,
  #wxo-container textarea::placeholder {
    color: var(--wxo-text-secondary) !important;
  }

  /* All text white */
  #wxo-container,
  #wxo-container * {
    color: var(--wxo-text-primary) !important;
  }

  /* Buttons transparent */
  #wxo-container button {
    background-color: transparent !important;
  }

  /* ALL SVG icons white via filter */
  #wxo-container svg {
    filter: brightness(0) invert(1) !important;
    background-color: transparent !important;
  }
`;

// Style element ID for DOM management
export const STYLE_ELEMENT_ID = "wxo-dark-mode";
