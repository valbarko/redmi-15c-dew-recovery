import java.lang.reflect.*;

/**
 * Root-only overlays for the exact dew / Android 15 GSI case in docs/usb-display.md.
 * Original overlay transaction was device-tested; public profile guards were
 * added for publication and compile-checked only. No phone or binary is bundled.
 */
public final class RedmiDisplay {
  static Class<?> fo, oi, tb;
  static Object dim(Object overlay, String resource, float pixels, String config) throws Exception {
    fo.getMethod("setResourceValue", String.class, float.class, int.class, String.class)
      .invoke(overlay, resource, pixels, 0, config);
    return overlay;
  }
  static Object overlay(String name, String target) throws Exception {
    Object o = fo.getConstructor(String.class, String.class).newInstance(name, target);
    fo.getMethod("setOwningPackage", String.class).invoke(o, "com.android.shell");
    return o;
  }
  static String property(String name) throws Exception {
    return (String) Class.forName("android.os.SystemProperties")
      .getMethod("get", String.class).invoke(null, name);
  }
  static void requireProfile() throws Exception {
    if (!property("ro.product.device").equals("dew") &&
        !property("ro.product.vendor.device").equals("dew"))
      throw new SecurityException("Expected locally verified dew device");
    if (!property("ro.build.id").equals("BP1A.250405.005.C1") ||
        !property("ro.build.version.sdk").equals("35"))
      throw new SecurityException("Expected the documented Android 15 GSI build");
    Object displayManager = Class.forName("android.hardware.display.DisplayManagerGlobal")
      .getMethod("getInstance").invoke(null);
    Object display = displayManager.getClass().getMethod("getRealDisplay", int.class)
      .invoke(displayManager, 0);
    if (display == null) throw new SecurityException("No default display");
    Class<?> metricsClass = Class.forName("android.util.DisplayMetrics");
    Object metrics = metricsClass.getConstructor().newInstance();
    Class.forName("android.view.Display").getMethod("getRealMetrics", metricsClass)
      .invoke(display, metrics);
    int width = metricsClass.getField("widthPixels").getInt(metrics);
    int height = metricsClass.getField("heightPixels").getInt(metrics);
    int density = metricsClass.getField("densityDpi").getInt(metrics);
    if (width != 720 || height != 1600 || density != 320)
      throw new SecurityException("Expected portrait 720x1600 at density 320");
  }
  public static void main(String[] args) throws Exception {
    String mode = args.length == 1 ? args[0] : "check";
    if (!mode.equals("check") && !mode.equals("apply") && !mode.equals("remove"))
      throw new IllegalArgumentException("Expected check, apply, or remove");
    int uid = (Integer) Class.forName("android.os.Process").getMethod("myUid").invoke(null);
    if (uid != 0) throw new SecurityException("Root is required");
    if (!mode.equals("remove")) requireProfile();
    fo = Class.forName("android.content.om.FabricatedOverlay");
    oi = Class.forName("android.content.om.OverlayIdentifier");
    tb = Class.forName("android.content.om.OverlayManagerTransaction$Builder");
    fo.getMethod("setResourceValue", String.class, float.class, int.class, String.class);
    if (mode.equals("check")) { System.out.println("Documented profile and dimension overlay API available"); return; }
    Object transaction = tb.getConstructor().newInstance();
    if (mode.equals("apply")) {
      Object framework = overlay("Redmi15CDisplay", "android");
      dim(framework, "android:dimen/rounded_corner_radius", 86, null);
      dim(framework, "android:dimen/rounded_corner_radius_top", 86, null);
      dim(framework, "android:dimen/rounded_corner_radius_bottom", 86, null);
      dim(framework, "android:dimen/rounded_corner_content_padding", 40, null);
      dim(framework, "android:dimen/status_bar_height_default", 74, null);
      dim(framework, "android:dimen/status_bar_height_portrait", 74, null);
      fo.getMethod("setResourceValue", String.class, int.class, String.class, String.class)
        .invoke(framework, "android:string/config_mainBuiltInDisplayCutout", 3,
                "M 0,0 H -41 V 74 H 41 V 0 H 0 Z", null);
      Object sysui = overlay("Redmi15CStatusBar", "com.android.systemui");
      dim(sysui, "com.android.systemui:dimen/status_bar_padding_top", 16, "port");
      for (Object o : new Object[] {framework, sysui}) {
        tb.getMethod("registerFabricatedOverlay", fo).invoke(transaction, o);
        Object id = fo.getMethod("getIdentifier").invoke(o);
        tb.getMethod("setEnabled", oi, boolean.class, int.class).invoke(transaction, id, true, 0);
      }
    } else {
      for (String name : new String[] {"Redmi15CDisplay", "Redmi15CStatusBar"}) {
        Object id = oi.getConstructor(String.class, String.class).newInstance("com.android.shell", name);
        tb.getMethod("unregisterFabricatedOverlay", oi).invoke(transaction, id);
      }
    }
    Class<?> binder = Class.forName("android.os.IBinder");
    Object service = Class.forName("android.os.ServiceManager")
      .getMethod("getService", String.class).invoke(null, "overlay");
    Object manager = Class.forName("android.content.om.IOverlayManager$Stub")
      .getMethod("asInterface", binder).invoke(null, service);
    Object built = tb.getMethod("build").invoke(transaction);
    Class.forName("android.content.om.IOverlayManager")
      .getMethod("commit", Class.forName("android.content.om.OverlayManagerTransaction"))
      .invoke(manager, built);
    System.out.println("Redmi display overlays: " + mode);
  }
}
