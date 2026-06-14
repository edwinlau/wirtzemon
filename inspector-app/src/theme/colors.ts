/**
 * Design system — dark navy + white base, amber accent for gamification.
 * Clean sans-serif typography (system default).
 */
export const colors = {
  // Base
  navy: '#0B1A2F',
  navyElevated: '#13263F',
  navyCard: '#16304F',
  border: '#23425F',

  // Text
  white: '#FFFFFF',
  textPrimary: '#F4F8FF',
  textSecondary: '#A7BAD0',
  textMuted: '#6E83A0',

  // Accent (gamification)
  amber: '#F5A623',
  amberSoft: '#FFD27A',

  // Status
  success: '#3DD68C',
  warning: '#F5A623',
  danger: '#FF6B6B',
  info: '#4DA3FF',

  // Misc
  inputBg: '#0F2238',
  overlay: 'rgba(0,0,0,0.5)',
} as const;

export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
} as const;

export const radii = {
  sm: 8,
  md: 12,
  lg: 20,
  pill: 999,
} as const;

export const typography = {
  title: { fontSize: 28, fontWeight: '700' as const },
  heading: { fontSize: 20, fontWeight: '700' as const },
  subheading: { fontSize: 16, fontWeight: '600' as const },
  body: { fontSize: 15, fontWeight: '400' as const },
  caption: { fontSize: 13, fontWeight: '400' as const },
} as const;
