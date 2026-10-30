# WASM UI design reference

The reference is `https://github.com/xulang-org/xu-ui-design`, version 0.1.0,
commit `81ca08379e213caea7debff9dc3bd2ae9c7d7e6a`.
`tokens.json` is an unchanged copy of its `tokens/tokens.json`; see LICENSE.

Run `python scripts/sync-playground-design.py` after updating the pinned tokens.
`--check` verifies the generated adapter and `www/playground-design.css`.
The stylesheet scopes the same tokens to the browser component experiences and
their top-layer dialogs, including both themes. The build embeds `stdlib/design.xu`.
Xu programs can select `playground.dark_theme()` / `light_theme()` for basic
controls, and `playground.dark_styles()` / `light_styles()` for styled controls.
Use `styles.background` to clear the canvas. Widgets still own state and input;
the Canvas host receives geometric drawing commands, without widget IDs.

The component experiences and gallery use the dark reference. The adapter maps
semantic colors, control height, padding, corner radii, and focus treatment.
Button, Checkbox, Switch, Radio, and Slider use desktop styled paint methods
for rounded borders, selection states, and focus. Their declarations and
dependencies load as a portable family when styled painting is requested.
Basic widgets continue to use their existing geometry, so this is not a claim
that every reference component has been ported. The legacy `ui-widgets`, drawing,
and counter examples retain their original editable themes.

The Canvas backing store follows device pixel density (bounded to 3x), keeping
640 x 360 logical drawing and hit-test coordinates. Clearing and resetting
transforms preserve that scale, so borders and curves stay sharp on HiDPI screens.

Text layout remains the bounded browser grid described in ../README.md; it does
not yet satisfy the reference typography contract. Native shaping/measurement,
editable text/IME, idle hover, animation, and per-widget accessibility remain
separate host work. The font tokens are retained in Styles for that integration;
the current browser text adapter does not honor font family or weight.
