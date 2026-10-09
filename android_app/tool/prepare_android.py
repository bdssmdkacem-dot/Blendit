from pathlib import Path

manifest = Path("android/app/src/main/AndroidManifest.xml")
if not manifest.is_file():
    raise SystemExit("Android manifest not found. Run flutter create --platforms=android . first.")

text = manifest.read_text(encoding="utf-8")
if "android:usesCleartextTraffic=" not in text:
    marker = "<application"
    if marker not in text:
        raise SystemExit("Could not find the application tag in AndroidManifest.xml.")
    text = text.replace(marker, marker + ' android:usesCleartextTraffic="true"', 1)
    manifest.write_text(text, encoding="utf-8")
print("Prepared Android manifest for the local HTTP bridge.")
print("Use only on a trusted private network; never expose the bridge to the public internet.")
