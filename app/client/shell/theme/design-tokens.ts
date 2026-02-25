/**
 * Centralized Design Tokens for A2UI Application
 * 
 * This file contains all design tokens including colors, spacing, border-radius,
 * and other visual properties. All components should use these tokens for consistency.
 * 
 * Color Palette:
 * - Agent: Dark blue-gray tones for the agent/dynamic module
 * - Oracle: Brand colors including coral, gold, and blue
 * - Chat: Purple-gray tones for the chat module
 * - Traditional: Teal/cyan tones for the traditional module
 */

import { css, unsafeCSS } from "lit";

// =============================================================================
// COLOR PALETTE (HEX VALUES)
// =============================================================================

export const colors = {
  // Agent Module Colors
  agent: {
    bg: '#181C27',           // Very dark blue-gray (primary background)
    bgSecondary: '#232935',  // Dark blue-gray (secondary background)
    accent: '#213E30',       // Dark green (accent)
    highlight: '#5A4A14',    // Dark gold/brown (highlight)
    border: '#1A2E52',       // Dark blue (borders)
  },

  // Oracle Brand Colors
  oracle: {
    bgDark: '#2B2F37',       // Dark gray (backgrounds)
    primary: '#88C2FF',      // Light blue (primary actions)
    secondary: '#D16556',    // Coral/salmon (secondary)
    accent: '#F0CC71',       // Gold/yellow (accent)
  },

  // Chat Module Colors
  chat: {
    bg: '#353951',           // Dark blue-purple (primary background)
    bgSecondary: '#7982A4',  // Medium gray-blue (secondary)
    surface: '#F0F2F6',      // Very light gray (surfaces in light mode)
  },

  // Traditional Module Colors (using Oracle palette for distinction)
  traditional: {
    primary: '#2B2F37',      // Oracle dark gray
    secondary: '#1A2E52',    // Agent border blue
  },

  // Neutral Colors
  neutral: {
    white: '#FFFFFF',
    black: '#000000',
    gray50: '#F9FAFB',
    gray100: '#F3F4F6',
    gray200: '#E5E7EB',
    gray300: '#D1D5DB',
    gray400: '#9CA3AF',
    gray500: '#6B7280',
    gray600: '#4B5563',
    gray700: '#374151',
    gray800: '#1F2937',
    gray900: '#111827',
  },

  // Semantic Colors
  semantic: {
    success: '#10B981',
    successDark: '#059669',
    error: '#EF4444',
    errorDark: '#DC2626',
    warning: '#F59E0B',
    info: '#3B82F6',
  },
} as const;

// =============================================================================
// SPACING & SIZING
// =============================================================================

export const spacing = {
  xs: '0.25rem',   // 4px
  sm: '0.5rem',    // 8px
  md: '1rem',      // 16px
  lg: '1.5rem',    // 24px
  xl: '2rem',      // 32px
  '2xl': '3rem',   // 48px
} as const;

// =============================================================================
// BORDER RADIUS
// =============================================================================

export const radius = {
  none: '0',
  sm: '0.25rem',   // 4px
  md: '0.5rem',    // 8px
  lg: '0.75rem',   // 12px
  xl: '1rem',      // 16px
  '2xl': '1.5rem', // 24px
  full: '9999px',  // Fully rounded
} as const;

// =============================================================================
// TYPOGRAPHY
// =============================================================================

export const typography = {
  fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
  fontFamilyMono: "'Monaco', 'Menlo', 'Ubuntu Mono', monospace",
  fontSize: {
    xs: '0.75rem',   // 12px
    sm: '0.875rem',  // 14px
    base: '1rem',    // 16px
    lg: '1.125rem',  // 18px
    xl: '1.25rem',   // 20px
    '2xl': '1.5rem', // 24px
  },
  fontWeight: {
    normal: '400',
    medium: '500',
    semibold: '600',
    bold: '700',
  },
  lineHeight: {
    tight: '1.25',
    normal: '1.5',
    relaxed: '1.75',
  },
} as const;

// =============================================================================
// SHADOWS
// =============================================================================

export const shadows = {
  sm: '0 1px 2px rgba(0, 0, 0, 0.05)',
  md: '0 4px 6px rgba(0, 0, 0, 0.1)',
  lg: '0 10px 25px rgba(0, 0, 0, 0.5)',
  glow: '0 4px 15px rgba(102, 126, 234, 0.4)',
} as const;

// =============================================================================
// TRANSITIONS
// =============================================================================

export const transitions = {
  fast: '0.1s ease',
  normal: '0.2s ease',
  slow: '0.3s ease',
} as const;

// =============================================================================
// CSS CUSTOM PROPERTIES (Design Tokens as CSS Variables)
// =============================================================================

export const designTokensCSS = css`
  :host {
    /* Agent Module Colors */
    --agent-bg: ${unsafeCSS(colors.agent.bg)};
    --agent-bg-secondary: ${unsafeCSS(colors.agent.bgSecondary)};
    --agent-accent: ${unsafeCSS(colors.agent.accent)};
    --agent-highlight: ${unsafeCSS(colors.agent.highlight)};
    --agent-border: ${unsafeCSS(colors.agent.border)};

    /* Oracle Brand Colors */
    --oracle-bg-dark: ${unsafeCSS(colors.oracle.bgDark)};
    --oracle-primary: ${unsafeCSS(colors.oracle.primary)};
    --oracle-secondary: ${unsafeCSS(colors.oracle.secondary)};
    --oracle-accent: ${unsafeCSS(colors.oracle.accent)};

    /* Chat Module Colors */
    --chat-bg: ${unsafeCSS(colors.chat.bg)};
    --chat-bg-secondary: ${unsafeCSS(colors.chat.bgSecondary)};
    --chat-surface: ${unsafeCSS(colors.chat.surface)};

    /* Traditional Module Colors */
    --traditional-primary: ${unsafeCSS(colors.traditional.primary)};
    --traditional-secondary: ${unsafeCSS(colors.traditional.secondary)};

    /* Neutral Colors */
    --neutral-white: ${unsafeCSS(colors.neutral.white)};
    --neutral-black: ${unsafeCSS(colors.neutral.black)};
    --neutral-50: ${unsafeCSS(colors.neutral.gray50)};
    --neutral-100: ${unsafeCSS(colors.neutral.gray100)};
    --neutral-200: ${unsafeCSS(colors.neutral.gray200)};
    --neutral-300: ${unsafeCSS(colors.neutral.gray300)};
    --neutral-400: ${unsafeCSS(colors.neutral.gray400)};
    --neutral-500: ${unsafeCSS(colors.neutral.gray500)};
    --neutral-600: ${unsafeCSS(colors.neutral.gray600)};
    --neutral-700: ${unsafeCSS(colors.neutral.gray700)};
    --neutral-800: ${unsafeCSS(colors.neutral.gray800)};
    --neutral-900: ${unsafeCSS(colors.neutral.gray900)};

    /* Semantic Colors */
    --color-success: ${unsafeCSS(colors.semantic.success)};
    --color-success-dark: ${unsafeCSS(colors.semantic.successDark)};
    --color-error: ${unsafeCSS(colors.semantic.error)};
    --color-error-dark: ${unsafeCSS(colors.semantic.errorDark)};
    --color-warning: ${unsafeCSS(colors.semantic.warning)};
    --color-info: ${unsafeCSS(colors.semantic.info)};

    /* Spacing */
    --space-xs: ${unsafeCSS(spacing.xs)};
    --space-sm: ${unsafeCSS(spacing.sm)};
    --space-md: ${unsafeCSS(spacing.md)};
    --space-lg: ${unsafeCSS(spacing.lg)};
    --space-xl: ${unsafeCSS(spacing.xl)};
    --space-2xl: ${unsafeCSS(spacing['2xl'])};

    /* Border Radius */
    --radius-none: ${unsafeCSS(radius.none)};
    --radius-sm: ${unsafeCSS(radius.sm)};
    --radius-md: ${unsafeCSS(radius.md)};
    --radius-lg: ${unsafeCSS(radius.lg)};
    --radius-xl: ${unsafeCSS(radius.xl)};
    --radius-2xl: ${unsafeCSS(radius['2xl'])};
    --radius-full: ${unsafeCSS(radius.full)};

    /* Typography */
    --font-family: ${unsafeCSS(typography.fontFamily)};
    --font-family-mono: ${unsafeCSS(typography.fontFamilyMono)};
    --font-size-xs: ${unsafeCSS(typography.fontSize.xs)};
    --font-size-sm: ${unsafeCSS(typography.fontSize.sm)};
    --font-size-base: ${unsafeCSS(typography.fontSize.base)};
    --font-size-lg: ${unsafeCSS(typography.fontSize.lg)};
    --font-size-xl: ${unsafeCSS(typography.fontSize.xl)};
    --font-size-2xl: ${unsafeCSS(typography.fontSize['2xl'])};
    --font-weight-normal: ${unsafeCSS(typography.fontWeight.normal)};
    --font-weight-medium: ${unsafeCSS(typography.fontWeight.medium)};
    --font-weight-semibold: ${unsafeCSS(typography.fontWeight.semibold)};
    --font-weight-bold: ${unsafeCSS(typography.fontWeight.bold)};
    --line-height-tight: ${unsafeCSS(typography.lineHeight.tight)};
    --line-height-normal: ${unsafeCSS(typography.lineHeight.normal)};
    --line-height-relaxed: ${unsafeCSS(typography.lineHeight.relaxed)};

    /* Shadows */
    --shadow-sm: ${unsafeCSS(shadows.sm)};
    --shadow-md: ${unsafeCSS(shadows.md)};
    --shadow-lg: ${unsafeCSS(shadows.lg)};
    --shadow-glow: ${unsafeCSS(shadows.glow)};

    /* Transitions */
    --transition-fast: ${unsafeCSS(transitions.fast)};
    --transition-normal: ${unsafeCSS(transitions.normal)};
    --transition-slow: ${unsafeCSS(transitions.slow)};

    /* =========================================================================
       SEMANTIC TOKENS (Contextual usage of design tokens)
       ========================================================================= */

    /* Application Background */
    --app-bg: var(--agent-bg);
    --app-bg-secondary: var(--agent-bg-secondary);

    /* Surface Colors */
    --surface-primary: var(--agent-bg-secondary);
    --surface-secondary: rgba(255, 255, 255, 0.1);
    --surface-elevated: rgba(255, 255, 255, 0.15);

    /* Text Colors */
    --text-primary: var(--neutral-white);
    --text-secondary: rgba(255, 255, 255, 0.7);
    --text-muted: rgba(255, 255, 255, 0.5);
    --text-inverse: var(--neutral-900);

    /* Border Colors */
    --border-primary: var(--agent-border);
    --border-secondary: rgba(255, 255, 255, 0.2);
    --border-subtle: rgba(255, 255, 255, 0.1);

    /* Interactive States */
    --hover-overlay: rgba(255, 255, 255, 0.1);
    --active-overlay: rgba(255, 255, 255, 0.2);
    --focus-ring: var(--oracle-primary);

    /* Module-Specific Backgrounds */
    --module-agent-bg: linear-gradient(135deg, var(--agent-bg-secondary) 0%, var(--agent-border) 100%);
    --module-chat-bg: linear-gradient(135deg, var(--chat-bg) 0%, #4a5073 100%);
    --module-traditional-bg: linear-gradient(135deg, var(--oracle-bg-dark) 0%, #1f2329 100%);

    /* Module-Specific Accent Colors */
    --module-agent-accent: var(--oracle-accent);       /* Gold for Agent */
    --module-chat-accent: var(--oracle-primary);       /* Blue for Chat */
    --module-traditional-accent: var(--oracle-secondary); /* Coral for Traditional */

    /* Module-Specific Active Tab/Button Colors */
    --module-agent-active: rgba(240, 204, 113, 0.2);   /* Gold glow */
    --module-chat-active: rgba(136, 194, 255, 0.2);    /* Blue glow */
    --module-traditional-active: rgba(209, 101, 86, 0.2); /* Coral glow */
  }
`;

// =============================================================================
// GLOBAL STYLES (Reset & Base Styles)
// =============================================================================

export const globalStyles = css`
  ${designTokensCSS}

  * {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }

  :host {
    font-family: var(--font-family);
    font-size: var(--font-size-base);
    line-height: var(--line-height-normal);
    color: var(--text-primary);
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }
`;

// =============================================================================
// COMPONENT-SPECIFIC STYLE MIXINS
// =============================================================================

/** Card styles with consistent border-radius and background */
export const cardStyles = css`
  .card {
    background: var(--surface-primary);
    border-radius: var(--radius-xl);
    padding: var(--space-md);
    border: 1px solid var(--border-subtle);
  }
`;

/** Button styles following the design system */
export const buttonStyles = css`
  .btn {
    padding: var(--space-sm) var(--space-md);
    border-radius: var(--radius-md);
    border: none;
    font-family: var(--font-family);
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-medium);
    cursor: pointer;
    transition: all var(--transition-normal);
  }

  .btn-primary {
    background: var(--oracle-primary);
    color: var(--neutral-900);
  }

  .btn-primary:hover {
    filter: brightness(1.1);
  }

  .btn-secondary {
    background: var(--surface-secondary);
    color: var(--text-primary);
    border: 1px solid var(--border-secondary);
  }

  .btn-secondary:hover {
    background: var(--hover-overlay);
  }

  .btn-success {
    background: var(--color-success);
    color: var(--neutral-white);
  }

  .btn-success:hover {
    background: var(--color-success-dark);
  }
`;

/** Input field styles */
export const inputStyles = css`
  .input {
    width: 100%;
    padding: var(--space-sm) var(--space-md);
    border-radius: var(--radius-full);
    border: 1px solid var(--border-secondary);
    background: var(--surface-primary);
    color: var(--text-primary);
    font-family: var(--font-family);
    font-size: var(--font-size-base);
    outline: none;
    transition: border-color var(--transition-normal);
  }

  .input::placeholder {
    color: var(--text-muted);
  }

  .input:focus {
    border-color: var(--focus-ring);
  }
`;

/** Status indicator styles */
export const statusStyles = css`
  .status-container {
    background: var(--surface-secondary);
    border-radius: var(--radius-md);
    padding: var(--space-sm);
    min-height: 80px;
    max-height: 250px;
    overflow-y: auto;
  }

  .status-item {
    padding: var(--space-xs) 0;
    border-bottom: 1px solid var(--border-secondary);
    font-size: var(--font-size-sm);
    line-height: var(--line-height-normal);
    display: flex;
    gap: var(--space-sm);
  }

  .status-item:last-child {
    border-bottom: none;
  }

  .status-duration {
    font-weight: var(--font-weight-bold);
    color: var(--text-primary);
    min-width: 4rem;
    text-align: right;
  }
`;

/** Suggestion chip styles */
export const suggestionStyles = css`
  .suggestions-list {
    display: flex;
    flex-direction: column;
    gap: var(--space-sm);
  }

  .suggestion-item {
    padding: var(--space-sm) var(--space-md);
    background: var(--surface-secondary);
    border-radius: var(--radius-md);
    cursor: pointer;
    transition: background var(--transition-normal), transform var(--transition-fast);
    border: 1px solid var(--border-secondary);
  }

  .suggestion-item:hover {
    background: var(--surface-elevated);
    transform: translateX(4px);
  }

  .suggestion-item:active {
    transform: scale(0.98);
  }
`;

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Creates an rgba color from a hex color with alpha
 */
export function hexToRgba(hex: string, alpha: number): string {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

/**
 * Gets module-specific color based on module type
 */
export function getModuleColor(module: 'agent' | 'chat' | 'traditional'): string {
  switch (module) {
    case 'agent':
      return colors.agent.bg;
    case 'chat':
      return colors.chat.bg;
    case 'traditional':
      return colors.traditional.primary;
    default:
      return colors.agent.bg;
  }
}
