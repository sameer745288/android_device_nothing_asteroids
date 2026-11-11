#!/usr/bin/env python3
"""LineageOS 24 Asteroids V7: standalone Updater-style banner item.

The SettingsLib expressive adapter normally applies a grey grouped background
AFTER Preference.onBindViewHolder(). V7 uses the public marker interfaces that
mark a Preference as a self-styled group divider, so its root is unadorned and
Compose owns the *entire* teal card, including all four corners.

Run from the Android source root. This device-tree-owned installer is idempotent,
and never modifies packages/apps/Updater. It copies Updater's current AGSL shader
and vector mark into Settings to keep the actual teal/header artwork in sync.
"""
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

root = Path.cwd()
settings = root / 'packages/apps/Settings'
updater = root / 'packages/apps/Updater'
fragment = settings / 'src/com/android/settings/deviceinfo/firmwareversion/FirmwareVersionSettings.java'
source = updater / 'app/src/main/java/org/lineageos/updater/deviceinfo/UpdaterCard.kt'
mark_source = updater / 'app/src/main/res/drawable/lineage_mark_tight.xml'
new_pref = settings / 'src/com/android/settings/deviceinfo/firmwareversion/LineageVersionBannerPreference.kt'
old_pref = new_pref.with_suffix('.java')
for p in (fragment, source, mark_source, root / 'device/nothing/asteroids'):
    if not p.is_file() and not p.is_dir():
        sys.exit(f'ERROR: Required source missing: {p}')

# Refuse silently incompatible SettingsLib branches rather than reverting to
# V6's nested card behavior. The adapter and markers are from the LOS24 tree.
adapter = root / 'frameworks/base/packages/SettingsLib/SettingsTheme/src/com/android/settingslib/widget/SettingsPreferenceGroupAdapter.kt'
mixin = root / 'frameworks/base/packages/SettingsLib/SettingsTheme/src/com/android/settingslib/widget/GroupSectionDividerMixin.kt'
normal_mixin = root / 'frameworks/base/packages/SettingsLib/SettingsTheme/src/com/android/settingslib/widget/NormalPaddingMixin.kt'
for required in (adapter, mixin, normal_mixin):
    if not required.is_file():
        sys.exit(f'ERROR: Missing SettingsLib source; refusing V7: {required}')
if 'is GroupSectionDividerMixin' not in adapter.read_text():
    sys.exit('ERROR: SettingsLib adapter behavior changed; refusing V7')

src = source.read_text()
match = re.search(r'private const val PATTERN_SHADER_SRC\s*=\s*"""(.*?)"""', src, re.S)
if not match:
    sys.exit('ERROR: Updater shader source changed. No changes applied.')
shader = match.group(1)
frag = fragment.read_text()
marker = 'new LineageVersionBannerPreference(requireContext())'
if marker not in frag:
    needle = '    @Override\n    protected int getPreferenceScreenResId() {'
    if frag.count(needle) != 1:
        sys.exit('ERROR: FirmwareVersionSettings API differs. No changes applied.')
    frag = frag.replace(needle, '''    // Device-tree customization: the genuine Updater-style header, in Settings only.
    @Override
    public void onCreatePreferences(android.os.Bundle savedInstanceState, String rootKey) {
        super.onCreatePreferences(savedInstanceState, rootKey);
        final androidx.preference.PreferenceScreen screen = getPreferenceScreen();
        if (screen != null && screen.findPreference("lineage_custom_version_banner") == null) {
            screen.addPreference(new LineageVersionBannerPreference(requireContext()));
        }
    }

''' + needle, 1)

# Get colours from the Updater's own values resources when available; fallbacks
# are pixel-matched to the photographed Updater teal, not the old V5 green.
color_fallbacks = {
    'brand_primary': 'FF167C80',
    'on_brand_surface': 'FFFFFFFF',
    'brand_pattern': 'FFFFFFFF',
    'brand_sheen': 'FFAEF4EF',
}
colors = {}
for xmlpath in (updater / 'app/src/main/res').glob('values*/**/*.xml'):
    try:
        doc = ET.parse(xmlpath).getroot()
    except ET.ParseError:
        continue
    for node in doc:
        if node.tag == 'color' or (node.tag == 'item' and node.attrib.get('type') == 'color'):
            name = node.attrib.get('name')
            if name in color_fallbacks and node.text and node.text.strip().startswith('#'):
                text = node.text.strip()[1:]
                if re.fullmatch(r'[0-9a-fA-F]{6}', text):
                    text = 'FF' + text
                if re.fullmatch(r'[0-9a-fA-F]{8}', text):
                    # Prefer values/ over values-night for consistent brand colours.
                    if name not in colors or xmlpath.parent.name == 'values':
                        colors[name] = text.upper()
for name, fallback in color_fallbacks.items():
    colors.setdefault(name, fallback)

# The original Updater shader/logo/version geometry is retained. Unlike V6,
# this preference is marked as a self-styled standalone group divider so the
# Settings expressive adapter does NOT add its grey background or row padding.
# The Compose container supplies Updater's own outer itemPadding and 16dp
# uniform content padding exactly once.
kotlin = r'''/*
 * SPDX-FileCopyrightText: The LineageOS Project
 * SPDX-License-Identifier: Apache-2.0
 *
 * Adapted from packages/apps/Updater/.../UpdaterCard.kt for Settings only.
 */
package com.android.settings.deviceinfo.firmwareversion

import android.content.Context
import android.graphics.RuntimeShader
import android.os.SystemProperties
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.drawWithCache
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.ColorFilter
import androidx.compose.ui.graphics.ShaderBrush
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.ComposeView
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.ViewCompositionStrategy
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.em
import androidx.compose.ui.unit.sp
import androidx.preference.Preference
import androidx.preference.PreferenceViewHolder
import com.android.settings.R
import com.android.settingslib.spa.framework.theme.SettingsDimension
import com.android.settingslib.spa.framework.theme.SettingsShape.CornerExtraLarge1
import com.android.settingslib.widget.GroupSectionDividerMixin
import com.android.settingslib.widget.NormalPaddingMixin
import com.android.settingslib.spa.framework.theme.SettingsSpace
import com.android.settingslib.spa.framework.theme.SettingsTheme
import kotlin.math.max
import kotlin.math.roundToInt

// Original Updater ratios; not approximations.
private const val MARK_X_HEIGHT_RATIO = 0.55f
private const val MARK_WIDTH_MULTIPLIER = 2.5f
private const val VERSION_MARK_SPACING_RATIO = 0.10f
private const val PATTERN_BASE_RADIUS_DP = 25
private const val PATTERN_TILE_RADIUS_RATIO = 6f

private const val PATTERN_SHADER_SRC = """__UPDATER_SHADER__"""

// Self-styled standalone item. These SettingsLib markers tell its adapter to
// omit the normal rounded grey row background and the grouped row padding.
class LineageVersionBannerPreference(context: Context) : Preference(context),
    GroupSectionDividerMixin, NormalPaddingMixin {
    init {
        key = "lineage_custom_version_banner"
        layoutResource = R.layout.lineage_version_banner_item
        order = -10000
        isSelectable = false
        isPersistent = false
        isIconSpaceReserved = false
    }

    override fun onBindViewHolder(holder: PreferenceViewHolder) {
        super.onBindViewHolder(holder)
        holder.isDividerAllowedAbove = false
        holder.isDividerAllowedBelow = false
        (holder.itemView as ComposeView).apply {
            // Initial state: the adapter runs after this method and recognizes
            // GroupSectionDividerMixin, so it clears the root background as well.
            setPadding(0, 0, 0, 0)
            background = null
            elevation = 0f
            clipToPadding = false
            setViewCompositionStrategy(ViewCompositionStrategy.DisposeOnViewTreeLifecycleDestroyed)
            setContent {
                SettingsTheme {
                    val buildVersion = SystemProperties.get("ro.lineage.build.version", "24.0")
                        .ifEmpty { "24.0" }
                    LineageUpdaterStyleCard(buildVersion)
                }
            }
        }
    }
}

@Composable
private fun LineageUpdaterStyleCard(buildVersion: String) {
    val brandColor = Color(0x__BRAND_PRIMARY__)
    val onBrandColor = Color(0x__ON_BRAND_SURFACE__)
    val patternColor = Color(0x__BRAND_PATTERN__)
    val sheenColor = Color(0x__BRAND_SHEEN__)
    val density = LocalDensity.current
    val displayLarge = MaterialTheme.typography.displayLarge
    val versionStyle = remember(displayLarge) {
        displayLarge.copy(
            fontFamily = FontFamily.SansSerif,
            fontWeight = FontWeight.Light,
            letterSpacing = (-0.08).em,
            lineHeight = displayLarge.fontSize,
        )
    }
    val markHeight = remember(versionStyle, density) {
        with(density) { (versionStyle.fontSize.toPx() * MARK_X_HEIGHT_RATIO).toDp() }
    }
    val markWidth = markHeight * MARK_WIDTH_MULTIPLIER
    Card(
        // Updater's itemPadding is the OUTER inset, not a second grey card.
        modifier = Modifier.fillMaxWidth().padding(SettingsDimension.itemPadding),
        // Standalone row: round all four corners (unlike Updater + action buttons).
        shape = CornerExtraLarge1,
        colors = CardDefaults.cardColors(
            containerColor = Color.Transparent,
            contentColor = onBrandColor,
        ),
    ) {
        Box(
            modifier = Modifier.fillMaxWidth().background(brandColor).updaterHeaderPattern(
                patternColor = patternColor, sheenColor = sheenColor,
            ),
        ) {
            // Equal 16dp Updater padding on all four INSIDE edges, applied ONCE.
            Column(
                modifier = Modifier.fillMaxWidth()
                    .padding(SettingsDimension.paddingLarge),
            ) {
                // Ported directly from Updater's mark + 24.0 header.
                Row(modifier = Modifier.fillMaxWidth()) {
                    Image(
                        painter = painterResource(R.drawable.lineage_version_banner_mark),
                        contentDescription = stringResource(R.string.lineage_version_banner_logo),
                        modifier = Modifier.width(markWidth).alignBy { it.measuredHeight },
                        contentScale = ContentScale.FillWidth,
                        colorFilter = ColorFilter.tint(onBrandColor),
                    )
                    Spacer(modifier = Modifier.width(markWidth * VERSION_MARK_SPACING_RATIO))
                    Text(
                        text = buildVersion,
                        style = versionStyle,
                        color = onBrandColor,
                        modifier = Modifier.alignByBaseline(),
                    )
                }
                Spacer(modifier = Modifier.height(SettingsSpace.medium5))
                // Two-line credit with a deliberate 2dp gap; card height stays
                // content-driven exactly like Updater (no fixed height).
                Column(
                    modifier = Modifier.fillMaxWidth(),
                    verticalArrangement = Arrangement.spacedBy(2.dp),
                ) {
                    Text(
                        text = stringResource(R.string.lineage_version_banner_byline),
                        style = MaterialTheme.typography.titleSmall.copy(
                            fontWeight = FontWeight.Normal,
                            fontSize = 14.sp,
                            lineHeight = 18.sp,
                        ),
                        color = onBrandColor,
                    )
                    Text(
                        text = stringResource(R.string.lineage_version_banner_author),
                        style = MaterialTheme.typography.titleLarge.copy(
                            fontWeight = FontWeight.Medium,
                            fontSize = 22.sp,
                            lineHeight = 26.sp,
                        ),
                        color = onBrandColor,
                    )
                }
            }
        }
    }
}

// Same AGSL tiling and pattern rendering as the original UpdaterCard.kt.
private fun Modifier.updaterHeaderPattern(patternColor: Color, sheenColor: Color): Modifier =
    drawWithCache {
        val baseRadiusPx = PATTERN_BASE_RADIUS_DP.dp.toPx()
        val radiusSteps = max(1, (size.height / baseRadiusPx).roundToInt())
        val radiusPx = size.height / radiusSteps
        val tileSizePx = radiusPx * PATTERN_TILE_RADIUS_RATIO
        val shader = RuntimeShader(PATTERN_SHADER_SRC).apply {
            setFloatUniform("iTileSize", tileSizePx)
            setFloatUniform("iRadius", radiusPx)
            setFloatUniform("iResolution", size.width, size.height)
            setColorUniform("iPatternColor", patternColor.toArgb())
            setColorUniform("iSheenColor", sheenColor.toArgb())
        }
        val brush = ShaderBrush(shader)
        onDrawBehind { drawRect(brush) }
    }
'''
kotlin = kotlin.replace('__UPDATER_SHADER__', shader)
for name, value in colors.items():
    kotlin = kotlin.replace('__' + name.upper() + '__', value)
if '__' in kotlin:
    # Unexpanded special placeholders are installer errors; never write partial Kotlin.
    if re.search(r'__[A-Z_]+__', kotlin):
        sys.exit('ERROR: Unexpanded Kotlin template value; nothing modified.')

strings = '''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="lineage_version_banner_logo">LineageOS</string>
    <string name="lineage_version_banner_byline">Built with love by</string>
    <string name="lineage_version_banner_author">Sameer</string>
</resources>
'''
# A dedicated root item avoids inheriting the ordinary Preference row layout.
# SettingsLib sees the marker interfaces and assigns no grouped grey background.
item_layout = '''<?xml version="1.0" encoding="utf-8"?>
<androidx.compose.ui.platform.ComposeView
    xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="wrap_content" />
'''

out = {
    fragment: frag,
    new_pref: kotlin,
    settings / 'res/layout/lineage_version_banner_item.xml': item_layout,
    settings / 'res/values/lineage_version_banner_strings.xml': strings,
    settings / 'res/drawable/lineage_version_banner_mark.xml': mark_source.read_text(),
}
# No Updater file is ever written.
for path, content in out.items():
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.read_text() != content:
        path.write_text(content)
        print('Updated:', path.relative_to(root))
    else:
        print('Already current:', path.relative_to(root))

# V5's Java implementation has the same class name; it cannot coexist.
if old_pref.exists():
    old_pref.unlink()
    print('Removed obsolete V5 class:', old_pref.relative_to(root))
for obsolete in (
    settings / 'res/layout/lineage_version_banner.xml',
    settings / 'res/raw/lineage_version_banner_pattern.txt',
):
    if obsolete.exists():
        obsolete.unlink()
        print('Removed obsolete V5 resource:', obsolete.relative_to(root))

print('V7 installed: standalone teal item; equal inner padding; Updater intrinsic height; Sameer 22sp Medium.')
print('Updater app remains untouched. Colours:', colors)
