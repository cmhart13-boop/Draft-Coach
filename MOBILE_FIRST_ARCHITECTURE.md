# Shiva Mobile-First Ecosystem

This repository is moving from a web-first Streamlit experience to a mobile-first product architecture.

## Core principle

The primary product is a native-feeling phone app. Desktop/web is secondary. Every interaction, layout, state transition, draft workflow, player profile, navigation pattern, and data call should be designed for one-handed mobile use first.

## Target architecture

- **Mobile client:** React Native + Expo + TypeScript
- **Navigation:** native stack + tab navigation, no browser-style page reload mental model
- **State:** persistent app state for draft room, queue, roster, favorites, player filters, league context, and Ask Shiva sessions
- **Backend:** Python API layer reusing the existing verified fantasy-football engines and datasets
- **Data contract:** JSON APIs for rankings, player profiles, weekly history, league history, mock-draft state, recommendations, and Ask Shiva evidence
- **Web/Streamlit:** retained only as a temporary prototype/admin/debug surface while mobile parity is built

## Mobile UX rules

1. No horizontal page scrolling for normal screens.
2. Bottom navigation is persistent and thumb-reachable.
3. Primary tap targets are at least 44x44 points.
4. Player names are tappable everywhere and open the same canonical player profile.
5. Draft Players / Queue / Draft Board / Roster are views of one shared live draft state, not separate pages that reset state.
6. Navigation transitions preserve position, filters, queue, roster, draft state, and return location.
7. Dense information is redesigned into mobile cards, sheets, segmented controls, and vertically scannable rows rather than shrinking desktop tables.
8. Draft actions must be usable with one thumb during a live draft.
9. Safe-area insets, iPhone home indicator, keyboard avoidance, and dynamic screen heights are first-class requirements.
10. Historical facts, current rankings, projections, and live news remain explicitly separated and data-verified.

## Migration rule

New product work should target the mobile client first. Existing Streamlit code should only receive fixes needed to keep the current prototype functional while equivalent mobile screens are built.

## Initial mobile screen map

- Home
- Mock Draft
  - Players Available
  - Queue
  - Draft Board
  - Roster
- Player Search
- Player Profile
- Team IQ / League History
- Draft Coach
- Sleepers
- Cheat Sheets
- Ask Shiva

## Shared engine rule

The existing Python fantasy logic is valuable and should not be duplicated inside the mobile UI. Draft logic, verified scoring, historical analysis, query routing, and Shiva evidence generation should be exposed behind a stable API so the mobile app remains presentation-focused and fast.
