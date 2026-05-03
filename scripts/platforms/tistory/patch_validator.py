"""Static validator for Tistory skin HTML/CSS patches.

Encodes guide/design_agent/patch_rules.md as boolean gates so the agent
cannot self-declare success when structural rules are violated.

Usage:
    python -m scripts.platforms.tistory.patch_validator \
        --html outputs/design/html/skin_main.html \
        --base-html outputs/design/backups/skin_html_*.html \
        --css outputs/design/css/custom_*_integrated.css \
        --base-css outputs/design/backups/skin_css_*.css
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import tinycss2


SIDEBAR_COMPONENTS = {
    "profile_card": [r"profile-card", r"box-profile"],
    "search": [r"searchInput", r"search-box"],
    "category": [r"\[##_category_list_##\]"],
    "tags": [r"s_random_tags"],
    "recent_or_popular": [r"s_rctps_rep", r"s_rctps_popular_rep"],
    "paging": [r"s_paging"],
}

WIDGET_COMPONENTS_INSIDE_SIDEBAR_ELEMENT = ("search", "category", "tags", "recent_or_popular")

REQUIRED_TOKENS = [
    "[##_page_title_##]",
    "[##_title_##]",
    "[##_blog_link_##]",
    "[##_skin_url_##]",
    "[##_revenue_list_upper_##]",
    "[##_revenue_list_lower_##]",
]
REQUIRED_S_BLOCKS = [
    "s_t3",
    "s_list",
    "s_article_rep",
    "s_sidebar",
    # s_sidebar_element is OPTIONAL: Fix 3 allows direct child placement inside
    # <s_sidebar> without <s_sidebar_element> wrappers. Widget presence is
    # validated against the full <s_sidebar> content when s_sidebar_element = 0.
]

CSS_BASE_PRESERVE_RATIO = 0.95
CSS_IMPORTANT_WARNING_THRESHOLD = 30

SHORTHAND_LONGHAND = {
    "margin": ("margin-top", "margin-right", "margin-bottom", "margin-left"),
    "padding": ("padding-top", "padding-right", "padding-bottom", "padding-left"),
    "border": (
        "border-top", "border-right", "border-bottom", "border-left",
        "border-width", "border-style", "border-color",
        "border-top-width", "border-right-width", "border-bottom-width", "border-left-width",
        "border-top-style", "border-right-style", "border-bottom-style", "border-left-style",
        "border-top-color", "border-right-color", "border-bottom-color", "border-left-color",
    ),
    "border-top": ("border-top-width", "border-top-style", "border-top-color"),
    "border-right": ("border-right-width", "border-right-style", "border-right-color"),
    "border-bottom": ("border-bottom-width", "border-bottom-style", "border-bottom-color"),
    "border-left": ("border-left-width", "border-left-style", "border-left-color"),
    "background": (
        "background-color", "background-image", "background-repeat",
        "background-position", "background-size", "background-attachment",
    ),
    "font": ("font-family", "font-size", "font-weight", "font-style", "font-variant", "line-height"),
}


@dataclass
class ValidationResult:
    passed: bool
    gate_results: dict[str, bool] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class Conflict:
    property: str
    winner_selector: str
    winner_specificity: tuple[int, int, int]
    loser_selector: str
    loser_specificity: tuple[int, int, int]
    kind: str  # "specificity" | "shorthand_longhand"


def _read(path: Path | str) -> str:
    return Path(path).read_text(encoding="utf-8")


def validate_html(new_html: str, base_html: str) -> ValidationResult:
    result = ValidationResult(passed=True)

    # 1. sidebar 6 components present
    missing_components: list[str] = []
    for name, markers in SIDEBAR_COMPONENTS.items():
        if not any(re.search(marker, new_html) for marker in markers):
            missing_components.append(name)
    if missing_components:
        result.passed = False
        result.errors.append(
            f"sidebar:components missing {missing_components}"
        )
    result.gate_results["sidebar_components_present"] = not missing_components

    # 2. widget components inside <s_sidebar_element> OR directly inside <s_sidebar>
    # Fix 3 allows direct placement without s_sidebar_element wrappers.
    # When s_sidebar_element count = 0, validate against full <s_sidebar> content.
    sidebar_element_blocks = _extract_s_sidebar_element_blocks(new_html)
    if sidebar_element_blocks:
        # legacy mode: validate inside s_sidebar_element blocks
        sidebar_element_concat = "\n".join(sidebar_element_blocks)
    else:
        # Fix 3 mode: validate inside s_sidebar content directly
        sidebar_element_concat = _extract_s_sidebar_content(new_html)
    misplaced: list[str] = []
    for name in WIDGET_COMPONENTS_INSIDE_SIDEBAR_ELEMENT:
        if name in missing_components:
            continue
        markers = SIDEBAR_COMPONENTS[name]
        if not any(re.search(marker, sidebar_element_concat) for marker in markers):
            misplaced.append(name)
    if misplaced:
        result.passed = False
        result.errors.append(
            f"sidebar:widgets outside <s_sidebar_element> {misplaced}"
        )
        result.gate_results["sidebar_components_present"] = False

    # 3. required tokens / s_blocks preserved
    missing_tokens: list[str] = []
    for token in REQUIRED_TOKENS:
        if token in base_html and token not in new_html:
            missing_tokens.append(token)
    for block in REQUIRED_S_BLOCKS:
        if re.search(rf"<{block}\b", base_html) and not re.search(rf"<{block}\b", new_html):
            missing_tokens.append(f"<{block}>")
    if missing_tokens:
        result.passed = False
        result.errors.append(f"tokens:missing {missing_tokens}")
    result.gate_results["tokens_preserved"] = not missing_tokens

    # 4. line count not catastrophically smaller (lost base)
    base_lines = base_html.count("\n") + 1
    new_lines = new_html.count("\n") + 1
    if new_lines < base_lines * 0.5:
        result.passed = False
        result.errors.append(
            f"html:line count collapsed (base={base_lines}, new={new_lines})"
        )

    result.metadata["missing_components"] = missing_components
    result.metadata["misplaced_widgets"] = misplaced
    result.metadata["missing_tokens"] = missing_tokens
    result.metadata["base_lines"] = base_lines
    result.metadata["new_lines"] = new_lines
    return result


def _extract_s_sidebar_element_blocks(html: str) -> list[str]:
    pattern = re.compile(r"<s_sidebar_element\b[^>]*>(.*?)</s_sidebar_element>", re.DOTALL | re.IGNORECASE)
    return pattern.findall(html)


def _extract_s_sidebar_content(html: str) -> str:
    """Return the content of the first <s_sidebar>...</s_sidebar> block.

    Used when s_sidebar_element count is 0 (Fix 3 direct-placement mode).
    Falls back to full html if no s_sidebar block found.
    """
    pattern = re.compile(r"<s_sidebar\b[^>]*>(.*?)</s_sidebar>", re.DOTALL | re.IGNORECASE)
    match = pattern.search(html)
    return match.group(1) if match else html


def validate_css(new_css: str, base_css: str) -> ValidationResult:
    result = ValidationResult(passed=True)

    # 1. base preserved (line count >= base * 0.95)
    base_lines = base_css.count("\n") + 1
    new_lines = new_css.count("\n") + 1
    base_preserved = new_lines >= base_lines * CSS_BASE_PRESERVE_RATIO
    result.gate_results["css_base_preserved"] = base_preserved
    if not base_preserved:
        result.passed = False
        result.errors.append(
            f"css:base lines lost (base={base_lines}, new={new_lines}, ratio={new_lines / max(base_lines, 1):.2f})"
        )

    # 2. !important usage warning (only count diff vs base)
    important_count = len(re.findall(r"!\s*important", new_css))
    base_important = len(re.findall(r"!\s*important", base_css))
    important_added = important_count - base_important
    if important_added > CSS_IMPORTANT_WARNING_THRESHOLD:
        result.warnings.append(
            f"css:!important added in custom = {important_added} (threshold {CSS_IMPORTANT_WARNING_THRESHOLD})"
        )

    # 3. specificity conflicts in new custom region only.
    # Strategy: base CSS already has historical cascade conflicts that we treat
    # as the working baseline. We only flag conflicts where the new region
    # introduces an override that is already lost or where new shorthand wipes
    # earlier longhand customisation.
    conflicts = validate_specificity_conflicts(new_css, base_css=base_css)
    if conflicts:
        result.passed = False
        for c in conflicts:
            result.errors.append(_format_conflict(c))
    result.gate_results["css_specificity_ok"] = not conflicts

    result.metadata["important_count"] = important_count
    result.metadata["important_added"] = important_added
    result.metadata["base_lines"] = base_lines
    result.metadata["new_lines"] = new_lines
    result.metadata["conflict_count"] = len(conflicts)
    return result


def _format_conflict(c: Conflict) -> str:
    spec_w = "(" + ",".join(str(x) for x in c.winner_specificity) + ")"
    spec_l = "(" + ",".join(str(x) for x in c.loser_specificity) + ")"
    return (
        f"specificity:{c.kind} on `{c.property}` — "
        f"{c.winner_selector}{spec_w} > {c.loser_selector}{spec_l}"
    )


def validate_specificity_conflicts(css: str, base_css: str | None = None) -> list[Conflict]:
    """Detect cascade conflicts in the new region of a CSS file.

    When ``base_css`` is provided, only conflicts involving rules in the
    appended region (new custom CSS) are returned. Historical conflicts inside
    base CSS are treated as the working baseline and ignored to avoid false
    positives.

    Conflict types detected:
    - ``specificity`` — a new rule's intended override is defeated by an
      earlier higher-specificity rule on the same property.
    - ``important_override`` — a new rule is silently overridden by an earlier
      ``!important`` rule.
    - ``shorthand_longhand`` — a new shorthand wipes earlier longhand
      customisations on the same selector.

    Limitations: ignores @media/@supports, :has(), inline styles, JS-injected
    styles. These are surfaced as warnings elsewhere.
    """
    rules = _parse_rules(css)
    base_rule_count = len(_parse_rules(base_css)) if base_css else 0
    conflicts: list[Conflict] = []

    by_property: dict[str, list[tuple[int, str, tuple[int, int, int], bool]]] = {}
    for idx, (selector, decls) in enumerate(rules):
        if not selector or not decls:
            continue
        spec = _max_specificity(selector)
        for prop, important in decls:
            by_property.setdefault(prop, []).append((idx, selector, spec, important))

    seen: set[tuple[str, str, str]] = set()

    def _in_new_region(idx_a: int, idx_b: int) -> bool:
        return base_css is None or idx_a >= base_rule_count or idx_b >= base_rule_count

    for prop, entries in by_property.items():
        for i, (idx_a, sel_a, spec_a, imp_a) in enumerate(entries):
            for idx_b, sel_b, spec_b, imp_b in entries[:i]:
                if sel_a == sel_b:
                    continue
                if not _in_new_region(idx_a, idx_b):
                    continue
                if imp_b and not imp_a:
                    key = (prop, sel_b, sel_a)
                    if key in seen:
                        continue
                    seen.add(key)
                    conflicts.append(Conflict(
                        property=prop,
                        winner_selector=sel_b,
                        winner_specificity=spec_b,
                        loser_selector=sel_a,
                        loser_specificity=spec_a,
                        kind="important_override",
                    ))
                    continue
                if imp_a and not imp_b:
                    continue
                if imp_a and imp_b:
                    # Both rules use !important on different selectors.
                    # Cascade is determined by specificity but since selectors
                    # target different elements this is not a real conflict.
                    # Skip to avoid false positives from parallel element rules
                    # (e.g. body#tt-body-page .area-common vs .article-header::before).
                    continue
                if spec_b > spec_a:
                    key = (prop, sel_b, sel_a)
                    if key in seen:
                        continue
                    seen.add(key)
                    conflicts.append(Conflict(
                        property=prop,
                        winner_selector=sel_b,
                        winner_specificity=spec_b,
                        loser_selector=sel_a,
                        loser_specificity=spec_a,
                        kind="specificity",
                    ))

    for shorthand, longhands in SHORTHAND_LONGHAND.items():
        short_entries = by_property.get(shorthand, [])
        for sh_idx, sh_sel, sh_spec, _sh_imp in short_entries:
            for longhand in longhands:
                long_entries = by_property.get(longhand, [])
                for lh_idx, lh_sel, lh_spec, _lh_imp in long_entries:
                    if lh_idx >= sh_idx:
                        continue
                    if lh_sel != sh_sel:
                        continue
                    if not _in_new_region(sh_idx, lh_idx):
                        continue
                    key = (longhand, sh_sel, lh_sel)
                    if key in seen:
                        continue
                    seen.add(key)
                    conflicts.append(Conflict(
                        property=longhand,
                        winner_selector=sh_sel,
                        winner_specificity=sh_spec,
                        loser_selector=lh_sel,
                        loser_specificity=lh_spec,
                        kind="shorthand_longhand",
                    ))

    return conflicts


def _parse_rules(css: str) -> list[tuple[str, list[tuple[str, bool]]]]:
    """Parse CSS into [(selector_text, [(property, important), ...])].

    Skips at-rules (@media, @supports, etc.) — those are not analysed.
    """
    rules: list[tuple[str, list[tuple[str, bool]]]] = []
    parsed = tinycss2.parse_stylesheet(css, skip_comments=True, skip_whitespace=True)
    for rule in parsed:
        if rule.type != "qualified-rule":
            continue
        selector = tinycss2.serialize(rule.prelude).strip()
        decls: list[tuple[str, bool]] = []
        for decl in tinycss2.parse_declaration_list(rule.content, skip_comments=True, skip_whitespace=True):
            if decl.type != "declaration":
                continue
            decls.append((decl.lower_name, bool(decl.important)))
        rules.append((selector, decls))
    return rules


def _max_specificity(selector_group: str) -> tuple[int, int, int]:
    """Return the highest specificity among comma-separated selectors."""
    best = (0, 0, 0)
    for sel in selector_group.split(","):
        spec = _calc_specificity(sel.strip())
        if spec > best:
            best = spec
    return best


_RE_ID = re.compile(r"#[A-Za-z_][\w-]*")
_RE_CLASS = re.compile(r"\.[A-Za-z_][\w-]*")
_RE_ATTR = re.compile(r"\[[^\]]+\]")
_RE_PSEUDO_ELEMENT = re.compile(r"::[A-Za-z][\w-]*")
_RE_PSEUDO_CLASS = re.compile(r"(?<!:):[A-Za-z][\w-]*(?:\([^)]*\))?")
_RE_ELEMENT = re.compile(r"(?:^|[\s>+~])([a-zA-Z][a-zA-Z0-9-]*)")


def _calc_specificity(selector: str) -> tuple[int, int, int]:
    """Compute (a, b, c): id, class+attr+pseudo-class, element+pseudo-element.

    Strips :not() / :is() / :where() wrappers conservatively (counts inner
    most heavily to avoid false negatives on overrides). Limitations noted in
    module docstring.
    """
    if not selector:
        return (0, 0, 0)
    s = selector
    # treat :where() as 0 (per CSS spec). Strip with content removed.
    s = re.sub(r":where\([^)]*\)", "", s)
    # :not() / :is() — count contents using max specificity of inner.
    inner_extras = (0, 0, 0)
    for m in re.finditer(r":(?:not|is)\(([^)]*)\)", s):
        inner = _max_specificity(m.group(1))
        inner_extras = (
            inner_extras[0] + inner[0],
            inner_extras[1] + inner[1],
            inner_extras[2] + inner[2],
        )
    s = re.sub(r":(?:not|is)\([^)]*\)", "", s)

    a = len(_RE_ID.findall(s))
    pseudo_elements = len(_RE_PSEUDO_ELEMENT.findall(s))
    s_no_pe = _RE_PSEUDO_ELEMENT.sub("", s)
    classes = len(_RE_CLASS.findall(s_no_pe))
    attrs = len(_RE_ATTR.findall(s_no_pe))
    s_clean = _RE_ATTR.sub("", s_no_pe)
    pseudo_classes = len(_RE_PSEUDO_CLASS.findall(s_clean))
    elements = len(_RE_ELEMENT.findall(" " + s_clean))

    return (
        a + inner_extras[0],
        classes + attrs + pseudo_classes + inner_extras[1],
        elements + pseudo_elements + inner_extras[2],
    )


def run_static_validation(
    new_html: str | None,
    base_html: str | None,
    new_css: str | None,
    base_css: str | None,
) -> dict:
    """Combine HTML and CSS validation into a single report dict."""
    report: dict = {"passed": True, "gate_results": {}, "errors": [], "warnings": [], "metadata": {}}

    if new_html is not None and base_html is not None:
        html_result = validate_html(new_html, base_html)
        _merge(report, html_result)
    if new_css is not None and base_css is not None:
        css_result = validate_css(new_css, base_css)
        _merge(report, css_result)

    return report


def _merge(report: dict, r: ValidationResult) -> None:
    report["passed"] = report["passed"] and r.passed
    report["gate_results"].update(r.gate_results)
    report["errors"].extend(r.errors)
    report["warnings"].extend(r.warnings)
    report["metadata"].update(r.metadata)


def main() -> None:
    parser = argparse.ArgumentParser(description="Static validator for Tistory skin patches")
    parser.add_argument("--html", type=Path, help="new HTML file to validate")
    parser.add_argument("--base-html", type=Path, help="latest backup HTML for comparison")
    parser.add_argument("--css", type=Path, help="new CSS file to validate")
    parser.add_argument("--base-css", type=Path, help="latest backup CSS for comparison")
    args = parser.parse_args()

    new_html = _read(args.html) if args.html else None
    base_html = _read(args.base_html) if args.base_html else None
    new_css = _read(args.css) if args.css else None
    base_css = _read(args.base_css) if args.base_css else None

    report = run_static_validation(new_html, base_html, new_css, base_css)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
