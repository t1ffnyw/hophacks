"""Anywidget: plant-a-tree animation with TreeBaltimore donate link."""

from __future__ import annotations

import anywidget
import traitlets


class TreeDonateWidget(anywidget.AnyWidget):
    _esm = """
    function render({ model, el }) {
      el.classList.add("tree-donate-widget");

      el.innerHTML = `
        <div class="tdw-card">
          <svg class="tdw-scene" viewBox="0 0 200 220" xmlns="http://www.w3.org/2000/svg">
            <!-- ground -->
            <ellipse class="tdw-ground" cx="100" cy="195" rx="70" ry="12"/>
            <ellipse class="tdw-mound" cx="100" cy="192" rx="22" ry="7"/>

            <!-- falling seed -->
            <circle class="tdw-seed" cx="100" cy="10" r="5"/>

            <!-- sprout + trunk (grows upward via scaleY) -->
            <rect class="tdw-trunk" x="97" y="120" width="6" height="75" rx="2"/>

            <!-- canopy leaves, each pops in with its own delay -->
            <g class="tdw-canopy">
              <circle class="tdw-leaf l1" cx="100" cy="110" r="55"/>
              <circle class="tdw-leaf l2" cx="65" cy="130" r="38"/>
              <circle class="tdw-leaf l3" cx="135" cy="130" r="38"/>
              <circle class="tdw-leaf l4" cx="100" cy="70" r="42"/>
            </g>

            <g class="tdw-falling-leaves">
              <circle class="tdw-fleaf f1" cx="70" cy="90" r="4"/>
              <circle class="tdw-fleaf f2" cx="130" cy="100" r="4"/>
              <circle class="tdw-fleaf f3" cx="100" cy="60" r="4"/>
            </g>
          </svg>

          <h3 class="tdw-title">Help Grow Baltimore's Tree Canopy</h3>
          <p class="tdw-subtitle tdw-subtitle-pre">Click below to plant your tree.</p>
          <p class="tdw-subtitle tdw-subtitle-post">Every donation helps plant and care for real trees across the city.</p>

          <button class="tdw-button tdw-plant-btn" type="button">🌱 Plant a Tree</button>
          <a class="tdw-button tdw-donate-btn" href="https://secure.qgiv.com/for/treebaltimore/" target="_blank" rel="noopener noreferrer">
            🌳 Donate to Plant More
          </a>
        </div>
      `;

      const card = el.querySelector(".tdw-card");
      const plantBtn = el.querySelector(".tdw-plant-btn");
      const donateBtn = el.querySelector(".tdw-donate-btn");

      plantBtn.addEventListener("click", () => {
        if (card.classList.contains("tdw-planted")) return;
        card.classList.add("tdw-planting");

        model.set("clicks", model.get("clicks") + 1);
        model.save_changes();

        // total sequence time matches the CSS animation timings below
        setTimeout(() => {
          card.classList.remove("tdw-planting");
          card.classList.add("tdw-planted");
        }, 2600);
      });

      donateBtn.addEventListener("mouseenter", () => card.classList.add("tdw-shake"));
      donateBtn.addEventListener("mouseleave", () => card.classList.remove("tdw-shake"));
    }
    export default { render };
    """

    _css = """
    .tree-donate-widget {
        display: flex;
        justify-content: center;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        padding: 20px 0;
    }

    .tdw-card {
        background: linear-gradient(180deg, #eef8ee 0%, #ffffff 100%);
        border: 1px solid #d7ead7;
        border-radius: 16px;
        padding: 24px 32px;
        text-align: center;
        max-width: 320px;
        box-shadow: 0 4px 14px rgba(0, 80, 0, 0.08);
    }

    .tdw-scene {
        display: block;
        margin: 0 auto;
        width: 140px;
        height: auto;
        overflow: visible;
    }

    .tdw-ground {
        fill: #c9a874;
    }
    .tdw-mound {
        fill: #a9855a;
        opacity: 0;
    }

    .tdw-seed {
        fill: #6b4423;
        opacity: 0;
    }

    .tdw-trunk {
        fill: #8b5a2b;
        transform-origin: 100px 195px;
        transform: scaleY(0);
    }

    .tdw-canopy {
        transform-origin: 100px 110px;
    }
    .tdw-leaf {
        fill: #4caf50;
        opacity: 0;
        transform-origin: center;
        transform: scale(0);
    }
    .tdw-leaf.l2 { fill: #43a047; }
    .tdw-leaf.l3 { fill: #388e3c; }
    .tdw-leaf.l4 { fill: #66bb6a; }

    .tdw-falling-leaves {
        opacity: 0;
    }
    .tdw-fleaf {
        fill: #4caf50;
    }

    .tdw-title {
        margin: 14px 0 4px;
        font-size: 17px;
        color: #234d24;
    }

    .tdw-subtitle {
        margin: 0 0 16px;
        font-size: 13px;
        color: #557a55;
    }
    .tdw-subtitle-post { display: none; }

    .tdw-button {
        display: inline-block;
        background: #2e7d32;
        color: white;
        text-decoration: none;
        font-weight: 600;
        font-family: inherit;
        font-size: 14px;
        border: none;
        cursor: pointer;
        padding: 10px 20px;
        border-radius: 999px;
        transition: transform 0.15s ease, background 0.15s ease;
    }
    .tdw-button:hover {
        background: #256428;
        transform: translateY(-2px) scale(1.03);
    }

    .tdw-donate-btn { display: none; }

    /* ---------- Planting sequence ---------- */

    /* 1. seed drops in (0 - 0.6s) */
    .tdw-planting .tdw-seed,
    .tdw-planted .tdw-seed {
        animation: tdw-seed-drop 0.6s ease-in forwards;
    }

    /* 2. soil mound bumps up as seed lands (0.5 - 0.8s) */
    .tdw-planting .tdw-mound,
    .tdw-planted .tdw-mound {
        animation: tdw-mound-pop 0.4s ease-out 0.5s forwards;
    }

    /* 3. trunk/sprout grows up out of the mound (0.8 - 1.6s) */
    .tdw-planting .tdw-trunk,
    .tdw-planted .tdw-trunk {
        animation: tdw-trunk-grow 0.8s ease-out 0.8s forwards;
    }

    /* 4. leaves pop in one by one (1.5 - 2.4s) */
    .tdw-planting .tdw-leaf.l1, .tdw-planted .tdw-leaf.l1 { animation: tdw-leaf-pop 0.35s ease-out 1.5s forwards; }
    .tdw-planting .tdw-leaf.l2, .tdw-planted .tdw-leaf.l2 { animation: tdw-leaf-pop 0.35s ease-out 1.7s forwards; }
    .tdw-planting .tdw-leaf.l3, .tdw-planted .tdw-leaf.l3 { animation: tdw-leaf-pop 0.35s ease-out 1.9s forwards; }
    .tdw-planting .tdw-leaf.l4, .tdw-planted .tdw-leaf.l4 { animation: tdw-leaf-pop 0.35s ease-out 2.1s forwards; }

    @keyframes tdw-seed-drop {
        0%   { opacity: 1; transform: translateY(0); }
        85%  { opacity: 1; transform: translateY(175px); }
        100% { opacity: 0; transform: translateY(180px); }
    }

    @keyframes tdw-mound-pop {
        0%   { opacity: 0; transform: scale(0.3); }
        100% { opacity: 1; transform: scale(1); }
    }

    @keyframes tdw-trunk-grow {
        0%   { transform: scaleY(0); }
        100% { transform: scaleY(1); }
    }

    @keyframes tdw-leaf-pop {
        0%   { opacity: 0; transform: scale(0); }
        70%  { opacity: 1; transform: scale(1.15); }
        100% { opacity: 1; transform: scale(1); }
    }

    /* once fully planted: gentle continuous sway + swap UI */
    .tdw-planted .tdw-canopy {
        animation: tdw-sway 4s ease-in-out infinite;
    }
    @keyframes tdw-sway {
        0%, 100% { transform: rotate(-1.5deg); }
        50%      { transform: rotate(1.5deg); }
    }

    .tdw-planted .tdw-plant-btn { display: none; }
    .tdw-planted .tdw-donate-btn {
        display: inline-block;
        animation: tdw-fade-in 0.6s ease-out;
    }
    .tdw-planted .tdw-subtitle-pre { display: none; }
    .tdw-planted .tdw-subtitle-post { display: block; }

    @keyframes tdw-fade-in {
        from { opacity: 0; transform: translateY(4px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    /* hover shake + falling leaves on donate button */
    .tdw-shake .tdw-canopy {
        animation: tdw-shake-anim 0.4s ease-in-out, tdw-sway 4s ease-in-out infinite 0.4s;
    }
    @keyframes tdw-shake-anim {
        0%, 100% { transform: rotate(0deg); }
        25%      { transform: rotate(-4deg); }
        75%      { transform: rotate(4deg); }
    }
    .tdw-shake .tdw-falling-leaves { opacity: 1; }
    .tdw-shake .f1 { animation: tdw-fall 1s ease-in forwards; }
    .tdw-shake .f2 { animation: tdw-fall 1.2s ease-in 0.15s forwards; }
    .tdw-shake .f3 { animation: tdw-fall 0.9s ease-in 0.3s forwards; }
    @keyframes tdw-fall {
        to { transform: translate(-10px, 90px) rotate(120deg); opacity: 0; }
    }
    """

    clicks = traitlets.Int(0).tag(sync=True)


def build_tree_donate_widget() -> TreeDonateWidget:
    return TreeDonateWidget()
