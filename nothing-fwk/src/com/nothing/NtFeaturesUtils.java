/*
 * Copyright (C) 2024-2026 The LineageOS Project
 * SPDX-License-Identifier: Apache-2.0
 */

package com.nothing;

import android.os.Build;
import android.os.SystemProperties;

import java.math.BigInteger;
import java.util.BitSet;

public class NtFeaturesUtils {

    // Read by name through reflection in Nothing Camera
    public static final int NTF_QCOM = 59;
    public static final int NTF_MTK = 60;
    public static final int NTF_PONG = 62;
    public static final int NTF_PACMAN = 63;
    public static final int NTF_TETRIS = 64;
    public static final int NTF_ASTEROIDS = 80;
    public static final int NTF_ASTEROIDS_PLUS = 86;
    public static final int NTF_JPN = 89;
    public static final int NTF_DRAGONITE = 110;
    public static final int NTF_BACKGROUND_RES_LIMIT = 115;

    private static final int MAX_FEATURES = 160;

    private static final BitSet sFeatures = new BitSet(MAX_FEATURES);

    static {
        final String fullProp = getFeatureProp("base");
        final String productDiffProp = getFeatureProp("diff.product." + Build.PRODUCT);
        String deviceDiffProp = getFeatureProp("diff.device." + Build.DEVICE);
        if ("0".equals(deviceDiffProp)) {
            deviceDiffProp = getFeatureProp("diff.device.Asteroids");
        }
        String plusDiffProp = getFeatureProp("diff.plus." + Build.DEVICE);
        if ("0".equals(plusDiffProp)) {
            plusDiffProp = getFeatureProp("diff.plus.Asteroids");
        }
        final String cmfDiffProp = getFeatureProp("diff.os.cmf");
        final String configCustomProp = SystemProperties.get("persist.sys.config.custom", "0");
        final String customProp = SystemProperties.get("persist.custom", "0");

        base(new BigInteger(replace(fullProp), 16));
        change(new BigInteger(replace(productDiffProp), 16));
        change(new BigInteger(replace(deviceDiffProp), 16));
        change(new BigInteger(replace(configCustomProp), 16));
        if ("pro".equalsIgnoreCase(SystemProperties.get("ro.boot.pbid", "base"))) {
            change(new BigInteger(replace(plusDiffProp), 16));
        }
        if ("true".equalsIgnoreCase(SystemProperties.get("ro.product.os.cmf", "false"))) {
            change(new BigInteger(replace(cmfDiffProp), 16));
        }
        change(new BigInteger(replace(customProp), 16));
    }

    public static boolean isSupport(int... features) {
        for (int feature : features) {
            if (feature < 0 || feature >= MAX_FEATURES) {
                return false;
            }
            if (!sFeatures.get(feature)) {
                return false;
            }
        }
        return true;
    }

    private static void base(BigInteger feature) {
        for (int i = 0; i < feature.bitLength(); i++) {
            if (feature.testBit(i)) {
                sFeatures.set(i);
            }
        }
    }

    private static void change(BigInteger feature) {
        for (int i = 0; i < feature.bitLength(); i++) {
            if (feature.testBit(i)) {
                sFeatures.flip(i);
            }
        }
    }

    private static String replace(String str) {
        if (str == null || str.isEmpty()) {
            return "0";
        }
        return str.replace("0x", "").replace("L", "");
    }

    private static String getFeatureProp(String suffix) {
        String prop = SystemProperties.get("ro.build.nothing.feature." + suffix, "");
        if (prop.isEmpty() || "0".equals(prop)) {
            prop = SystemProperties.get("ro.vendor.nothing.feature." + suffix, "0");
        }
        return prop;
    }
}
