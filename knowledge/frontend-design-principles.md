# Frontend Design Principles

Shared rules for all design-* and build modes working on frontend interfaces.

## Visual Direction
- Choose a clear visual direction for each project — avoid defaulting to generic layouts
- Define CSS variables for colors, spacing, and typography early
- Use gradients, shapes, or subtle patterns for backgrounds instead of flat single colors

## Typography
- Select expressive, purposeful fonts — avoid generic defaults (Inter, Roboto, Arial, system)
- Establish a type scale and use it consistently

## Color
- No purple-on-white defaults, no automatic dark mode bias
- Ensure contrast meets WCAG AA (4.5:1 normal text, 3:1 large text)

## Motion
- Use meaningful animations at key moments (page load, staggered reveals)
- Avoid gratuitous micro-animations on every interaction

## Responsive
- Verify layouts work on both desktop and mobile
- Touch targets meet 44x44px minimum on mobile

## When Working in Existing Systems
- Preserve established patterns, structure, and visual language
- Match the existing design system rather than introducing new directions

Tags: frontend, design, css, ui
