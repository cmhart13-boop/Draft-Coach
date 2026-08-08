from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components


def hide_streamlit_branding() -> None:
    """Remove Streamlit/Community Cloud chrome that overlaps the mobile app nav.

    CSS handles normal Streamlit chrome. A tiny zero-height browser component also
    injects CSS into the parent document and watches for Community Cloud controls
    that are mounted after Streamlit finishes rendering.
    """
    st.markdown(
        r"""
        <style>
        header,
        footer,
        #MainMenu,
        #stDecoration,
        [data-testid="stHeader"],
        [data-testid="stToolbar"],
        [data-testid="stToolbarActions"],
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"],
        [data-testid="stStatusWidget"] *,
        [data-testid="stAppDeployButton"],
        [data-testid="stMainMenu"],
        [data-testid="stBaseButton-header"],
        [data-testid="stBaseButton-headerNoPadding"],
        .stAppDeployButton,
        .stDeployButton,
        .viewerBadge_container__1QSob,
        .styles_viewerBadge__1yB5_,
        .viewerBadge_link__1S137,
        .viewerBadge_text__1JaDK,
        [class*="viewerBadge"],
        [class*="ViewerBadge"],
        [class*="hostedWithStreamlit"],
        [class*="HostedWithStreamlit"],
        [class*="manageApp"],
        [class*="ManageApp"],
        [aria-label*="Hosted with Streamlit"],
        [aria-label*="Streamlit Community Cloud"],
        [aria-label*="Manage app"],
        [title*="Hosted with Streamlit"],
        [title*="Streamlit Community Cloud"],
        [title*="Manage app"],
        a[href*="share.streamlit.io"],
        a[href*="streamlit.io/cloud"] {
            display:none !important;
            visibility:hidden !important;
            opacity:0 !important;
            pointer-events:none !important;
            width:0 !important;
            height:0 !important;
            min-width:0 !important;
            min-height:0 !important;
            overflow:hidden !important;
        }
        [data-testid="stAppViewContainer"] > header,
        [data-testid="stAppViewContainer"] > footer {
            display:none !important;
            height:0 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Community Cloud can render its red Streamlit crown / account badge outside
    # the regular Streamlit content tree and can add it after our CSS is parsed.
    # This parent-document observer removes those late-mounted controls and any
    # small fixed floating widget occupying the bottom-right corner, while
    # explicitly preserving Shiva's own bottom nav and live draft status card.
    components.html(
        r"""
        <script>
        (() => {
          const doc = window.parent.document;
          const win = window.parent;
          const STYLE_ID = 'shiva-hide-streamlit-cloud-ui';

          if (!doc.getElementById(STYLE_ID)) {
            const style = doc.createElement('style');
            style.id = STYLE_ID;
            style.textContent = `
              header, footer, #MainMenu, #stDecoration,
              [data-testid="stHeader"], [data-testid="stToolbar"],
              [data-testid="stToolbarActions"], [data-testid="stDecoration"],
              [data-testid="stStatusWidget"], [data-testid="stAppDeployButton"],
              [data-testid="stMainMenu"], [data-testid="stBaseButton-header"],
              [data-testid="stBaseButton-headerNoPadding"],
              .stAppDeployButton, .stDeployButton,
              [class*="viewerBadge"], [class*="ViewerBadge"],
              [class*="hostedWithStreamlit"], [class*="HostedWithStreamlit"],
              [class*="manageApp"], [class*="ManageApp"],
              [aria-label*="Hosted with Streamlit"],
              [aria-label*="Streamlit Community Cloud"],
              [aria-label*="Manage app"],
              [title*="Hosted with Streamlit"],
              [title*="Streamlit Community Cloud"],
              [title*="Manage app"],
              a[href*="share.streamlit.io"], a[href*="streamlit.io/cloud"] {
                display:none !important; visibility:hidden !important;
                opacity:0 !important; pointer-events:none !important;
              }
            `;
            doc.head.appendChild(style);
          }

          const kill = (el) => {
            if (!el || el.nodeType !== 1) return;
            if (el.closest && (el.closest('.bottom-nav') || el.closest('.draft-status'))) return;
            el.style.setProperty('display','none','important');
            el.style.setProperty('visibility','hidden','important');
            el.style.setProperty('opacity','0','important');
            el.style.setProperty('pointer-events','none','important');
          };

          const sweep = () => {
            const selectors = [
              '[data-testid="stStatusWidget"]',
              '[data-testid="stAppDeployButton"]',
              '[data-testid="stToolbar"]',
              '[data-testid="stToolbarActions"]',
              '[data-testid="stMainMenu"]',
              '[data-testid="stBaseButton-header"]',
              '[data-testid="stBaseButton-headerNoPadding"]',
              '[class*="viewerBadge"]', '[class*="ViewerBadge"]',
              '[class*="hostedWithStreamlit"]', '[class*="HostedWithStreamlit"]',
              '[class*="manageApp"]', '[class*="ManageApp"]',
              '[aria-label*="Streamlit"]', '[title*="Streamlit"]',
              '[aria-label*="Manage app"]', '[title*="Manage app"]',
              'a[href*="share.streamlit.io"]', 'a[href*="streamlit.io/cloud"]'
            ];
            selectors.forEach(s => doc.querySelectorAll(s).forEach(kill));

            // Last-resort mobile cleanup for the exact type of floating controls
            // shown in the bottom-right screenshot. Restrict this to small fixed
            // elements hugging the bottom-right edge so app content is untouched.
            doc.querySelectorAll('body *').forEach(el => {
              if (el.closest('.bottom-nav') || el.closest('.draft-status')) return;
              const cs = win.getComputedStyle(el);
              if (cs.position !== 'fixed') return;
              const r = el.getBoundingClientRect();
              if (!r.width || !r.height) return;
              const nearRight = (win.innerWidth - r.right) <= 18;
              const nearBottom = (win.innerHeight - r.bottom) <= 95;
              const small = r.width <= 190 && r.height <= 190;
              if (nearRight && nearBottom && small) kill(el);
            });
          };

          sweep();
          const observer = new MutationObserver(sweep);
          observer.observe(doc.documentElement, {childList:true, subtree:true, attributes:true});
          win.setTimeout(sweep, 250);
          win.setTimeout(sweep, 1000);
          win.setTimeout(sweep, 2500);
        })();
        </script>
        """,
        height=0,
        width=0,
    )
